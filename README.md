# Mwago — Your Remote Mouse & Projector Controller
**Safe Spaces AI Innovation Hub • Mbarara, Uganda**  
*Website:* [safespaceshub.com](https://safespaceshub.com) • *Landing Page:* [mwago.safespaceshub.com](https://mwago.safespaceshub.com) • *Repository:* [Safe-Spaces-AI/mwago](https://github.com/Safe-Spaces-AI/mwago)

[![Safe Spaces](https://img.shields.io/badge/Safe_Spaces_AI-Innovation_Hub-10b981.svg)](https://safespaceshub.com)
[![Platform](https://img.shields.io/badge/Platform-Windows_10_%2F_11-38bdf8.svg)](#)
[![Mobile Support](https://img.shields.io/badge/Mobile-Android_4.0%2B_%7C_iOS-emerald.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](#)

---

## Overview

**Mwago** is a lightweight, local-first utility that transforms any smartphone into a precision touchpad, presentation clicker, and multi-monitor controller for Windows PCs and HDMI projectors.

Built following the **Safe Spaces AI Hub Data Sovereignty and Inclusive Edge Computing Manifesto**, Mwago features:
- **Works Down to Android 4.0+ (Ice Cream Sandwich & KitKat):** Zero APKs, zero app installs. Hand-crafted in backward-compatible ES5 for legacy WebKit browsers.
- **Smart Projector & Multi-Display Lock:** Teleport the cursor to your secondary screen (e.g. HDMI projector) and lock boundary coordinates so your mouse never drifts back onto your laptop screen.
- **Sub-5ms Local Wi-Fi Latency:** Direct communication with rate-limited delta buffers.
- **100% Offline & Private:** Zero external telemetry, zero tracking, zero cloud dependencies.
- **Presentation Controls:** Dedicated clicker bar for PowerPoint, Google Slides, and PDF presentations (`PageDown`, `PageUp`, `F5`, `Esc`).
- **Instant Block Paste & Wireless Text Beam:** Paste multi-line code blocks, scripts, and indented text directly into your PC's active window with exact indentation and formatting preserved. Also supports legacy character-by-character typing.

---

## Repository Structure

```
mwago/
├── app.py                 # Core Python server & Win32 input injector
├── mwago.exe              # Standalone 7.9MB Windows executable
├── mwago.spec             # PyInstaller build specification
├── logo.png               # Official Mwago brand mark
├── amplify.yml            # AWS Amplify Hosting configuration
├── vercel.json            # Vercel hosting rules and download headers
└── public/                # Web landing page & distribution assets
    ├── index.html         # Landing page (mwago.safespaceshub.com)
    ├── logo.png           # Brand icon
    ├── favicon.png        # Browser favicon
    └── downloads/
        └── mwago.exe      # Direct download mirror
```

---

## Quick Start (For Users)

1. **Download:** Get the latest [`mwago.exe`](https://github.com/Safe-Spaces-AI/mwago/releases/latest/download/mwago.exe) from GitHub Releases or from [mwago.safespaceshub.com](https://mwago.safespaceshub.com).
2. **Run:** Double-click `mwago.exe`. It automatically detects your primary and secondary displays and launches your private server.
3. **Connect:** Ensure your phone is on the same Wi-Fi. Open your phone's browser and go to the IP address displayed (e.g., `http://192.168.18.4:5000`).

---

## Building from Source

```bash
# Clone the repository
git clone https://github.com/Safe-Spaces-AI/mwago.git
cd mwago

# Run the Python server directly
python app.py 5000

# Build the standalone Windows executable
pyinstaller --onefile --name mwago app.py
```

---

## How to Create GitHub Releases

The landing page and download buttons automatically resolve downloads from:  
`https://github.com/Safe-Spaces-AI/mwago/releases/latest/download/mwago.exe`

To publish a new release:
1. Go to [https://github.com/Safe-Spaces-AI/mwago/releases](https://github.com/Safe-Spaces-AI/mwago/releases).
2. Click **"Draft a new release"**.
3. In **"Choose a tag"**, enter `v1.0.0` (or your next version) and choose **"Create new tag on publish"**.
4. Set the **Release title** (e.g. `Mwago v1.0.0 — Remote Mouse & Projector Controller`).
5. In the **"Attach binaries"** drop area, attach `mwago.exe` (7.9 MB).
6. Check **"Set as the latest release"** and click **"Publish release"**.

---

## Cloud Hosting for `mwago.safespaceshub.com`

The landing page is in `public/index.html` and can be deployed with zero hassle:

### Option A: AWS Amplify Hosting (Recommended)
1. In the [AWS Amplify Console](https://console.aws.amazon.com/amplify), click **Host web app**.
2. Connect your GitHub repository (`Safe-Spaces-AI/mwago`) and branch `main`.
3. Amplify will auto-detect [`amplify.yml`](amplify.yml) and deploy the `public/` directory with global CDN caching.
4. Under **Domain management**, map your custom domain (`mwago.safespaceshub.com`).

### Option B: AWS S3 + CloudFront
```powershell
# Create bucket and upload public folder
aws s3 mb s3://mwago-landing-page --region us-east-1
aws s3 sync public/ s3://mwago-landing-page
```

### Option C: Vercel or GitHub Pages
- **Vercel:** Run `vercel --prod` inside `public/` or connect the GitHub repo.
- **GitHub Pages:** Set GitHub Pages source to `/public` on `main`.

---

## About Safe Spaces AI Innovation Hub

Safe Spaces AI Innovation Hub (SMC Limited) is based in Mbarara, Uganda. We pioneer localized edge AI, offline-first architectures, and inclusive technologies for underserved communities.

- **Website:** [safespaceshub.com](https://safespaceshub.com)
- **Email:** [info@safespaceshub.com](mailto:info@safespaceshub.com)
- **Physical Location:** Hive Colab, 4th Floor • Amazon Building, Mbarara High Street, Uganda
- **Google Maps:** [Open Location on Google Maps](https://maps.google.com/?q=Hive+Colab,+Amazon+Building,+High+Street,+Mbarara,+Uganda)

---

## License

Released under the [MIT License](LICENSE).