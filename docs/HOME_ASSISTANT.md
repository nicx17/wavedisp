# Home Assistant

WaveDisp can show up in Home Assistant as native entities, so you can switch modes and set brightness from a regular dashboard page and use the display in automations. Nothing changes on the Pi: Home Assistant talks to the existing [HTTP API](API.md).

| Entity | What it does |
|---|---|
| `light.wavedisp` | On/off and brightness. Off is WaveDisp's `off` mode; turning it on restores the last mode. |
| `select.wavedisp_mode` | The display mode, with the same names as the WaveDisp dashboard. |
| `sensor.wavedisp_status` | The raw API mode, polled every 10 seconds. Changes made elsewhere (dashboard, scheduler, presets) show up within one poll. |

The files live in [`home-assistant/`](../home-assistant/):

- `wavedisp.yaml`: a Home Assistant package with the entities above.
- `dashboard.yaml`: a dashboard view with a brightness slider and one tile per mode.

## 1. Add the package

If you don't use packages yet, add this to `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Copy `home-assistant/wavedisp.yaml` to `<config>/packages/wavedisp.yaml` and change the `resource:` address to your Pi. If WaveDisp runs with `WAVEDISP_USE_HTTPS=true` and a self-signed certificate, use `https://` and set `verify_ssl` to `false` in the line below it.

Check the configuration (**Developer tools → YAML → Check configuration**) and restart Home Assistant.

## 2. Install Mushroom

The mode tiles use the Mushroom template card. Install **Mushroom** from HACS (Frontend) and reload the browser.

## 3. Add the page

Open the dashboard you want it in, choose **Edit dashboard → + (add view)**, open the three-dot menu, pick **Edit in YAML**, and paste in `home-assistant/dashboard.yaml`. Change the address in the heading's `tap_action` to your Pi; tapping the **WaveDisp** heading opens the full WaveDisp dashboard for colours, layouts, drawing, and QR codes.

## Automations

The entities work like any other light or select. For example, turn the display off with the rest of the house at night:

```yaml
actions:
  - action: light.turn_off
    target:
      entity_id: light.wavedisp
```

Or switch to Spotify when music starts:

```yaml
actions:
  - action: select.select_option
    target:
      entity_id: select.wavedisp_mode
    data:
      option: Spotify
```
