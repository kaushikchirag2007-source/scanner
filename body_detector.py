"""
body_detector.py — Body detection via MediaPipe Selfie Segmentation + Pose.

Returns a binary mask and pose landmarks for each processed frame.
Applies temporal smoothing (rolling average of last N masks) to eliminate
outline flicker between frames.
"""

import cv2
import numpy as np
import mediapipe as mp
from collections import deque


# ─── Distance classification ─────────────────────────────────────────────────
def _classify_distance(body_fraction: float) -> str:
    """
    Estimate distance from camera using the fraction of frame height
    occupied by the detected body bounding box.

    body_fraction = bounding_box_height / frame_height
    """
    if body_fraction >= 0.70:
        return "close"       # ~0.5–1.5 m
    elif body_fraction >= 0.35:
        return "medium"      # ~1.5–3 m
    elif body_fraction >= 0.12:
        return "far"         # ~3–5 m
    else:
        return "beyond"      # >5 m — skip outline


class BodyDetector:
    """
    Wraps MediaPipe Selfie Segmentation and Pose estimator.

    Process a frame with `process(frame)` to get:
      - binary mask  (np.uint8, 0 or 255)
      - landmarks    (mediapipe NormalizedLandmarkList or None)
      - distance     ('close' | 'medium' | 'far' | 'beyond')
      - detected     (bool)
    """

    def __init__(
        self,
        smoothing_window: int = 3,
        confidence_threshold: float = 0.70,
    ):
        self._conf_thresh = confidence_threshold
        self._smooth_window = smoothing_window

        # MediaPipe Selfie Segmentation (model_selection=1 → landscape/general)
        mp_seg = mp.solutions.selfie_segmentation
        self._segmentor = mp_seg.SelfieSegmentation(model_selection=1)

        # MediaPipe Pose
        mp_pose = mp.solutions.pose
        self._pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=0.60,
        )

        # Rolling buffer for temporal smoothing
        self._mask_buffer: deque = deque(maxlen=smoothing_window)

    # ─────────────────────────────────────────────────────────────────────────
    def process(self, frame: np.ndarray) -> dict:
        """
        Detect the human body in `frame` (BGR, already mirrored).

        Returns a dict:
            mask       : np.ndarray (H×W, uint8, 0 or 255)
            landmarks  : mediapipe landmarks or None
            distance   : str
            detected   : bool
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ── Segmentation ──────────────────────────────────────────────────────
        seg_result = self._segmentor.process(rgb)
        confidence_map = seg_result.segmentation_mask  # float32, 0–1

        # Threshold at min confidence
        binary = (confidence_map >= self._conf_thresh).astype(np.uint8) * 255

        # ── Temporal smoothing ────────────────────────────────────────────────
        self._mask_buffer.append(binary.astype(np.float32))
        smoothed = np.mean(self._mask_buffer, axis=0)
        mask = (smoothed >= 128).astype(np.uint8) * 255

        # ── Check if any body is detected ─────────────────────────────────────
        white_ratio = np.sum(mask > 0) / (h * w)
        detected = white_ratio > 0.02  # at least 2% of pixels are body

        # ── Distance estimation ───────────────────────────────────────────────
        distance = "beyond"
        if detected:
            ys, xs = np.where(mask > 0)
            if len(ys):
                bbox_h_frac = (ys.max() - ys.min()) / h
                distance = _classify_distance(bbox_h_frac)
                if distance == "beyond":
                    # Body too small — treat as not detected for outline
                    detected = False

        # ── Pose landmarks ────────────────────────────────────────────────────
        landmarks = None
        if detected and distance in ("close", "medium"):
            pose_result = self._pose.process(rgb)
            landmarks = pose_result.pose_landmarks

        return {
            "mask":      mask,
            "landmarks": landmarks,
            "distance":  distance,
            "detected":  detected,
        }

    def close(self):
        self._segmentor.close()
        self._pose.close()
