<p align="center">
  <img src="assets/logo.svg" alt="WaveDisp Logo" width="150" />
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=raspberrypi&logoColor=white" alt="Raspberry Pi" />
  <img src="https://img.shields.io/badge/Spotify-1DB954?style=for-the-badge&logo=spotify&logoColor=white" alt="Spotify" />
</p>

# WaveDisp

WaveDisp is a comprehensive UI and control dashboard for Raspberry Pi LED matrix displays, built and tested for the Waveshare RGB-Matrix-Px-64x64 P2.5 64x64 HUB75 panel. It pairs a FastAPI backend with a Vite/React frontend dashboard, allowing you to seamlessly switch display modes, tune rendering settings, draw pixels, generate QR codes, and show Spotify album art directly from any browser.

The backend leverages `hzeller/rpi-rgb-led-matrix` to drive the Raspberry Pi hardware, while the interactive UI dashboard can be built and accessed from any network-connected device.

## Features

- **Live Control Dashboard:** React-based UI served by FastAPI or Vite during development for real-time matrix control.
- **Display Modes:** Clock, warning sign, smiley, alarm, matrix rain, Game of Life, Bad Apple, QR code, drawing canvas, and Spotify album art.
- **10-Slot Preset Memory:** Save, load, and manage up to 10 distinct configuration presets instantly via the UI.
- **Advanced Clock Layouts:** Configurable 12/24-hour formats, manual vs. stacked positioning, and millisecond rendering options.
- **Hardware Integration:** Persistent JSON config with debounced writes to reduce SD card churn, plus an MJPEG preview stream mirroring the matrix framebuffer.
- **Security & Deployment:** Optional HTTPS, and a streamlined SSH/systemd deployment pipeline for Raspberry Pi.

## Hardware

Tested target:

