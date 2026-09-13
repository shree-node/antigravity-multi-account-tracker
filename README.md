# ?? Antigravity Multi-Account Tracker

A sleek, neon-themed desktop widget for tracking your Google Antigravity API quotas across multiple accounts in real-time.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ? Features

- **Multi-Account Dashboard** — Track quotas for multiple Google accounts side by side
- **Live Countdown Timers** — Real-time ticking countdown showing exactly when each model's quota resets (5-hour daily / weekly)
- **Cascading Animated Refresh** — Click the global refresh and watch it sequentially animate through each account
- **Per-Account Refresh** — Click any individual account's refresh button to update just that one
- **Modern Neon UI** — Dark Onyx background, Deep Orange title bar, Neon Green progress bars
- **Smart Tooltips** — Hover over any progress bar to see exact used/limit numbers and UTC reset time
- **Thread-Safe Architecture** — Proper locking, subprocess timeouts, and input validation
- **Zero Dependencies** — Uses only Python standard library (Tkinter) — no pip installs needed

---

## ?? Prerequisites

- **Python 3.10+** with Tkinter (included by default on Windows)
- **Antigravity CLI** installed and authenticated:
  `ash
  antigravity-usage accounts add
  `

---

## ?? Quick Start

1. **Clone the repo:**
   `ash
   git clone https://github.com/YOUR_USERNAME/antigravity-multi-account-tracker.git
   cd antigravity-multi-account-tracker
   `

2. **Launch the widget:**
   `ash
   # Option A: Double-click launch.bat
   # Option B: Run from terminal
   python quota_widget.py
   `

3. **Add your accounts** using the ? button in the title bar

---

## ?? UI Overview

| Element | Color | Hex |
|---|---|---|
| Background | Midnight Onyx | `#09090B` |
| Title Bar | Dark Orange | `#9A3412` |
| Model Labels | Bright Orange | `#F97316` |
| Progress Bars | Neon Green | `#4ADE80` |
| Low Quota Warning | Red | `#EF4444` |
| Reset Timer | Amber Yellow | `#FCD34D` |

---

## ??? Security

- **No shell injection** — All subprocess calls use argument lists, never `shell=True` with interpolation
- **Email validation** — Regex-validated before any CLI invocation
- **Subprocess timeouts** — 20-second timeout prevents permanent app lockup
- **No API keys stored** — Authentication is handled entirely by the Antigravity CLI

---

## ?? Project Structure

`
antigravity-multi-account-tracker/
+-- quota_widget.py      # Main application
+-- launch.bat           # One-click Windows launcher
+-- quota_icon.ico       # Custom app icon
+-- refresh_icon.png     # Green arrow refresh button
+-- spinner_frame_*.png  # 8-frame loading animation
+-- .gitignore
+-- LICENSE              # MIT
+-- README.md
`

---

## ?? Contributing

Pull requests welcome! If you'd like to add features like:
- Linux/macOS support
- VS Code extension port
- Auto-start on Windows login
- Notification alerts when quota drops below threshold

Feel free to open an issue or PR.

---

## ? Support

If this tool saves you time, consider buying me a coffee!

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/)

---

## ?? License

MIT License — see [LICENSE](LICENSE) for details.

> **Disclaimer:** This is an unofficial community tool. Not affiliated with or endorsed by Google.
