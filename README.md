# Mwago — Your Remote Mouse & Projector Controller
**Safe Spaces AI Innovation Hub • Mbarara, Uganda**  
*Website:* [safespaceshub.com](https://safespaceshub.com) • *Landing Page:* [mwago.safespaceshub.com](https://mwago.safespaceshub.com)

[![Safe Spaces](https://img.shields.io/badge/Safe_Spaces_AI-Innovation_Hub-10b981.svg)](https://safespaceshub.com)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-38bdf8.svg)](#)
[![Mobile Support](https://img.shields.io/badge/Mobile-Android_4.0%2B_%7C_iOS-emerald.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](#)

---

## Overview

**Mwago** is a lightweight, local-first utility that transforms any smartphone into a precision touchpad, presentation clicker, and multi-monitor controller for Windows PCs and HDMI projectors.

Built following the **Safe Spaces AI Hub Data Sovereignty and Inclusive Edge Computing Manifesto**, Mwago features:
- **Works Down to Android 4.0 (Ice Cream Sandwich & KitKat):** Zero APKs, zero app installs. Hand-crafted in backward-compatible ES5 for legacy WebKit browsers.
- **Smart Projector & Multi-Display Lock:** Teleport the cursor to your secondary screen (e.g. HDMI projector) and lock boundary coordinates so your mouse never drifts back onto your laptop screen.
- **Sub-5ms Local Wi-Fi Latency:** Direct communication with rate-limited delta buffers.
- **100% Offline & Private:** Zero external telemetry, zero tracking, zero cloud dependencies.
- **Presentation Controls:** Dedicated clicker bar for PowerPoint, Google Slides, and PDF presentations (`PageDown`, `PageUp`, `F5`, `Esc`).

---

## Quick Start (For Users)

1. **Download:** Get the latest [`mwago.exe`](https://github.com/safe-spaces-solutions/mwago/releases/latest/download/mwago.exe) from GitHub Releases or from [mwago.safespaceshub.com](https://mwago.safespaceshub.com).
2. **Run:** Double-click `mwago.exe`. It automatically detects your primary and secondary displays and launches your private server.
3. **Connect:** Ensure your phone is on the same Wi-Fi. Open your phone's browser and go to the IP address displayed (e.g., `http://192.168.18.4:5000`).

---

## Building from Source

```bash
# Clone the repository
git clone https://github.com/safe-spaces-solutions/mwago.git
cd mwago

# Run the Python server directly
python app.py 5000

# Build the standalone Windows executable
pyinstaller --onefile --name mwago app.py
```

---

## Hosting `mwago.safespaceshub.com`

The landing page is in `public/index.html`. It can be deployed in 1 click:
- **Vercel:** Run `vercel --prod` inside `public/` or connect the GitHub repo.
- **GitHub Pages:** Set GitHub Pages source to `/public`.
- Point the DNS CNAME record for `mwago.safespaceshub.com` to `cname.vercel-dns.com` (or your GitHub Pages domain).

---

## About Safe Spaces AI Innovation Hub

Safe Spaces AI Innovation Hub (SMC Limited) is based in Mbarara, Uganda at Hive Colab, Amazon Building. We pioneer localized edge AI, offline-first architectures, and inclusive technologies for underserved communities.
