from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD

import theme
from compressor import CompressionJob, next_output_path, output_directory, probe, write_run_log
from pages.about_page import AboutPage
from pages.compress_page import CompressPage
from pages.settings_page import SettingsPage
from version import APP_VERSION
from widgets import IconButton


FORMATS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".ts")
TARGETS = ("5 MB", "8 MB", "10 MB", "15 MB", "20 MB", "25 MB", "50 MB", "100 MB", "Custom")


def resource_path(name):
    import sys
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / name)


class VideoCompressorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """V2 beta application shell; UI callbacks stay on Tk's thread."""

    TARGETS = TARGETS

    def __init__(self):
        ctk.CTk.__init__(self)
        self.TkdndVersion = TkinterDnD._require(self)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=theme.APP_BG)
        self.title("Video Compressor Beta")
        self.geometry(f"{theme.WINDOW['width']}x{theme.WINDOW['height']}")
        self.minsize(theme.WINDOW["min_width"], theme.WINDOW["min_height"])
        try:
            self.iconbitmap(resource_path("VideoCompressor.ico"))
        except Exception:
            pass

        self.beta_appdata = Path(os.environ.get("APPDATA", Path.home())) / "VideoCompressor-Beta"
        self.prefs_path = self.beta_appdata / "settings.json"
        self.stable_prefs_path = Path(os.environ.get("APPDATA", Path.home())) / "VideoCompressor" / "settings.json"
        self.path = None
        self.meta = None
        self.job = None
        self.final_path = None
        self.is_compressing = False
        self.custom_output_dir = None
        self.active_output_dir = None
        self._load_preferences()
        self.target = ctk.StringVar(value=self.initial_target)
        self.custom_target = ctk.StringVar(value=self.initial_custom_target)
        self.output_folder_value = ctk.StringVar(value=str(self.active_output_dir))

        self.grid_columnconfigure(0, weight=0, minsize=theme.RAIL_WIDTH)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_navigation()
        self.page_host = ctk.CTkFrame(self, fg_color="transparent")
        self.page_host.grid(row=1, column=1, sticky="nsew", padx=(theme.SPACE["lg"], theme.SPACE["xxl"]),
                            pady=(theme.SPACE["lg"], theme.SPACE["xl"]))
        self.page_host.grid_columnconfigure(0, weight=1)
        self.page_host.grid_rowconfigure(0, weight=1)
        self.pages = {
            "compress": CompressPage(self.page_host, self),
            "settings": SettingsPage(self.page_host, self),
            "about": AboutPage(self.page_host, self),
        }
        self.nav_buttons["compress"].set_active(True)
        self.show_page("compress")
        self.target_changed(self.target.get(), save=False)
        self.settings_page = self.pages["settings"]
        self.settings_page.reset_button.configure(state="normal" if self.custom_output_dir else "disabled")
        if self.should_import_stable:
            self.save_preferences()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _load_preferences(self):
        saved = {}
        self.should_import_stable = not self.prefs_path.exists()
        source = self.prefs_path if self.prefs_path.exists() else (self.stable_prefs_path if self.should_import_stable else None)
        if source is not None:
            try:
                saved = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                saved = {}
        candidate = str(saved.get("target", "20 MB"))
        self.initial_target = candidate if candidate in TARGETS else "20 MB"
        self.initial_custom_target = str(saved.get("custom_target_mb", "20"))
        saved_output = saved.get("output_folder")
        self.custom_output_dir = str(Path(saved_output).expanduser()) if saved_output and Path(saved_output).is_dir() else None
        self.active_output_dir = output_directory(self.custom_output_dir)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=theme.PANEL_BG, corner_radius=0, height=76,
                              border_width=1, border_color=theme.BORDER)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)
        mark = ctk.CTkLabel(header, text="VC", width=38, height=38, corner_radius=theme.RADIUS["md"],
                            fg_color=theme.ACCENT_SOFT, text_color=theme.ACCENT,
                            font=theme.font("body", "bold"))
        mark.grid(row=0, column=0, rowspan=2, padx=(theme.SPACE["xl"], theme.SPACE["md"]))
        ctk.CTkLabel(header, text="Video Compressor", anchor="w", text_color=theme.TEXT,
                     font=theme.font("heading", "bold")).grid(row=0, column=1, sticky="sw", pady=(13, 0))
        ctk.CTkLabel(header, text="Smaller files. Same story.", anchor="w", text_color=theme.MUTED,
                     font=theme.font("small")).grid(row=1, column=1, sticky="nw", pady=(1, 11))
        badge = ctk.CTkLabel(header, text="BETA", width=48, height=24, corner_radius=theme.RADIUS["sm"],
                             fg_color=theme.ACCENT_SOFT, text_color=theme.ACCENT,
                             font=theme.font("caption", "bold"))
        badge.grid(row=0, column=2, rowspan=2, padx=theme.SPACE["md"])
        ctk.CTkLabel(header, text=f"v{APP_VERSION}", text_color=theme.MUTED,
                     font=theme.font("small")).grid(row=0, column=3, rowspan=2, padx=(0, theme.SPACE["xxl"]))

    def _build_navigation(self):
        rail = ctk.CTkFrame(self, width=theme.RAIL_WIDTH, fg_color=theme.PANEL_BG,
                            corner_radius=0, border_width=1, border_color=theme.BORDER)
        rail.grid(row=1, column=0, sticky="nsew")
        rail.grid_propagate(False)
        rail.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(rail, text="WORKSPACE", text_color=theme.FAINT,
                     font=theme.font("caption", "bold")).grid(row=0, column=0, padx=theme.SPACE["sm"],
                                                               pady=(theme.SPACE["lg"], theme.SPACE["md"]))
        self.nav_buttons = {}
        entries = (("compress", "compress", "Compress"), ("settings", "settings", "Settings"),
                   ("about", "about", "About & updates"))
        for index, (key, icon, label) in enumerate(entries, 1):
            button = IconButton(rail, icon, label, lambda page=key: self.show_page(page))
            button.grid(row=index, column=0, sticky="ew", padx=theme.SPACE["sm"], pady=theme.SPACE["xs"])
            self.nav_buttons[key] = button
        ctk.CTkLabel(rail, text="LOCAL BETA", text_color=theme.FAINT,
                     font=theme.font("caption")).grid(row=8, column=0, padx=theme.SPACE["sm"],
                                                       pady=(theme.SPACE["xl"], theme.SPACE["md"]), sticky="s")

    def show_page(self, name):
        for key, page in self.pages.items():
            page.pack_forget()
            self.nav_buttons[key].set_active(key == name)
        self.pages[name].pack(fill="both", expand=True)

    def target_changed(self, value, save=True):
        page = self.pages.get("compress") if hasattr(self, "pages") else None
        if isinstance(page, CompressPage):
            if value == "Custom":
                page.custom_entry.grid()
            else:
                page.custom_entry.grid_remove()
        if save:
            self.save_preferences()

    def save_preferences(self):
        try:
            self.beta_appdata.mkdir(parents=True, exist_ok=True)
            self.prefs_path.write_text(json.dumps({
                "target": self.target.get(),
                "custom_target_mb": self.custom_target.get(),
                "output_folder": self.custom_output_dir,
            }, indent=2), encoding="utf-8")
        except OSError:
            pass

    def choose_output_folder(self):
        selected = filedialog.askdirectory(title="Choose output folder", initialdir=str(self.active_output_dir), mustexist=True)
        if not selected:
            return
        try:
            self.active_output_dir = output_directory(selected)
        except OSError as error:
            messagebox.showerror("Folder unavailable", f"Could not use this output folder.\n\n{error}")
            return
        self.custom_output_dir = str(self.active_output_dir)
        self.output_folder_value.set(str(self.active_output_dir))
        self.settings_page.output_entry.xview_moveto(1)
        self.settings_page.reset_button.configure(state="normal")
        self.save_preferences()

    def reset_output_folder(self):
        self.custom_output_dir = None
        self.active_output_dir = output_directory()
        self.output_folder_value.set(str(self.active_output_dir))
        self.settings_page.output_entry.xview_moveto(1)
        self.settings_page.reset_button.configure(state="disabled")
        self.save_preferences()

    def pick(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi *.webm *.flv *.wmv *.m4v *.ts"), ("All files", "*.*")])
        if path:
            self.load_file(path)

    def dropped(self, event):
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            paths = [event.data.strip("{}").strip()]
        if paths:
            self.load_file(paths[0])

    def load_file(self, path):
        if Path(path).suffix.lower() not in FORMATS:
            messagebox.showerror("Unsupported file", "Choose a supported video file.")
            return
        self.pages["compress"].set_status("Reading video details…")
        try:
            meta = probe(path)
        except Exception as error:
            self.pages["compress"].set_status("Could not read this video")
            messagebox.showerror("Could not load video", str(error))
            return
        self.path, self.meta = path, meta
        self.pages["compress"].set_file(path, meta)

    def start(self):
        if not self.path:
            return
        try:
            self.active_output_dir = output_directory(self.custom_output_dir)
        except OSError as error:
            messagebox.showerror("Output folder unavailable", f"Could not create or access the output folder.\n\n{error}")
            return
        try:
            mb = float(self.custom_target.get()) if self.target.get() == "Custom" else float(self.target.get().split()[0])
            if mb <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Invalid target", "Enter a target size greater than zero MB.")
            return
        size = os.path.getsize(self.path)
        if size < mb * 1_000_000:
            answer = messagebox.askyesnocancel("Already under target", "This video is already smaller than the target.\n\nYes: copy it as an MP4 output\nNo: re-encode anyway\nCancel: do nothing")
            if answer is None:
                return
            if answer:
                output = self._copy_output()
                try:
                    write_run_log(self.path, mb, {"path": output, "size": os.path.getsize(output)}, output,
                                  self.meta, ["Copied the source file without re-encoding because it was already below the target size."],
                                  custom_output_dir=self.active_output_dir)
                except OSError:
                    pass
                self.final_path = output
                self.pages["compress"].set_finished({"path": output, "size": os.path.getsize(output)})
                return
        page = self.pages["compress"]
        page.progress_bar.set(0)
        page.set_busy(True)
        self.is_compressing = True
        self.job = CompressionJob(self.path, mb,
                                  lambda fraction, remaining: self.after(0, page.set_progress, fraction, remaining),
                                  lambda status: self.after(0, page.set_status, status),
                                  lambda result: self.after(0, self.finished, result), str(self.active_output_dir))
        threading.Thread(target=self.job.run, daemon=True).start()

    def _copy_output(self):
        source = Path(self.path)
        destination = next_output_path(self.path, source.suffix, self.active_output_dir)
        shutil.copy2(source, destination)
        return str(destination)

    def finished(self, result):
        self.is_compressing = False
        page = self.pages["compress"]
        page.set_busy(False)
        if result.get("cancelled"):
            page.set_finished(result)
            return
        if result.get("error"):
            page.set_finished(result)
            messagebox.showerror("Compression failed", result["error"])
            return
        self.final_path = result["path"]
        page.set_finished(result)

    def cancel(self):
        if self.job:
            self.job.cancel()
            self.pages["compress"].set_status("Cancelling…")

    def folder(self):
        if self.final_path:
            os.startfile(str(Path(self.final_path).parent))

    def open(self):
        if self.final_path:
            os.startfile(self.final_path)

    def _close(self):
        if self.is_compressing:
            if not messagebox.askyesno("Compression running", "Cancel compression and close the beta?"):
                return
            self.cancel()
        self.destroy()
