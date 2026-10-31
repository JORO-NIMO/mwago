"""
Mwago - Your Remote Mouse & Projector Controller
Developed for Safe Spaces AI Innovation Hub (https://safespaceshub.com)
Mbarara, Uganda

Enables any mobile phone (down to Android 4.0+) to act as a high-precision
touchpad, presentation remote, and multi-monitor controller over Wi-Fi.
"""

import sys
import os
import json
import socket
import ctypes
import webbrowser
import time
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Windows API Constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21  # Page Up
VK_NEXT = 0x22   # Page Down
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_V = 0x56
VK_F5 = 0x74

GMEM_MOVEABLE = 0x0002
GMEM_DDESHARE = 0x2000
CF_UNICODETEXT = 13
HWND_MESSAGE = -3

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Configure 64-bit safe Win32 API ctypes signatures
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_bool

user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_bool
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = ctypes.c_bool
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.c_bool

user32.CreateWindowExW.argtypes = [
    ctypes.c_ulong, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
]
user32.CreateWindowExW.restype = ctypes.c_void_p
user32.DestroyWindow.argtypes = [ctypes.c_void_p]
user32.DestroyWindow.restype = ctypes.c_bool

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
        ("szDevice", ctypes.c_wchar * 32),
    ]

# Monitor detection
screens = []
projector_bounds = {"x_min": 1366, "x_max": 2732, "y_min": 0, "y_max": 768}
primary_bounds = {"x_min": 0, "x_max": 1366, "y_min": 0, "y_max": 768}
lock_to_projector = False

def detect_monitors():
    global screens, projector_bounds, primary_bounds
    screens = []
    
    def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
        info = MONITORINFOEX()
        info.cbSize = ctypes.sizeof(MONITORINFOEX)
        if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info)):
            r = info.rcMonitor
            is_primary = bool(info.dwFlags & 1)
            screens.append({
                "device": info.szDevice,
                "is_primary": is_primary,
                "x_min": r.left,
                "x_max": r.right,
                "y_min": r.top,
                "y_max": r.bottom,
                "width": r.right - r.left,
                "height": r.bottom - r.top
            })
        return True

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(RECT),
        ctypes.c_void_p
    )

    cb = MONITORENUMPROC(monitor_enum_proc)
    ctypes.windll.user32.EnumDisplayMonitors(None, None, cb, 0)

    if screens:
        # Sort so primary is first
        screens.sort(key=lambda s: not s["is_primary"])
        primary_bounds = screens[0]
        if len(screens) > 1:
            projector_bounds = screens[1]
        else:
            projector_bounds = screens[0]

detect_monitors()

def attach_interactive_desktop():
    """Ensure the calling thread attaches to the active interactive Windows desktop."""
    try:
        u32 = ctypes.windll.user32
        hwinsta = u32.OpenWindowStationW('WinSta0', False, 0x037F)
        if hwinsta:
            u32.SetProcessWindowStation(hwinsta)
        hdesk = u32.OpenDesktopW('Default', 0, False, 0x01FF)
        if hdesk:
            u32.SetThreadDesktop(hdesk)
    except Exception:
        pass

def get_cursor_pos():
    attach_interactive_desktop()
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def set_cursor_pos(x, y):
    attach_interactive_desktop()
    global lock_to_projector, projector_bounds
    if lock_to_projector:
        x = max(projector_bounds["x_min"], min(projector_bounds["x_max"] - 1, x))
        y = max(projector_bounds["y_min"], min(projector_bounds["y_max"] - 1, y))
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def move_mouse_relative(dx, dy):
    curr_x, curr_y = get_cursor_pos()
    set_cursor_pos(curr_x + dx, curr_y + dy)

def jump_to_projector():
    attach_interactive_desktop()
    target_x = projector_bounds["x_min"] + (projector_bounds["x_max"] - projector_bounds["x_min"]) // 2
    target_y = projector_bounds["y_min"] + (projector_bounds["y_max"] - projector_bounds["y_min"]) // 2
    ctypes.windll.user32.SetCursorPos(target_x, target_y)

def jump_to_primary():
    attach_interactive_desktop()
    target_x = primary_bounds["x_min"] + (primary_bounds["x_max"] - primary_bounds["x_min"]) // 2
    target_y = primary_bounds["y_min"] + (primary_bounds["y_max"] - primary_bounds["y_min"]) // 2
    ctypes.windll.user32.SetCursorPos(target_x, target_y)

