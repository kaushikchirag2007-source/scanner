"""
style_manager.py — State container for all visual settings.
Manages style, color, thickness, glow, and background mode.
"""

# ─── Style definitions ────────────────────────────────────────────────────────
STYLES = [
    "Neon Glow",
    "Wireframe Scan",
    "Heat Map Body",
    "Solid Silhouette",
    "Skeleton Overlay",
]

# ─── Color palette (name → BGR) ──────────────────────────────────────────────
COLORS = {
    "Neon Green":   (65, 255, 0),      # #00FF41
    "Cyber Blue":   (255, 245, 0),     # #00F5FF
    "Hot Pink":     (127, 0, 255),     # #FF007F
    "Solar Orange": (0, 102, 255),     # #FF6600
    "Pure White":   (255, 255, 255),   # #FFFFFF
    "Gold":         (0, 215, 255),     # #FFD700
    "Red Alert":    (0, 0, 255),       # #FF0000
    "Purple Void":  (255, 0, 191),     # #BF00FF
}

COLOR_NAMES = list(COLORS.keys())

# ─── Background modes ─────────────────────────────────────────────────────────
BACKGROUND_MODES = ["Original", "Black", "Blur", "Solid Color"]

# ─── Thickness options (px) ───────────────────────────────────────────────────
THICKNESS_OPTIONS = [2, 4, 6]


class StyleManager:
    """Holds all runtime visual settings and provides mutation helpers."""

    def __init__(self):
        self._style_idx = 0        # index into STYLES
        self._color_idx = 0        # index into COLOR_NAMES
        self._thickness_idx = 1    # default: 4 px (medium)
        self.glow_intensity = 60   # 0–100
        self.glow_enabled = True
        self._bg_idx = 0           # index into BACKGROUND_MODES

    # ── Accessors ─────────────────────────────────────────────────────────────
    @property
    def style(self) -> str:
        return STYLES[self._style_idx]

    @property
    def color_name(self) -> str:
        return COLOR_NAMES[self._color_idx]

    @property
    def color_bgr(self) -> tuple:
        return COLORS[self.color_name]

    @property
    def thickness(self) -> int:
        return THICKNESS_OPTIONS[self._thickness_idx]

    @property
    def background_mode(self) -> str:
        return BACKGROUND_MODES[self._bg_idx]

    # ── Mutations ─────────────────────────────────────────────────────────────
    def next_style(self):
        self._style_idx = (self._style_idx + 1) % len(STYLES)

    def next_color(self):
        self._color_idx = (self._color_idx + 1) % len(COLOR_NAMES)

    def increase_thickness(self):
        self._thickness_idx = min(self._thickness_idx + 1, len(THICKNESS_OPTIONS) - 1)

    def decrease_thickness(self):
        self._thickness_idx = max(self._thickness_idx - 1, 0)

    def toggle_glow(self):
        self.glow_enabled = not self.glow_enabled

    def next_background(self):
        self._bg_idx = (self._bg_idx + 1) % len(BACKGROUND_MODES)

    def info_dict(self) -> dict:
        """Return a snapshot of current settings (for HUD display)."""
        return {
            "style":      self.style,
            "color":      self.color_name,
            "thickness":  self.thickness,
            "glow":       self.glow_enabled,
            "glow_level": self.glow_intensity,
            "bg":         self.background_mode,
        }
