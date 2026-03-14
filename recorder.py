"""
recorder.py — Handles video recording to timestamped .mp4 files.
Toggle recording on/off with a single call to toggle().
"""

import cv2
import os
from datetime import datetime


class Recorder:
    """Wraps cv2.VideoWriter with start/stop toggle and auto-naming."""

    def __init__(self, fps: float = 30.0, resolution: tuple = (1280, 720)):
        self._fps = fps
        self._resolution = resolution  # (width, height)
        self._writer: cv2.VideoWriter | None = None
        self._is_recording = False
        self._save_path: str = ""

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def save_path(self) -> str:
        return self._save_path

    def toggle(self, output_dir: str = ".") -> str:
        """
        Start recording if not active; stop and flush if active.
        Returns a status message string.
        """
        if self._is_recording:
            return self._stop()
        else:
            return self._start(output_dir)

    def _start(self, output_dir: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.mp4"
        self._save_path = os.path.join(output_dir, filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            self._save_path, fourcc, self._fps, self._resolution
        )

        if not self._writer.isOpened():
            self._writer = None
            return "⚠ Recording failed to start — codec error."

        self._is_recording = True
        return f"● REC started → {self._save_path}"

    def _stop(self) -> str:
        if self._writer:
            self._writer.release()
            self._writer = None
        self._is_recording = False
        return f"■ Recording saved → {self._save_path}"

    def write(self, frame):
        """Write a frame if currently recording. Frame must match _resolution."""
        if self._is_recording and self._writer:
            # Resize to match recorder resolution if needed
            h, w = frame.shape[:2]
            rw, rh = self._resolution
            if (w, h) != (rw, rh):
                frame = cv2.resize(frame, (rw, rh))
            self._writer.write(frame)

    def release(self):
        """Force-stop and release resources (call on app exit)."""
        if self._is_recording:
            self._stop()