def mouse_click(button="left", double=False):
    attach_interactive_desktop()
    if button == "left":
        down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button == "right":
        down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    elif button == "middle":
        down, up = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP
    else:
        return

    ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
    ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)
    if double:
        ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

def mouse_drag(action="start"):
    attach_interactive_desktop()
    if action == "start":
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif action == "stop":
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def mouse_scroll(delta):
    attach_interactive_desktop()
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)

def send_key(vk_code):
    attach_interactive_desktop()
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def set_clipboard_text(text):
    """Place unicode text into the Windows clipboard with exact formatting and line breaks."""
    attach_interactive_desktop()
    # Normalize line breaks to standard Windows \r\n format so indents & newlines are respected everywhere
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    text_bytes = (text + '\0').encode('utf-16le')

    hwnd = None
    try:
        hwnd = user32.CreateWindowExW(0, "STATIC", "MwagoClip", 0, 0, 0, 0, 0, HWND_MESSAGE, 0, 0, 0)
    except Exception:
        pass

    opened = False
    for _ in range(10):
        try:
            if user32.OpenClipboard(hwnd):
                opened = True
                break
        except Exception:
            pass
        time.sleep(0.01)

    if not opened:
        if hwnd:
            try:
                user32.DestroyWindow(hwnd)
            except Exception:
                pass
        return False

    success = False
    try:
        user32.EmptyClipboard()
        size = len(text_bytes)
        hCd = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_DDESHARE, size)
        if hCd:
            pchData = kernel32.GlobalLock(hCd)
            if pchData:
                ctypes.memmove(pchData, text_bytes, size)
                kernel32.GlobalUnlock(hCd)
                res = user32.SetClipboardData(CF_UNICODETEXT, hCd)
                if res:
                    success = True
    except Exception:
        pass
    finally:
        try:
            user32.CloseClipboard()
        except Exception:
            pass
        if hwnd:
            try:
                user32.DestroyWindow(hwnd)
            except Exception:
                pass

    return success

def copy_to_clipboard(text):
    """Copy text to clipboard with Win32 API and clip.exe fallback."""
    if set_clipboard_text(text):
        return True
    try:
        p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True, encoding="utf-8")
        p.communicate(text)
        if p.returncode == 0:
            return True
    except Exception:
        pass
    return False

def send_paste_shortcut():
    """Simulate Ctrl+V to paste the clipboard contents into the active window."""
    attach_interactive_desktop()
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

def type_text_fast(text):
    """Fallback fast typing character-by-character with clean newline/tab handling."""
    attach_interactive_desktop()
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    for char in text:
        if char == '\n':
            user32.keybd_event(VK_RETURN, 0, 0, 0)
            user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
        elif char == '\t':
            user32.keybd_event(VK_TAB, 0, 0, 0)
            user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
        else:
            val = ord(char)
            user32.keybd_event(0, val, KEYEVENTF_UNICODE, 0)
            user32.keybd_event(0, val, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)

def paste_block_to_pc(text):
    """Pastes text block directly into the focused PC application as-is with exact indentation."""
    attach_interactive_desktop()
    if copy_to_clipboard(text):
        time.sleep(0.03)
        send_paste_shortcut()
        return True
    else:
        type_text_fast(text)
        return False

def type_text(text):
    paste_block_to_pc(text)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.18.4"

