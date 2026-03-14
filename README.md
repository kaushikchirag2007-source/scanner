# 🔵 Body Outline Scanner (BOS)

Real-time human body detection and stylized outline drawing using your
laptop/PC webcam, OpenCV, and MediaPipe.

---



## ⌨️ Keyboard Controls

| Key | Action |
|-----|--------|
| `S` | Cycle outline style (5 styles) |
| `C` | Cycle outline colour (8 colours) |
| `B` | Cycle background mode |
| `+` | Increase outline thickness |
| `-` | Decrease outline thickness |
| `G` | Toggle glow effect on/off |
| `F` | Toggle fullscreen |
| `R` | Start / Stop recording (saves `.mp4`) |
| `Q` or `Esc` | Quit |

---

## 🎨 Outline Styles

| # | Style | Description |
|---|-------|-------------|
| 1 | **Neon Glow** | Glowing neon edge — sci-fi look |
| 2 | **Wireframe Scan** | Thin clean contour — security scanner |
| 3 | **Heat Map Body** | Thermal gradient fill — medical/fitness |
| 4 | **Solid Silhouette** | Semi-transparent fill + bold border |
| 5 | **Skeleton Overlay** | Outline + 33-point skeleton joints |

---

## 🌈 Colour Options

`Neon Green` · `Cyber Blue` · `Hot Pink` · `Solar Orange`  
`Pure White` · `Gold` · `Red Alert` · `Purple Void`

---

## 🖥️ Background Modes

| Mode | Effect |
|------|--------|
| **Original** | Live webcam background |
| **Black** | Black background, body in colour |
| **Blur** | Blurred background (portrait mode) |
| **Solid Color** | Dark grey background |

---

## 📁 Project Structure

```
scanner live/
├── main.py             ← Entry point (run this)
├── body_detector.py    ← MediaPipe segmentation + pose
├── outline_drawer.py   ← 5 visual style renderers
├── style_manager.py    ← Runtime state (style, colour, etc.)
├── display_manager.py  ← HUD overlay and window management
├── recorder.py         ← .mp4 recording with timestamps
└── requirements.txt    ← Python dependencies
```

---

## 💡 Tips

- **Multiple people**: MediaPipe Selfie Segmentation can handle multiple people in frame simultaneously.
- **Low light**: Works best with at least some ambient light; try increasing room brightness.
- **Far distance**: Body outlines are suppressed beyond ~5 m automatically.
- **Recordings**: Saved as `recording_YYYYMMDD_HHMMSS.mp4` in the project folder.
- **Camera index**: If your webcam isn't detected, change `CAMERA_INDEX = 0` to `1` or `2` in `main.py`.

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Webcam not opening | Change `CAMERA_INDEX` in `main.py` |
| Low FPS | Close other apps; reduce resolution in `main.py` |
| `mediapipe` install error | Run `pip install --upgrade pip` first |
| Black window on start | Check that your webcam drivers are installed |
