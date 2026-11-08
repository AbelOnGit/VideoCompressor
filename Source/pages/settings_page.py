"""Searchable settings presented as compact label/helper/control rows."""
import customtkinter as ctk

import theme
from widgets import Card, SectionHeading, SettingRow


class SettingsPage(ctk.CTkFrame):

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(self, text="Settings", anchor="w", text_color=theme.TEXT,
                     font=theme.font("title", "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self, text="Choose where compressed videos and logs are saved.", anchor="w",
                     text_color=theme.MUTED, font=theme.font("subtitle")).grid(row=1, column=0, sticky="w", pady=(5, theme.SPACE["lg"]))
        self.search_var = ctk.StringVar(value="Search settings")
        self.search = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Search settings",
                                   height=40, fg_color=theme.INPUT_BG, border_color=theme.BORDER,
                                   corner_radius=theme.RADIUS["md"], font=theme.font("body"))
        self.search.grid(row=2, column=0, sticky="new", pady=(0, theme.SPACE["lg"]))
        self.search.bind("<KeyRelease>", lambda _event: self.filter_rows())
        self.search.bind("<FocusIn>", self._search_focus_in)
        self.search.bind("<FocusOut>", self._search_focus_out)
        self.groups_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=theme.BORDER,
                                                   scrollbar_button_hover_color=theme.FAINT)
        self.groups_frame.grid(row=3, column=0, sticky="nsew")
        self.groups_frame.grid_columnconfigure(0, weight=1)
        self.rows = []
        self.groups = []
        self._build_output_group()
        self._build_behavior_group()
        self.filter_rows()

    def _group(self, title, row):
        heading = SectionHeading(self.groups_frame, title)
        heading.grid(row=row * 2, column=0, sticky="w", pady=(theme.SPACE["sm"], theme.SPACE["sm"]))
        card = Card(self.groups_frame, corner_radius=theme.RADIUS["md"])
        card.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, theme.SPACE["md"]))
        card.grid_columnconfigure(0, weight=1)
        self.groups.append((heading, card))
        return card

    def _row(self, parent, title, helper, key, row):
        item = SettingRow(parent, title, helper)
        item.grid(row=row, column=0, sticky="ew", padx=theme.SPACE["lg"], pady=theme.SPACE["md"])
        self.rows.append((item, key))
        return item

    def _build_output_group(self):
        card = self._group("Files and output", 0)
        row = self._row(card, "Output folder", "Compressed videos and logs are saved here.", "output folder files output", 0)
        self.output_entry = ctk.CTkEntry(row.control, textvariable=self.app.output_folder_value, width=210,
                                         height=34, state="readonly", fg_color=theme.INPUT_BG,
                                         border_color=theme.BORDER, font=theme.font("small"))
        self.output_entry.pack(side="left")
        ctk.CTkButton(row.control, text="Choose…", command=self.app.choose_output_folder, width=84, height=34,
                      fg_color=theme.CARD_ALT, hover_color=theme.BORDER, text_color=theme.TEXT,
                      font=theme.font("small", "bold")).pack(side="left", padx=(theme.SPACE["sm"], 0))
        self.reset_button = ctk.CTkButton(row.control, text="Reset", command=self.app.reset_output_folder,
                                          width=62, height=34, fg_color="transparent", border_width=1,
                                          border_color=theme.BORDER, hover_color=theme.CARD_ALT,
                                          text_color=theme.MUTED, font=theme.font("small"))
        self.reset_button.pack(side="left", padx=(theme.SPACE["sm"], 0))

    def _build_behavior_group(self):
        card = self._group("Accepted formats", 1)
        formats_row = self._row(card, "Video formats", "MP4 · MOV · MKV · AVI · WebM · FLV · WMV · M4V · TS",
                                "video formats file picker compression", 0)
        formats_row.control.grid_remove()

    def _search_focus_in(self, _event=None):
        if self.search_var.get() == "Search settings":
            self.search_var.set("")
            self.filter_rows()

    def _search_focus_out(self, _event=None):
        if not self.search_var.get().strip():
            self.search_var.set("Search settings")
        self.filter_rows()

    def filter_rows(self):
        query = self.search_var.get().strip().casefold()
        if query == "search settings":
            query = ""
        visible_groups = set()
        for widget, keywords in self.rows:
            title = getattr(widget, "title_label", None)
            helper = getattr(widget, "helper_label", None)
            content = " ".join([keywords, title.cget("text") if title else "", helper.cget("text") if helper else widget.cget("text")]).casefold()
            visible = not query or query in content
            if visible:
                widget.grid()
                visible_groups.add(widget.master)
            else:
                widget.grid_remove()
        for heading, card in self.groups:
            visible = card in visible_groups
            card.grid() if visible else card.grid_remove()
            heading.grid() if visible else heading.grid_remove()