def handle_command(cmd, params):
    global lock_to_projector, projector_bounds
    if cmd == "move":
        dx = float(params.get("dx", 0))
        dy = float(params.get("dy", 0))
        move_mouse_relative(dx, dy)
    elif cmd == "click":
        btn = params.get("button", "left")
        dbl = bool(params.get("double", False))
        mouse_click(btn, dbl)
    elif cmd == "drag":
        act = params.get("action", "start")
        mouse_drag(act)
    elif cmd == "scroll":
        delta = int(params.get("delta", 0))
        mouse_scroll(delta)
    elif cmd == "jump_screen":
        scr = params.get("screen", "projector")
        if scr == "projector":
            jump_to_projector()
        else:
            jump_to_primary()
    elif cmd == "toggle_lock":
        lock_to_projector = not lock_to_projector
        if lock_to_projector:
            jump_to_projector()
        return {"lock": lock_to_projector}
    elif cmd == "key":
        k = params.get("key")
        mapping = {
            "pagedown": VK_NEXT,
            "pageup": VK_PRIOR,
            "f5": VK_F5,
            "esc": VK_ESCAPE,
            "space": VK_SPACE,
            "enter": VK_RETURN,
            "backspace": VK_BACK,
            "left": VK_LEFT,
            "right": VK_RIGHT,
            "up": VK_UP,
            "down": VK_DOWN
        }
        if k in mapping:
            send_key(mapping[k])
    elif cmd in ("text", "paste_text"):
        t = params.get("text", "")
        mode = params.get("mode", "paste")
        if t:
            if mode == "type":
                type_text_fast(t)
            else:
                paste_block_to_pc(t)
    elif cmd == "status":
        x, y = get_cursor_pos()
        on_proj = (
            x >= projector_bounds["x_min"] and x <= projector_bounds["x_max"] and
            y >= projector_bounds["y_min"] and y <= projector_bounds["y_max"]
        )
        return {
            "x": x,
            "y": y,
            "lock": lock_to_projector,
            "on_projector": on_proj,
            "screen_count": len(screens)
        }
    return {"status": "ok"}

