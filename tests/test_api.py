import pytest
from fastapi.testclient import TestClient

from backend.api import create_app


@pytest.fixture
def client(store, channels, tmp_path):
    app = create_app(store, channels[1], dashboard_dist=str(tmp_path / "missing"))
    with TestClient(app) as c:
        yield c


def test_get_config_hides_secret(client, store):
    store.set_spotify_link("cid", "s3cret", True)
    res = client.get("/api/config")
    assert res.status_code == 200
    body = res.json()
    assert "spotify_client_secret" not in body
    assert "s3cret" not in res.text
    assert body["spotify_linked"] is True
    assert res.headers["x-config-version"] == str(store.version)


def test_patch_and_version(client, store):
    res = client.patch("/api/config", json={"mode": "life"})
    assert res.status_code == 200
    assert res.json()["version"] == store.version
    assert client.get("/api/version").json() == {"version": store.version}
    assert store.get("mode") == "life"


def test_patch_validation_errors(client):
    assert client.patch("/api/config", json={"brightness": 101}).status_code == 422
    assert client.patch("/api/config", json={"bogus": 1}).status_code == 422
    assert client.patch("/api/config", json={"spotify_linked": True}).status_code == 422
    assert (
        client.patch("/api/config", json={"font_file": "../x.bdf"}).status_code == 422
    )


def test_full_config_post_round_trip(client, store):
    cfg = client.get("/api/config").json()
    cfg["mode"] = "smiley"
    assert client.post("/api/config", json=cfg).status_code == 200
    assert store.get("mode") == "smiley"


def test_cross_origin_writes_are_blocked(client, store):
    res = client.patch(
        "/api/config", json={"mode": "off"}, headers={"Origin": "https://evil.example"}
    )
    assert res.status_code == 403
    res = client.post("/api/presets/load/slot_1", headers={"Origin": "http://evil"})
    assert res.status_code == 403
    assert store.get("mode") == "clock"


def test_same_origin_and_originless_writes_allowed(client):
    res = client.patch(
        "/api/config", json={"mode": "rain"}, headers={"Origin": "http://testserver"}
    )
    assert res.status_code == 200
    assert client.patch("/api/config", json={"mode": "life"}).status_code == 200


def test_cross_origin_reads_have_no_cors_headers(client):
    res = client.get("/api/config", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in res.headers


def test_presets(client, store):
    assert client.post("/api/presets/load/slot_1").status_code == 404
    assert client.post("/api/presets/save/slot_99").status_code == 404
    assert client.post("/api/presets/save/slot_1").status_code == 200
    client.patch("/api/config", json={"mode": "rain"})
    assert client.post("/api/presets/load/slot_1").status_code == 200
    assert store.get("mode") == "clock"


def test_stopwatch_actions(client, store):
    assert client.post("/api/stopwatch", json={"action": "start"}).status_code == 200
    assert store.get("sw_state") == "running"
    assert client.post("/api/stopwatch", json={"action": "boom"}).status_code == 422


def test_spotify_unlink(client, store):
    store.set_spotify_link("cid", "s3cret", True)
    assert client.post("/api/spotify/unlink").status_code == 200
    assert store.get("spotify_client_secret") == ""
    assert store.get("spotify_linked") is False


def test_spotify_callback_rejects_bad_url(client):
    res = client.post(
        "/api/spotify/callback",
        json={"client_id": "a", "client_secret": "b", "url": "not a callback"},
    )
    assert res.status_code == 400
    assert res.json()["status"] == "error"


def test_preview_encoder_caches_jpeg(channels):
    from backend.api import PreviewEncoder

    frames = channels[1]
    enc = PreviewEncoder(frames)
    assert enc.latest() == (0, b"")
    frames.write(bytes(64 * 64 * 3))
    seq, jpeg = enc.latest()
    assert seq == 1 and jpeg.startswith(b"\xff\xd8")
    assert enc.latest()[1] is jpeg  # not re-encoded
