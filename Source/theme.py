"""Central design tokens for the local v2 beta interface."""

APP_BG = "#101319"
PANEL_BG = "#151a22"
CARD_BG = "#1b222d"
CARD_ALT = "#202a37"
INPUT_BG = "#121820"
BORDER = "#2b3543"
TEXT = "#f3f6fb"
MUTED = "#9aa8bb"
FAINT = "#68788e"
ACCENT = "#4f8cff"
ACCENT_HOVER = "#70a2ff"
ACCENT_SOFT = "#1e365a"
SUCCESS = "#49c792"
WARNING = "#f0b95e"
DANGER = "#ee6e78"

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"
FONT_SIZES = {"caption": 10, "small": 11, "body": 13, "control": 13,
              "subtitle": 14, "heading": 19, "title": 25, "hero": 27}

SPACE = {"xs": 4, "sm": 8, "md": 12, "lg": 18, "xl": 24, "xxl": 32}
RADIUS = {"sm": 8, "md": 12, "lg": 16, "xl": 20}
WINDOW = {"width": 1080, "height": 800, "min_width": 900, "min_height": 680}
RAIL_WIDTH = 184


def font(size="body", weight="normal"):
    import customtkinter as ctk
    points = FONT_SIZES.get(size, size)
    return ctk.CTkFont(family=FONT_FAMILY, size=points, weight=weight)
