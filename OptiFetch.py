import yt_dlp
import os
import json
import shutil
import sys
import subprocess
from pathlib import Path

CONFIG_FILE = "optifetch_config.json"
DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")

DEFAULT_CONFIG = {
    "save_path": DEFAULT_SAVE_PATH,
    "resolution": "best",
    "format": "mp4",
    "mp3_bitrate": "192"
}

current_settings = {}

# -------------------- Auto-update yt-dlp --------------------
def update_yt_dlp():
    print("\n🔄 Checking for yt-dlp executable updates...")
    
    # 1. Try to find 'yt-dlp.exe' in the script's directory first, then in the system PATH
    local_exe = Path(sys.argv[0]).parent / "yt-dlp.exe"
    if local_exe.exists():
        yt_dlp_path = str(local_exe)
    else:
        yt_dlp_path = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    
    # 2. If not found at all, warn the user and exit the function
    if not yt_dlp_path:
        print("⚠️ Error: 'yt-dlp.exe' could not be found in the script directory or system PATH.\n")
        return

    # 3. Run the standalone update command
    try:
        print(f"📦 Found executable at: {yt_dlp_path}")
        result = subprocess.run(
            [yt_dlp_path, "-U"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # 4. Parse the output for robust feedback
        if result.returncode == 0:
            if "latest version" in result.stdout.lower() or "up to date" in result.stdout.lower():
                print("✅ yt-dlp is already up to date.\n")
            else:
                print("✨ yt-dlp updated successfully!\n")
        else:
            print(f"⚠️ Update failed with exit code {result.returncode}.\nDetails: {result.stderr.strip()}\n")
            
    except Exception as e:
        print(f"⚠️ Could not update yt-dlp: {e}\n")

# -------------------- ffmpeg detection --------------------
def _is_executable(path):
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)

def _verify_ffmpeg(path):
    try:
        proc = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        return proc.returncode == 0
    except Exception:
        return False

def find_ffmpeg():
    candidates = []

    # PATH
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        candidates.append(which_ff)

    # Common locations
    if sys.platform.startswith("win"):
        candidates += [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]
    else:
        candidates += [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
        ]

    # PyInstaller bundle
    if hasattr(sys, "_MEIPASS"):
        bundle_dir = sys._MEIPASS
        candidates.append(os.path.join(bundle_dir, "ffmpeg"))
        candidates.append(os.path.join(bundle_dir, "ffmpeg.exe"))

    # Deduplicate
    seen = set()
    final = []
    for c in candidates:
        if not c:
            continue
        c_norm = os.path.normpath(c)
        if c_norm not in seen:
            seen.add(c_norm)
            final.append(c_norm)

    for cand in final:
        if _is_executable(cand) and _verify_ffmpeg(cand):
            print(f"✓ ffmpeg found at: {cand}")
            return cand

    print("⚠️ ffmpeg not found. Install it or add to PATH.")
    return None

# -------------------- Config --------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print("✓ Configuration saved!")
    except Exception as e:
        print(f"Error saving config: {e}")

def get_current_settings():
    cfg = load_config()
    cfg.update(current_settings)
    return cfg

def ensure_save_path(path):
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating save path '{path}': {e}")
        return False

# -------------------- UI --------------------
def display_main_menu():
    print("\n" + "=" * 50)
    print("      OptiFetch - Video Downloader")
    print("=" * 50)
    print("1. Download Video")
    print("2. Download Audio (MP3)")
    print("3. View Current Settings")
    print("4. Change Settings (Temporary)")
    print("5. Change Settings (Permanent)")
    print("6. Reset to Default Settings")
    print("7. Update yt-dlp")
    print("8. Exit")
    print("=" * 50)

def display_settings(settings):
    print("\n" + "-" * 50)
    print("      CURRENT SETTINGS")
    print("-" * 50)
    print(f"Save Path:    {settings['save_path']}")
    print(f"Resolution:   {settings['resolution']}")
    print(f"Video Format: {settings['format']}")
    print(f"MP3 Bitrate:  {settings.get('mp3_bitrate')}")
    print("-" * 50)

# -------------------- Settings menus --------------------
def change_resolution():
    print("\nResolution Options:")
    resolutions = {
        "1": ("best", "Best Quality"),
        "2": ("1080", "1080p"),
        "3": ("720", "720p"),
        "4": ("480", "480p"),
        "5": ("360", "360p"),
    }
    for key, (_, name) in resolutions.items():
        print(f"  {key}. {name}")
    choice = input("Select resolution (1-5): ").strip()
    return resolutions.get(choice, ("best",))[0]

def change_video_format():
    print("\nVideo Format Options:")
    formats = {
        "1": ("mp4", "MP4"),
        "2": ("mkv", "MKV"),
        "3": ("webm", "WEBM"),
    }
    for key, (_, name) in formats.items():
        print(f"  {key}. {name}")
    choice = input("Select format (1-3): ").strip()
    return formats.get(choice, ("mp4",))[0]

def change_save_path():
    settings = get_current_settings()
    print("\nCurrent save path:", settings["save_path"])
    path = input("Enter new save path (or press Enter to keep current): ").strip()
    if not path:
        return None
    if not os.path.exists(path):
        create = input(f"Path doesn't exist. Create it? (y/n): ").strip().lower()
        if create == "y":
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except Exception as e:
                print(f"Error creating path: {e}")
                return None
        else:
            return None
    return path

def temporary_settings_menu():
    global current_settings
    print("\n" + "=" * 50)
    print("       TEMPORARY SETTINGS")
    print("=" * 50)
    while True:
        settings = get_current_settings()
        print(f"\n1. Resolution: {settings['resolution']}")
        print(f"2. Video Format: {settings['format']}")
        print(f"3. Save Path: {settings['save_path']}")
        print(f"4. MP3 Bitrate: {settings.get('mp3_bitrate')}")
        print("5. Back")
        choice = input("\nSelect option (1-5): ").strip()
        if choice == "1":
            current_settings["resolution"] = change_resolution()
        elif choice == "2":
            current_settings["format"] = change_video_format()
        elif choice == "3":
            path = change_save_path()
            if path:
                current_settings["save_path"] = path
        elif choice == "4":
            br = input("Enter MP3 bitrate [192]: ").strip() or "192"
            current_settings["mp3_bitrate"] = br
        elif choice == "5":
            break
        else:
            print("Invalid choice!")

def permanent_settings_menu():
    cfg = load_config()
    print("\n" + "=" * 50)
    print("       PERMANENT SETTINGS")
    print("=" * 50)
    while True:
        print(f"\n1. Resolution: {cfg['resolution']}")
        print(f"2. Video Format: {cfg['format']}")
        print(f"3. Save Path: {cfg['save_path']}")
        print(f"4. MP3 Bitrate: {cfg.get('mp3_bitrate')}")
        print("5. Back")
        choice = input("\nSelect option (1-5): ").strip()
        if choice == "1":
            cfg["resolution"] = change_resolution()
            save_config(cfg)
        elif choice == "2":
            cfg["format"] = change_video_format()
            save_config(cfg)
        elif choice == "3":
            path = change_save_path()
            if path:
                cfg["save_path"] = path
                save_config(cfg)
        elif choice == "4":
            br = input("Enter MP3 bitrate [192]: ").strip() or "192"
            cfg["mp3_bitrate"] = br
            save_config(cfg)
        elif choice == "5":
            break
        else:
            print("Invalid choice!")

# -------------------- Download helpers --------------------
def build_video_format_option(resolution, format_type):
    if resolution == "best":
        return f"bestvideo+bestaudio/best"
    else:
        return f"bestvideo[height<={resolution}]+bestaudio/best"

def progress_hook(d):
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        if total:
            pct = downloaded / total * 100
            sys.stdout.write(f"\rProgress: {pct:5.1f}%")
            sys.stdout.flush()
    elif d.get("status") == "finished":
        print("\n✓ Finished downloading, post-processing...")

def build_common_ydl_opts(ffmpeg_path, out_template, is_audio=False, settings=None):
    """
    403-proof yt-dlp options (Android client)
    """
    opts = {
        "outtmpl": out_template,
        "ffmpeg_location": ffmpeg_path,
        "noplaylist": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "progress_hooks": [progress_hook],
        "quiet": False,
        "no_warnings": True,

        # 403 bypass
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },

        # Force IPv4
        "source_address": "0.0.0.0",

        # Safe user-agent
        "user_agent": "Mozilla/5.0 (Linux; Android 10)",

        # Throttling mitigation
        "ratelimit": 5_000_000,
    }

    if is_audio:
        bitrate = str(settings.get("mp3_bitrate", DEFAULT_CONFIG["mp3_bitrate"]))
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate
        }]
    else:
        opts["format"] = build_video_format_option(settings["resolution"], settings["format"])
        opts["merge_output_format"] = settings["format"]

    return opts

