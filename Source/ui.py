from __future__ import annotations
import json, os, subprocess, sys, threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from compressor import CompressionJob, next_output_path, output_directory, probe, write_run_log
from updater import check_for_update, download_update
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
        self.is_compressing = False; self.pending_installer = None
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="VIDEO COMPRESSOR", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0,column=0,pady=(24,12))
        self.drop = ctk.CTkFrame(self, corner_radius=18, border_width=2, border_color="#3b82f6")
        self.drop.grid(row=1,column=0,sticky="nsew",padx=28,pady=10); self.drop.grid_columnconfigure(0,weight=1)
        self.drop.bind("<Button-1>", lambda _: self.pick()); self.drop.drop_target_register(DND_FILES); self.drop.dnd_bind("<<Drop>>", self.dropped)
        self.drop_text = ctk.CTkLabel(self.drop,text="Drag and drop a video here\nor click to select",font=ctk.CTkFont(size=20),justify="center")
        self.drop_text.grid(row=0,column=0,sticky="nsew",pady=52); self.drop_text.bind("<Button-1>",lambda _:self.pick())
        self.info = ctk.CTkLabel(self,text="",justify="left",font=ctk.CTkFont(size=14)); self.info.grid(row=2,column=0,padx=28,pady=(8,4),sticky="w")
        controls=ctk.CTkFrame(self,fg_color="transparent"); controls.grid(row=3,column=0,padx=28,pady=(4,8),sticky="ew"); controls.grid_columnconfigure(1,weight=1)
        ctk.CTkLabel(controls,text="Target size").grid(row=0,column=0,padx=(0,12))
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
        self.after(2500,self.check_updates)

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
        p=filedialog.askopenfilename(filetypes=[("Video files","*.mp4 *.mov *.mkv *.avi *.webm *.flv *.wmv *.m4v *.ts"),("All files","*.*")])
        if p:self.load_file(p)
    def dropped(self,event):
        try: paths=self.tk.splitlist(event.data)
        except Exception: paths=[event.data.strip("{}")]
        if paths:self.load_file(paths[0])
    def load_file(self,p):
        if Path(p).suffix.lower() not in FORMATS: messagebox.showerror("Unsupported file","Choose a supported video file."); return
        self.status.configure(text="Reading video details…"); self.update_idletasks()
        try: meta=probe(p)
        except Exception as e: self.status.configure(text="Error"); messagebox.showerror("Could not load video",str(e)); return
        self.path,self.meta=p,meta; self.drop_text.configure(text=Path(p).name)
        self.info.configure(text=f"{Path(p).name}\n{os.path.getsize(p)/1048576:.2f} MB  ·  {meta['duration']/60:.2f} min  ·  {meta['width']} × {meta['height']}")
        self.compress.configure(state="normal"); self.status.configure(text="Ready"); self.result.configure(text="")
    def start(self):
        if not self.path:return
        try:self.active_output_dir=output_directory(self.custom_output_dir)
        except OSError as e:messagebox.showerror("Output folder unavailable",f"Could not create or access the output folder.\n\n{e}"); return
        try: mb=float(self.custom.get()) if self.target.get()=="Custom" else float(self.target.get().split()[0]); assert mb>0
        except Exception: messagebox.showerror("Invalid target","Enter a target size greater than zero MB."); return
        size=os.path.getsize(self.path)
        if size < mb*1048576:
            answer=messagebox.askyesnocancel("Already under target", "This video is already smaller than the target.\n\nYes: copy it as an MP4 output\nNo: re-encode anyway\nCancel: do nothing")
            if answer is None:return
            if answer:
                out=self._copy_output()
                try:
                    write_run_log(self.path, mb, {"path": out, "size": os.path.getsize(out)}, out, self.meta,
                                  ["Copied the source file without re-encoding because it was already below the target size."],
                                  custom_output_dir=self.active_output_dir)
                except OSError: pass
                self.final_path=out; self.result.configure(text=f"Done · {os.path.getsize(out)/1048576:.2f} MB"); self.open_folder.configure(state="normal"); self.open_file.configure(state="normal"); self.status.configure(text="Done"); return
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
        if self.pending_installer:
            installer,self.pending_installer=self.pending_installer,None
            self.launch_update(installer); return
        if r.get("cancelled"): self.status.configure(text="Cancelled"); self.progress.set(0); return
        if r.get("error"): self.status.configure(text="Error"); messagebox.showerror("Compression failed",r["error"]); return
        self.final_path=r["path"]; self.progress.set(1); self.percent.configure(text="100% · 0:00 remaining"); self.status.configure(text="Done")
        self.result.configure(text=f"Final size: {r['size']/1048576:.2f} MB"); self.open_folder.configure(state="normal"); self.open_file.configure(state="normal")
    def cancel(self):
        if self.job:self.job.cancel(); self.status.configure(text="Cancelling…")
    def folder(self):
        if self.final_path:os.startfile(str(Path(self.final_path).parent))
    def open(self):
        if self.final_path:os.startfile(self.final_path)
    def check_updates(self):
        installed_dir=Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "VideoCompressor"
        if not getattr(sys,"frozen",False) or Path(sys.executable).resolve().parent != installed_dir.resolve():return
        def worker():
            try:
                release=check_for_update(APP_VERSION)
                if release is None:
                    self.after(0,lambda:self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Up to date"))
                    return
                tag=release.get("tag_name","new release")
                self.after(0,lambda:self.updater_status.configure(text=f"Downloading update {tag}…"))
                installer=download_update(release)
                self.after(0,lambda:self.launch_update(installer))
            except Exception:
                try:self.after(0,lambda:self.updater_status.configure(text=f"Video Compressor v{APP_VERSION} · Update check unavailable"))
                except Exception:pass
        threading.Thread(target=worker,daemon=True).start()
    def launch_update(self,installer):
        if self.is_compressing:
            self.pending_installer=installer
            self.updater_status.configure(text="Update ready · Will install after compression finishes")
            return
        try:
            flags=getattr(subprocess,"DETACHED_PROCESS",0x00000008)|getattr(subprocess,"CREATE_NO_WINDOW",0)
            subprocess.Popen([str(installer),"/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART",
                              "/DIR="+str(Path(sys.executable).resolve().parent)],
                             creationflags=flags,close_fds=True)
            self.after(250,self.destroy)
        except OSError:
            self.updater_status.configure(text="Update downloaded · Could not start the installer")
