#!/usr/bin/env python3
"""
Entry point for the backend services.

Process layout:
- main process: Uvicorn/FastAPI, the scheduler and Spotify threads, and the
  authoritative StateStore.
- matrix process: the render loop that owns the LED panel (backend/matrix_controller).

The two share nothing but the shared-memory channels in backend/channels.py. If the
matrix process dies, the whole service exits so systemd restarts it, rather than
leaving a dashboard that looks healthy in front of a frozen panel.
"""

import multiprocessing
import os
import sys
import threading

import uvicorn

# Ensure the backend module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import create_app
from backend.channels import FrameChannel, SnapshotChannel
from backend.config import load_config
from backend.matrix_controller import start_matrix_process
from backend.scheduler import start_scheduler
from backend.settings import env, env_bool, resolve_path
from backend.spotify_manager import start_spotify_poller
from backend.state import StateStore

shutting_down = threading.Event()


def watch_renderer(process, store):
    process.join()
    if shutting_down.is_set():
        return
    print(f"Matrix process exited (code {process.exitcode}); stopping service.")
    store.saver.flush()
    os._exit(0 if process.exitcode == 0 else 1)


def main():
    # fork (not spawn/forkserver) so the renderer shares already-imported modules
    # copy-on-write; it matters on a 512 MB Pi Zero 2 W. No threads exist yet.
    ctx = multiprocessing.get_context("fork")
    snapshots = SnapshotChannel(ctx)
    frames = FrameChannel(ctx)
    store = StateStore(load_config(), snapshots)

    renderer = ctx.Process(
        target=start_matrix_process,
        args=(snapshots, frames),
        name="wavedisp-matrix",
        daemon=True,
    )
    renderer.start()
    threading.Thread(
        target=watch_renderer, args=(renderer, store), daemon=True, name="Watchdog"
    ).start()

    start_spotify_poller(store)
    start_scheduler(store)

    host = env("WAVEDISP_HOST", "0.0.0.0")
    port = int(env("WAVEDISP_PORT", "5000"))
    use_https = env_bool("WAVEDISP_USE_HTTPS", False)
    cert_path = resolve_path(env("WAVEDISP_CERT_FILE", "certs/cert.pem"))
    key_path = resolve_path(env("WAVEDISP_KEY_FILE", "certs/key.pem"))

    ssl_args = {}
    scheme = "http"
    if use_https:
        if not cert_path.exists() or not key_path.exists():
            raise SystemExit(
                "WAVEDISP_USE_HTTPS=true but the configured cert/key files do not exist."
            )
        print("HTTPS enabled by WAVEDISP_USE_HTTPS.")
        ssl_args = {"ssl_certfile": str(cert_path), "ssl_keyfile": str(key_path)}
        scheme = "https"

    print(f"Starting FastAPI server at {scheme}://{host}:{port}")
    try:
        uvicorn.run(create_app(store, frames), host=host, port=port, **ssl_args)
    finally:
        shutting_down.set()
        store.saver.flush()
        renderer.terminate()  # SIGTERM: the renderer clears the panel and exits
        renderer.join(timeout=5)


if __name__ == "__main__":
    main()