# Embedded HTML for standalone execution (0 dependencies)
EMBEDDED_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mwago - Remote Mouse</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎯</text></svg>">
  <style>
    * { -webkit-box-sizing: border-box; box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; -webkit-user-select: none; user-select: none; }
    html, body { width: 100%; height: 100%; overflow: hidden; background: #0c0e14; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; touch-action: none; }
    #container { display: block; width: 100%; height: 100%; position: relative; }
    #header { width: 100%; height: 50px; background: #151922; border-bottom: 1px solid #232a3b; padding: 7px 10px; overflow: hidden; }
    .brand-pill { float: left; height: 34px; line-height: 34px; font-size: 13px; font-weight: bold; color: #10b981; letter-spacing: 0.5px; margin-right: 8px; }
    .h-btn { float: left; height: 34px; padding: 0 10px; margin-right: 6px; background: #1e2536; color: #38bdf8; border: 1px solid #334155; border-radius: 6px; font-size: 12px; font-weight: bold; line-height: 32px; text-align: center; }
    .h-btn:active, .h-btn.active { background: #0284c7; color: #ffffff; border-color: #38bdf8; }
    #status-dot { float: right; height: 34px; line-height: 34px; font-size: 11px; color: #10b981; font-weight: bold; }
    #pres-bar { width: 100%; height: 38px; background: #11141c; border-bottom: 1px solid #1e2433; padding: 4px 8px; }
    .p-btn { float: left; width: 23%; height: 30px; margin-right: 2%; background: #1c2230; color: #94a3b8; border: 1px solid #2d3748; border-radius: 4px; font-size: 12px; font-weight: bold; line-height: 28px; text-align: center; }
    .p-btn:active { background: #0284c7; color: #ffffff; }
    #touch-wrap { position: absolute; top: 88px; bottom: 82px; left: 0; right: 0; width: 100%; background: #0c0e14; }
    #touchpad { position: absolute; top: 6px; bottom: 6px; left: 6px; right: 58px; background: #131722; border: 2px dashed #232b3e; border-radius: 10px; }
    #tp-guide { position: absolute; top: 40%; width: 100%; text-align: center; color: #475569; font-size: 13px; pointer-events: none; line-height: 20px; }
    #scroll-strip { position: absolute; top: 6px; bottom: 6px; right: 6px; width: 46px; background: #161b26; border: 1px solid #2a3449; border-radius: 8px; text-align: center; }
    #scroll-label { position: absolute; top: 40%; width: 100%; text-align: center; color: #64748b; font-size: 11px; line-height: 15px; pointer-events: none; }
    #footer-bar { position: absolute; bottom: 0; left: 0; right: 0; width: 100%; height: 82px; background: #131722; border-top: 1px solid #232a3b; padding: 8px; }
    .c-btn { float: left; height: 64px; border-radius: 8px; font-size: 15px; font-weight: bold; text-align: center; line-height: 62px; }
    #b-left { width: 64%; background: #10b981; color: #022c22; border: 1px solid #34d399; margin-right: 2%; }
    #b-left:active { background: #059669; color: #ffffff; }
    #b-right { width: 34%; background: #262f40; color: #e2e8f0; border: 1px solid #3b475e; }
    #b-right:active { background: #1a202c; }
    #text-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(4, 6, 10, 0.88);
      z-index: 100;
      padding: 14px;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      box-sizing: border-box;
    }
    .modal-card {
      max-width: 480px;
      margin: 10px auto;
      background: #131722;
      border: 1px solid #2a3449;
      border-radius: 10px;
      padding: 16px;
      box-shadow: 0 12px 36px rgba(0,0,0,0.85);
      box-sizing: border-box;
    }
    .modal-head {
      overflow: hidden;
      margin-bottom: 6px;
    }
    .modal-title {
      float: left;
      font-size: 15px;
      font-weight: bold;
      color: #10b981;
      line-height: 28px;
    }
    .modal-close {
      float: right;
      width: 28px;
      height: 28px;
      line-height: 26px;
      text-align: center;
      background: #1c2230;
      color: #94a3b8;
      border: 1px solid #2d3748;
      border-radius: 6px;
      font-size: 14px;
      cursor: pointer;
    }
    .modal-sub {
      font-size: 12px;
      color: #94a3b8;
      margin-bottom: 10px;
      line-height: 1.4;
      clear: both;
    }
    #t-input {
      width: 100%;
      height: 140px;
      min-height: 110px;
      font-family: Consolas, 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.45;
      padding: 8px;
      border: 1px solid #334155;
      border-radius: 6px;
      background: #090c13;
      color: #f1f5f9;
      margin-bottom: 8px;
      white-space: pre;
      overflow-wrap: normal;
      overflow-x: auto;
      tab-size: 4;
      -moz-tab-size: 4;
      -webkit-user-select: text !important;
      user-select: text !important;
      touch-action: auto !important;
      box-sizing: border-box;
      outline: none;
    }
    #t-input:focus {
      border-color: #10b981;
    }
    .text-tools {
      overflow: hidden;
      margin-bottom: 12px;
      font-size: 11px;
      color: #64748b;
      line-height: 26px;
    }
    .tool-group {
      float: left;
    }
    .tool-btn {
      float: left;
      height: 26px;
      line-height: 24px;
      padding: 0 8px;
      margin-right: 6px;
      background: #1c2333;
      color: #38bdf8;
      border: 1px solid #2a3449;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      cursor: pointer;
    }
    .tool-btn:active {
      background: #0284c7;
      color: #ffffff;
    }
    #text-stats {
      float: right;
    }
    .action-row {
      overflow: hidden;
    }
    .dlg-btn {
      height: 40px;
      line-height: 38px;
      font-size: 13px;
      font-weight: bold;
      border-radius: 6px;
      border: none;
      cursor: pointer;
      text-align: center;
      padding: 0 10px;
      box-sizing: border-box;
    }
    #b-send {
      width: 60%;
      float: left;
      background: #10b981;
      color: #022c22;
      border: 1px solid #34d399;
      margin-right: 2%;
    }
    #b-send:active {
      background: #059669;
      color: #ffffff;
    }
    #b-type {
      width: 25%;
      float: left;
      background: #1e2638;
      color: #38bdf8;
      border: 1px solid #334155;
      margin-right: 2%;
    }
    #b-type:active {
      background: #0f172a;
    }
    #b-cancel {
      width: 11%;
      float: left;
      background: #202738;
      color: #94a3b8;
      border: 1px solid #2f3b52;
    }
  </style>
</head>
<body>
<div id="container">
  <div id="header">
    <div class="brand-pill">MWAGO</div>
    <div id="btn-jump" class="h-btn" onclick="jumpProjector()">🎯 Screen</div>
    <div id="btn-lock" class="h-btn" onclick="toggleLock()">🔓 Unlock</div>
    <div class="h-btn" onclick="showText()">⌨️ Text</div>
    <div id="status-dot">● Ready</div>
  </div>
  <div id="pres-bar">
    <div class="p-btn" onclick="sendKey('pageup')">◀ Prev</div>
    <div class="p-btn" onclick="sendKey('pagedown')">Next ▶</div>
    <div class="p-btn" onclick="sendKey('f5')">🖥️ F5</div>
    <div class="p-btn" onclick="sendKey('esc')">✕ Esc</div>
  </div>
  <div id="touch-wrap">
    <div id="touchpad">
      <div id="tp-guide">Safe Spaces • Mwago<br>Slide to move<br>Tap to click • 2-finger right click</div>
    </div>
    <div id="scroll-strip">
      <div id="scroll-label">▲<br>S<br>C<br>R<br>O<br>L<br>L<br>▼</div>
    </div>
  </div>
  <div id="footer-bar">
    <div id="b-left" class="c-btn" onmousedown="leftClick()" ontouchstart="leftClick()">LEFT CLICK</div>
    <div id="b-right" class="c-btn" onmousedown="rightClick()" ontouchstart="rightClick()">RIGHT</div>
  </div>
