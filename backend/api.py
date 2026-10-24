"""
FastAPI application defining the endpoints for the Web Dashboard.

ARCHITECTURE OVERVIEW:
The API runs via Uvicorn in the main process. Every config change goes through the
`StateStore` (backend/state.py), which validates it, publishes it to the render
process and schedules a debounced save. Handlers never touch the disk directly, so
slow SD card writes can't delay a response or the display.

SECURITY:
The dashboard is served from this same origin, so browsers need no CORS access.
Cross-origin browser writes are rejected (a web page you visit must not be able to
drive the display), and the Spotify client secret is never returned by the API.
Requests without an Origin header (curl, Home Assistant, scripts) are unaffected.
"""

import asyncio
import io
import os
from contextlib import asynccontextmanager
from typing import Literal
from urllib.parse import urlsplit

from fastapi import Body, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from backend.config import PublicConfig
from backend.settings import env, resolve_path
from backend.spotify_manager import get_auth_manager
from backend.state import ConfigError

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
STREAM_FPS = 15
STREAM_KEEPALIVE_S = 1.0


class NoCacheHTMLMiddleware:
    """Prevent browsers from caching index.html so deploys are always picked up."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "") if scope["type"] == "http" else ""
        if path != "/" and not path.endswith(".html"):
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers += [
                    (b"cache-control", b"no-cache, no-store, must-revalidate"),
                    (b"pragma", b"no-cache"),
                    (b"expires", b"0"),
                ]
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)


class SameOriginWritesMiddleware:
    """Reject state-changing browser requests that come from another origin (CSRF)."""

    def __init__(self, app, allowed_origins=()):
        self.app = app
        self.allowed = frozenset(allowed_origins)

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] == "http"
            and scope["method"] not in SAFE_METHODS
            and scope["path"].startswith("/api/")
        ):
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode("latin-1")
            host = headers.get(b"host", b"").decode("latin-1")
            if (
                origin
                and origin not in self.allowed
                and urlsplit(origin).netloc != host
            ):
                response = JSONResponse(
                    {"detail": "Cross-origin requests are not allowed"}, status_code=403
                )
                return await response(scope, receive, send)
        await self.app(scope, receive, send)


class PreviewEncoder:
    """JPEG-encodes the latest frame once, however many dashboards are watching."""

    def __init__(self, frames):
        self.frames = frames
        self._seq = 0
        self._jpeg = b""

    def latest(self):
        seq = self.frames.seq
        if seq != self._seq:
            seq, raw = self.frames.read()
            if raw:
                buf = io.BytesIO()
                Image.frombytes("RGB", (64, 64), raw).save(
                    buf, format="JPEG", quality=75
                )
                self._jpeg = buf.getvalue()
            self._seq = seq
        return self._seq, self._jpeg


class StopwatchAction(BaseModel):
    action: Literal["start", "stop", "reset"]


class SpotifyAuthRequest(BaseModel):
    client_id: str
    client_secret: str


class SpotifyCallbackRequest(BaseModel):
    client_id: str
    client_secret: str
    url: str


def _cors_origins():
    raw = env("WAVEDISP_CORS_ORIGINS", "")
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def create_app(store, frames=None, dashboard_dist=None):
    @asynccontextmanager
    async def lifespan(_app):
        yield
        store.saver.flush()  # don't lose a debounced save on shutdown

    app = FastAPI(title="WaveDisp", lifespan=lifespan)
    cors_origins = _cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(SameOriginWritesMiddleware, allowed_origins=cors_origins)
    app.add_middleware(NoCacheHTMLMiddleware)

    encoder = PreviewEncoder(frames) if frames is not None else None

    def ok(version):
        return {"status": "success", "version": version}

    @app.get("/api/config", response_model=PublicConfig)
    def get_config(response: Response):
        """Retrieve the current matrix configuration state."""
        response.headers["X-Config-Version"] = str(store.version)
        return store.public_config()

    @app.get("/api/version")
    def get_version():
        """Cheap change detection for dashboards: bumps on every state change."""
        return {"version": store.version}

    @app.post("/api/config")
    def update_config(new_config: PublicConfig):
        """Replace the full public config. Read-only keys are ignored."""
        try:
            return ok(store.replace(new_config.model_dump()))
        except ConfigError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.patch("/api/config")
    def patch_config(patch_data: dict = Body(...)):
        """Update only the given keys, validated against the full config schema."""
        try:
            return ok(store.patch(patch_data))
        except ConfigError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/stream")
    async def stream_matrix():
        """MJPEG stream of the matrix framebuffer."""
        if encoder is None:
            raise HTTPException(status_code=503, detail="Preview unavailable")

        async def frames_gen():
            last_seq = None
            last_sent = 0.0
            loop = asyncio.get_running_loop()
            while True:
                seq, jpeg = encoder.latest()
                now = loop.time()
                # Send new frames, and repeat the last one periodically so a static
                # display (e.g. a clock between seconds) still renders in browsers.
                if jpeg and (seq != last_seq or now - last_sent >= STREAM_KEEPALIVE_S):
                    yield (
                        b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                        + str(len(jpeg)).encode()
                        + b"\r\n\r\n"
                        + jpeg
                        + b"\r\n"
                    )
                    last_seq, last_sent = seq, now
                await asyncio.sleep(1.0 / STREAM_FPS)

        return StreamingResponse(
            frames_gen(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )

    @app.post("/api/stopwatch")
    def update_stopwatch(payload: StopwatchAction):
        """Handle precise start/stop/reset actions for the stopwatch."""
        return ok(store.stopwatch(payload.action))

    @app.post("/api/spotify/auth_url")
    def get_spotify_auth_url(payload: SpotifyAuthRequest):
        auth_manager = get_auth_manager(payload.client_id, payload.client_secret)
        return {"url": auth_manager.get_authorize_url()}

    @app.post("/api/spotify/callback")
    def handle_spotify_callback(payload: SpotifyCallbackRequest):
        try:
            auth_manager = get_auth_manager(payload.client_id, payload.client_secret)
            code = auth_manager.parse_response_code(payload.url)
            if code and code != payload.url:
                auth_manager.get_access_token(code, as_dict=False)
                return ok(
                    store.set_spotify_link(
                        payload.client_id, payload.client_secret, True
                    )
                )
        except Exception as e:  # pylint: disable=broad-exception-caught
            return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
        return JSONResponse(
            {"status": "error", "message": "Invalid callback URL"}, status_code=400
        )

    @app.post("/api/spotify/unlink")
    def unlink_spotify():
        return ok(store.set_spotify_link("", "", False))

    @app.post("/api/presets/save/{slot_id}")
    def save_preset(slot_id: str):
        try:
            return ok(store.save_preset(slot_id))
        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/presets/load/{slot_id}")
    def load_preset(slot_id: str):
        try:
            if not store.load_preset(slot_id):
                raise HTTPException(status_code=404, detail="Preset is empty")
        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return ok(store.version)

    # Serve dashboard statically when the Vite build output exists.
    dist = dashboard_dist or resolve_path(
        env("WAVEDISP_DASHBOARD_DIST", "dashboard/dist")
    )
    if os.path.isdir(dist):
        app.mount("/", StaticFiles(directory=dist, html=True), name="static")

    return app
