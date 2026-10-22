import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import queue
import json
import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
import yt_dlp

# ==========================================
# 1. CORE ENGINE LOGIC
# ==========================================

CONFIG_FILE = "optifetch_config.json"
DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")

DEFAULT_CONFIG = {
    "save_path": DEFAULT_SAVE_PATH,
    "resolution": "best",
    "format": "mp4",
    "mp3_bitrate": "192"
}

def load_config():
    """Loads configuration from JSON file or returns defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(settings):
    """Saves configuration to JSON file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"⚠️ Failed to save config: {e}")

# --- Stream Redirector for GUI Console ---
class StdoutRedirector:
    def __init__(self, text_queue):
        self.text_queue = text_queue

    def write(self, string):
        if string:
            self.text_queue.put(string)

    def flush(self):
        pass

# --- Helper Functions ---

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def update_yt_dlp():
    print("\n🔄 Checking for yt-dlp executable updates...")
    local_exe = Path(sys.argv[0]).parent / "yt-dlp.exe" if hasattr(sys, '_MEIPASS') else None
    
    which_path = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if not which_path and not local_exe:
        print("⚠️ Error: 'yt-dlp' could not be found.")
        return

    yt_dlp_path = str(local_exe) if local_exe and local_exe.exists() else which_path
    
    try:
        result = subprocess.run(
            [yt_dlp_path, "-U"],
            capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print("✅ yt-dlp is already up to date.")
        else:
            print(f"⚠️ Update finished or returned code {result.returncode}.")
    except Exception as e:
        print(f"Could not update yt-dlp: {e}")

def find_ffmpeg():
    candidates = []
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        candidates.append(which_ff)

    if sys.platform.startswith("win"):
        candidates += [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        ]
    else:
        candidates += [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
        ]

    if hasattr(sys, "_MEIPASS"):
        bundle_dir = sys._MEIPASS
        candidates.append(os.path.join(bundle_dir, "ffmpeg"))
        candidates.append(os.path.join(bundle_dir, "ffmpeg.exe"))

    seen = set()
    final = []
    for c in candidates:
        if not c: continue
        c_norm = os.path.normpath(c)
        if c_norm not in seen:
            seen.add(c_norm)
            final.append(c_norm)

    for cand in final:
        try:
            proc = subprocess.run([cand, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
            if proc.returncode == 0:
                return cand
        except Exception:
            pass
            
    print("⚠️ ffmpeg not found. Install it or add to PATH.")
    return None

def build_common_ydl_opts(ffmpeg_path, out_template, is_audio=False, settings=None):
    opts = {
        "outtmpl": out_template,
        "ffmpeg_location": ffmpeg_path,
        "noplaylist": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "progress_hooks": [], 
        "quiet": False,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "source_address": "0.0.0.0",
        "user_agent": "Mozilla/5.0 (Linux; Android 10)",
    }

    if is_audio:
        bitrate = str(settings.get("mp3_bitrate", DEFAULT_CONFIG["mp3_bitrate"])) if settings else "192"
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate
        }]
    else:
        res = "best"
        if settings and "resolution" in settings:
            res_val = settings["resolution"]
            if res_val != "Best Quality":
                res = res_val.replace("p", "")
            
        if res == "best":
            opts["format"] = "bestvideo+bestaudio/best"
        else:
            opts["format"] = f"bestvideo[height<={res}]+bestaudio/best"
            
        opts["merge_output_format"] = settings.get("format", "mp4") if settings else "mp4"

    return opts

# ==========================================
# 2. GUI WRAPPER
# ==========================================

class OptiFetchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OptiFetch — Internet Video Downloader")
        # Use the function to safely load the bundled icon file
        try:
            icon_file = resource_path("Logo_V2.ico")
            root.iconbitmap(icon_file)
        except Exception as e:
            print(f"Icon failed to load: {e}")
        
        # Load saved configuration or fall back to defaults
        self.settings = load_config()
        
        # Thread-safe queues
        self.progress_queue = queue.Queue()
        self.console_queue = queue.Queue()

        # --- Layout Setup ---
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- Header ---
        header_label = ttk.Label(main_frame, text="WELCOME TO OPTIFETCH", font=("Arial", 22, "bold"))
        header_label.grid(row=0, column=0, pady=(0, 10))

        # --- Terms Frame with Hyperlink ---
        terms_frame = ttk.Frame(main_frame)
        terms_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(
            terms_frame, 
            text="By utilizing this tool you agree to the ",
            font=("Arial", 9),
            foreground="#555"
        ).pack(side=tk.LEFT)
        
        link_label = tk.Label(
            terms_frame, 
            text="Terms & Conditions",
            font=("Arial", 9, "underline"),
            foreground="#0066cc",
            cursor="hand2"
        )
        link_label.pack(side=tk.LEFT)
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/yosuf-e/OptiFetch/blob/main/README.md#%EF%B8%8F-terms-and-conditions"))
        
        ttk.Label(
            terms_frame, 
            text=" (Liability Falls on the user)",
            font=("Arial", 9),
            foreground="#555"
        ).pack(side=tk.LEFT)

        # --- Input Area ---
        url_frame = ttk.LabelFrame(main_frame, text="Input URL Link", padding="10")
        url_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(fill=tk.X, padx=5, pady=5)

        # --- Mode Selection (Video vs Audio) ---
        mode_frame = ttk.LabelFrame(main_frame, text="Mode", padding="10")
        mode_frame.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.mode_var = tk.StringVar(value="video")
        
        self.btn_video = ttk.Radiobutton(mode_frame, text="🎬 Video", variable=self.mode_var, value="video", command=self.toggle_mode)
        self.btn_video.pack(side=tk.LEFT, padx=5)
        
        self.btn_audio = ttk.Radiobutton(mode_frame, text="🎵 Audio (MP3)", variable=self.mode_var, value="audio", command=self.toggle_mode)
        self.btn_audio.pack(side=tk.LEFT, padx=5)

        # --- Dynamic Settings Container ---
        self.settings_container = ttk.Frame(main_frame)
        self.settings_container.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))

        # --- Save Path Choice Area ---
        path_frame = ttk.LabelFrame(main_frame, text="Download Directory", padding="10")
        path_frame.grid(row=5, column=0, pady=5, sticky=(tk.W, tk.E))
        path_frame.columnconfigure(0, weight=1)

        self.path_var = tk.StringVar(value=self.settings["save_path"])
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=48)
        self.path_entry.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.btn_browse = ttk.Button(path_frame, text="Browse...", command=self.browse_directory)
        self.btn_browse.grid(row=0, column=1, padx=5, pady=5)

        # --- Action Buttons ---
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        action_frame.grid(row=6, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.btn_update = ttk.Button(action_frame, text="Update (yt-dlp)", command=self.update_yt_dlp)
        self.btn_update.pack(side=tk.LEFT, padx=5)

        self.btn_reset = ttk.Button(action_frame, text="Reset Config", command=self.reset_config)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        self.btn_console = ttk.Button(action_frame, text="Show Console", command=self.toggle_console)
        self.btn_console.pack(side=tk.LEFT, padx=5)

        self.btn_download = ttk.Button(action_frame, text="Download ⬇️", command=self.start_download)
        self.btn_download.pack(side=tk.RIGHT, padx=5)

        # --- Status Bar & Progress ---
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=7, column=0, pady=(10, 5), sticky=(tk.W, tk.E))
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, expand=True, padx=5, pady=(0, 4))

        self.status_label = ttk.Label(status_frame, text="Status: Ready", foreground="#444")
        self.status_label.pack(anchor=tk.W, padx=5)

        # --- Collapsible Console Frame ---
        self.console_frame = ttk.LabelFrame(main_frame, text="Output Console Log", padding="5")
        self.console_text = scrolledtext.ScrolledText(self.console_frame, height=8, width=70, state='disabled', bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console_visible = False

        # --- Initialize UI Elements ---
        self._create_settings_widgets("video")
        
        # Redirect standard output to console queue
        sys.stdout = StdoutRedirector(self.console_queue)
        sys.stderr = StdoutRedirector(self.console_queue)

        # Start queue polling loop
        self.root.after(100, self.process_queues)

    def toggle_mode(self):
        mode = self.mode_var.get()
        self._create_settings_widgets(mode)

    def browse_directory(self):
        """Opens folder browser to choose download save path"""
        chosen_dir = filedialog.askdirectory(initialdir=self.path_var.get())
        if chosen_dir:
            self.path_var.set(chosen_dir)
            self.settings["save_path"] = chosen_dir
            save_config(self.settings)

    def toggle_console(self):
        """Shows or hides the bottom console text box"""
        if self.console_visible:
            self.console_frame.grid_remove()
            self.btn_console.config(text="Show Console")
            self.console_visible = False
        else:
            self.console_frame.grid(row=8, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.btn_console.config(text="Hide Console")
            self.console_visible = True

    def _create_settings_widgets(self, mode):
        """Helper to dynamically create setting widgets based on mode"""
        for widget in self.settings_container.winfo_children():
            widget.destroy()

        if mode == "video":
            v_frame = ttk.LabelFrame(self.settings_container, text="Video Settings", padding="5")
            v_frame.pack(fill=tk.X, expand=True)
            
            ttk.Label(v_frame, text="Resolution:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            self.res_var = tk.StringVar(value=self.settings["resolution"])
            self.combo_resolution = ttk.Combobox(v_frame, textvariable=self.res_var, state='readonly', width=22)
            self.combo_resolution['values'] = ["Best Quality", "1080p", "720p", "480p", "360p"]
            self.combo_resolution.grid(row=0, column=1, padx=5, pady=5)

            ttk.Label(v_frame, text="Format:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
            self.fmt_var = tk.StringVar(value=self.settings["format"])
            self.combo_format = ttk.Combobox(v_frame, textvariable=self.fmt_var, state='readonly', width=22)
            self.combo_format['values'] = ["mp4", "mkv", "webm"]
            self.combo_format.grid(row=1, column=1, padx=5, pady=5)

        elif mode == "audio":
            a_frame = ttk.LabelFrame(self.settings_container, text="Audio Settings", padding="5")
            a_frame.pack(fill=tk.X, expand=True)
            
            ttk.Label(a_frame, text="MP3 Bitrate (kbps):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
            self.br_var = tk.StringVar(value=self.settings.get("mp3_bitrate", "192"))
            self.entry_bitrate = ttk.Entry(a_frame, textvariable=self.br_var, width=25)
            self.entry_bitrate.grid(row=0, column=1, padx=5, pady=5)

    def update_yt_dlp(self):
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        try:
            update_yt_dlp()
            self.root.after(0, lambda: self.update_status("Update Complete", 100))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Update Failed: {e}", 0))

    def reset_config(self):
        if messagebox.askyesno("Reset Config", "Are you sure you want to reset all settings?"):
            self.settings = DEFAULT_CONFIG.copy()
            save_config(self.settings)
            self.path_var.set(self.settings["save_path"])
            self.mode_var.set("video")
            self._create_settings_widgets("video")
            self.update_status("Settings Reset", 0)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Error", "Please enter a valid URL.")
            return

        mode = self.mode_var.get()
        try:
            self.settings["save_path"] = self.path_var.get().strip()
            if mode == "video":
                self.settings["resolution"] = self.combo_resolution.get()
                self.settings["format"] = self.combo_format.get()
            else:
                self.settings["mp3_bitrate"] = self.entry_bitrate.get()
            
            # Save configuration choices
            save_config(self.settings)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read settings: {e}")
            return

        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            messagebox.showwarning("Missing Dependency", "ffmpeg is required. Please install it or put it in path.")
            return

        self.update_status(f"Downloading... ({url[:25]}...)", 0)
        
        worker = DownloadWorker(self, ffmpeg_path, self.settings, mode == "audio", url)
        worker.start()

    def update_status(self, message, progress):
        """Thread-safe UI status update helper"""
        self.status_label.config(text=f"Status: {message}")
        if progress is not None:
            self.progress_bar.configure(value=progress)

    def process_queues(self):
        """Polls queues from background threads to safely update GUI elements & console"""
        try:
            while True:
                data = self.progress_queue.get_nowait()
                if isinstance(data, tuple):
                    msg, val = data
                    self.update_status(msg, val)
                elif isinstance(data, (int, float)):
                    self.progress_bar.configure(value=data)
                self.progress_queue.task_done()
        except queue.Empty:
            pass

        try:
            while True:
                msg = self.console_queue.get_nowait()
                self.console_text.config(state='normal')
                self.console_text.insert(tk.END, msg)
                self.console_text.see(tk.END)
                self.console_text.config(state='disabled')
                self.console_queue.task_done()
        except queue.Empty:
            pass

        self.root.after(100, self.process_queues)


# ==========================================
# 3. WORKER THREAD CLASS
# ==========================================

class DownloadWorker(threading.Thread):
    def __init__(self, app, ffmpeg_path, settings, is_audio, url):
        super().__init__()
        self.app = app
        self.ffmpeg_path = ffmpeg_path
        self.settings = settings
        self.is_audio = is_audio
        self.url = url
        self.is_cancelled = False
        
    def _on_progress(self, data):
        if data['status'] == 'downloading':
            try:
                total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
                downloaded = data.get("downloaded_bytes", 0)
                if total > 0:
                    pct = (downloaded / total) * 100
                    self.app.progress_queue.put(pct)
            except Exception:
                pass
        elif data['status'] == 'finished':
            self.app.progress_queue.put(("Processing / Converting...", 100))

    def run(self):
        try:
            out_template = os.path.join(self.settings["save_path"], "%(title)s.%(ext)s")
            ydl_opts = build_common_ydl_opts(
                ffmpeg_path=self.ffmpeg_path, 
                out_template=out_template, 
                is_audio=self.is_audio, 
                settings=self.settings
            )
            ydl_opts["progress_hooks"] = [self._on_progress]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
                
            self.app.progress_queue.put(("Download Complete! 🎉", 100))
        except Exception as e:
            self.app.progress_queue.put((f"Error: {e}", 0))

# ==========================================
# 4. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = OptiFetchGUI(root)
    root.mainloop()
