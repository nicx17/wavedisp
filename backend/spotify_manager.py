"""
Spotify Manager
Handles OAuth Flow and background polling of the currently playing track.
Complies with Spotify's Developer TOS by not permanently caching art.
"""

import io
import os
import threading
import time

import requests
import spotipy
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

from backend.settings import env

SPOTIFY_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".spotify_caches"
)
os.makedirs(SPOTIFY_CACHE_PATH, exist_ok=True)


def get_auth_manager(client_id, client_secret):
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=env("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
        scope="user-read-currently-playing",
        cache_path=os.path.join(SPOTIFY_CACHE_PATH, f"token_{client_id}.json"),
        open_browser=False,
    )


def fetch_album_art(url):
    """Download album art and return it as 64x64 raw RGB bytes."""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    return img.resize((64, 64), Image.Resampling.LANCZOS).tobytes()


def start_spotify_poller(store, interval=5):
    """Starts a daemon thread that polls the Spotify API every few seconds."""
    thread = threading.Thread(
        target=_spotify_poll_loop, args=(store, interval), daemon=True, name="Spotify"
    )
    thread.start()
    return thread


def _spotify_poll_loop(store, interval):
    last_track_id = None
    auth_manager = None
    client = None
    client_key = None

    while True:
        try:
            if store.get("mode") == "spotify" and store.get("spotify_linked"):
                creds = (
                    store.get("spotify_client_id"),
                    store.get("spotify_client_secret"),
                )
                if all(creds) and creds != client_key:
                    auth_manager = get_auth_manager(*creds)
                    client = spotipy.Spotify(auth_manager=auth_manager)
                    client_key = creds
                    last_track_id = None
                # Without a cached token spotipy would fall back to an interactive
                # stdin prompt, which would hang this thread under systemd.
                if all(creds) and auth_manager.get_cached_token():
                    current_track = client.current_user_playing_track()
                    item = (current_track or {}).get("item")
                    # Re-fetch when the track changes, or when the art was cleared
                    # (e.g. after unlinking and re-linking during the same song).
                    if item and (
                        item["id"] != last_track_id or not store.spotify_image
                    ):
                        images = item["album"]["images"]
                        if images:
                            # Smallest image is last (64x64 or 300x300)
                            store.set_spotify_image(fetch_album_art(images[-1]["url"]))
                            last_track_id = item["id"]
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Spotify Poll Error: {e}")

        time.sleep(interval)
