"""Video selection, target size, compression progress and result actions."""
from pathlib import Path
import customtkinter as ctk
from tkinterdnd2 import DND_FILES

import theme
from widgets import Card, SectionHeading


class CompressPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE["lg"]))
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hero, text="Compress video", anchor="w", text_color=theme.TEXT,
                     font=theme.font("title", "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hero, text="Make large videos easier to share without guesswork.", anchor="w",
                     text_color=theme.MUTED, font=theme.font("subtitle")).grid(row=1, column=0,
                                                                                sticky="w", pady=(5, 0))

        body = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=theme.BORDER,
                                      scrollbar_button_hover_color=theme.FAINT)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        self.drop_card = Card(body, fg_color=theme.PANEL_BG, corner_radius=theme.RADIUS["xl"],
                              border_color=theme.ACCENT, border_width=1)
        self.drop_card.grid(row=0, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        self.drop_card.grid_columnconfigure(0, weight=1)
        self.drop_icon = ctk.CTkLabel(self.drop_card, text="↑", width=58, height=58,
                                      corner_radius=theme.RADIUS["lg"], fg_color=theme.ACCENT_SOFT,
                                      text_color=theme.ACCENT, font=theme.font(32, "bold"))
        self.drop_icon.grid(row=0, column=0, pady=(theme.SPACE["xl"], theme.SPACE["sm"]))
        self.drop_title = ctk.CTkLabel(self.drop_card, text="Drop a video to get started", text_color=theme.TEXT,
                                       font=theme.font("heading", "bold"))
        self.drop_title.grid(row=1, column=0)
        self.drop_hint = ctk.CTkLabel(self.drop_card, text="or browse files on your computer", text_color=theme.MUTED,
                                      font=theme.font("body"))
        self.drop_hint.grid(row=2, column=0, pady=(theme.SPACE["xs"], theme.SPACE["md"]))
        self.pick_button = ctk.CTkButton(self.drop_card, text="Choose video", command=self.app.pick,
                                         height=36, width=140, corner_radius=theme.RADIUS["sm"],
                                         fg_color=theme.CARD_ALT, hover_color=theme.BORDER,
                                         text_color=theme.TEXT, font=theme.font("body", "bold"))
        self.pick_button.grid(row=3, column=0, pady=(0, theme.SPACE["xl"]))
        self._bind_drop(self.drop_card)
        for widget in (self.drop_icon, self.drop_title, self.drop_hint):
            self._bind_drop(widget)

        SectionHeading(body, "Video details").grid(row=1, column=0, sticky="w", pady=(theme.SPACE["sm"], theme.SPACE["sm"]))
        self.file_card = Card(body)
        self.file_card.grid(row=2, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        self.file_card.grid_columnconfigure(0, weight=1)
        self.file_name = ctk.CTkLabel(self.file_card, text="No video selected", anchor="w", text_color=theme.TEXT,
                                      font=theme.font("body", "bold"))
        self.file_name.grid(row=0, column=0, sticky="ew", padx=theme.SPACE["lg"], pady=(theme.SPACE["md"], theme.SPACE["xs"]))
        self.file_details = ctk.CTkLabel(self.file_card, text="Name, size, duration and resolution will appear here.",
                                         anchor="w", text_color=theme.MUTED, font=theme.font("small"))
        self.file_details.grid(row=1, column=0, sticky="ew", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))

        SectionHeading(body, "Output target").grid(row=3, column=0, sticky="w", pady=(theme.SPACE["sm"], theme.SPACE["sm"]))
        target_card = Card(body)
        target_card.grid(row=4, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        target_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(target_card, text="Target size", anchor="w", text_color=theme.TEXT,
                     font=theme.font("body", "bold")).grid(row=0, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(theme.SPACE["md"], 2))
        ctk.CTkLabel(target_card, text="The compressed file will aim for this size.", anchor="w", text_color=theme.MUTED,
                     font=theme.font("small")).grid(row=1, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))
        self.target_menu = ctk.CTkOptionMenu(target_card, variable=app.target, values=app.TARGETS,
                                              command=app.target_changed, width=142, height=36,
                                              fg_color=theme.CARD_ALT, button_color=theme.ACCENT,
                                              button_hover_color=theme.ACCENT_HOVER,
                                              dropdown_fg_color=theme.CARD_ALT, dropdown_hover_color=theme.ACCENT_SOFT,
                                              font=theme.font("control"))
        self.target_menu.grid(row=0, column=1, rowspan=2, sticky="e", padx=(theme.SPACE["md"], theme.SPACE["lg"]))
        self.custom_entry = ctk.CTkEntry(target_card, textvariable=app.custom_target, width=100, height=36,
                                         placeholder_text="MB", fg_color=theme.INPUT_BG, border_color=theme.BORDER,
                                         font=theme.font("control"))
        self.custom_entry.grid(row=0, column=2, rowspan=2, sticky="e", padx=(0, theme.SPACE["lg"]))
        self.custom_entry.grid_remove()

        SectionHeading(body, "Progress").grid(row=5, column=0, sticky="w", pady=(theme.SPACE["sm"], theme.SPACE["sm"]))
        self.progress_card = Card(body)
        self.progress_card.grid(row=6, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        self.progress_card.grid_columnconfigure(0, weight=1)
        self.progress_status = ctk.CTkLabel(self.progress_card, text="Ready when you are", anchor="w",
                                            text_color=theme.TEXT, font=theme.font("body", "bold"))
        self.progress_status.grid(row=0, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(theme.SPACE["md"], theme.SPACE["sm"]))
        self.progress_percent = ctk.CTkLabel(self.progress_card, text="0%", text_color=theme.MUTED,
                                             font=theme.font("body", "bold"))
        self.progress_percent.grid(row=0, column=1, sticky="e", padx=theme.SPACE["lg"], pady=(theme.SPACE["md"], theme.SPACE["sm"]))
        self.progress_bar = ctk.CTkProgressBar(self.progress_card, height=9, corner_radius=99,
                                               progress_color=theme.ACCENT, fg_color=theme.INPUT_BG)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["sm"]))
        self.progress_bar.set(0)
        self.progress_meta = ctk.CTkLabel(self.progress_card, text="0:00 remaining", anchor="w",
                                          text_color=theme.MUTED, font=theme.font("small"))
        self.progress_meta.grid(row=2, column=0, sticky="w", padx=theme.SPACE["lg"], pady=(0, theme.SPACE["md"]))

        self.compress_button = ctk.CTkButton(body, text="Compress video", command=self.app.start,
                                             height=48, corner_radius=theme.RADIUS["md"],
                                             fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                                             text_color="#ffffff", font=theme.font("subtitle", "bold"), state="disabled")
        self.compress_button.grid(row=7, column=0, sticky="ew", pady=(theme.SPACE["xs"], theme.SPACE["sm"]))
        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.grid(row=8, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        actions.grid_columnconfigure((0, 1, 2), weight=1)
        self.cancel_button = ctk.CTkButton(actions, text="Cancel", command=self.app.cancel, height=36,
                                           fg_color=theme.CARD_ALT, hover_color=theme.BORDER,
                                           text_color=theme.TEXT, font=theme.font("body"), state="disabled")
        self.cancel_button.grid(row=0, column=0, sticky="ew", padx=(0, theme.SPACE["sm"]))
        self.open_folder_button = ctk.CTkButton(actions, text="Open folder", command=self.app.folder, height=36,
                                                fg_color=theme.CARD_ALT, hover_color=theme.BORDER,
                                                text_color=theme.TEXT, font=theme.font("body"), state="disabled")
        self.open_folder_button.grid(row=0, column=1, sticky="ew", padx=theme.SPACE["sm"])
        self.open_file_button = ctk.CTkButton(actions, text="Open file", command=self.app.open, height=36,
                                              fg_color=theme.CARD_ALT, hover_color=theme.BORDER,
                                              text_color=theme.TEXT, font=theme.font("body"), state="disabled")
        self.open_file_button.grid(row=0, column=2, sticky="ew", padx=(theme.SPACE["sm"], 0))

        self.drop_card.bind("<Button-1>", lambda _event: self.app.pick(), add="+")

    def _bind_drop(self, widget):
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", self.app.dropped)
        widget.bind("<Button-1>", lambda _event: self.app.pick(), add="+")

    def set_file(self, path, meta):
        p = Path(path)
        size = p.stat().st_size / 1_000_000
        minutes, seconds = divmod(int(meta["duration"]), 60)
        self.file_name.configure(text=p.name)
        self.file_details.configure(text=f"{size:.2f} MB   ·   {minutes}:{seconds:02d}   ·   {meta['width']} × {meta['height']}")
        self.drop_title.configure(text="Video ready to compress")
        self.drop_hint.configure(text="Drop a different video here or browse to replace it")
        self.compress_button.configure(state="normal")
        self.progress_status.configure(text="Ready when you are")
        self.progress_percent.configure(text="0%")
        self.progress_meta.configure(text="0:00 remaining")
        self.progress_bar.set(0)
        self.open_folder_button.configure(state="disabled")
        self.open_file_button.configure(state="disabled")

    def set_busy(self, busy):
        self.compress_button.configure(state="disabled" if busy else ("normal" if self.app.path else "disabled"))
        self.cancel_button.configure(state="normal" if busy else "disabled")
        self.pick_button.configure(state="disabled" if busy else "normal")
        self.target_menu.configure(state="disabled" if busy else "normal")
        self.custom_entry.configure(state="disabled" if busy else "normal")

    def set_progress(self, fraction, remaining):
        fraction = min(1, max(0, fraction))
        self.progress_bar.set(fraction)
        self.progress_percent.configure(text=f"{fraction * 100:.0f}%")
        self.progress_meta.configure(text=f"{int(remaining // 60)}:{int(remaining % 60):02d} remaining")

    def set_status(self, status):
        self.progress_status.configure(text=status)

    def set_finished(self, result):
        if result.get("cancelled"):
            self.progress_status.configure(text="Compression cancelled")
            self.progress_bar.set(0)
            self.progress_percent.configure(text="0%")
            self.progress_meta.configure(text="The partial output was removed")
        elif result.get("error"):
            self.progress_status.configure(text="Compression failed")
        else:
            self.progress_bar.set(1)
            self.progress_percent.configure(text="100%")
            self.progress_meta.configure(text=f"Saved {result['size'] / 1_000_000:.2f} MB")
            self.progress_status.configure(text="Compression complete")
            self.open_folder_button.configure(state="normal")
            self.open_file_button.configure(state="normal")
