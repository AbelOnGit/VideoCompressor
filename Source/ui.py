from __future__ import annotations
import json, os, queue, shutil, subprocess, sys, threading, time, webbrowser
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from compressor import CompressionJob, next_output_path, output_directory, probe, write_run_log
from updater import (check_for_update, cleanup_obsolete_updates,
                     cleanup_previous_executables, download_update)
from tools import ensure_tools, tools_are_ready
from version import APP_VERSION

APPDATA = Path(os.environ.get("APPDATA", Path.home())) / "VideoCompressor"
PREFS = APPDATA / "settings.json"
FORMATS = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".ts")

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base / name)

class VideoCompressorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        ctk.CTk.__init__(self); self.TkdndVersion = TkinterDnD._require(self)
        self.title("Video Compressor"); self.geometry("720x760"); self.minsize(640, 680)
        try: self.iconbitmap(resource_path("VideoCompressor.ico"))
        except Exception: pass
        ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("blue")
        self.path = None; self.meta = None; self.job = None; self.final_path = None
        try: saved = json.loads(PREFS.read_text(encoding="utf-8"))
        except Exception: saved = {}
        initial = str(saved.get("target", "20 MB"))
        saved_output = saved.get("output_folder")
        self.custom_output_dir = str(Path(saved_output).expanduser()) if saved_output and Path(saved_output).is_dir() else None
        self.active_output_dir = output_directory(self.custom_output_dir)
        self.is_compressing = False
        self.update_events=queue.Queue(); self.update_release=None; self.update_window=None
        self.update_progress_bar=None; self.update_status_label=None; self.restart_button=None
        self.installed_update_version=None
        self.tools_ready=tools_are_ready(); self.tools_window=None
        self.tools_progress_bar=None; self.tools_status_label=None
        if self._is_installed_copy():
            cleanup_obsolete_updates(APP_VERSION)
            cleanup_previous_executables(Path(sys.executable).resolve().parent)
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="VIDEO COMPRESSOR", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0,column=0,pady=(24,12))
        self.drop = ctk.CTkFrame(self, corner_radius=18, border_width=2, border_color="#3b82f6")
        self.drop.grid(row=1,column=0,sticky="nsew",padx=28,pady=10); self.drop.grid_columnconfigure(0,weight=1)
        self.drop.bind("<Button-1>", lambda _: self.pick()); self.drop.drop_target_register(DND_FILES); self.drop.dnd_bind("<<Drop>>", self.dropped)
        self.drop_text = ctk.CTkLabel(self.drop,text="Drag and drop a video here\nor click to select",font=ctk.CTkFont(size=20),justify="center")
        self.drop_text.grid(row=0,column=0,sticky="nsew",pady=52); self.drop_text.bind("<Button-1>",lambda _:self.pick())
        self.info = ctk.CTkLabel(self,text="",justify="left",font=ctk.CTkFont(size=14)); self.info.grid(row=2,column=0,padx=28,pady=(8,4),sticky="w")
        controls=ctk.CTkFrame(self,fg_color="transparent"); controls.grid(row=3,column=0,padx=28,pady=(4,8),sticky="ew"); controls.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(controls,text="Target size · decimal MB").grid(row=0,column=0,padx=(0,12))
        self.target=ctk.StringVar(value=initial if initial in ["5 MB","8 MB","10 MB","15 MB","20 MB","25 MB","50 MB","100 MB","Custom"] else "20 MB")
        self.menu=ctk.CTkOptionMenu(controls,values=["5 MB","8 MB","10 MB","15 MB","20 MB","25 MB","50 MB","100 MB","Custom"],variable=self.target,command=self.target_changed); self.menu.grid(row=0,column=1,sticky="w")
        self.custom=ctk.CTkEntry(controls,width=100,placeholder_text="MB"); self.custom.grid(row=0,column=2,padx=12); self.custom.grid_remove()
        folder=ctk.CTkFrame(self,fg_color="transparent"); folder.grid(row=4,column=0,padx=28,pady=(0,4),sticky="ew"); folder.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(folder,text="Output folder",font=ctk.CTkFont(size=13,weight="bold")).grid(row=0,column=0,padx=(0,10),sticky="w")
        self.output_folder_value=ctk.StringVar(value=str(self.active_output_dir))
        self.output_entry=ctk.CTkEntry(folder,textvariable=self.output_folder_value,state="readonly",height=34)
        self.output_entry.grid(row=0,column=1,sticky="ew")
        self.browse_button=ctk.CTkButton(folder,text="Browse…",width=88,height=34,command=self.choose_output_folder)
        self.browse_button.grid(row=0,column=2,padx=(8,0))
        self.default_button=ctk.CTkButton(folder,text="Default",width=78,height=34,command=self.reset_output_folder,
                                          fg_color="transparent",border_width=1,text_color=("#1f2937","#e5e7eb"))
        self.default_button.grid(row=0,column=3,padx=(8,0))
        ctk.CTkLabel(folder,text="Compressed videos and run logs are saved here.",font=ctk.CTkFont(size=11),
                     text_color="gray70").grid(row=1,column=1,columnspan=3,pady=(4,0),sticky="w")
        self.default_button.configure(state="normal" if self.custom_output_dir else "disabled")
        self.compress=ctk.CTkButton(self,text="Compress",height=48,font=ctk.CTkFont(size=18,weight="bold"),command=self.start,state="disabled"); self.compress.grid(row=5,column=0,padx=28,pady=8,sticky="ew")
        self.progress=ctk.CTkProgressBar(self); self.progress.set(0); self.progress.grid(row=6,column=0,padx=28,pady=(12,4),sticky="ew")
        row=ctk.CTkFrame(self,fg_color="transparent"); row.grid(row=7,column=0,padx=28,sticky="ew"); row.grid_columnconfigure(0,weight=1)
        self.status=ctk.CTkLabel(row,text="Ready",anchor="w"); self.status.grid(row=0,column=0,sticky="w")
        self.percent=ctk.CTkLabel(row,text="0% · — remaining"); self.percent.grid(row=0,column=1,sticky="e")
        self.cancel_btn=ctk.CTkButton(self,text="Cancel",command=self.cancel,fg_color="#8b2d2d",hover_color="#a33",state="disabled"); self.cancel_btn.grid(row=8,column=0,padx=28,pady=8,sticky="ew")
        self.result=ctk.CTkLabel(self,text="",font=ctk.CTkFont(size=14)); self.result.grid(row=9,column=0,pady=4)
        actions=ctk.CTkFrame(self,fg_color="transparent"); actions.grid(row=10,column=0,pady=(0,4))
        self.open_folder=ctk.CTkButton(actions,text="Open folder",command=self.folder,state="disabled"); self.open_folder.grid(row=0,column=0,padx=6)
        self.open_file=ctk.CTkButton(actions,text="Open file",command=self.open,state="disabled"); self.open_file.grid(row=0,column=1,padx=6)
        self.updater_status=ctk.CTkLabel(self,text=f"Video Compressor v{APP_VERSION} · Automatic updates for installed copies",
                                         font=ctk.CTkFont(size=10),text_color="gray60")
        self.updater_status.grid(row=11,column=0,pady=(0,8))
        if self.target.get()=="Custom": self.target_changed("Custom")
        self.after(100,self.process_update_events)
        if self.tools_ready:
            self.after(2500,self.check_updates)
        else:
            self.after(250,self.start_tools_download)

    def _is_installed_copy(self):
        installed_dir=Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "VideoCompressor"
        return (getattr(sys,"frozen",False)
                and Path(sys.executable).resolve().parent == installed_dir.resolve())

    def target_changed(self,value):
        if value=="Custom": self.custom.grid()
        else: self.custom.grid_remove()
        self.save_preferences()
    def save_preferences(self):
        try:
            APPDATA.mkdir(parents=True,exist_ok=True)
            PREFS.write_text(json.dumps({"target":self.target.get(),"output_folder":self.custom_output_dir},indent=2),encoding="utf-8")
        except OSError: pass
    def choose_output_folder(self):
        selected=filedialog.askdirectory(title="Choose output folder",initialdir=str(self.active_output_dir),mustexist=True)
        if not selected:return
        try:self.active_output_dir=output_directory(selected)
        except OSError as e:messagebox.showerror("Folder unavailable",f"Could not use this output folder.\n\n{e}"); return
        self.custom_output_dir=str(self.active_output_dir)
        self.output_folder_value.set(str(self.active_output_dir)); self.output_entry.xview_moveto(1)
        self.default_button.configure(state="normal"); self.save_preferences()
    def reset_output_folder(self):
        self.custom_output_dir=None; self.active_output_dir=output_directory()
        self.output_folder_value.set(str(self.active_output_dir)); self.output_entry.xview_moveto(1)
        self.default_button.configure(state="disabled"); self.save_preferences()
    def pick(self):
        if not self.tools_ready:
            self.status.configure(text="Downloading the video tools needed to open videos...")
            return
        p=filedialog.askopenfilename(filetypes=[("Video files","*.mp4 *.mov *.mkv *.avi *.webm *.flv *.wmv *.m4v *.ts"),("All files","*.*")])
        if p:self.load_file(p)
    def dropped(self,event):
        if not self.tools_ready:
            self.status.configure(text="Downloading the video tools needed to open videos...")
            return
        try: paths=self.tk.splitlist(event.data)
        except Exception: paths=[event.data.strip("{}")]
        if paths:self.load_file(paths[0])
    def load_file(self,p):
        if not self.tools_ready:
            self.status.configure(text="Downloading the video tools needed to open videos...")
            return
        if Path(p).suffix.lower() not in FORMATS: messagebox.showerror("Unsupported file","Choose a supported video file."); return
        self.status.configure(text="Reading video details…"); self.update_idletasks()
        try: meta=probe(p)
        except Exception as e: self.status.configure(text="Error"); messagebox.showerror("Could not load video",str(e)); return
        self.path,self.meta=p,meta; self.drop_text.configure(text=Path(p).name)
        self.info.configure(text=f"{Path(p).name}\n{os.path.getsize(p)/1_000_000:.2f} MB  ·  {meta['duration']/60:.2f} min  ·  {meta['width']} × {meta['height']}")
        self.compress.configure(state="normal"); self.status.configure(text="Ready"); self.result.configure(text="")
    def start(self):
        if not self.tools_ready:
            self.status.configure(text="Video tools are still downloading...")
            return
        if not self.path:return
        try:self.active_output_dir=output_directory(self.custom_output_dir)
        except OSError as e:messagebox.showerror("Output folder unavailable",f"Could not create or access the output folder.\n\n{e}"); return
        try: mb=float(self.custom.get()) if self.target.get()=="Custom" else float(self.target.get().split()[0]); assert mb>0
        except Exception: messagebox.showerror("Invalid target","Enter a target size greater than zero MB."); return
        size=os.path.getsize(self.path)
        if size < mb*1_000_000:
            answer=messagebox.askyesnocancel("Already under target", "This video is already smaller than the target.\n\nYes: copy it as an MP4 output\nNo: re-encode anyway\nCancel: do nothing")
            if answer is None:return
            if answer:
                out=self._copy_output()
                try:
                    write_run_log(self.path, mb, {"path": out, "size": os.path.getsize(out)}, out, self.meta,
                                  ["Copied the source file without re-encoding because it was already below the target size."],
                                  custom_output_dir=self.active_output_dir)
                except OSError: pass
                self.final_path=out; self.result.configure(text=f"Done · {os.path.getsize(out)/1_000_000:.2f} MB"); self.open_folder.configure(state="normal"); self.open_file.configure(state="normal"); self.status.configure(text="Done"); return
        self.result.configure(text=""); self.open_folder.configure(state="disabled"); self.open_file.configure(state="disabled"); self.progress.set(0)
        self.compress.configure(state="disabled"); self.cancel_btn.configure(state="normal")
        self.is_compressing=True; self.browse_button.configure(state="disabled"); self.default_button.configure(state="disabled")
        self.job=CompressionJob(self.path,mb,lambda p,t:self.after(0,self.update_progress,p,t),lambda s:self.after(0,lambda:self.status.configure(text=s)),lambda r:self.after(0,self.finished,r),str(self.active_output_dir))
        threading.Thread(target=self.job.run,daemon=True).start()
    def _copy_output(self):
        import shutil
        src=Path(self.path); dest=next_output_path(self.path, src.suffix, self.active_output_dir)
        shutil.copy2(src,dest); return str(dest)
    def update_progress(self,p,t): self.progress.set(p); self.percent.configure(text=f"{p*100:.0f}% · {int(t//60)}:{int(t%60):02d} remaining")
    def finished(self,r):
        self.is_compressing=False
        self.browse_button.configure(state="normal")
        self.default_button.configure(state="normal" if self.custom_output_dir else "disabled")
        self.compress.configure(state="normal" if self.path else "disabled"); self.cancel_btn.configure(state="disabled")
        self._enable_restart_if_ready()
        if r.get("cancelled"): self.status.configure(text="Cancelled"); self.progress.set(0); return
        if r.get("error"): self.status.configure(text="Error"); messagebox.showerror("Compression failed",r["error"]); return
        self.final_path=r["path"]; self.progress.set(1); self.percent.configure(text="100% · 0:00 remaining"); self.status.configure(text="Done")
        self.result.configure(text=f"Final size: {r['size']/1_000_000:.2f} MB"); self.open_folder.configure(state="normal"); self.open_file.configure(state="normal")
    def cancel(self):
        if self.job:self.job.cancel(); self.status.configure(text="Cancelling…")
    def folder(self):
        if self.final_path:os.startfile(str(Path(self.final_path).parent))
    def open(self):
        if self.final_path:os.startfile(self.final_path)
    def check_updates(self):
        if not self._is_installed_copy():return
        def worker():
            try:
                release=check_for_update(APP_VERSION)
                self.update_events.put(("available" if release else "up_to_date", release))
            except Exception as e:
                self.update_events.put(("check_error",str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def process_update_events(self):
        try:
            while True:
                event,value=self.update_events.get_nowait()
                if event=="available": self.show_update_available(value)
                elif event=="up_to_date": self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Up to date")
                elif event=="check_error":
                    self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Update check unavailable")
                    self.show_update_error(f"The app could not check GitHub for updates.\n\n{value}")
                elif event=="download_progress": self.set_download_progress(value[0],value[1])
                elif event=="update_status": self.set_update_status(value)
                elif event=="update_bootstrap_status": self.set_bootstrap_progress(value[0],value[1])
                elif event=="installed": self.show_update_installed(value)
                elif event=="update_error": self.show_update_error(value)
                elif event=="tools_progress": self.set_tools_progress(value[0],value[1])
                elif event=="tools_status": self.set_tools_status(value)
                elif event=="tools_ready": self.finish_tools_download()
                elif event=="tools_error": self.show_tools_error(value)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100,self.process_update_events)

    def start_tools_download(self):
        if self.tools_ready or (self.tools_window is not None and self.tools_window.winfo_exists()):
            return
        self.tools_window=ctk.CTkToplevel(self)
        self.tools_window.title("Preparing Video Compressor")
        self.tools_window.geometry("500x230")
        self.tools_window.resizable(False,False)
        self.tools_window.transient(self)
        self.tools_window.protocol("WM_DELETE_WINDOW",lambda:None)
        self.tools_window.grab_set()
        content=ctk.CTkFrame(self.tools_window,fg_color="transparent")
        content.pack(fill="both",expand=True,padx=28,pady=24)
        ctk.CTkLabel(content,text="Preparing Video Compressor",font=ctk.CTkFont(size=22,weight="bold")).pack(anchor="w",pady=(4,18))
        self.tools_status_label=ctk.CTkLabel(content,text="Downloading video tools... 0%",anchor="w",font=ctk.CTkFont(size=13))
        self.tools_status_label.pack(fill="x",pady=(0,12))
        self.tools_progress_bar=ctk.CTkProgressBar(content,height=14)
        self.tools_progress_bar.set(0); self.tools_progress_bar.pack(fill="x")
        ctk.CTkLabel(content,text="This one-time download is saved for future launches.",font=ctk.CTkFont(size=11),
                     text_color="gray70").pack(anchor="w",pady=(12,0))
        self.updater_status.configure(text="Downloading video tools from GitHub...")
        threading.Thread(target=self._download_tools_worker,daemon=True).start()

    def _download_tools_worker(self):
        try:
            ensure_tools(
                on_progress=lambda received,total:self.update_events.put(("tools_progress",(received,total))),
                on_status=lambda status:self.update_events.put(("tools_status",status)),
            )
            self.update_events.put(("tools_ready",None))
        except Exception as e:
            self.update_events.put(("tools_error",str(e)))

    def set_tools_progress(self,received,total):
        if self.tools_progress_bar is None:return
        fraction=min(1.0,received/max(total,1))
        self.tools_progress_bar.set(fraction)
        self.tools_status_label.configure(text=f"Downloading video tools... {fraction*100:.0f}%")

    def set_tools_status(self,status):
        if self.tools_status_label is not None:
            self.tools_status_label.configure(text=status)
        self.updater_status.configure(text=status)

    def finish_tools_download(self):
        self.tools_ready=True
        if self.tools_window is not None:
            try:self.tools_window.destroy()
            except Exception:pass
            self.tools_window=None
        self.tools_status_label=None; self.tools_progress_bar=None
        self.status.configure(text="Ready")
        self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Video tools ready")
        self.after(2500,self.check_updates)

    def show_tools_error(self,message):
        if self.tools_window is not None:
            try:self.tools_window.destroy()
            except Exception:pass
            self.tools_window=None
        self.tools_status_label=None; self.tools_progress_bar=None
        content=self._new_update_window("Video tools unavailable","520x320")
        ctk.CTkLabel(content,text="Video tools could not be downloaded",font=ctk.CTkFont(size=21,weight="bold"),
                     text_color="#f87171").pack(anchor="w",pady=(4,12))
        ctk.CTkLabel(content,text=f"Video Compressor needs ffmpeg.exe and ffprobe.exe to process videos.\n\n{message}",
                     justify="left",wraplength=450,font=ctk.CTkFont(size=12)).pack(anchor="w",fill="both",expand=True)
        buttons=ctk.CTkFrame(content,fg_color="transparent")
        buttons.pack(side="bottom",fill="x",pady=(18,0))
        ctk.CTkButton(buttons,text="Close",width=90,fg_color="transparent",border_width=1,
                      command=self.ignore_update).pack(side="right",padx=(8,0))
        ctk.CTkButton(buttons,text="Retry",width=90,command=self.retry_tools_download).pack(side="right",padx=(8,0))
        ctk.CTkButton(buttons,text="Open GitHub Releases",width=170,
                      command=lambda:self.open_releases(self.update_window)).pack(side="right")

    def retry_tools_download(self):
        if self.update_window is not None:
            try:self.update_window.destroy()
            except Exception:pass
            self.update_window=None
        self.start_tools_download()

    def _new_update_window(self,title,geometry):
        if self.update_window is not None:
            try:self.update_window.destroy()
            except Exception:pass
        self.update_window=ctk.CTkToplevel(self)
        self.update_window.title(title)
        self.update_window.geometry(geometry)
        self.update_window.resizable(False,False)
        self.update_window.transient(self)
        self.update_window.protocol("WM_DELETE_WINDOW",self.ignore_update)
        self.update_window.grab_set()
        content=ctk.CTkFrame(self.update_window,fg_color="transparent")
        content.pack(fill="both",expand=True,padx=28,pady=24)
        return content

    def show_update_available(self,release):
        if self.update_window is not None:
            try:
                if self.update_window.winfo_exists():return
            except Exception:pass
        self.update_release=release
        new_version=str(release.get("tag_name","unknown")).removeprefix("v")
        content=self._new_update_window("Update available","500x270")
        ctk.CTkLabel(content,text="Update available",font=ctk.CTkFont(size=25,weight="bold")).pack(anchor="w",pady=(8,12))
        ctk.CTkLabel(content,text=f"A newer version of Video Compressor is ready.\n\nCurrent version: {APP_VERSION}\nNew version: {new_version}",
                     justify="left",font=ctk.CTkFont(size=15)).pack(anchor="w",fill="x")
        buttons=ctk.CTkFrame(content,fg_color="transparent")
        buttons.pack(side="bottom",fill="x",pady=(20,0))
        ctk.CTkButton(buttons,text="Ignore",width=110,fg_color="transparent",border_width=1,
                      command=self.ignore_update).pack(side="right",padx=(8,0))
        ctk.CTkButton(buttons,text="Update",width=130,command=self.begin_update).pack(side="right")

    def ignore_update(self):
        if self.update_window is not None:
            try:self.update_window.destroy()
            except Exception:pass
            self.update_window=None
        if self.update_release:
            version=self.update_release.get("tag_name","new version")
            self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Ignoring {version} until next launch")
        self.update_release=None

    def begin_update(self):
        release=self.update_release
        if not release:return
        self.update_release=None
        content=self._new_update_window("Updating Video Compressor","500x270")
        ctk.CTkLabel(content,text="Updating Video Compressor",font=ctk.CTkFont(size=22,weight="bold")).pack(anchor="w",pady=(8,24))
        self.update_status_label=ctk.CTkLabel(content,text="Downloading update... 0%",anchor="w",font=ctk.CTkFont(size=14))
        self.update_status_label.pack(fill="x",pady=(0,12))
        self.update_progress_bar=ctk.CTkProgressBar(content,height=14)
        self.update_progress_bar.set(0); self.update_progress_bar.pack(fill="x")
        self.updater_status.configure(text=f"Downloading update {release.get('tag_name','')}…")
        threading.Thread(target=self.install_update_worker,args=(release,),daemon=True).start()

    def set_download_progress(self,downloaded,total):
        if self.update_status_label is None:return
        fraction=min(1.0,downloaded/max(total,1))
        self.update_progress_bar.set(fraction)
        self.update_status_label.configure(text=f"Downloading update... {fraction*100:.0f}%")

    def set_update_status(self,status):
        if self.update_status_label is not None:
            self.update_status_label.configure(text=status)
        if status=="Installing update..." and self.update_progress_bar is not None:
            self.update_progress_bar.set(1)

    def set_bootstrap_progress(self,status,percent):
        if self.update_status_label is None:return
        self.update_status_label.configure(text=(f"{status} {percent}%" if status.startswith("Downloading") else status))
        if self.update_progress_bar is not None:
            self.update_progress_bar.set(max(0,min(100,percent))/100)

    @staticmethod
    def _clean_child_environment():
        environment=os.environ.copy()
        for name in list(environment):
            upper=name.upper()
            if (upper in {"_MEIPASS", "_MEIPASS2"}
                    or upper.startswith("_PYI_")
                    or upper.startswith("PYINSTALLER_")):
                environment.pop(name,None)
        return environment

    def install_update_worker(self,release):
        try:
            installer=download_update(
                release,
                on_progress=lambda downloaded,total:self.update_events.put(("download_progress",(downloaded,total))),
                on_status=lambda status:self.update_events.put(("update_status",status)),
            )
            self.update_events.put(("update_status","Starting online installer..."))
            app_exe=Path(sys.executable).resolve()
            old_exe=app_exe.with_name(f"VideoCompressor.old-{os.getpid()}.exe")
            if old_exe.exists():
                old_exe.unlink()
            app_exe.rename(old_exe)

            local_app_data=Path(os.environ.get("LOCALAPPDATA",Path.home())) / "VideoCompressor"
            local_app_data.mkdir(parents=True,exist_ok=True)
            log_path=local_app_data / "update-install.log"
            flags=(getattr(subprocess,"DETACHED_PROCESS",0x00000008)
                   |getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0x00000200)
                   |getattr(subprocess,"CREATE_BREAKAWAY_FROM_JOB",0x01000000))
            install_dir=app_exe.parent
            progress_path=Path(os.environ.get("LOCALAPPDATA",Path.home())) / "VideoCompressor" / "online-installer-progress.json"
            try:progress_path.unlink(missing_ok=True)
            except OSError:pass
            process=subprocess.Popen(
                [str(installer),"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART",
                 f"/DIR={install_dir}",f'/LOG="{log_path}"'],
                cwd=str(installer.parent),env=self._clean_child_environment(),
                creationflags=flags,close_fds=True,
            )
            last_progress=None
            while process.poll() is None:
                try:
                    progress=json.loads(progress_path.read_text(encoding="utf-8"))
                    state=(str(progress.get("stage","Installing update...")),int(progress.get("percent",0)))
                    if state!=last_progress:
                        self.update_events.put(("update_bootstrap_status",state))
                        last_progress=state
                except (OSError,ValueError,TypeError):
                    pass
                time.sleep(0.2)
            exit_code=process.wait()
            try:progress_path.unlink(missing_ok=True)
            except OSError:pass
            log_text=log_path.read_text(encoding="utf-8",errors="replace") if log_path.exists() else ""
            if exit_code!=0 or "Installation process succeeded." not in log_text or not app_exe.is_file():
                detail=f"Installer exit code: {exit_code}. Log: {log_path}"
                if log_text:
                    detail += "\n\n" + "\n".join(log_text.splitlines()[-12:])
                raise RuntimeError(detail)

            installed_version=str(release.get("tag_name","new version")).removeprefix("v")
            shutil.rmtree(installer.parent,ignore_errors=True)
            try:(installer.parent.parent).rmdir()
            except OSError:pass
            self.update_events.put(("installed",installed_version))
        except Exception as e:
            try:
                app_exe=Path(sys.executable).resolve()
                old_exe=app_exe.with_name(f"VideoCompressor.old-{os.getpid()}.exe")
                if old_exe.exists() and not app_exe.exists():old_exe.rename(app_exe)
            except OSError:pass
            self.update_events.put(("update_error",str(e)))

    def show_update_installed(self,version):
        self.installed_update_version=version
        self.updater_status.configure(text=f"Update installed · v{version} is ready")
        content=self._new_update_window("Update installed","500x270")
        ctk.CTkLabel(content,text="Update installed",font=ctk.CTkFont(size=25,weight="bold")).pack(anchor="w",pady=(8,12))
        ctk.CTkLabel(content,text=f"Video Compressor v{version} is installed.",justify="left",
                     font=ctk.CTkFont(size=15)).pack(anchor="w",fill="x")
        self.restart_note=ctk.CTkLabel(content,text="Restart now to use the new version.",anchor="w",font=ctk.CTkFont(size=12))
        self.restart_note.pack(anchor="w",pady=(18,0))
        buttons=ctk.CTkFrame(content,fg_color="transparent")
        buttons.pack(side="bottom",fill="x",pady=(16,0))
        ctk.CTkButton(buttons,text="Restart later",width=130,fg_color="transparent",border_width=1,
                      command=self.restart_later).pack(side="right",padx=(8,0))
        self.restart_button=ctk.CTkButton(buttons,text="Restart now",width=130,command=self.restart_now)
        self.restart_button.pack(side="right")
        self._enable_restart_if_ready()

    def _enable_restart_if_ready(self):
        if self.installed_update_version and self.restart_button is not None:
            if self.is_compressing:
                self.restart_button.configure(state="disabled")
                self.restart_note.configure(text="Restart is available when compression finishes.")
            else:
                self.restart_button.configure(state="normal")
                self.restart_note.configure(text="Restart now to use the new version.")

    def restart_later(self):
        if self.update_window is not None:
            try:self.update_window.destroy()
            except Exception:pass
        self.update_window=None; self.restart_button=None
        self.updater_status.configure(text=f"Update v{self.installed_update_version} installed · Restart later to use it")

    def restart_now(self):
        if self.is_compressing:return
        app_exe=Path(sys.executable).resolve().with_name("VideoCompressor.exe")
        if not app_exe.is_file():
            self.show_update_error(f"The new app executable was not found at:\n{app_exe}")
            return
        flags=(getattr(subprocess,"DETACHED_PROCESS",0x00000008)
               |getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0x00000200)
               |getattr(subprocess,"CREATE_BREAKAWAY_FROM_JOB",0x01000000))
        try:
            subprocess.Popen([str(app_exe)],cwd=str(app_exe.parent),env=self._clean_child_environment(),
                             creationflags=flags,close_fds=True)
        except OSError as e:
            self.show_update_error(f"The update is installed, but the new app could not be started.\n\n{e}")
            return
        self.destroy()
        os._exit(0)

    def show_update_error(self,message):
        content=self._new_update_window("Update error","520x320")
        ctk.CTkLabel(content,text="Update could not be completed",font=ctk.CTkFont(size=21,weight="bold"),
                     text_color="#f87171").pack(anchor="w",pady=(4,12))
        ctk.CTkLabel(content,text=message,justify="left",wraplength=450,
                     font=ctk.CTkFont(size=12)).pack(anchor="w",fill="both",expand=True)
        buttons=ctk.CTkFrame(content,fg_color="transparent")
        buttons.pack(side="bottom",fill="x",pady=(18,0))
        ctk.CTkButton(buttons,text="Close",width=100,fg_color="transparent",border_width=1,
                      command=self.ignore_update).pack(side="right",padx=(8,0))
        ctk.CTkButton(buttons,text="Open GitHub Releases",width=170,
                      command=lambda:self.open_releases(self.update_window)).pack(side="right")

    @staticmethod
    def open_releases(dialog=None):
        webbrowser.open("https://github.com/AbelOnGit/VideoCompressor/releases")
        if dialog is not None:
            dialog.destroy()
