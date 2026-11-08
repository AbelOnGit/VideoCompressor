"""Small reusable CustomTkinter components for the v2 beta UI."""
import customtkinter as ctk

import theme


class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", theme.CARD_BG)
        kwargs.setdefault("corner_radius", theme.RADIUS["lg"])
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.BORDER)
        super().__init__(master, **kwargs)


class SettingRow(ctk.CTkFrame):
    def __init__(self, master, title, helper, **kwargs):
        super().__init__(master, fg_color="transparent", height=64, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(self, text=title, anchor="w", text_color=theme.TEXT,
                                        font=theme.font("body", "bold"))
        self.title_label.grid(row=0, column=0, sticky="ew")
        self.helper_label = ctk.CTkLabel(self, text=helper, anchor="w", justify="left",
                                         text_color=theme.MUTED, font=theme.font("small"))
        self.helper_label.grid(row=1, column=0, sticky="ew", pady=(theme.SPACE["xs"], 0))
        self.control = ctk.CTkFrame(self, fg_color="transparent")
        self.control.grid(row=0, column=1, rowspan=2, sticky="e", padx=(theme.SPACE["lg"], 0))


class SectionHeading(ctk.CTkLabel):
    def __init__(self, master, text):
        super().__init__(master, text=text.upper(), anchor="w", text_color=theme.MUTED,
                         font=theme.font("small", "bold"))


class IconButton(ctk.CTkButton):
    """Navigation button using a hand-drawn Canvas glyph, with no third-party artwork."""
    def __init__(self, master, icon, label, command):
        super().__init__(master, text=f"      {label}", command=command, anchor="w",
                         height=44, corner_radius=theme.RADIUS["md"],
                         fg_color="transparent", hover_color=theme.CARD_ALT,
                         text_color=theme.MUTED, font=theme.font("body"))
        self.icon_name = icon
        self.bind("<Configure>", self._ensure_glyph, add="+")
        self.after(30, self._ensure_glyph)

    def set_active(self, active):
        self.configure(fg_color=theme.ACCENT_SOFT if active else "transparent",
                       text_color=theme.TEXT if active else theme.MUTED)
        if hasattr(self, "_glyph") and self._glyph.winfo_exists():
            self._glyph.configure(bg=theme.ACCENT_SOFT if active else theme.PANEL_BG)
        self._draw_glyph()

    def _ensure_glyph(self, _event=None):
        if not hasattr(self, "_glyph") or not self._glyph.winfo_exists():
            self._glyph = ctk.CTkCanvas(self, width=22, height=22, bg=theme.ACCENT_SOFT,
                                        highlightthickness=0, bd=0)
            self._glyph.place(x=12, rely=.5, anchor="w")
        self._draw_glyph()

    def _draw_glyph(self):
        if not hasattr(self, "_glyph") or not self._glyph.winfo_exists():
            return
        canvas = self._glyph
        canvas.delete("all")
        color = theme.TEXT if self.cget("text_color") == theme.TEXT else theme.MUTED
        if self.icon_name == "compress":
            canvas.create_rectangle(3, 4, 19, 18, outline=color, width=1.5)
            canvas.create_line(7, 8, 15, 8, fill=color, width=1.5)
            canvas.create_line(7, 12, 12, 12, fill=color, width=1.5)
            canvas.create_line(14, 12, 18, 16, fill=theme.ACCENT, width=1.7)
        elif self.icon_name == "settings":
            canvas.create_oval(4, 4, 18, 18, outline=color, width=1.5)
            canvas.create_oval(9, 9, 13, 13, outline=color, width=1.5)
            for x1, y1, x2, y2 in ((11, 1, 11, 4), (11, 18, 11, 21), (1, 11, 4, 11),
                                  (18, 11, 21, 11), (4, 4, 6, 6), (16, 16, 18, 18),
                                  (16, 6, 18, 4), (4, 18, 6, 16)):
                canvas.create_line(x1, y1, x2, y2, fill=color, width=1.5)
        else:
            canvas.create_circle = None
            canvas.create_oval(3, 3, 19, 19, outline=color, width=1.5)
            canvas.create_line(11, 10, 11, 15, fill=color, width=1.7)
            canvas.create_oval(10.2, 6.2, 11.8, 7.8, fill=theme.ACCENT, outline=theme.ACCENT)
