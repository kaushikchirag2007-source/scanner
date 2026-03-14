"""
outline_drawer.py — Draws all 5 visual outline styles on a frame.

Styles:
  1. Neon Glow       — Canny edge with multi-layer blur glow
  2. Wireframe Scan  — Thin clean contour, no fill
  3. Heat Map Body   — Thermal gradient fill + yellow outline
  4. Solid Silhouette— Semi-transparent fill + bold outline
  5. Skeleton Overlay— Outline + 33-keypoint skeleton lines
"""

import cv2
import numpy as np
import mediapipe as mp


# ─── Skeleton connections (MediaPipe Pose 33 landmarks) ───────────────────────
_MP_POSE = mp.solutions.pose
SKELETON_CONNECTIONS = [
    # Face-ish
    (_MP_POSE.PoseLandmark.LEFT_EAR,       _MP_POSE.PoseLandmark.LEFT_EYE),
    (_MP_POSE.PoseLandmark.LEFT_EYE,       _MP_POSE.PoseLandmark.NOSE),
    (_MP_POSE.PoseLandmark.NOSE,           _MP_POSE.PoseLandmark.RIGHT_EYE),
    (_MP_POSE.PoseLandmark.RIGHT_EYE,      _MP_POSE.PoseLandmark.RIGHT_EAR),
    # Shoulders
    (_MP_POSE.PoseLandmark.LEFT_SHOULDER,  _MP_POSE.PoseLandmark.RIGHT_SHOULDER),
    # Left arm
    (_MP_POSE.PoseLandmark.LEFT_SHOULDER,  _MP_POSE.PoseLandmark.LEFT_ELBOW),
    (_MP_POSE.PoseLandmark.LEFT_ELBOW,     _MP_POSE.PoseLandmark.LEFT_WRIST),
    # Right arm
    (_MP_POSE.PoseLandmark.RIGHT_SHOULDER, _MP_POSE.PoseLandmark.RIGHT_ELBOW),
    (_MP_POSE.PoseLandmark.RIGHT_ELBOW,    _MP_POSE.PoseLandmark.RIGHT_WRIST),
    # Torso
    (_MP_POSE.PoseLandmark.LEFT_SHOULDER,  _MP_POSE.PoseLandmark.LEFT_HIP),
    (_MP_POSE.PoseLandmark.RIGHT_SHOULDER, _MP_POSE.PoseLandmark.RIGHT_HIP),
    (_MP_POSE.PoseLandmark.LEFT_HIP,       _MP_POSE.PoseLandmark.RIGHT_HIP),
    # Left leg
    (_MP_POSE.PoseLandmark.LEFT_HIP,       _MP_POSE.PoseLandmark.LEFT_KNEE),
    (_MP_POSE.PoseLandmark.LEFT_KNEE,      _MP_POSE.PoseLandmark.LEFT_ANKLE),
    (_MP_POSE.PoseLandmark.LEFT_ANKLE,     _MP_POSE.PoseLandmark.LEFT_HEEL),
    (_MP_POSE.PoseLandmark.LEFT_HEEL,      _MP_POSE.PoseLandmark.LEFT_FOOT_INDEX),
    # Right leg
    (_MP_POSE.PoseLandmark.RIGHT_HIP,      _MP_POSE.PoseLandmark.RIGHT_KNEE),
    (_MP_POSE.PoseLandmark.RIGHT_KNEE,     _MP_POSE.PoseLandmark.RIGHT_ANKLE),
    (_MP_POSE.PoseLandmark.RIGHT_ANKLE,    _MP_POSE.PoseLandmark.RIGHT_HEEL),
    (_MP_POSE.PoseLandmark.RIGHT_HEEL,     _MP_POSE.PoseLandmark.RIGHT_FOOT_INDEX),
]


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _get_contours(mask: np.ndarray):
    """Return the largest external contour(s) from a binary mask."""
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    # Filter tiny noise contours
    contours = [c for c in contours if cv2.contourArea(c) > 500]
    return contours


