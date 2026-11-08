"""Version, release, and data location information."""
import webbrowser

import customtkinter as ctk

import theme
from version import APP_VERSION
from widgets import Card, SectionHeading


class AboutPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="About & updates", anchor="w", text_color=theme.TEXT,
                     font=theme.font("title", "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self, text="Video Compressor V2", anchor="w",
                     text_color=theme.MUTED, font=theme.font("subtitle")).grid(row=1, column=0, sticky="w", pady=(5, theme.SPACE["xl"]))
        SectionHeading(self, "About this build").grid(row=2, column=0, sticky="w", pady=(0, theme.SPACE["sm"]))
        card = Card(self)
        card.grid(row=3, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text="Video Compressor", anchor="w", text_color=theme.TEXT,
                     font=theme.font("heading", "bold")).grid(row=0, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(theme.SPACE["lg"], theme.SPACE["xs"]))
        ctk.CTkLabel(card, text=f"Stable release  ·  v{APP_VERSION}", anchor="w", text_color=theme.ACCENT,
                     font=theme.font("body", "bold")).grid(row=1, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))
        ctk.CTkLabel(card, text="Open GitHub Releases to see the latest version and download setup.",
                     anchor="w", justify="left", wraplength=620, text_color=theme.MUTED,
                     font=theme.font("body")).grid(row=2, column=0, sticky="ew", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))
        ctk.CTkButton(card, text="Open GitHub Releases",
                      command=lambda: webbrowser.open("https://github.com/AbelOnGit/VideoCompressor/releases/latest")
                      ).grid(row=3, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["lg"]))
        SectionHeading(self, "Your data").grid(row=4, column=0, sticky="w", pady=(theme.SPACE["xl"], theme.SPACE["sm"]))
        path_card = Card(self)
        path_card.grid(row=5, column=0, sticky="ew")
        path_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(path_card, text="Settings are stored at", anchor="w", text_color=theme.MUTED,
                     font=theme.font("small")).grid(row=0, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(theme.SPACE["md"], theme.SPACE["xs"]))
        ctk.CTkLabel(path_card, text=str(app.appdata), anchor="w", text_color=theme.TEXT,
                     font=theme.font("body")).grid(row=1, column=0, sticky="ew", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))