</div>
<div id="text-overlay">
  <div class="modal-card">
    <div class="modal-head">
      <div class="modal-title">📋 Send Text / Code to PC</div>
      <div class="modal-close" onclick="hideText()">✕</div>
    </div>
    <div class="modal-sub">
      Paste indented code, paragraphs, or commands. Formatted blocks, indentation, and tabs are preserved.
    </div>
    <textarea id="t-input" placeholder="Paste or type text / code here..." wrap="off" spellcheck="false" oninput="updateTextStats()"></textarea>
    <div class="text-tools">
      <div class="tool-group">
        <button class="tool-btn" type="button" onclick="pasteFromPhone()">📋 Paste from Phone</button>
        <button class="tool-btn" type="button" onclick="clearText()">🗑️ Clear</button>
      </div>
      <div id="text-stats">0 lines • 0 chars</div>
    </div>
    <div class="action-row">
      <button class="dlg-btn" id="b-send" type="button" onclick="sendText('paste')">⚡ Paste to PC (Block)</button>
      <button class="dlg-btn" id="b-type" type="button" onclick="sendText('type')">⌨️ Type</button>
      <button class="dlg-btn" id="b-cancel" type="button" onclick="hideText()">✕</button>
    </div>
  </div>
</div>
<script>
  // Strict ES5 for full Android 4.0 - 4.4 compatibility
  var touchpad = document.getElementById("touchpad");
  var scrollStrip = document.getElementById("scroll-strip");
  var lockBtn = document.getElementById("btn-lock");
  var lastX = 0, lastY = 0, touchStart = 0, moved = false, touches = 0;
  var sensitivity = 1.7;
  var isSending = false, qDx = 0, qDy = 0;

  function sendCmd(cmd, params, cb) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/cmd", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && cb) {
        try { cb(JSON.parse(xhr.responseText)); } catch(e) { cb(null); }
      }
    };
    xhr.send(JSON.stringify({ cmd: cmd, params: params || {} }));
  }

  function flush() {
    if (isSending || (qDx === 0 && qDy === 0)) return;
    var dx = qDx, dy = qDy;
    qDx = 0; qDy = 0; isSending = true;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/cmd", true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4) {
        isSending = false;
        if (qDx !== 0 || qDy !== 0) flush();
      }
    };
    xhr.send(JSON.stringify({ cmd: "move", params: { dx: dx, dy: dy } }));
  }

  touchpad.addEventListener("touchstart", function(e) {
    e.preventDefault();
    touches = e.touches.length;
    var t = e.touches[0];
    lastX = t.clientX; lastY = t.clientY;
    touchStart = new Date().getTime();
    moved = false;
  }, false);

  touchpad.addEventListener("touchmove", function(e) {
    e.preventDefault();
    if (e.touches.length === 1) {
      var t = e.touches[0];
      var dx = (t.clientX - lastX) * sensitivity;
      var dy = (t.clientY - lastY) * sensitivity;
      if (Math.abs(dx) > 1 || Math.abs(dy) > 1) moved = true;
      lastX = t.clientX; lastY = t.clientY;
      qDx += dx; qDy += dy; flush();
    }
  }, false);

  touchpad.addEventListener("touchend", function(e) {
    e.preventDefault();
    var dur = new Date().getTime() - touchStart;
    if (!moved && dur < 280) {
      if (touches === 1) leftClick();
      else if (touches === 2) rightClick();
    }
    touches = e.touches.length;
  }, false);

  var lastScroll = 0;
  scrollStrip.addEventListener("touchstart", function(e) { e.preventDefault(); lastScroll = e.touches[0].clientY; }, false);
  scrollStrip.addEventListener("touchmove", function(e) {
    e.preventDefault();
    var y = e.touches[0].clientY;
    var dy = y - lastScroll;
    if (Math.abs(dy) > 8) {
      sendCmd("scroll", { delta: dy < 0 ? 120 : -120 });
      lastScroll = y;
    }
  }, false);

  function leftClick() { sendCmd("click", { button: "left" }); }
  function rightClick() { sendCmd("click", { button: "right" }); }
  function jumpProjector() { sendCmd("jump_screen", { screen: "projector" }); }
  function toggleLock() {
    sendCmd("toggle_lock", {}, function(d) {
      if (d && d.lock) { lockBtn.className = "h-btn active"; lockBtn.innerHTML = "🔒 Locked"; }
      else { lockBtn.className = "h-btn"; lockBtn.innerHTML = "🔓 Unlock"; }
    });
  }
  function sendKey(k) { sendCmd("key", { key: k }); }
  function updateTextStats() {
    var el = document.getElementById("t-input");
    var v = (el && el.value) ? el.value : "";
    var lines = v ? v.split(String.fromCharCode(10)).length : 0;
    var chars = v.length;
    var stats = document.getElementById("text-stats");
    if (stats) stats.innerText = lines + " line" + (lines === 1 ? "" : "s") + " • " + chars + " char" + (chars === 1 ? "" : "s");
  }

  function showText() {
    document.getElementById("text-overlay").style.display = "block";
    updateTextStats();
    setTimeout(function() {
      var el = document.getElementById("t-input");
      if (el) el.focus();
    }, 80);
  }

  function hideText() {
    document.getElementById("text-overlay").style.display = "none";
  }

  function clearText() {
    var el = document.getElementById("t-input");
    if (el) {
      el.value = "";
      updateTextStats();
      el.focus();
    }
  }

  function pasteFromPhone() {
    var el = document.getElementById("t-input");
    if (navigator.clipboard && navigator.clipboard.readText) {
      navigator.clipboard.readText().then(function(clipText) {
        if (clipText) {
          el.value = clipText;
          updateTextStats();
          el.focus();
        }
      })["catch"](function() {
        alert("Please tap and hold in the box to paste directly.");
        if (el) el.focus();
      });
    } else {
      alert("Please tap and hold in the box to paste directly.");
      if (el) el.focus();
    }
  }

  function sendText(mode) {
    var el = document.getElementById("t-input");
    var v = el ? el.value : "";
    if (v) {
      var btn = document.getElementById("b-send");
      var original = btn.innerText;
      btn.innerText = "✓ Pasted!";
      sendCmd("paste_text", { text: v, mode: mode || "paste" }, function() {
        setTimeout(function() {
          btn.innerText = original;
          hideText();
        }, 300);
      });
    } else {
      hideText();
    }
  }

  var tInput = document.getElementById("t-input");
  if (tInput) {
    tInput.addEventListener("keydown", function(e) {
      if ((e.ctrlKey || e.metaKey) && e.keyCode === 13) {
        e.preventDefault();
        sendText("paste");
      }
    }, false);
  }
