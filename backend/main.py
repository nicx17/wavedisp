#!/usr/bin/env python3
"""
Entry point for the backend services.
Starts the Uvicorn ASGI server and the matrix rendering thread.
"""

import multiprocessing
import os
import sys

import uvicorn

# Ensure the backend module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import app, set_shared_state
from backend.config import load_config
from backend.matrix_controller import start_matrix_process
from backend.scheduler import start_scheduler
from backend.settings import env, env_bool, resolve_path
from backend.spotify_manager import start_spotify_poller

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    shared_state = manager.dict(load_config())
    shared_lock = manager.Lock()
    dirty_flag = multiprocessing.Value("d", shared_state.get("_last_updated", 0.0))

    set_shared_state(shared_state, shared_lock, dirty_flag)

    # Start matrix process
    p = multiprocessing.Process(
        target=start_matrix_process, args=(shared_state, shared_lock, dirty_flag)
    )
    p.start()

    # Start Spotify background poller thread
    start_spotify_poller(shared_state, shared_lock, dirty_flag)

    # Start Scheduler thread
    start_scheduler(shared_state, shared_lock, dirty_flag)

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
    uvicorn.run(app, host=host, port=port, **ssl_args)