# -------------------- Download flows --------------------
def download_video(url):
    settings = get_current_settings()
    if not url:
        print("Invalid URL.")
        return

    if not ensure_save_path(settings["save_path"]):
        return

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("\n❌ ffmpeg is required.")
        return

    out_template = os.path.join(settings["save_path"], "%(title)s.%(ext)s")
    ydl_opts = build_common_ydl_opts(ffmpeg_path, out_template, is_audio=False, settings=settings)

    print(f"\n📥 Downloading VIDEO:")
    print(f"   Resolution: {settings['resolution']}")
    print(f"   Format:     {settings['format']}")
    print(f"   Save Path:  {settings['save_path']}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✓ Video download complete.")
    except Exception as e:
        print(f"\n❌ Error downloading video: {e}")

def download_audio_mp3(url):
    settings = get_current_settings()
    if not url:
        print("Invalid URL.")
        return

    if not ensure_save_path(settings["save_path"]):
        return

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("\n❌ ffmpeg is required.")
        return

    out_template = os.path.join(settings["save_path"], "%(title)s.%(ext)s")
    ydl_opts = build_common_ydl_opts(ffmpeg_path, out_template, is_audio=True, settings=settings)

    print(f"\n📥 Downloading AUDIO (MP3):")
    print(f"   Bitrate:   {settings.get('mp3_bitrate', DEFAULT_CONFIG['mp3_bitrate'])} kbps")
    print(f"   Save Path: {settings['save_path']}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✓ Audio download complete.")
    except Exception as e:
        print(f"\n❌ Error downloading audio: {e}")

# -------------------- Main --------------------
def main():
    print(" (By Using This Software, You Agree To The Terms And Conditions.)")
    print("   https://github.com/yosuf-e/OptiFetch")
    print("\n🎥 Welcome to OptiFetch!")

    while True:
        display_main_menu()
        choice = input("Select option (1-8): ").strip()
        if choice == "1":
            url = input("\nEnter video URL: ").strip()
            download_video(url)
        elif choice == "2":
            url = input("\nEnter video/audio URL: ").strip()
            download_audio_mp3(url)
        elif choice == "3":
            display_settings(get_current_settings())
        elif choice == "4":
            temporary_settings_menu()
        elif choice == "5":
            permanent_settings_menu()
        elif choice == "6":
            confirm = input("\nReset to default settings? (y/n): ").strip().lower()
            if confirm == "y":
                save_config(DEFAULT_CONFIG.copy())
                current_settings.clear()
                print("✓ Reset to defaults!")
        elif choice == "7":
            update_yt_dlp()
        elif choice == "8":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
