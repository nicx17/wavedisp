"""
FastAPI application defining the endpoints for the Web Dashboard.

ARCHITECTURE OVERVIEW:
The API runs via Uvicorn in the main application thread. It exposes GET and POST endpoints to interface with the web dashboard.
It modifies a single global `config_state` object which is simultaneously read by the `matrix_controller` thread.

LOCKING & PERFORMANCE:
To prevent race conditions, `state_lock` (a threading.Lock) is used.
CRITICAL: When the `update_config` POST route receives new data, it locks the state, updates memory, and immediately UNLOCKS.
It only calls `config_state.save()` AFTER the lock is released. Because SD card I/O is very slow (tens of milliseconds), keeping the lock during file saving would cause the LED matrix thread to stall and skip frames, resulting in visible visual stutter.
"""

import os
import time

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import ConfigModel, save_debounced
from backend.settings import env, resolve_path
from backend.spotify_manager import get_auth_manager

app = FastAPI()


class NoCacheHTMLMiddleware(BaseHTTPMiddleware):
    """Prevent browsers from caching index.html so deploys are always picked up."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheHTMLMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

shared_state = None
shared_lock = None
dirty_flag = None


def set_shared_state(state, lock, flag=None):
    global shared_state, shared_lock, dirty_flag
    shared_state = state
    shared_lock = lock
    dirty_flag = flag


def mark_state_dirty():
    """Update both legacy and shared-memory change markers."""
    now = time.time()
    shared_state["_last_updated"] = now
    if dirty_flag is not None:
        dirty_flag.value = now
    return now


def validated_patch_state(patch_data):
    with shared_lock:
        state_copy = dict(shared_state)
        state_copy.update(patch_data)
        validated = ConfigModel(**state_copy).model_dump()
        for k in patch_data:
            shared_state[k] = validated[k]
        mark_state_dirty()


class StopwatchAction(BaseModel):
    action: str


class SpotifyAuthRequest(BaseModel):
    client_id: str
    client_secret: str


class SpotifyCallbackRequest(BaseModel):
    client_id: str
    client_secret: str
    url: str


@app.get("/api/config", response_model=ConfigModel)
def get_config():
    """Retrieve the current matrix configuration state."""
    with shared_lock:
        state_copy = shared_state.copy()

        # Sanitize presets to remove private/byte keys that may have leaked
        presets = state_copy.get("presets", {})
        clean_presets = {}
        for slot, preset_data in presets.items():
            if isinstance(preset_data, dict):
                clean_presets[slot] = {
                    k: v
                    for k, v in preset_data.items()
                    if not k.startswith("_") and k != "spotify_image_bytes"
                }
        state_copy["presets"] = clean_presets

        return ConfigModel(**state_copy)


def generate_frames():
    """Generator for streaming JPEG frames."""
    while True:
        with shared_lock:
            frame_bytes = shared_state.get("_framebuffer_bytes")
        if frame_bytes:
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.1)


@app.get("/api/stream")
def stream_matrix():
    """MJPEG stream of the matrix framebuffer."""
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/api/config")
def update_config(new_config: ConfigModel):
    """Update the matrix configuration state and persist to disk."""
    with shared_lock:
        for k, v in new_config.model_dump().items():
            shared_state[k] = v
        mark_state_dirty()
    # Save outside the lock to prevent rendering stutter
    save_debounced(shared_state, 0.5)
    return {"status": "success"}


@app.patch("/api/config")
def patch_config(patch_data: dict = Body(...)):
    """Update only changed config keys, validating against the full config schema."""
    allowed_keys = set(ConfigModel.model_fields)
    invalid_keys = set(patch_data) - allowed_keys
    if invalid_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown config keys: {', '.join(sorted(invalid_keys))}",
        )
    try:
        validated_patch_state(patch_data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    save_debounced(shared_state, 0.5)
    return {"status": "success"}


@app.post("/api/stopwatch")
def update_stopwatch(payload: StopwatchAction):
    """Handle precise start/stop/reset actions for the stopwatch."""
    with shared_lock:
        if payload.action == "start":
            if shared_state["sw_state"] != "running":
                shared_state["sw_start_time"] = time.time()
                shared_state["sw_state"] = "running"
        elif payload.action == "stop":
            if shared_state["sw_state"] == "running":
                shared_state["sw_elapsed"] += (
                    time.time() - shared_state["sw_start_time"]
                )
                shared_state["sw_state"] = "stopped"
        elif payload.action == "reset":
            shared_state["sw_elapsed"] = 0.0
            shared_state["sw_start_time"] = 0.0
            shared_state["sw_state"] = "stopped"

        mark_state_dirty()

    save_debounced(shared_state, 0.5)
    return {"status": "success"}


@app.post("/api/spotify/auth_url")
def get_spotify_auth_url(payload: SpotifyAuthRequest):
    auth_manager = get_auth_manager(payload.client_id, payload.client_secret)
    return {"url": auth_manager.get_authorize_url()}


@app.post("/api/spotify/callback")
def handle_spotify_callback(payload: SpotifyCallbackRequest):
    try:
        auth_manager = get_auth_manager(payload.client_id, payload.client_secret)
        code = auth_manager.parse_response_code(payload.url)
        if code:
            auth_manager.get_access_token(code)
            with shared_lock:
                shared_state["spotify_client_id"] = payload.client_id
                shared_state["spotify_client_secret"] = payload.client_secret
                shared_state["spotify_linked"] = True
                mark_state_dirty()
            save_debounced(shared_state, 0.5)
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Invalid callback URL"}


@app.post("/api/spotify/unlink")
def unlink_spotify():
    with shared_lock:
        shared_state["spotify_linked"] = False
        shared_state["spotify_client_id"] = ""
        shared_state["spotify_client_secret"] = ""
        shared_state["spotify_image_bytes"] = b""
        mark_state_dirty()
    save_debounced(shared_state, 0.5)
    return {"status": "success"}


@app.post("/api/presets/save/{slot_id}")
def save_preset(slot_id: str):
    valid_slots = [f"slot_{i}" for i in range(1, 11)]
    if slot_id not in valid_slots:
        return {"status": "error", "message": "Invalid slot"}

    with shared_lock:
        current_state = dict(shared_state)
        # Scrub non-preset keys and private keys
        keys_to_remove = [
            "presets",
            "spotify_client_id",
            "spotify_client_secret",
            "spotify_linked",
            "spotify_image_bytes",
        ]
        keys_to_remove.extend([k for k in current_state if k.startswith("_")])
        for key in keys_to_remove:
            current_state.pop(key, None)

        presets = dict(shared_state.get("presets", {}))
        presets[slot_id] = current_state
        shared_state["presets"] = presets
        mark_state_dirty()

    save_debounced(shared_state, 0.5)
    return {"status": "success"}


@app.post("/api/presets/load/{slot_id}")
def load_preset(slot_id: str):
    from backend.config import apply_preset

    with shared_lock:
        presets = shared_state.get("presets", {})
        target_preset = presets.get(slot_id)
        if not target_preset:
            return {"status": "error", "message": "Preset is empty"}

        success = apply_preset(shared_state, target_preset)
        if not success:
            return {"status": "error", "message": "Failed to apply preset"}
        if dirty_flag is not None:
            dirty_flag.value = shared_state.get("_last_updated", time.time())

    save_debounced(shared_state, 0.5)
    return {"status": "success"}


# Serve dashboard statically when the Vite build output exists.
dashboard_dist = resolve_path(env("WAVEDISP_DASHBOARD_DIST", "dashboard/dist"))
if os.path.isdir(dashboard_dist):
    app.mount(
        "/",
        StaticFiles(directory=dashboard_dist, html=True),
        name="static",
    )
