"""
display_manager.py — Composites the output frame and draws the HUD overlay.

Responsibilities:
- Apply background mode (Original / Black / Blur / Solid Color)
- Draw the FPS counter, detection badge, style/color bar
- Show recording indicator
- Handle fullscreen toggling
"""

import cv2
import numpy as np
import time
from collections import deque

WINDOW_NAME = "Body Outline Scanner"

# Background solid color (dark teal) for "Solid Color" mode
SOLID_BG_COLOR = (30, 30, 30)  # very dark grey


class DisplayManager:
    """
    Manages display composition and HUD rendering.
    Call `setup()` once, then `render()` each frame.
    """

    def __init__(self, fps_window: int = 10):
        self._fps_queue: deque = deque(maxlen=fps_window)
        self._last_time: float = time.time()
        self._fullscreen: bool = False
        self._window_ready: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    def setup(self):
        """Create the named window."""
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, 1280, 720)
        self._window_ready = True

    def toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            cv2.setWindowProperty(
                WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )
        else:
            cv2.setWindowProperty(
                WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
            )
            cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    # ─────────────────────────────────────────────────────────────────────────
    def _tick_fps(self) -> float:
        now = time.time()
        dt = now - self._last_time
        self._last_time = now
        if dt > 0:
            self._fps_queue.append(1.0 / dt)
        return float(np.mean(self._fps_queue)) if self._fps_queue else 0.0

    # ─────────────────────────────────────────────────────────────────────────
    def apply_background(
        self, frame: np.ndarray, mask: np.ndarray, bg_mode: str
    ) -> np.ndarray:
        """Return frame with modified background according to bg_mode."""
        if bg_mode == "Original" or mask is None:
            return frame

        if bg_mode == "Black":
            result = np.zeros_like(frame)
            result[mask > 0] = frame[mask > 0]
            return result

        if bg_mode == "Blur":
            blurred = cv2.GaussianBlur(frame, (51, 51), 0)
            result = blurred.copy()
            result[mask > 0] = frame[mask > 0]
            return result

        if bg_mode == "Solid Color":
            result = np.full_like(frame, SOLID_BG_COLOR)
            result[mask > 0] = frame[mask > 0]
            return result

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def _draw_hud(
        self,
        frame: np.ndarray,
        fps: float,
        detected: bool,
        style: str,
        color_name: str,
        is_recording: bool,
        bg_mode: str,
        thickness: int,
        glow_on: bool,
    ) -> np.ndarray:
        h, w = frame.shape[:2]

        font       = cv2.FONT_HERSHEY_SIMPLEX
        dark_panel = (10, 10, 10)
        white      = (240, 240, 240)
        green      = (60, 220, 60)
        red        = (60, 60, 220)
        amber      = (0, 190, 255)

        # ── Translucent top bar ───────────────────────────────────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 44), dark_panel, -1)
        frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

        # ── FPS — top left ────────────────────────────────────────────────────
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(frame, fps_text, (12, 30), font, 0.8, amber, 2, cv2.LINE_AA)

        # ── Detection badge — top right ───────────────────────────────────────
        if detected:
            badge_text  = "DETECTED"
            badge_color = green
            badge_icon  = "+"
        else:
            badge_text  = "NOT DETECTED"
            badge_color = red
            badge_icon  = "x"

        badge_full = f"[{badge_icon}] {badge_text}"
        (bw, _), _ = cv2.getTextSize(badge_full, font, 0.7, 2)
        cv2.putText(frame, badge_full, (w - bw - 12, 30), font, 0.7, badge_color, 2, cv2.LINE_AA)

        # ── Recording indicator — top center ──────────────────────────────────
        if is_recording:
            rec_text = "● REC"
            (rw, _), _ = cv2.getTextSize(rec_text, font, 0.75, 2)
            cv2.putText(frame, rec_text, (w // 2 - rw // 2, 30), font, 0.75, (60, 60, 255), 2, cv2.LINE_AA)

        # ── Bottom info bar ───────────────────────────────────────────────────
        bar_h = 42
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, h - bar_h), (w, h), dark_panel, -1)
        frame = cv2.addWeighted(overlay2, 0.55, frame, 0.45, 0)

        left_text  = f"Style: {style}  |  Color: {color_name}"
        right_text = f"BG: {bg_mode}  Thick:{thickness}px  Glow:{'ON' if glow_on else 'OFF'}"
        controls   = "[S]Style [C]Color [+/-]Thick [G]Glow [B]BG [F]Full [R]Rec [Q]Quit"

        cv2.putText(frame, left_text,  (12, h - bar_h + 18), font, 0.52, white,  1, cv2.LINE_AA)
        (rw2, _), _ = cv2.getTextSize(right_text, font, 0.50, 1)
        cv2.putText(frame, right_text, (w - rw2 - 10, h - bar_h + 18), font, 0.50, amber, 1, cv2.LINE_AA)
        cv2.putText(frame, controls,   (12, h - 8), font, 0.40, (160, 160, 160), 1, cv2.LINE_AA)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    def render(
        self,
        frame: np.ndarray,
        mask: np.ndarray,
        detected: bool,
        style: str,
        color_name: str,
        is_recording: bool,
        bg_mode: str,
        thickness: int,
        glow_on: bool,
    ) -> np.ndarray:
        """
        Final pipeline step:
        1. Tick FPS counter
        2. Apply background
        3. Draw HUD
        4. Show in window
        Returns the composited frame.
        """
        fps = self._tick_fps()
        frame = self.apply_background(frame, mask, bg_mode)
        frame = self._draw_hud(
            frame, fps, detected, style, color_name,
            is_recording, bg_mode, thickness, glow_on
        )

        if self._window_ready:
            cv2.imshow(WINDOW_NAME, frame)

        return frame
