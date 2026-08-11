# WaveDisp API Reference

WaveDisp exposes a small HTTP API from the FastAPI backend. By default it is available at:

```text
http://<wavedisp-host>:5000
```

FastAPI also provides interactive OpenAPI documentation while the backend is running:

```text
http://<wavedisp-host>:5000/docs
```

## Notes

- All JSON endpoints use `Content-Type: application/json`.
- `POST /api/config` replaces the full public config.
- `PATCH /api/config` updates only the keys you send and is the preferred endpoint for automations.
- HTML dashboard files are served with no-cache headers; content-hashed JS/CSS assets can still be cached normally.
- The API currently has no built-in authentication. Keep it on a trusted LAN, behind a VPN, or behind a reverse proxy with auth.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/config` | Return the active matrix configuration. |
| `POST` | `/api/config` | Replace the full matrix configuration. |
| `PATCH` | `/api/config` | Update one or more config keys. |
| `GET` | `/api/stream` | MJPEG framebuffer preview stream. |
| `POST` | `/api/stopwatch` | Start, stop, or reset stopwatch mode. |
| `POST` | `/api/presets/save/{slot_id}` | Save current config into a preset slot. |
| `POST` | `/api/presets/load/{slot_id}` | Load a preset slot. |
| `POST` | `/api/spotify/auth_url` | Create a Spotify OAuth URL. |
| `POST` | `/api/spotify/callback` | Complete Spotify OAuth linking. |
| `POST` | `/api/spotify/unlink` | Clear Spotify link state. |

Preset slots are named `slot_1` through `slot_10`.

## Common Config Keys

The full schema lives in `backend/config.py` as `ConfigModel`. These are the most useful keys for integrations:

| Key | Type | Example |
|---|---|---|
| `mode` | string | `"clock"`, `"rain"`, `"qrcode"`, `"spotify"`, `"off"` |
| `brightness` | integer | `25` |
| `show_grid` | boolean | `false` |
| `color_h`, `color_m`, `color_s` | RGB object | `{"r": 255, "g": 80, "b": 0}` |
| `format_12h` | boolean | `true` |
| `show_ms` | boolean | `false` |
| `qr_data` | string | `"https://example.com"` |
| `qr_color_fg`, `qr_color_bg` | RGB object | `{"r": 255, "g": 255, "b": 255}` |
| `rain_color`, `life_color` | RGB object | `{"r": 0, "g": 255, "b": 180}` |
| `rain_speed`, `life_speed`, `alarm_speed` | integer | `10` |
| `badapple_invert` | boolean | `false` |
| `draw_data` | object | `{"12,20": "#ff0000"}` |

Supported `mode` values:

```text
off, clock, stopwatch, warning, smiley, alarm, rain, life, badapple, qrcode, draw, spotify
```

## Examples

Read the current config:

```bash
curl http://wavedisp.local:5000/api/config
```

Turn the display off:

```bash
curl -X PATCH http://wavedisp.local:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"mode":"off"}'
```

Set clock mode at 35% brightness:

```bash
curl -X PATCH http://wavedisp.local:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"mode":"clock","brightness":35}'
```

Show a QR code:

```bash
curl -X PATCH http://wavedisp.local:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"mode":"qrcode","qr_data":"https://example.com"}'
```

Load preset 3:

```bash
curl -X POST http://wavedisp.local:5000/api/presets/load/slot_3
```

Start, stop, and reset the stopwatch:

```bash
curl -X POST http://wavedisp.local:5000/api/stopwatch \
  -H "Content-Type: application/json" \
  -d '{"action":"start"}'
```

The valid stopwatch actions are `start`, `stop`, and `reset`.