def _apply_glow(
    layer: np.ndarray,
    color_bgr: tuple,
    intensity: int,
    passes: int = 4,
) -> np.ndarray:
    """
    Create a glow effect by blurring the layer and blending it back.
    intensity: 0–100 — how strong the glow is.
    """
    if intensity <= 0:
        return layer

    alpha = intensity / 100.0
    glow = layer.copy()
    for k in range(passes, 0, -1):
        ksize = k * 8 + 1  # 9, 17, 25, 33
        blurred = cv2.GaussianBlur(glow, (ksize, ksize), 0)
        # Tint with color
        tinted = np.zeros_like(blurred)
        tinted[:] = color_bgr
        colored = cv2.bitwise_and(blurred, tinted)
        glow = cv2.addWeighted(glow, 1.0, colored, alpha / passes, 0)
    return glow


def _make_outline_layer(mask: np.ndarray) -> np.ndarray:
    """Dilate → erode to get a clean edge mask."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    edge = cv2.subtract(dilated, mask)
    return edge


def _draw_skeleton(
    canvas: np.ndarray,
    landmarks,
    color_bgr: tuple,
    thickness: int,
    h: int,
    w: int,
):
    """Draw skeleton lines between pose landmarks onto canvas."""
    if landmarks is None:
        return
    lm_list = landmarks.landmark
    for start_lm, end_lm in SKELETON_CONNECTIONS:
        s = lm_list[start_lm.value]
        e = lm_list[end_lm.value]
        if s.visibility < 0.5 or e.visibility < 0.5:
            continue
        p1 = (int(s.x * w), int(s.y * h))
        p2 = (int(e.x * w), int(e.y * h))
        cv2.line(canvas, p1, p2, color_bgr, thickness)

    # Draw joint dots
    dot_r = max(3, thickness)
    for lm in lm_list:
        if lm.visibility < 0.5:
            continue
        pt = (int(lm.x * w), int(lm.y * h))
        cv2.circle(canvas, pt, dot_r, color_bgr, -1)


# ─── Thermal gradient helper ─────────────────────────────────────────────────

def _make_thermal_body(mask: np.ndarray) -> np.ndarray:
    """
    Fill the body region with a top-to-bottom thermal gradient:
    head = red/orange, feet = blue/purple.
    """
    h, w = mask.shape
    thermal = np.zeros((h, w, 3), dtype=np.uint8)

    # Build vertical gradient strip (H×1)
    gradient = np.zeros((h, 1, 3), dtype=np.uint8)
    for row in range(h):
        t = row / h  # 0 = top (hot), 1 = bottom (cool)
        r = int(255 * (1 - t))
        g = int(180 * max(0.0, 0.5 - abs(t - 0.5)) * 2)
        b = int(255 * t)
        gradient[row, 0] = (b, g, r)

    # Tile gradient across full width
    gradient_full = np.repeat(gradient, w, axis=1)

    # Apply only where mask is white
    body_bool = mask > 0
    thermal[body_bool] = gradient_full[body_bool]
    return thermal


# ─── Style drawing functions ──────────────────────────────────────────────────

def draw_neon_glow(
    frame: np.ndarray,
    mask: np.ndarray,
    color_bgr: tuple,
    thickness: int,
    glow_intensity: int,
) -> np.ndarray:
    """Style 1 — Neon glow outline."""
    h, w = frame.shape[:2]
    canvas = frame.copy()

    contours = _get_contours(mask)
    if not contours:
        return canvas

    # Draw outline on a blank layer
    outline_layer = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.drawContours(outline_layer, contours, -1, color_bgr, thickness)

    # Apply glow
    if glow_intensity > 0:
        outline_layer = _apply_glow(outline_layer, color_bgr, glow_intensity)

    # Blend onto canvas
    mask_3 = cv2.cvtColor(
        np.clip(outline_layer.sum(axis=2), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR
    )
    alpha_mask = (mask_3 > 0).astype(np.float32) / 255.0 * np.clip(
        outline_layer.max(axis=2, keepdims=True).astype(np.float32) / 255.0 * 1.2, 0, 1
    )
    canvas = (canvas * (1 - alpha_mask) + outline_layer * alpha_mask).astype(np.uint8)
    return canvas


def draw_wireframe_scan(
    frame: np.ndarray,
    mask: np.ndarray,
    color_bgr: tuple,
    thickness: int,
    glow_intensity: int,
) -> np.ndarray:
    """Style 2 — Thin clean wireframe scan line."""
    canvas = frame.copy()
    contours = _get_contours(mask)
    if not contours:
        return canvas
    cv2.drawContours(canvas, contours, -1, color_bgr, thickness)
    return canvas


def draw_heat_map(
    frame: np.ndarray,
    mask: np.ndarray,
    color_bgr: tuple,
    thickness: int,
    glow_intensity: int,
) -> np.ndarray:
    """Style 3 — Thermal heat map fill + yellow outline."""
    canvas = frame.copy()
    thermal = _make_thermal_body(mask)

    # Blend thermal fill
    body_bool = (mask > 0)[:, :, np.newaxis]
    canvas = np.where(body_bool, cv2.addWeighted(canvas, 0.25, thermal, 0.75, 0), canvas)

    # Yellow outline
    outline_color = (0, 255, 255)  # yellow in BGR
    contours = _get_contours(mask)
    if contours:
        cv2.drawContours(canvas, contours, -1, outline_color, thickness + 1)
        if glow_intensity > 0:
            glow_layer = np.zeros_like(canvas)
            cv2.drawContours(glow_layer, contours, -1, outline_color, thickness + 1)
            glow_layer = _apply_glow(glow_layer, outline_color, glow_intensity // 2)
            canvas = cv2.addWeighted(canvas, 1.0, glow_layer, 0.6, 0)
    return canvas


def draw_solid_silhouette(
    frame: np.ndarray,
    mask: np.ndarray,
    color_bgr: tuple,
    thickness: int,
    glow_intensity: int,
) -> np.ndarray:
    """Style 4 — Semi-transparent solid fill + bold outline."""
    canvas = frame.copy()

    # Semi-transparent fill (50% opacity)
    fill_layer = np.zeros_like(frame)
    fill_layer[mask > 0] = color_bgr
    canvas = cv2.addWeighted(canvas, 1.0, fill_layer, 0.45, 0)

    # Bold outline
    contours = _get_contours(mask)
    if contours:
        cv2.drawContours(canvas, contours, -1, color_bgr, thickness + 2)
    return canvas


def draw_skeleton_overlay(
    frame: np.ndarray,
    mask: np.ndarray,
    landmarks,
    color_bgr: tuple,
    thickness: int,
    glow_intensity: int,
) -> np.ndarray:
    """Style 5 — Body outline + full skeleton joint lines."""
    h, w = frame.shape[:2]
    canvas = frame.copy()

    # Outline
    contours = _get_contours(mask)
    if contours:
        cv2.drawContours(canvas, contours, -1, color_bgr, thickness)
        if glow_intensity > 0:
            glow_layer = np.zeros_like(canvas)
            cv2.drawContours(glow_layer, contours, -1, color_bgr, thickness)
            glow_layer = _apply_glow(glow_layer, color_bgr, glow_intensity // 2)
            canvas = cv2.addWeighted(canvas, 1.0, glow_layer, 0.5, 0)

    # Skeleton
    _draw_skeleton(canvas, landmarks, color_bgr, max(1, thickness - 1), h, w)
    return canvas


# ─── Dispatcher ───────────────────────────────────────────────────────────────

def draw_outline(
    frame: np.ndarray,
    mask: np.ndarray,
    landmarks,
    style: str,
    color_bgr: tuple,
    thickness: int,
    glow_enabled: bool,
    glow_intensity: int,
) -> np.ndarray:
    """
    Main entry point. Routes to the appropriate style function.
    Returns the composited frame.
    """
    if mask is None or not mask.any():
        return frame

    intensity = glow_intensity if glow_enabled else 0

    if style == "Neon Glow":
        return draw_neon_glow(frame, mask, color_bgr, thickness, intensity)
    elif style == "Wireframe Scan":
        return draw_wireframe_scan(frame, mask, color_bgr, thickness, intensity)
    elif style == "Heat Map Body":
        return draw_heat_map(frame, mask, color_bgr, thickness, intensity)
    elif style == "Solid Silhouette":
        return draw_solid_silhouette(frame, mask, color_bgr, thickness, intensity)
    elif style == "Skeleton Overlay":
        return draw_skeleton_overlay(frame, mask, landmarks, color_bgr, thickness, intensity)
    else:
        return frame
