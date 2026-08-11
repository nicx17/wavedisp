
with open("dashboard/src/App.jsx", "r") as f:
    lines = f.readlines()

# 1. Update imports
for i, line in enumerate(lines):
    if "Timer," in line:
        lines.insert(i + 1, "  Power,\n")
        break

# 2. Update buttons
for i, line in enumerate(lines):
    if 'onClick={() => handleMode("clock")}' in line:
        button_code = """                <button
                  onClick={() => handleMode("off")}
                  className={`mode-btn ${config.mode === "off" ? "active" : ""}`}
                >
                  <Power size={16} /> Off
                </button>
"""
        lines.insert(i - 1, button_code)

        button_code2 = """                <button
                  onClick={() => handleMode("stopwatch")}
                  className={`mode-btn ${config.mode === "stopwatch" ? "active" : ""}`}
                >
                  <Timer size={16} /> Stopwatch
                </button>
"""
        lines.insert(i + 4, button_code2)  # after the clock button closes
        break

# 3. Move stopwatch settings
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "<Timer size={20} /> Stopwatch" in line:
        start_idx = i - 12  # Find the <h3>
        break

if start_idx != -1:
    for i in range(start_idx, len(lines)):
        if "             </>" in lines[i]:
            # It ends with </> then )}
            end_idx = i + 1
            break

    if end_idx != -1:
        # Extract the stopwatch lines
        stopwatch_lines = lines[start_idx : end_idx + 1]
        del lines[start_idx : end_idx + 1]

        # Now find where to insert it (before {config.mode === "warning" && ()
        for i, line in enumerate(lines):
            if '{config.mode === "warning" && (' in line:
                # build the new panel
                new_panel = '            {config.mode === "stopwatch" && (\n              <div className="state-panel">\n'
                new_panel += '                <h3\n                  style={{\n                    marginBottom: "1rem",\n'
                new_panel += '                    borderBottom: "2px solid var(--border)",\n                    paddingBottom: "0.5rem",\n'
                new_panel += '                    display: "flex",\n                    alignItems: "center",\n'
                new_panel += '                    gap: "0.5rem",\n                  }}\n                >\n'
                new_panel += "                  <Timer size={20} /> Stopwatch\n                </h3>\n\n"

                # filter out the toggle for Enable Stopwatch Overlay (which was in control-group row with Force Show Hours)
                # Actually it's easier to just recreate the body of stopwatch settings.
                break
