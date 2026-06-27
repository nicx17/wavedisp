"""
Spotify Manager
Handles OAuth Flow and background polling of the currently playing track.
Complies with Spotify's Developer TOS by not permanently caching art.
"""

import os
import time
import threading
import io
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image
import requests
from backend.settings import env

SPOTIFY_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".spotify_caches"
)
if not os.path.exists(SPOTIFY_CACHE_PATH):
    os.makedirs(SPOTIFY_CACHE_PATH)


def get_auth_manager(client_id, client_secret):
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=env("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
        scope="user-read-currently-playing",
        cache_path=os.path.join(SPOTIFY_CACHE_PATH, f"token_{client_id}.json"),
        open_browser=False,
    )


def start_spotify_poller(shared_state, shared_lock):
    """Starts a daemon thread that polls the Spotify API every 5 seconds."""
    thread = threading.Thread(
        target=_spotify_poll_loop, args=(shared_state, shared_lock), daemon=True
    )
    thread.start()


def _spotify_poll_loop(shared_state, shared_lock):
    last_track_id = None

    while True:
        with shared_lock:
            mode = shared_state.get("mode")
            linked = shared_state.get("spotify_linked")
            client_id = shared_state.get("spotify_client_id")
            client_secret = shared_state.get("spotify_client_secret")

        if mode == "spotify" and linked and client_id and client_secret:
            try:
                auth_manager = get_auth_manager(client_id, client_secret)
                token_info = auth_manager.get_cached_token()

                if token_info:
                    sp = spotipy.Spotify(auth_manager=auth_manager)
                    # Use official OpenAPI compliant endpoint
                    current_track = sp.current_user_playing_track()

                    if current_track and current_track.get("item"):
                        track_id = current_track["item"]["id"]

                        if track_id != last_track_id:
                            # Song changed! Download album art
                            images = current_track["item"]["album"]["images"]
                            if images:
                                # Get the smallest image that is >= 64x64, usually the last one (64x64 or 300x300)
                                img_url = images[-1]["url"]
                                response = requests.get(img_url, timeout=5)
                                if response.status_code == 200:
                                    img = Image.open(
                                        io.BytesIO(response.content)
                                    ).convert("RGB")
                                    img = img.resize((64, 64), Image.Resampling.LANCZOS)

                                    with shared_lock:
                                        shared_state["spotify_image_bytes"] = (
                                            img.tobytes()
                                        )
                                        shared_state["_last_updated"] = time.time()

                                    last_track_id = track_id
            except Exception as e:
                print(f"Spotify Poll Error: {e}")

        time.sleep(5)