</script>
</body>
</html>
"""

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class MwagoHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(EMBEDDED_HTML.encode("utf-8"))
        elif self.path.startswith("/status"):
            res = handle_command("status", {})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
        elif self.path in ("/favicon.ico", "/favicon.png"):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        try:
            data = json.loads(post_body.decode("utf-8"))
            cmd = data.get("cmd")
            params = data.get("params", {})
            result = handle_command(cmd, params)
            if result is None:
                result = {"status": "ok"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def main():
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    ip = get_local_ip()
    url = f"http://{ip}:{port}"

    print("=" * 64)
    print("   MWAGO - YOUR REMOTE MOUSE & PROJECTOR CONTROLLER")
    print("   Safe Spaces AI Innovation Hub • Mbarara, Uganda")
    print("   https://safespaceshub.com  |  mwago.safespaceshub.com")
    print("=" * 64)
    print(f"\n[+] Detected {len(screens)} screen(s) connected to PC.")
    for i, s in enumerate(screens):
        primary_tag = "(Primary)" if s["is_primary"] else "(Extended / Projector)"
        print(f"    - Screen {i+1}: {s['width']}x{s['height']} {primary_tag}")
    print(f"\n[+] Mwago Server is ACTIVE on your local Wi-Fi:")
    print(f"\n    👉  {url}  👈\n")
    print("    Open this address in your phone's browser (Android 4+ supported).")
    print("    Press Ctrl+C to stop.\n" + "=" * 64)

    try:
        httpd = ThreadingHTTPServer(("0.0.0.0", port), MwagoHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMwago stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
