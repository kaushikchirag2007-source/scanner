"""
main.py — Entry point for the Real-Time Body Outline Scanner (BOS).

Run with:
    python main.py

Keyboard Controls:
    S  — Switch outline style (cycles through 5 styles)
    C  — Change outline colour (cycles through 8 colours)
    B  — Cycle background mode
    +  — Increase outline thickness
    -  — Decrease outline thickness
    G  — Toggle glow effect on/off
    F  — Toggle fullscreen
    R  — Start/stop recording (saves timestamped .mp4)
    Q  — Quit

Requirements (install once):
    pip install -r requirements.txt
"""

import cv2
import sys
import numpy as np

from body_detector  import BodyDetector
from outline_drawer import draw_outline
from style_manager  import StyleManager
from display_manager import DisplayManager
from recorder       import Recorder


# ─── Configuration ────────────────────────────────────────────────────────────
CAMERA_INDEX   = 0          # 0 = default webcam; change if using USB cam
TARGET_WIDTH   = 1280
TARGET_HEIGHT  = 720
TARGET_FPS     = 30
RECORD_FPS     = 30.0


def main():
    # ── Initialise components ─────────────────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check CAMERA_INDEX in main.py.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  TARGET_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          TARGET_FPS)

    detector = BodyDetector(
        smoothing_window=3,
        confidence_threshold=0.70,
    )

    style_mgr   = StyleManager()
    display_mgr = DisplayManager(fps_window=10)
    recorder    = Recorder(fps=RECORD_FPS, resolution=(TARGET_WIDTH, TARGET_HEIGHT))

    display_mgr.setup()

    print("=" * 60)
    print("  Body Outline Scanner — Running")
    print("  Controls: S=Style  C=Color  B=BG  +/-=Thick")
    print("            G=Glow   F=Full   R=Rec  Q=Quit")
    print("=" * 60)

    # ── Main processing loop ──────────────────────────────────────────────────
    while True:
        ret, raw_frame = cap.read()
        if not ret:
            print("[WARN] Failed to read frame — retrying...")
            continue

        # Mirror for natural selfie view
        frame = cv2.flip(raw_frame, 1)

        # ── Detect body ───────────────────────────────────────────────────────
        detection = detector.process(frame)
        mask       = detection["mask"]
        landmarks  = detection["landmarks"]
        detected   = detection["detected"]
        distance   = detection["distance"]

        # ── Adjust style detail by distance ───────────────────────────────────
        # (far → reduce glow level for performance; beyond → skip drawing)
        effective_glow = style_mgr.glow_intensity
        if distance == "far":
            effective_glow = min(effective_glow, 30)

        # ── Draw outline ──────────────────────────────────────────────────────
        if detected:
            composite = draw_outline(
                frame       = frame.copy(),
                mask        = mask,
                landmarks   = landmarks,
                style       = style_mgr.style,
                color_bgr   = style_mgr.color_bgr,
                thickness   = style_mgr.thickness,
                glow_enabled= style_mgr.glow_enabled,
                glow_intensity=effective_glow,
            )
        else:
            composite = frame.copy()

        # ── Compose HUD + background ──────────────────────────────────────────
        output = display_mgr.render(
            frame        = composite,
            mask         = mask if detected else None,
            detected     = detected,
            style        = style_mgr.style,
            color_name   = style_mgr.color_name,
            is_recording = recorder.is_recording,
            bg_mode      = style_mgr.background_mode,
            thickness    = style_mgr.thickness,
            glow_on      = style_mgr.glow_enabled,
        )

        # ── Write to recorder ─────────────────────────────────────────────────
        if recorder.is_recording:
            recorder.write(output)

        # ── Keyboard input ────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q') or key == 27:  # Q or Esc to quit
            print("[INFO] Quitting...")
            break

        elif key == ord('s') or key == ord('S'):
            style_mgr.next_style()
            print(f"[STYLE] → {style_mgr.style}")

        elif key == ord('c') or key == ord('C'):
            style_mgr.next_color()
            print(f"[COLOR] → {style_mgr.color_name}")

        elif key == ord('b') or key == ord('B'):
            style_mgr.next_background()
            print(f"[BACKGROUND] → {style_mgr.background_mode}")

        elif key == ord('+') or key == ord('='):
            style_mgr.increase_thickness()
            print(f"[THICKNESS] → {style_mgr.thickness}px")

        elif key == ord('-') or key == ord('_'):
            style_mgr.decrease_thickness()
            print(f"[THICKNESS] → {style_mgr.thickness}px")

        elif key == ord('g') or key == ord('G'):
            style_mgr.toggle_glow()
            state = "ON" if style_mgr.glow_enabled else "OFF"
            print(f"[GLOW] → {state}")

        elif key == ord('f') or key == ord('F'):
            display_mgr.toggle_fullscreen()

        elif key == ord('r') or key == ord('R'):
            msg = recorder.toggle(output_dir=".")
            print(f"[REC] {msg}")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    recorder.release()
    detector.close()
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Scanner stopped. Goodbye!")


if __name__ == "__main__":
    main()