- Raspberry Pi Zero 2 W
- [Waveshare RGB-Matrix-Px-64x64, P2.5 64x64 variant](https://docs.waveshare.com/RGB-Matrix-Px-64x64?variant=P2.5-64x64)
- Adafruit RGB Matrix Bonnet or compatible wiring
- 5V power supply sized for your panel

Install and configure the matrix driver from the upstream project:

- https://docs.waveshare.com/RGB-Matrix-Px-64x64?variant=P2.5-64x64
- https://github.com/hzeller/rpi-rgb-led-matrix
- https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/wiring.md

If the panel flickers or shows artifacts, increase `gpio_slowdown` in the dashboard UI. Pi Zero 2 W and newer boards often need `2` or higher.

## Backend Setup

Create a Python environment and install the app dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Raspberry Pi hardware, also install the Python bindings for `hzeller/rpi-rgb-led-matrix`. That dependency is intentionally not in `requirements.txt` because it is built from the hardware driver project.

Copy the example environment file:

```bash
cp .env.example .env
```

Start the backend:

```bash
sudo .venv/bin/python backend/main.py
```

The API listens on port `5000` by default.

## Configuration Reference (`.env`)

WaveDisp relies on environment variables for deployment and backend configuration. 

| Variable | Default Value | Description |
|---|---|---|
| `WAVEDISP_HOST` | `0.0.0.0` | IP address for the FastAPI backend to listen on. |
| `WAVEDISP_PORT` | `5000` | Port for the backend API and Dashboard. |
| `WAVEDISP_USE_HTTPS` | `false` | Set to `true` to enable HTTPS. Requires cert/key files. |
| `WAVEDISP_CERT_FILE` | `certs/cert.pem` | Path to the HTTPS certificate (if enabled). |
| `WAVEDISP_KEY_FILE` | `certs/key.pem` | Path to the HTTPS private key (if enabled). |
| `WAVEDISP_DASHBOARD_DIST` | `dashboard/dist` | Path to the compiled React dashboard frontend. |
| `WAVEDISP_CONFIG_FILE` | `backend/config.json` | Path where persistent matrix state is saved. |
| `SPOTIFY_REDIRECT_URI` | `http://127.0.0.1:5000/callback` | OAuth redirect URI for Spotify integrations. |
| `RGB_MATRIX_FONTS_DIR` | *(empty)* | Optional path to custom `.bdf` fonts. Overrides default font lookup. |
| `PI_USER` | `nick` | SSH user for `deploy.sh` script. |
| `PI_HOST` | `192.168.0.208` | SSH host/IP for `deploy.sh` script. |
| `PI_APP_DIR` | `/opt/wavedisp` | Target remote directory for `deploy.sh` script. |
| `PI_SERVICE_NAME` | `wavedisp` | Target systemd service name for `deploy.sh` script. |

## Dashboard UI Setup

For dashboard development:

```bash
cd dashboard
npm install
npm run dev
```

For production/static serving through FastAPI:

```bash
cd dashboard
npm run build
```

The backend serves `dashboard/dist` when it exists. Change `WAVEDISP_DASHBOARD_DIST` if your build output lives somewhere else.

## Optional HTTPS

HTTP is the default. To enable HTTPS, create your own cert and key, then update `.env`:

```dotenv
WAVEDISP_USE_HTTPS=true
WAVEDISP_CERT_FILE=certs/cert.pem
WAVEDISP_KEY_FILE=certs/key.pem
```

WaveDisp will exit with a clear error if HTTPS is enabled and either file is missing. Do not commit real certificates or private keys.

## Spotify Mode

Spotify mode uses the Spotify Developer API and stores tokens in `backend/.spotify_caches/`, which is ignored by Git.

By default, register this redirect URI in your Spotify app:

```text
http://127.0.0.1:5000/callback
```

If you enable HTTPS or change the backend port, update `SPOTIFY_REDIRECT_URI` in `.env` and register the exact same URI in the Spotify Developer dashboard.

## Bad Apple Mode

`backend/bad_apple.bin` is generated data and is not committed. To regenerate it locally, you will need `yt-dlp` installed on your system in addition to OpenCV:

```bash
pip install opencv-python numpy
# Make sure yt-dlp is installed and available in your PATH!
python scripts/generate_bad_apple.py
```

If the binary is missing, Bad Apple mode stays blank and logs a message instead of crashing the renderer.

## Deployment

`deploy.sh` is an optional SSH/systemd script to deploy WaveDisp to a remote Raspberry Pi. It assumes you have already prepared Python, Node, the matrix driver, and a virtual environment on the Pi.

1. Ensure your `.env` contains the required deployment variables (`PI_USER`, `PI_HOST`, `PI_APP_DIR`, `PI_SERVICE_NAME`).
2. Copy the service template:
   ```bash
   cp wavedisp.service.example wavedisp.service
   ```
3. Edit your local `wavedisp.service` to point to the correct deployment paths on your Pi.
4. Run the script:
   ```bash
   ./deploy.sh
   ```

## API

- `GET /api/config` returns the active matrix config.
- `POST /api/config` accepts a full config payload from the dashboard. For a detailed reference on the payload structure, inspect the `ConfigModel` in `backend/config.py`.
- `POST /api/stopwatch` handles stopwatch `start`, `stop`, and `reset`.
- `GET /api/stream` returns an MJPEG preview stream.
- `POST /api/presets/save/{slot_id}` and `POST /api/presets/load/{slot_id}` manage presets.
- `POST /api/spotify/auth_url`, `POST /api/spotify/callback`, and `POST /api/spotify/unlink` manage Spotify linking.

<details>
<summary><b>Example JSON Payload for POST /api/config</b></summary>

```json
{
  "mode": "clock",
  "brightness": 100,
  "show_grid": false,
  "gpio_slowdown": 2,
  "hardware_mapping": "regular",
  "color_h": {"r": 0, "g": 255, "b": 255},
  "color_m": {"r": 0, "g": 200, "b": 255},
  "color_s": {"r": 255, "g": 0, "b": 100},
  "color_ms": {"r": 255, "g": 100, "b": 0},
  "pos_x": 4,
  "pos_y": 36,
  "show_hh": true,
  "show_mm": true,
  "show_ss": true,
  "show_colons": true,
  "pos_hh_x": 4,
  "pos_hh_y": 36,
  "pos_mm_x": 26,
  "pos_mm_y": 36,
  "pos_ss_x": 48,
  "pos_ss_y": 36,
  "font_file": "7x14B.bdf",
  "clock_size": 14,
  "clock_thickness": 1,
  "format_12h": false,
  "show_ms": false,
  "clock_layout": "single",
  "ms_position": "inline",
  "gap_x": 2,
  "gap_y": 2,
  "show_stopwatch": false,
  "sw_pos_x": 4,
  "sw_pos_y": 50,
  "sw_show_hours": false,
  "sw_ms_position": "inline",
  "color_sw_h": {"r": 0, "g": 255, "b": 255},
  "color_sw_m": {"r": 0, "g": 200, "b": 255},
  "color_sw_s": {"r": 255, "g": 0, "b": 100},
  "color_sw_ms": {"r": 255, "g": 100, "b": 0},
  "sw_state": "stopped",
  "sw_start_time": 0.0,
  "sw_elapsed": 0.0,
  "warning_color": {"r": 255, "g": 200, "b": 0},
  "warning_thickness": 3,
  "warning_blink_speed": 50,
  "warning_size": 44,
  "smiley_face_color": {"r": 255, "g": 200, "b": 0},
  "smiley_cheek_color": {"r": 200, "g": 50, "b": 0},
  "smiley_eye_color": {"r": 255, "g": 255, "b": 255},
  "smiley_tongue_color": {"r": 255, "g": 50, "b": 50},
  "rain_color": {"r": 0, "g": 255, "b": 0},
  "rain_speed": 10,
  "life_color": {"r": 0, "g": 255, "b": 255},
  "life_speed": 10,
  "alarm_speed": 5,
  "badapple_invert": false,
  "qr_data": "https://github.com/nicx17",
  "qr_error_correction": "L",
  "qr_color_fg": {"r": 255, "g": 255, "b": 255},
  "qr_color_bg": {"r": 0, "g": 0, "b": 0},
  "qr_pos_x": 0,
  "qr_pos_y": 0,
  "qr_size": 58,
  "qr_border": 1,
  "qr_use_micro": false,
  "qr_wobble": false,
  "qr_size_mode": "auto",
  "draw_data": {},
  "draw_color_bg": {"r": 0, "g": 0, "b": 0},
  "spotify_client_id": "",
  "spotify_client_secret": "",
  "spotify_linked": false,
  "presets": {},
  "preset_names": {}
}
```
</details>

## License

MIT
