import { useState, useEffect, useRef } from "react";
import {
  Clock,
  Palette,
  Type,
  Move,
  Sun,
  AlertTriangle,
  Smile,
  Bell,
  CloudRain,
  Activity,
  Film,
  Moon,
  Hash,
  Timer,
  Play,
  Square,
  RotateCcw,
  QrCode,
  Edit3,
  Trash2,
  Music,
} from "lucide-react";

const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 0, g: 0, b: 0 };
};

const rgbToHex = (r, g, b) => {
  return "#" + ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1);
};

function PresetsPanel({ config, updateConfig, activePreset, setActivePreset }) {
  const [loading, setLoading] = useState(false);
  const slots = Array.from({ length: 10 }, (_, i) => i + 1);

  const handleSave = async (slotId) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/presets/save/slot_${slotId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "success") {
        const cfgRes = await fetch("/api/config");
        const newConfig = await cfgRes.json();
        updateConfig(newConfig);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleLoad = async (slotId) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/presets/load/slot_${slotId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "success") {
        const cfgRes = await fetch("/api/config");
        const newConfig = await cfgRes.json();
        updateConfig(newConfig, "preset_load");
        setActivePreset(slotId);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleNameChange = (slotId, rawValue) => {
    // Basic sanitization: alphanumeric, spaces, dashes, underscores. Max 15 chars.
    let cleanValue = rawValue.replace(/[^a-zA-Z0-9\s-_]/g, "").slice(0, 15);
    const newNames = { ...(config.preset_names || {}) };
    newNames[`slot_${slotId}`] = cleanValue;
    updateConfig({ ...config, preset_names: newNames }, "preset_rename");
  };

  return (
    <div className="glass-panel" style={{ marginTop: "0" }}>
      <h3
        style={{
          marginBottom: "1rem",
          borderBottom: "2px solid var(--border)",
          paddingBottom: "0.5rem",
          fontWeight: 900,
        }}
      >
        CONFIGURATION PRESETS
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {slots.map((i) => {
          const hasData =
            config.presets &&
            config.presets[`slot_${i}`] &&
            Object.keys(config.presets[`slot_${i}`]).length > 0;
          const slotName =
            (config.preset_names && config.preset_names[`slot_${i}`]) !==
            undefined
              ? config.preset_names[`slot_${i}`]
              : `Slot ${i}`;
          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "8px",
                justifyContent: "space-between",
                alignItems: "center",
                background:
                  activePreset === i ? "var(--accent)" : "var(--input-bg)",
                padding: "10px",
                border: "var(--border)",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "8px" }}
              >
                {activePreset === i && (
                  <div
                    style={{
                      width: "10px",
                      height: "10px",
                      borderRadius: "50%",
                      background: "var(--panel-bg)",
                      border: "2px solid var(--struct)",
                    }}
                  ></div>
                )}
                <input
                  type="text"
                  value={slotName}
                  onChange={(e) => handleNameChange(i, e.target.value)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--text-primary)",
                    fontWeight: "900",
                    textTransform: "uppercase",
                    width: "120px",
                    outline: "none",
                    borderBottom: "1px solid var(--text-primary)",
                  }}
                />
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  className="mode-btn"
                  onClick={() => handleSave(i)}
                  disabled={loading}
                  style={{ padding: "6px 12px" }}
                >
                  Save
                </button>
                <button
                  className="mode-btn"
                  onClick={() => handleLoad(i)}
                  disabled={loading || !hasData}
                  style={{
                    padding: "6px 12px",
                    opacity: hasData ? 1 : 0.5,
                    cursor: hasData ? "pointer" : "not-allowed",
                  }}
                >
                  Load
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MatrixPreview() {
  const containerStyle = {
    width: "256px",
    height: "256px",
    background: "#000",
    margin: "0 auto 2rem auto",
    borderRadius: "12px",
    border: `4px solid rgba(255,255,255,0.1)`,
    position: "relative",
    overflow: "hidden",
    boxShadow: "0 0 20px rgba(0,0,0,0.5) inset, 0 10px 30px rgba(0,0,0,0.3)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  };

  return (
    <div style={containerStyle}>
      <img
        src="/api/stream"
        alt="Matrix Stream"
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          imageRendering: "pixelated",
        }}
      />
    </div>
  );
}

function App() {
  const [isDark, setIsDark] = useState(
    localStorage.getItem("theme") === "dark",
  );
  const [showPreview, setShowPreview] = useState(
    localStorage.getItem("showPreview") !== "false",
  );
  const [activePreset, setActivePreset] = useState(null);
  const [config, setConfig] = useState({
    mode: "clock",
    brightness: 100,
    show_grid: false,
    color_h: { r: 0, g: 255, b: 255 },
    color_m: { r: 0, g: 200, b: 255 },
    color_s: { r: 255, g: 0, b: 100 },
    color_ms: { r: 255, g: 100, b: 0 },
    pos_x: 4,
    pos_y: 36,
    font_file: "PressStart2P.ttf",
    clock_size: 14,
    clock_thickness: 1,
    format_12h: false,
    show_ms: false,
    warning_color: { r: 255, g: 200, b: 0 },
    warning_thickness: 3,
    warning_blink_speed: 5,
    warning_size: 40,
    gpio_slowdown: 2,
    hardware_mapping: "regular",
    smiley_face_color: { r: 150, g: 150, b: 0 },
    smiley_cheek_color: { r: 200, g: 50, b: 0 },
    smiley_eye_color: { r: 255, g: 255, b: 255 },
    smiley_tongue_color: { r: 255, g: 50, b: 50 },
    rain_color: { r: 0, g: 255, b: 0 },
    rain_speed: 10,
    life_color: { r: 0, g: 255, b: 255 },
    life_speed: 10,
    alarm_speed: 5,
    badapple_invert: false,
    show_stopwatch: false,
    sw_pos_x: 4,
    sw_pos_y: 50,
    sw_show_hours: false,
    sw_ms_position: "inline",
    color_sw_h: { r: 0, g: 255, b: 255 },
    color_sw_m: { r: 0, g: 200, b: 255 },
    color_sw_s: { r: 255, g: 0, b: 100 },
    color_sw_ms: { r: 255, g: 100, b: 0 },
    sw_state: "stopped",
    sw_start_time: 0.0,
    sw_elapsed: 0.0,
    qr_data: "https://github.com",
    qr_error_correction: "L",
    qr_color_fg: { r: 255, g: 255, b: 255 },
    qr_color_bg: { r: 0, g: 0, b: 0 },
    qr_pos_x: 0,
    qr_pos_y: 0,
    qr_size: 58,
    qr_border: 1,
    qr_use_micro: false,
    qr_wobble: false,
    qr_size_mode: "auto",
    draw_data: {},
    draw_color_bg: { r: 0, g: 0, b: 0 },
  });

  const [drawColor, setDrawColor] = useState("#ffffff");
  const [isDrawing, setIsDrawing] = useState(false);
  const updateTimeoutRef = useRef(null);
  const pendingConfigRef = useRef(null);

  const [qrPayload, setQrPayload] = useState({
    type: "text",
    text: "",
    wifiSsid: "",
    wifiPass: "",
    wifiType: "WPA",
    vcardName: "",
    vcardPhone: "",
    vcardEmail: "",
    smsPhone: "",
    smsMsg: "",
  });

  const handleQrPayloadChange = (field, value) => {
    const next = { ...qrPayload, [field]: value };
    setQrPayload(next);
    let data = "";
    if (next.type === "text") data = next.text;
    else if (next.type === "wifi")
      data = `WIFI:T:${next.wifiType};S:${next.wifiSsid};P:${next.wifiPass};;`;
    else if (next.type === "vcard")
      data = `MECARD:N:${next.vcardName};TEL:${next.vcardPhone};EMAIL:${next.vcardEmail};;`;
    else if (next.type === "sms")
      data = `SMSTO:${next.smsPhone}:${next.smsMsg}`;

    updateConfig({ ...config, qr_data: data });
  };

  useEffect(() => {
    if (isDark) {
      document.body.classList.add("dark-mode");
      localStorage.setItem("theme", "dark");
      document.body.style.setProperty(
        "--bg-color",
        config.ui_dark_bg ?? "#000000",
      );
      document.body.style.setProperty(
        "--panel-bg",
        config.ui_dark_panel ?? "#000000",
      );
      document.body.style.setProperty(
        "--text-primary",
        config.ui_dark_text ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--text-secondary",
        config.ui_dark_text ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--accent",
        config.ui_dark_accent ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--struct",
        config.ui_dark_border ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--border",
        `4px solid ${config.ui_dark_border ?? "#ffde00"}`,
      );
      document.body.style.setProperty(
        "--shadow",
        `8px 8px 0px ${config.ui_dark_border ?? "#ffde00"}`,
      );
      document.body.style.setProperty(
        "--shadow-hover",
        `12px 12px 0px ${config.ui_dark_border ?? "#ffde00"}`,
      );
      document.body.style.setProperty("--input-bg", "#000000");
    } else {
      document.body.classList.remove("dark-mode");
      localStorage.setItem("theme", "light");
      document.body.style.setProperty(
        "--bg-color",
        config.ui_light_bg ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--panel-bg",
        config.ui_light_panel ?? "#f4f4f0",
      );
      document.body.style.setProperty(
        "--text-primary",
        config.ui_light_text ?? "#000000",
      );
      document.body.style.setProperty(
        "--text-secondary",
        config.ui_light_text ?? "#000000",
      );
      document.body.style.setProperty(
        "--accent",
        config.ui_light_accent ?? "#ffde00",
      );
      document.body.style.setProperty(
        "--struct",
        config.ui_light_border ?? "#000000",
      );
      document.body.style.setProperty(
        "--border",
        `4px solid ${config.ui_light_border ?? "#000000"}`,
      );
      document.body.style.setProperty(
        "--shadow",
        `8px 8px 0px ${config.ui_light_border ?? "#000000"}`,
      );
      document.body.style.setProperty(
        "--shadow-hover",
        `12px 12px 0px ${config.ui_light_border ?? "#000000"}`,
      );
      document.body.style.setProperty("--input-bg", "#ffffff");
    }
  }, [
    isDark,
    config.ui_light_bg,
    config.ui_light_panel,
    config.ui_light_accent,
    config.ui_light_text,
    config.ui_light_border,
    config.ui_dark_bg,
    config.ui_dark_panel,
    config.ui_dark_accent,
    config.ui_dark_text,
    config.ui_dark_border,
  ]);

  useEffect(() => {
    localStorage.setItem("showPreview", showPreview);
  }, [showPreview]);

  useEffect(() => {
    fetch("/api/config")
      .then((res) => res.json())
      .then((data) => setConfig(data))
      .catch((err) => console.error("Failed to load config:", err));
  }, []);

  const updateConfig = (newConfig, source = null) => {
    setConfig(newConfig);
    if (source !== "preset_load" && source !== "preset_rename") {
      setActivePreset(null);
    }
    pendingConfigRef.current = newConfig;

    if (!updateTimeoutRef.current) {
      updateTimeoutRef.current = setTimeout(() => {
        fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(pendingConfigRef.current),
        }).catch((err) => console.error("Update failed:", err));
        updateTimeoutRef.current = null;
      }, 30); // 33 FPS Network Throttle
    }
  };

  const handleDrawEvent = (e, shouldDraw) => {
    if (!shouldDraw && e.type !== "click" && e.type !== "touchstart") return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    const x = Math.floor((clientX - rect.left) / (rect.width / 64));
    const y = Math.floor((clientY - rect.top) / (rect.height / 64));

    if (x >= 0 && x < 64 && y >= 0 && y < 64) {
      const coord = `${x},${y}`;
      if (config.draw_data?.[coord] === drawColor) return;
      const nextData = { ...(config.draw_data || {}), [coord]: drawColor };
      updateConfig({ ...config, draw_data: nextData });
    }
  };

  const handleColor = (key, e) => {
    updateConfig({ ...config, [key]: hexToRgb(e.target.value) });
  };

  const handleMode = (modeStr) => {
    updateConfig({ ...config, mode: modeStr });
  };

  const handleStopwatchAction = (action) => {
    fetch("/api/stopwatch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    })
      .then(() => {
        fetch("/api/config")
          .then((res) => res.json())
          .then((data) => setConfig(data));
      })
      .catch((err) => console.error("Action failed:", err));
  };

  return (
    <div className="container">
      <div className="dashboard-layout">
        {/* LEFT COLUMN */}
        <div className="layout-col">
          <div className="glass-panel">
            <div className="header-row">
              <h1>RGB Matrix Control</h1>
              <button
                className="theme-toggle"
                onClick={() => setIsDark(!isDark)}
              >
                {isDark ? <Sun size={20} /> : <Moon size={20} />}
              </button>
            </div>

            <div className="control-group">
              <label>Display Mode</label>
              <div
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  marginBottom: "1.5rem",
                  flexWrap: "wrap",
                }}
              >
                <button
                  onClick={() => handleMode("clock")}
                  className={`mode-btn ${config.mode === "clock" ? "active" : ""}`}
                >
                  <Clock size={16} /> Clock
                </button>
                <button
                  onClick={() => handleMode("warning")}
                  className={`mode-btn ${config.mode === "warning" ? "active" : ""}`}
                >
                  <AlertTriangle size={16} /> Warning
                </button>
                <button
                  onClick={() => handleMode("smiley")}
                  className={`mode-btn ${config.mode === "smiley" ? "active" : ""}`}
                >
                  <Smile size={16} /> Smiley
                </button>
                <button
                  onClick={() => handleMode("alarm")}
                  className={`mode-btn ${config.mode === "alarm" ? "active" : ""}`}
                >
                  <Bell size={16} /> Alarm
                </button>
                <button
                  onClick={() => handleMode("rain")}
                  className={`mode-btn ${config.mode === "rain" ? "active" : ""}`}
                >
                  <CloudRain size={16} /> Rain
                </button>
                <button
                  onClick={() => handleMode("life")}
                  className={`mode-btn ${config.mode === "life" ? "active" : ""}`}
                >
                  <Activity size={16} /> Life
                </button>
                <button
                  onClick={() => handleMode("badapple")}
                  className={`mode-btn ${config.mode === "badapple" ? "active" : ""}`}
                >
                  <Film size={16} /> Bad Apple
                </button>
                <button
                  onClick={() => handleMode("qrcode")}
                  className={`mode-btn ${config.mode === "qrcode" ? "active" : ""}`}
                >
                  <QrCode size={16} /> QR Code
                </button>
                <button
                  onClick={() => handleMode("draw")}
                  className={`mode-btn ${config.mode === "draw" ? "active" : ""}`}
                >
                  <Edit3 size={16} /> Draw
                </button>
                <button
                  onClick={() => handleMode("spotify")}
                  className={`mode-btn ${config.mode === "spotify" ? "active" : ""}`}
                >
                  <Music size={16} /> Spotify
                </button>
              </div>
            </div>

            <div className="control-group">
              <label>
                <Sun size={16} /> Brightness
              </label>
              <div className="color-picker-container">
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={config.brightness}
                  onChange={(e) =>
                    updateConfig({
                      ...config,
                      brightness: parseInt(e.target.value),
                    })
                  }
                />
                <span className="slider-val">{config.brightness}%</span>
              </div>
            </div>

            <div className="control-group">
              <label>
                <Hash size={16} /> Show Grid Overlay
              </label>
              <div
                className="toggle-switch"
                onClick={() =>
                  updateConfig({ ...config, show_grid: !config.show_grid })
                }
              >
                <div style={{ flex: 1, fontWeight: 600 }}>
                  {config.show_grid ? "ON" : "OFF"}
                </div>
                <input
                  type="checkbox"
                  checked={config.show_grid}
                  readOnly
                  style={{ pointerEvents: "none" }}
                />
              </div>
            </div>

            <div className="control-group">
              <label>
                <Activity size={16} /> GPIO Slowdown
              </label>
              <div
                className="color-picker-container"
                style={{ display: "flex", gap: "1rem" }}
              >
                <input
                  type="range"
                  min="0"
                  max="4"
                  value={config.gpio_slowdown ?? 2}
                  onChange={(e) =>
                    updateConfig({
                      ...config,
                      gpio_slowdown: parseInt(e.target.value),
                    })
                  }
                />
                <span className="slider-val">{config.gpio_slowdown ?? 2}</span>
              </div>
              <small
                style={{ display: "block", marginTop: "5px", opacity: 0.6 }}
              >
                Increase if display glitches (Pi 3/4 need 2-4)
              </small>
            </div>

            <div className="control-group">
              <label>
                <Type size={16} /> Hardware Mapping
              </label>
              <select
                value={config.hardware_mapping || "regular"}
                onChange={(e) =>
                  updateConfig({ ...config, hardware_mapping: e.target.value })
                }
              >
                <option value="regular">Regular</option>
                <option value="adafruit-hat">Adafruit HAT</option>
                <option value="adafruit-hat-pwm">Adafruit HAT (PWM)</option>
                <option value="regular-pi1">Regular Pi 1</option>
              </select>
            </div>

            <div className="control-group">
              <label>
                <Palette size={16} /> Dashboard Theme (
                {isDark ? "Dark" : "Light"})
              </label>
              <div
                className="control-group row"
                style={{
                  padding: 0,
                  border: "none",
                  background: "transparent",
                  marginBottom: 0,
                }}
              >
                <div className="col" style={{ minWidth: 0 }}>
                  <label style={{ fontSize: "0.75rem" }}>Page Bg</label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={
                        isDark
                          ? (config.ui_dark_bg ?? "#000000")
                          : (config.ui_light_bg ?? "#ffde00")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_bg" : "ui_light_bg"]:
                            e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      value={
                        isDark
                          ? (config.ui_dark_bg ?? "#000000")
                          : (config.ui_light_bg ?? "#ffde00")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_bg" : "ui_light_bg"]:
                            e.target.value,
                        })
                      }
                      style={{
                        width: "70px",
                        padding: "4px",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        margin: 0,
                      }}
                    />
                  </div>
                </div>
                <div className="col" style={{ minWidth: 0 }}>
                  <label style={{ fontSize: "0.75rem" }}>Panel Bg</label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={
                        isDark
                          ? (config.ui_dark_panel ?? "#000000")
                          : (config.ui_light_panel ?? "#f4f4f0")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_panel" : "ui_light_panel"]:
                            e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      value={
                        isDark
                          ? (config.ui_dark_panel ?? "#000000")
                          : (config.ui_light_panel ?? "#f4f4f0")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_panel" : "ui_light_panel"]:
                            e.target.value,
                        })
                      }
                      style={{
                        width: "70px",
                        padding: "4px",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        margin: 0,
                      }}
                    />
                  </div>
                </div>
              </div>
              <div
                className="control-group row"
                style={{
                  padding: 0,
                  border: "none",
                  background: "transparent",
                  marginTop: "10px",
                  marginBottom: 0,
                }}
              >
                <div className="col" style={{ minWidth: 0 }}>
                  <label style={{ fontSize: "0.75rem" }}>Accent</label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={
                        isDark
                          ? (config.ui_dark_accent ?? "#ffde00")
                          : (config.ui_light_accent ?? "#ffde00")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_accent" : "ui_light_accent"]:
                            e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      value={
                        isDark
                          ? (config.ui_dark_accent ?? "#ffde00")
                          : (config.ui_light_accent ?? "#ffde00")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_accent" : "ui_light_accent"]:
                            e.target.value,
                        })
                      }
                      style={{
                        width: "70px",
                        padding: "4px",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        margin: 0,
                      }}
                    />
                  </div>
                </div>
                <div className="col" style={{ minWidth: 0 }}>
                  <label style={{ fontSize: "0.75rem" }}>Text</label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={
                        isDark
                          ? (config.ui_dark_text ?? "#ffde00")
                          : (config.ui_light_text ?? "#000000")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_text" : "ui_light_text"]:
                            e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      value={
                        isDark
                          ? (config.ui_dark_text ?? "#ffde00")
                          : (config.ui_light_text ?? "#000000")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_text" : "ui_light_text"]:
                            e.target.value,
                        })
                      }
                      style={{
                        width: "70px",
                        padding: "4px",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        margin: 0,
                      }}
                    />
                  </div>
                </div>
              </div>
              <div
                className="control-group row"
                style={{
                  padding: 0,
                  border: "none",
                  background: "transparent",
                  marginTop: "10px",
                  marginBottom: 0,
                }}
              >
                <div className="col" style={{ minWidth: 0 }}>
                  <label style={{ fontSize: "0.75rem" }}>Border/Shadow</label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={
                        isDark
                          ? (config.ui_dark_border ?? "#ffde00")
                          : (config.ui_light_border ?? "#000000")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_border" : "ui_light_border"]:
                            e.target.value,
                        })
                      }
                    />
                    <input
                      type="text"
                      value={
                        isDark
                          ? (config.ui_dark_border ?? "#ffde00")
                          : (config.ui_light_border ?? "#000000")
                      }
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          [isDark ? "ui_dark_border" : "ui_light_border"]:
                            e.target.value,
                        })
                      }
                      style={{
                        width: "70px",
                        padding: "4px",
                        fontSize: "0.75rem",
                        fontFamily: "monospace",
                        margin: 0,
                      }}
                    />
                  </div>
                </div>
                <div className="col" style={{ minWidth: 0 }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* MIDDLE COLUMN */}
        <div className="layout-col">
          <div className="glass-panel">
            {/* ----------------- STATE SPECIFIC PANELS ----------------- */}

            {config.mode === "clock" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Clock Settings
                </h3>
                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Palette size={16} /> Hours
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.color_h.r,
                          config.color_h.g,
                          config.color_h.b,
                        )}
                        onChange={(e) => handleColor("color_h", e)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Palette size={16} /> Mins
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.color_m.r,
                          config.color_m.g,
                          config.color_m.b,
                        )}
                        onChange={(e) => handleColor("color_m", e)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Palette size={16} /> Secs
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.color_s.r,
                          config.color_s.g,
                          config.color_s.b,
                        )}
                        onChange={(e) => handleColor("color_s", e)}
                      />
                    </div>
                  </div>
                  {config.show_ms && (
                    <div className="col">
                      <label>
                        <Palette size={16} /> MS
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="color"
                          value={
                            config.color_ms
                              ? rgbToHex(
                                  config.color_ms.r,
                                  config.color_ms.g,
                                  config.color_ms.b,
                                )
                              : "#ff6400"
                          }
                          onChange={(e) => handleColor("color_ms", e)}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div
                  className="control-group row"
                  style={{ marginTop: "15px" }}
                >
                  <div
                    className="col"
                    style={{
                      flex: 1,
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={config.show_hh ?? true}
                      onChange={(e) =>
                        updateConfig({ ...config, show_hh: e.target.checked })
                      }
                      id="show_hh"
                    />
                    <label
                      htmlFor="show_hh"
                      style={{ margin: 0, cursor: "pointer" }}
                    >
                      Show HH
                    </label>
                  </div>
                  <div
                    className="col"
                    style={{
                      flex: 1,
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={config.show_mm ?? true}
                      onChange={(e) =>
                        updateConfig({ ...config, show_mm: e.target.checked })
                      }
                      id="show_mm"
                    />
                    <label
                      htmlFor="show_mm"
                      style={{ margin: 0, cursor: "pointer" }}
                    >
                      Show MM
                    </label>
                  </div>
                  <div
                    className="col"
                    style={{
                      flex: 1,
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={config.show_ss ?? true}
                      onChange={(e) =>
                        updateConfig({ ...config, show_ss: e.target.checked })
                      }
                      id="show_ss"
                    />
                    <label
                      htmlFor="show_ss"
                      style={{ margin: 0, cursor: "pointer" }}
                    >
                      Show SS
                    </label>
                  </div>
                  <div
                    className="col"
                    style={{
                      flex: 1,
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={config.show_colons ?? true}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          show_colons: e.target.checked,
                        })
                      }
                      id="show_colons"
                    />
                    <label
                      htmlFor="show_colons"
                      style={{ margin: 0, cursor: "pointer" }}
                    >
                      Colons (:)
                    </label>
                  </div>
                </div>

                {config.clock_layout !== "manual" ? (
                  <div className="control-group row">
                    <div className="col">
                      <label>
                        <Move size={16} /> Global X Pos
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="range"
                          min="-10"
                          max="64"
                          value={config.pos_x}
                          onChange={(e) =>
                            updateConfig({
                              ...config,
                              pos_x: parseInt(e.target.value),
                            })
                          }
                        />
                        <span className="slider-val">{config.pos_x}</span>
                      </div>
                    </div>
                    <div className="col">
                      <label>
                        <Move size={16} /> Global Y Pos
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="range"
                          min="-10"
                          max="80"
                          value={config.pos_y}
                          onChange={(e) =>
                            updateConfig({
                              ...config,
                              pos_y: parseInt(e.target.value),
                            })
                          }
                        />
                        <span className="slider-val">{config.pos_y}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      background: "var(--input-bg)",
                      padding: "10px",
                      borderRadius: "0",
                      border: "var(--border)",
                      marginBottom: "15px",
                    }}
                  >
                    <h4
                      style={{
                        margin: "0 0 10px 0",
                        fontSize: "0.85rem",
                        opacity: 0.8,
                      }}
                    >
                      Manual Positioning
                    </h4>
                    {(config.show_hh ?? true) && (
                      <div
                        className="control-group row"
                        style={{ marginBottom: "5px" }}
                      >
                        <div className="col" style={{ flex: "0 0 40px" }}>
                          <label>HH</label>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_hh_x ?? 4}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_hh_x: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            X:{config.pos_hh_x ?? 4}
                          </span>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_hh_y ?? 36}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_hh_y: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            Y:{config.pos_hh_y ?? 36}
                          </span>
                        </div>
                      </div>
                    )}
                    {(config.show_mm ?? true) && (
                      <div
                        className="control-group row"
                        style={{ marginBottom: "5px" }}
                      >
                        <div className="col" style={{ flex: "0 0 40px" }}>
                          <label>MM</label>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_mm_x ?? 26}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_mm_x: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            X:{config.pos_mm_x ?? 26}
                          </span>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_mm_y ?? 36}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_mm_y: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            Y:{config.pos_mm_y ?? 36}
                          </span>
                        </div>
                      </div>
                    )}
                    {(config.show_ss ?? true) && (
                      <div
                        className="control-group row"
                        style={{ marginBottom: "0" }}
                      >
                        <div className="col" style={{ flex: "0 0 40px" }}>
                          <label>SS</label>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_ss_x ?? 48}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_ss_x: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            X:{config.pos_ss_x ?? 48}
                          </span>
                        </div>
                        <div className="col">
                          <input
                            type="range"
                            min="-20"
                            max="80"
                            value={config.pos_ss_y ?? 36}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                pos_ss_y: parseInt(e.target.value),
                              })
                            }
                          />
                          <span
                            className="slider-val"
                            style={{ width: "20px" }}
                          >
                            Y:{config.pos_ss_y ?? 36}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="control-group">
                  <label>
                    <Type size={16} /> Font File
                  </label>
                  <select
                    value={config.font_file}
                    onChange={(e) =>
                      updateConfig({ ...config, font_file: e.target.value })
                    }
                  >
                    <optgroup label="Matrix BDF (Fixed Size)">
                      <option value="4x6.bdf">Micro (4x6)</option>
                      <option value="5x8.bdf">Tiny (5x8)</option>
                      <option value="6x10.bdf">Mini (6x10)</option>
                      <option value="6x13.bdf">Small (6x13)</option>
                      <option value="6x13B.bdf">Small Bold (6x13)</option>
                      <option value="7x13.bdf">Medium (7x13)</option>
                      <option value="7x14B.bdf">Medium Bold (7x14)</option>
                      <option value="8x13B.bdf">Large Bold (8x13)</option>
                      <option value="9x15B.bdf">XL Bold (9x15)</option>
                      <option value="9x18B.bdf">Jumbo Bold (9x18)</option>
                      <option value="10x20.bdf">Huge (10x20)</option>
                    </optgroup>
                    <optgroup label="Custom TTF (Scalable)">
                      <option value="ttf">System Default</option>
                      <option value="Anton.ttf">Anton (Blocky)</option>
                      <option value="BebasNeue.ttf">Bebas Neue (Tall)</option>
                      <option value="VT323.ttf">VT323 (Terminal)</option>
                      <option value="PressStart2P.ttf">
                        Press Start 2P (8-bit)
                      </option>
                      <option value="RubikMonoOne.ttf">
                        Rubik Mono (Thick)
                      </option>
                    </optgroup>
                  </select>
                </div>

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Type size={16} /> TTF Size
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="8"
                        max="40"
                        value={config.clock_size}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            clock_size: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">{config.clock_size}px</span>
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Type size={16} /> TTF Thickness
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={config.clock_thickness}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            clock_thickness: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">
                        {config.clock_thickness}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="control-group">
                  <select
                    value={config.clock_layout || "single"}
                    onChange={(e) =>
                      updateConfig({ ...config, clock_layout: e.target.value })
                    }
                  >
                    <option value="single">Single Line (Inline)</option>
                    <option value="stacked">Stacked (Two Lines)</option>
                    <option value="manual">Manual (Absolute X/Y)</option>
                  </select>
                </div>

                {config.show_ms && config.clock_layout === "single" && (
                  <div className="control-group">
                    <label>MS Position</label>
                    <select
                      value={config.ms_position || "inline"}
                      onChange={(e) =>
                        updateConfig({ ...config, ms_position: e.target.value })
                      }
                    >
                      <option value="inline">Inline</option>
                      <option value="above">Above Clock</option>
                      <option value="below">Below Clock</option>
                    </select>
                  </div>
                )}

                {config.clock_layout !== "manual" && (
                  <div className="control-group">
                    <label>X Spacing (Gap)</label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="0"
                        max="20"
                        value={config.gap_x ?? 2}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            gap_x: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="value-display">
                        {config.gap_x ?? 2}px
                      </span>
                    </div>
                  </div>
                )}

                {(config.clock_layout === "stacked" ||
                  (config.show_ms && config.ms_position !== "inline")) && (
                  <div className="control-group">
                    <label>Y Spacing (Gap)</label>
                    <div className="slider-container">
                      <input
                        type="range"
                        min="-10"
                        max="30"
                        value={config.gap_y ?? 2}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            gap_y: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="value-display">
                        {config.gap_y ?? 2}px
                      </span>
                    </div>
                  </div>
                )}

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Clock size={16} /> Time Format
                    </label>
                    <div
                      style={{ display: "flex", gap: "8px", marginTop: "10px" }}
                    >
                      <button
                        className={`mode-btn ${config.format_12h ? "active" : ""}`}
                        onClick={() =>
                          updateConfig({ ...config, format_12h: true })
                        }
                        style={{
                          flex: 1,
                          padding: "10px",
                          justifyContent: "center",
                        }}
                      >
                        12-Hour
                      </button>
                      <button
                        className={`mode-btn ${!config.format_12h ? "active" : ""}`}
                        onClick={() =>
                          updateConfig({ ...config, format_12h: false })
                        }
                        style={{
                          flex: 1,
                          padding: "10px",
                          justifyContent: "center",
                        }}
                      >
                        24-Hour
                      </button>
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Clock size={16} /> Milliseconds
                    </label>
                    <div
                      className="toggle-switch"
                      onClick={() =>
                        updateConfig({ ...config, show_ms: !config.show_ms })
                      }
                    >
                      <div style={{ flex: 1, fontWeight: 600 }}>
                        {config.show_ms ? "ON" : "OFF"}
                      </div>
                      <input
                        type="checkbox"
                        checked={config.show_ms}
                        readOnly
                        style={{ pointerEvents: "none" }}
                      />
                    </div>
                  </div>
                </div>

                <h3
                  style={{
                    marginTop: "2rem",
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Timer size={20} /> Stopwatch
                </h3>

                <div className="control-group row">
                  <div className="col">
                    <label>Enable Stopwatch Overlay</label>
                    <div
                      className="toggle-switch"
                      onClick={() =>
                        updateConfig({
                          ...config,
                          show_stopwatch: !config.show_stopwatch,
                        })
                      }
                    >
                      <div style={{ flex: 1, fontWeight: 600 }}>
                        {config.show_stopwatch ? "ON" : "OFF"}
                      </div>
                      <input
                        type="checkbox"
                        checked={config.show_stopwatch}
                        readOnly
                        style={{ pointerEvents: "none" }}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>Force Show Hours</label>
                    <div
                      className="toggle-switch"
                      onClick={() =>
                        updateConfig({
                          ...config,
                          sw_show_hours: !config.sw_show_hours,
                        })
                      }
                    >
                      <div style={{ flex: 1, fontWeight: 600 }}>
                        {config.sw_show_hours ? "ON" : "OFF"}
                      </div>
                      <input
                        type="checkbox"
                        checked={config.sw_show_hours}
                        readOnly
                        style={{ pointerEvents: "none" }}
                      />
                    </div>
                  </div>
                </div>

                {config.show_stopwatch && (
                  <>
                    <div
                      className="control-group"
                      style={{
                        display: "flex",
                        gap: "1rem",
                        justifyContent: "center",
                        margin: "1rem 0",
                      }}
                    >
                      <button
                        onClick={() => handleStopwatchAction("start")}
                        className={`mode-btn ${config.sw_state === "running" ? "active" : ""}`}
                      >
                        <Play size={16} /> Start
                      </button>
                      <button
                        onClick={() => handleStopwatchAction("stop")}
                        className={`mode-btn ${config.sw_state === "stopped" && config.sw_elapsed > 0 ? "active" : ""}`}
                      >
                        <Square size={16} /> Stop
                      </button>
                      <button
                        onClick={() => handleStopwatchAction("reset")}
                        className="mode-btn"
                      >
                        <RotateCcw size={16} /> Reset
                      </button>
                    </div>

                    <div className="control-group row">
                      <div className="col">
                        <label>
                          <Move size={16} /> X Position
                        </label>
                        <div className="color-picker-container">
                          <input
                            type="range"
                            min="-10"
                            max="64"
                            value={config.sw_pos_x ?? 4}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                sw_pos_x: parseInt(e.target.value),
                              })
                            }
                          />
                          <span className="slider-val">
                            {config.sw_pos_x ?? 4}
                          </span>
                        </div>
                      </div>
                      <div className="col">
                        <label>
                          <Move size={16} /> Y Position
                        </label>
                        <div className="color-picker-container">
                          <input
                            type="range"
                            min="-10"
                            max="80"
                            value={config.sw_pos_y ?? 50}
                            onChange={(e) =>
                              updateConfig({
                                ...config,
                                sw_pos_y: parseInt(e.target.value),
                              })
                            }
                          />
                          <span className="slider-val">
                            {config.sw_pos_y ?? 50}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="control-group row">
                      <div className="col">
                        <label>
                          <Palette size={16} /> Mins
                        </label>
                        <div className="color-picker-container">
                          <input
                            type="color"
                            value={
                              config.color_sw_m
                                ? rgbToHex(
                                    config.color_sw_m.r,
                                    config.color_sw_m.g,
                                    config.color_sw_m.b,
                                  )
                                : "#00ffff"
                            }
                            onChange={(e) => handleColor("color_sw_m", e)}
                          />
                        </div>
                      </div>
                      <div className="col">
                        <label>
                          <Palette size={16} /> Secs
                        </label>
                        <div className="color-picker-container">
                          <input
                            type="color"
                            value={
                              config.color_sw_s
                                ? rgbToHex(
                                    config.color_sw_s.r,
                                    config.color_sw_s.g,
                                    config.color_sw_s.b,
                                  )
                                : "#ff0064"
                            }
                            onChange={(e) => handleColor("color_sw_s", e)}
                          />
                        </div>
                      </div>
                      <div className="col">
                        <label>
                          <Palette size={16} /> MS
                        </label>
                        <div className="color-picker-container">
                          <input
                            type="color"
                            value={
                              config.color_sw_ms
                                ? rgbToHex(
                                    config.color_sw_ms.r,
                                    config.color_sw_ms.g,
                                    config.color_sw_ms.b,
                                  )
                                : "#ff6400"
                            }
                            onChange={(e) => handleColor("color_sw_ms", e)}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="control-group">
                      <label>MS Position</label>
                      <select
                        value={config.sw_ms_position || "inline"}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            sw_ms_position: e.target.value,
                          })
                        }
                      >
                        <option value="inline">Inline</option>
                        <option value="above">Above Stopwatch</option>
                        <option value="below">Below Stopwatch</option>
                      </select>
                    </div>
                  </>
                )}
              </div>
            )}

            {config.mode === "warning" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Warning Settings
                </h3>
                <div className="control-group">
                  <label>
                    <Palette size={16} /> Sign Color
                  </label>
                  <div className="color-picker-container">
                    <input
                      type="color"
                      value={rgbToHex(
                        config.warning_color.r,
                        config.warning_color.g,
                        config.warning_color.b,
                      )}
                      onChange={(e) => handleColor("warning_color", e)}
                    />
                  </div>
                </div>
                <div className="control-group">
                  <label>
                    <Activity size={16} /> Size
                  </label>
                  <div className="color-picker-container">
                    <input
                      type="range"
                      min="10"
                      max="64"
                      value={config.warning_size}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          warning_size: parseInt(e.target.value),
                        })
                      }
                    />
                    <span className="slider-val">{config.warning_size}</span>
                  </div>
                </div>
                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Activity size={16} /> Thickness
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={config.warning_thickness}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            warning_thickness: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">
                        {config.warning_thickness}
                      </span>
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Activity size={16} /> Blink Speed
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="1"
                        max="50"
                        value={config.warning_blink_speed}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            warning_blink_speed: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">
                        {config.warning_blink_speed}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "smiley" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Smiley Settings
                </h3>
                <div className="control-group row" style={{ flexWrap: "wrap" }}>
                  <div className="col" style={{ minWidth: "45%" }}>
                    <label>
                      <Palette size={16} /> Face Color
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.smiley_face_color.r,
                          config.smiley_face_color.g,
                          config.smiley_face_color.b,
                        )}
                        onChange={(e) => handleColor("smiley_face_color", e)}
                      />
                    </div>
                  </div>
                  <div className="col" style={{ minWidth: "45%" }}>
                    <label>
                      <Palette size={16} /> Cheeks
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.smiley_cheek_color.r,
                          config.smiley_cheek_color.g,
                          config.smiley_cheek_color.b,
                        )}
                        onChange={(e) => handleColor("smiley_cheek_color", e)}
                      />
                    </div>
                  </div>
                  <div className="col" style={{ minWidth: "45%" }}>
                    <label>
                      <Palette size={16} /> Eyes
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.smiley_eye_color.r,
                          config.smiley_eye_color.g,
                          config.smiley_eye_color.b,
                        )}
                        onChange={(e) => handleColor("smiley_eye_color", e)}
                      />
                    </div>
                  </div>
                  <div className="col" style={{ minWidth: "45%" }}>
                    <label>
                      <Palette size={16} /> Tongue
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.smiley_tongue_color.r,
                          config.smiley_tongue_color.g,
                          config.smiley_tongue_color.b,
                        )}
                        onChange={(e) => handleColor("smiley_tongue_color", e)}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "rain" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Matrix Rain Settings
                </h3>
                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Palette size={16} /> Color
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.rain_color.r,
                          config.rain_color.g,
                          config.rain_color.b,
                        )}
                        onChange={(e) => handleColor("rain_color", e)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Activity size={16} /> Fall Speed
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="1"
                        max="50"
                        value={config.rain_speed}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            rain_speed: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">{config.rain_speed}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "life" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Game of Life Settings
                </h3>
                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Palette size={16} /> Cell Color
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={rgbToHex(
                          config.life_color.r,
                          config.life_color.g,
                          config.life_color.b,
                        )}
                        onChange={(e) => handleColor("life_color", e)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Activity size={16} /> Evo Speed
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="1"
                        max="20"
                        value={config.life_speed}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            life_speed: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">{config.life_speed}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "alarm" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Alarm Settings
                </h3>
                <div className="control-group">
                  <label>
                    <Activity size={16} /> Strobe Speed
                  </label>
                  <div className="color-picker-container">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={config.alarm_speed}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          alarm_speed: parseInt(e.target.value),
                        })
                      }
                    />
                    <span className="slider-val">{config.alarm_speed}</span>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "badapple" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Bad Apple Settings
                </h3>
                <div className="control-group">
                  <label>
                    <Film size={16} /> Invert Colors
                  </label>
                  <div
                    style={{ display: "flex", gap: "8px", marginTop: "10px" }}
                  >
                    <button
                      className={`mode-btn ${!config.badapple_invert ? "active" : ""}`}
                      onClick={() =>
                        updateConfig({ ...config, badapple_invert: false })
                      }
                      style={{
                        flex: 1,
                        padding: "10px",
                        justifyContent: "center",
                      }}
                    >
                      NORMAL (Black BG)
                    </button>
                    <button
                      className={`mode-btn ${config.badapple_invert ? "active" : ""}`}
                      onClick={() =>
                        updateConfig({ ...config, badapple_invert: true })
                      }
                      style={{
                        flex: 1,
                        padding: "10px",
                        justifyContent: "center",
                      }}
                    >
                      INVERTED (White BG)
                    </button>
                  </div>
                </div>
              </div>
            )}

            {config.mode === "qrcode" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  QR Code Settings
                </h3>

                <div className="control-group">
                  <label>
                    <Type size={16} /> Payload Builder
                  </label>
                  <select
                    value={qrPayload.type}
                    onChange={(e) =>
                      handleQrPayloadChange("type", e.target.value)
                    }
                    style={{ marginBottom: "8px" }}
                  >
                    <option value="text">Raw Text / URL</option>
                    <option value="wifi">WiFi Network</option>
                    <option value="vcard">Contact (vCard)</option>
                    <option value="sms">SMS Message</option>
                  </select>

                  {qrPayload.type === "text" && (
                    <input
                      type="text"
                      placeholder="https://..."
                      value={qrPayload.text}
                      onChange={(e) =>
                        handleQrPayloadChange("text", e.target.value)
                      }
                    />
                  )}
                  {qrPayload.type === "wifi" && (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      <input
                        type="text"
                        placeholder="SSID (Network Name)"
                        value={qrPayload.wifiSsid}
                        onChange={(e) =>
                          handleQrPayloadChange("wifiSsid", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Password"
                        value={qrPayload.wifiPass}
                        onChange={(e) =>
                          handleQrPayloadChange("wifiPass", e.target.value)
                        }
                      />
                      <select
                        value={qrPayload.wifiType}
                        onChange={(e) =>
                          handleQrPayloadChange("wifiType", e.target.value)
                        }
                      >
                        <option value="WPA">WPA/WPA2</option>
                        <option value="WEP">WEP</option>
                        <option value="nopass">No Password</option>
                      </select>
                    </div>
                  )}
                  {qrPayload.type === "vcard" && (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      <input
                        type="text"
                        placeholder="Full Name"
                        value={qrPayload.vcardName}
                        onChange={(e) =>
                          handleQrPayloadChange("vcardName", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Phone Number"
                        value={qrPayload.vcardPhone}
                        onChange={(e) =>
                          handleQrPayloadChange("vcardPhone", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Email"
                        value={qrPayload.vcardEmail}
                        onChange={(e) =>
                          handleQrPayloadChange("vcardEmail", e.target.value)
                        }
                      />
                    </div>
                  )}
                  {qrPayload.type === "sms" && (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      <input
                        type="text"
                        placeholder="Phone Number"
                        value={qrPayload.smsPhone}
                        onChange={(e) =>
                          handleQrPayloadChange("smsPhone", e.target.value)
                        }
                      />
                      <input
                        type="text"
                        placeholder="Message"
                        value={qrPayload.smsMsg}
                        onChange={(e) =>
                          handleQrPayloadChange("smsMsg", e.target.value)
                        }
                      />
                    </div>
                  )}
                </div>

                <div className="control-group">
                  <label>Resulting Matrix Payload:</label>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      opacity: 0.7,
                      wordBreak: "break-all",
                    }}
                  >
                    {config.qr_data || " "}
                  </div>
                </div>

                <div className="control-group row">
                  <div className="col">
                    <label>Micro QR (if possible)</label>
                    <div
                      className="toggle-switch"
                      onClick={() =>
                        updateConfig({
                          ...config,
                          qr_use_micro: !config.qr_use_micro,
                        })
                      }
                    >
                      <div style={{ flex: 1, fontWeight: 600 }}>
                        {config.qr_use_micro ? "ON" : "OFF"}
                      </div>
                      <input
                        type="checkbox"
                        checked={config.qr_use_micro}
                        readOnly
                        style={{ pointerEvents: "none" }}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>Error Correction</label>
                    <select
                      value={config.qr_error_correction || "L"}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          qr_error_correction: e.target.value,
                        })
                      }
                    >
                      <option value="L">L (7% Rec)</option>
                      <option value="M">M (15% Rec)</option>
                      <option value="Q">Q (25% Rec)</option>
                      <option value="H">H (30% Rec)</option>
                    </select>
                  </div>
                </div>

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Palette size={16} /> Foreground
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={
                          config.qr_color_fg
                            ? rgbToHex(
                                config.qr_color_fg.r,
                                config.qr_color_fg.g,
                                config.qr_color_fg.b,
                              )
                            : "#ffffff"
                        }
                        onChange={(e) => handleColor("qr_color_fg", e)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Palette size={16} /> Background
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={
                          config.qr_color_bg
                            ? rgbToHex(
                                config.qr_color_bg.r,
                                config.qr_color_bg.g,
                                config.qr_color_bg.b,
                              )
                            : "#000000"
                        }
                        onChange={(e) => handleColor("qr_color_bg", e)}
                      />
                    </div>
                  </div>
                </div>

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Activity size={16} /> Size Mode
                    </label>
                    <select
                      value={config.qr_size_mode || "auto"}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          qr_size_mode: e.target.value,
                        })
                      }
                    >
                      <option value="auto">Auto-Fit (Cleanest)</option>
                      <option value="stretch">Stretch Fill (64x64)</option>
                      <option value="manual">Manual Scale</option>
                    </select>
                  </div>
                  <div className="col">
                    <label>
                      <Activity size={16} /> Wobulation
                    </label>
                    <div
                      className="toggle-switch"
                      onClick={() =>
                        updateConfig({
                          ...config,
                          qr_wobble: !config.qr_wobble,
                        })
                      }
                    >
                      <div style={{ flex: 1, fontWeight: 600 }}>
                        {config.qr_wobble ? "ON (Anti-alias)" : "OFF"}
                      </div>
                      <input
                        type="checkbox"
                        checked={config.qr_wobble}
                        readOnly
                        style={{ pointerEvents: "none" }}
                      />
                    </div>
                  </div>
                </div>

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Hash size={16} /> Quiet Border
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={config.qr_border ?? 1}
                        onChange={(e) =>
                          updateConfig({
                            ...config,
                            qr_border: parseInt(e.target.value),
                          })
                        }
                      />
                      <span className="slider-val">
                        {config.qr_border ?? 1}px
                      </span>
                    </div>
                  </div>

                  {config.qr_size_mode === "manual" && (
                    <div className="col">
                      <label>
                        <Activity size={16} /> Manual Size (Pixels)
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="range"
                          min="10"
                          max="64"
                          value={config.qr_size ?? 58}
                          onChange={(e) =>
                            updateConfig({
                              ...config,
                              qr_size: parseInt(e.target.value),
                            })
                          }
                        />
                        <span className="slider-val">
                          {config.qr_size ?? 58}px
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {config.qr_size_mode === "manual" && (
                  <div className="control-group row">
                    <div className="col">
                      <label>
                        <Move size={16} /> X Position
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="range"
                          min="-64"
                          max="64"
                          value={config.qr_pos_x ?? 0}
                          onChange={(e) =>
                            updateConfig({
                              ...config,
                              qr_pos_x: parseInt(e.target.value),
                            })
                          }
                        />
                        <span className="slider-val">
                          {config.qr_pos_x ?? 0}
                        </span>
                      </div>
                    </div>
                    <div className="col">
                      <label>
                        <Move size={16} /> Y Position
                      </label>
                      <div className="color-picker-container">
                        <input
                          type="range"
                          min="-64"
                          max="64"
                          value={config.qr_pos_y ?? 0}
                          onChange={(e) =>
                            updateConfig({
                              ...config,
                              qr_pos_y: parseInt(e.target.value),
                            })
                          }
                        />
                        <span className="slider-val">
                          {config.qr_pos_y ?? 0}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {config.mode === "draw" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Freehand Draw
                </h3>

                <div className="control-group row">
                  <div className="col">
                    <label>
                      <Palette size={16} /> Brush Color
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={drawColor}
                        onChange={(e) => setDrawColor(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="col">
                    <label>
                      <Palette size={16} /> Background
                    </label>
                    <div className="color-picker-container">
                      <input
                        type="color"
                        value={
                          config.draw_color_bg
                            ? rgbToHex(
                                config.draw_color_bg.r,
                                config.draw_color_bg.g,
                                config.draw_color_bg.b,
                              )
                            : "#000000"
                        }
                        onChange={(e) => handleColor("draw_color_bg", e)}
                      />
                    </div>
                  </div>
                  <div
                    className="col"
                    style={{ display: "flex", alignItems: "flex-end" }}
                  >
                    <button
                      onClick={() => updateConfig({ ...config, draw_data: {} })}
                      className="mode-btn"
                      style={{ width: "100%", justifyContent: "center" }}
                    >
                      <Trash2 size={16} /> Clear
                    </button>
                  </div>
                </div>

                <div className="control-group">
                  <label>Drawing Canvas (64x64 Matrix Representation)</label>
                  <div
                    style={{
                      width: "100%",
                      aspectRatio: "1/1",
                      background: config.draw_color_bg
                        ? rgbToHex(
                            config.draw_color_bg.r,
                            config.draw_color_bg.g,
                            config.draw_color_bg.b,
                          )
                        : "#000",
                      border: "var(--border)",
                      borderRadius: "8px",
                      position: "relative",
                      overflow: "hidden",
                      cursor: "crosshair",
                      touchAction: "none",
                    }}
                    onClick={(e) => handleDrawEvent(e, true)}
                    onMouseDown={(e) => {
                      setIsDrawing(true);
                      handleDrawEvent(e, true);
                    }}
                    onMouseUp={() => setIsDrawing(false)}
                    onMouseLeave={() => setIsDrawing(false)}
                    onMouseMove={(e) => handleDrawEvent(e, isDrawing)}
                    onTouchStart={(e) => {
                      setIsDrawing(true);
                      handleDrawEvent(e, true);
                    }}
                    onTouchEnd={() => setIsDrawing(false)}
                    onTouchMove={(e) => {
                      e.preventDefault();
                      handleDrawEvent(e, isDrawing);
                    }}
                  >
                    {/* Visual Grid Lines */}
                    <div
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundImage:
                          "linear-gradient(var(--text-primary) 1px, transparent 1px), linear-gradient(90deg, var(--text-primary) 1px, transparent 1px)",
                        opacity: 0.2,
                        backgroundSize: "1.5625% 1.5625%",
                        pointerEvents: "none",
                      }}
                    />

                    {/* Render existing pixels as dots */}
                    {Object.entries(config.draw_data || {}).map(
                      ([coord, color]) => {
                        const [x, y] = coord.split(",");
                        return (
                          <div
                            key={coord}
                            style={{
                              position: "absolute",
                              left: `${(x / 64) * 100}%`,
                              top: `${(y / 64) * 100}%`,
                              width: "1.5625%",
                              height: "1.5625%",
                              background: color,
                              borderRadius: "50%",
                              boxShadow: `0 0 4px ${color}`,
                              pointerEvents: "none",
                            }}
                          />
                        );
                      },
                    )}
                  </div>
                  <p
                    style={{
                      fontSize: "0.8rem",
                      opacity: 0.7,
                      marginTop: "8px",
                      textAlign: "center",
                    }}
                  >
                    Click or drag across the grid to paint pixels directly to
                    the matrix.
                  </p>
                </div>
              </div>
            )}

            {config.mode === "spotify" && (
              <div className="state-panel">
                <h3
                  style={{
                    marginBottom: "1rem",
                    borderBottom: "2px solid var(--border)",
                    paddingBottom: "0.5rem",
                  }}
                >
                  Spotify Integration
                </h3>

                <div className="control-group">
                  <label>1. Spotify Developer Credentials</label>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      marginTop: "10px",
                    }}
                  >
                    <input
                      type="text"
                      placeholder="Client ID"
                      value={config.spotify_client_id || ""}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          spotify_client_id: e.target.value,
                        })
                      }
                      style={{ marginBottom: "8px" }}
                    />
                    <input
                      type="password"
                      placeholder="Client Secret"
                      value={config.spotify_client_secret || ""}
                      onChange={(e) =>
                        updateConfig({
                          ...config,
                          spotify_client_secret: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                {!config.spotify_linked ? (
                  <>
                    <div className="control-group">
                      <label>2. Authorization</label>
                      <p
                        style={{
                          fontSize: "0.85rem",
                          opacity: 0.8,
                          marginBottom: "10px",
                        }}
                      >
                        Make sure your Spotify Developer app has the backend
                        redirect URI registered. The default is{" "}
                        <strong style={{ color: "#1DB954" }}>
                          http://127.0.0.1:5000/callback
                        </strong>
                        .
                      </p>
                      <button
                        onClick={async () => {
                          const res = await fetch("/api/spotify/auth_url", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              client_id: config.spotify_client_id,
                              client_secret: config.spotify_client_secret,
                            }),
                          });
                          const data = await res.json();
                          if (data.url) window.open(data.url, "_blank");
                        }}
                        className="mode-btn"
                      >
                        Get Auth URL
                      </button>
                    </div>
                    <div className="control-group">
                      <label>3. Paste Callback URL</label>
                      <p
                        style={{
                          fontSize: "0.85rem",
                          opacity: 0.8,
                          marginBottom: "10px",
                        }}
                      >
                        After logging in, your browser may fail to load the
                        local callback URL. Copy that full URL and paste it
                        here:
                      </p>
                      <div style={{ display: "flex", gap: "10px" }}>
                        <input
                          type="text"
                          placeholder="http://127.0.0.1:5000/callback?code=..."
                          id="spotify_callback_input"
                        />
                        <button
                          onClick={async () => {
                            const url = document.getElementById(
                              "spotify_callback_input",
                            ).value;
                            const res = await fetch("/api/spotify/callback", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                client_id: config.spotify_client_id,
                                client_secret: config.spotify_client_secret,
                                url: url,
                              }),
                            });
                            const data = await res.json();
                            if (data.status === "success") {
                              updateConfig({ ...config, spotify_linked: true });
                              document.getElementById(
                                "spotify_callback_input",
                              ).value = "";
                            } else {
                              alert(data.message);
                            }
                          }}
                          className="mode-btn"
                        >
                          Link
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div
                    className="control-group"
                    style={{ background: "var(--input-bg)" }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        color: "var(--text-primary)",
                        fontWeight: "900",
                        textTransform: "uppercase",
                        marginBottom: "10px",
                      }}
                    >
                      <div
                        style={{
                          width: "16px",
                          height: "16px",
                          background: "var(--accent)",
                          border: "var(--border)",
                        }}
                      />
                      Spotify is Linked!
                    </div>
                    <button
                      onClick={async () => {
                        await fetch("/api/spotify/unlink", { method: "POST" });
                        updateConfig({
                          ...config,
                          spotify_linked: false,
                          spotify_client_id: "",
                          spotify_client_secret: "",
                        });
                      }}
                      className="mode-btn"
                    >
                      Unlink Account
                    </button>
                    <p
                      style={{
                        fontSize: "0.8rem",
                        opacity: 0.8,
                        marginTop: "10px",
                      }}
                    >
                      Play a song on Spotify and the album art will
                      automatically appear on your matrix.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="layout-col">
          <div
            className="glass-panel"
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
              }}
            >
              <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>
                Live Preview
              </h3>
              <div
                className="toggle-switch"
                style={{
                  width: "auto",
                  margin: 0,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                }}
                onClick={() => setShowPreview(!showPreview)}
              >
                <span style={{ fontSize: "0.8rem", opacity: 0.8 }}>
                  {showPreview ? "ON" : "OFF"}
                </span>
                <input
                  type="checkbox"
                  checked={showPreview}
                  readOnly
                  style={{ pointerEvents: "none" }}
                />
              </div>
            </div>
            {showPreview ? (
              <MatrixPreview />
            ) : (
              <div
                style={{
                  width: "256px",
                  height: "256px",
                  background: "var(--input-bg)",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  color: "var(--text-primary)",
                  border: "var(--border)",
                  marginBottom: "2rem",
                }}
              >
                Preview Disabled
              </div>
            )}
          </div>
          <PresetsPanel
            config={config}
            updateConfig={updateConfig}
            activePreset={activePreset}
            setActivePreset={setActivePreset}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
