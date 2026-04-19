#!/usr/bin/env python3
"""
OptiFetch 2026 - Updated: separate audio and video download flows.
Drop-in replacement for your script. Keeps settings persistence and adds
distinct "Download Video" and "Download Audio" actions.
"""
import yt_dlp
import os
import json
import shutil
import sys

CONFIG_FILE = "youtube_downloader_config.json"
DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")

DEFAULT_CONFIG = {
    "save_path": DEFAULT_SAVE_PATH,
    "resolution": "best",
    "format": "mp4",     # used for video downloads: mp4, mkv, webm
    "mp3_bitrate": "192" # used for audio downloads
}

current_settings = {}

# -------------------- Utilities --------------------
def find_ffmpeg():
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✓ ffmpeg found at: {ffmpeg_path}")
    else:
        print("⚠️  WARNING: ffmpeg not found in PATH!")
        print("   Please install ffmpeg or add it to your system PATH")
    return ffmpeg_path

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print("✓ Configuration saved permanently!")
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
    print("\n" + "="*50)
    print("      OptiFetch 2026 - YouTube Downloader")
    print("="*50)
    print("1. Download Video")
    print("2. Download Audio (MP3)")
    print("3. View Current Settings")
    print("4. Change Settings (Temporary)")
    print("5. Change Settings (Permanent)")
    print("6. Reset to Default Settings")
    print("7. Exit")
    print("="*50)

def display_settings(settings):
    print("\n" + "-"*50)
    print("      CURRENT SETTINGS")
    print("-"*50)
    print(f"Save Path:    {settings['save_path']}")
    print(f"Resolution:   {settings['resolution']}")
    print(f"Video Format: {settings['format']}")
    print(f"MP3 Bitrate:  {settings.get('mp3_bitrate')}")
    print("-"*50)

def change_resolution():
    print("\nResolution Options:")
    resolutions = {
        '1': ('best', 'Best Quality (auto-select)'),
        '2': ('1080', '1080p (Full HD)'),
        '3': ('720', '720p (HD)'),
        '4': ('480', '480p (SD)'),
        '5': ('360', '360p (Low)'),
    }
    for key, (_, name) in resolutions.items():
        print(f"  {key}. {name}")
    choice = input("Select resolution (1-5): ").strip()
    return resolutions.get(choice, ('best',))[0]

def change_video_format():
    print("\nVideo Format Options:")
    formats = {
        '1': ('mp4', 'MP4 (Most Compatible)'),
        '2': ('mkv', 'MKV (Higher Quality)'),
        '3': ('webm', 'WEBM (Web Format)'),
    }
    for key, (_, name) in formats.items():
        print(f"  {key}. {name}")
    choice = input("Select format (1-3): ").strip()
    return formats.get(choice, ('mp4',))[0]

def change_save_path():
    print("\nCurrent save path:", DEFAULT_SAVE_PATH)
    path = input("Enter new save path (or press Enter to keep current): ").strip()
    if not path:
        return None
    if not os.path.exists(path):
        create = input(f"Path doesn't exist. Create it? (y/n): ").strip().lower()
        if create == 'y':
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
    print("\n" + "="*50)
    print("       TEMPORARY SETTINGS (This Session Only)")
    print("="*50)
    while True:
        settings = get_current_settings()
        print(f"\n1. Resolution: {settings['resolution']}")
        print(f"2. Video Format: {settings['format']}")
        print(f"3. Save Path: {settings['save_path']}")
        print(f"4. MP3 Bitrate: {settings.get('mp3_bitrate')}")
        print("5. Back to Main Menu")
        choice = input("\nSelect option to change (1-5): ").strip()
        if choice == '1':
            current_settings['resolution'] = change_resolution()
        elif choice == '2':
            current_settings['format'] = change_video_format()
        elif choice == '3':
            path = change_save_path()
            if path:
                current_settings['save_path'] = path
        elif choice == '4':
            br = input("Enter MP3 bitrate (e.g., 128, 192, 320) [192]: ").strip() or "192"
            current_settings['mp3_bitrate'] = br
        elif choice == '5':
            break
        else:
            print("Invalid choice!")

def permanent_settings_menu():
    cfg = load_config()
    print("\n" + "="*50)
    print("       PERMANENT SETTINGS (Saved for Future Use)")
    print("="*50)
    while True:
        print(f"\n1. Resolution: {cfg['resolution']}")
        print(f"2. Video Format: {cfg['format']}")
        print(f"3. Save Path: {cfg['save_path']}")
        print(f"4. MP3 Bitrate: {cfg.get('mp3_bitrate')}")
        print("5. Back to Main Menu")
        choice = input("\nSelect option to change (1-5): ").strip()
        if choice == '1':
            cfg['resolution'] = change_resolution()
            save_config(cfg)
        elif choice == '2':
            cfg['format'] = change_video_format()
            save_config(cfg)
        elif choice == '3':
            path = change_save_path()
            if path:
                cfg['save_path'] = path
                save_config(cfg)
        elif choice == '4':
            br = input("Enter MP3 bitrate (e.g., 128, 192, 320) [192]: ").strip() or "192"
            cfg['mp3_bitrate'] = br
            save_config(cfg)
        elif choice == '5':
            break
        else:
            print("Invalid choice!")

# -------------------- Download helpers --------------------
def build_video_format_option(resolution, format_type):
    if resolution == 'best':
        return f'bestvideo[ext={format_type}]+bestaudio[ext=m4a]/best[ext={format_type}]/best'
    else:
        return f'bestvideo[height<={resolution}][ext={format_type}]+bestaudio/best[height<={resolution}]/best'

def progress_hook(d):
    if d.get('status') == 'finished':
        print('\n✓ Finished downloading, post-processing...')

# -------------------- Separate download flows --------------------
def download_video(url):
    settings = get_current_settings()
    if not url:
        print("Invalid URL.")
        return

    if not ensure_save_path(settings['save_path']):
        return

# Check ffmpeg presence when needed (merging or audio extraction)
    ffmpeg_needed = True  # yt-dlp uses ffmpeg for merging and audio extraction
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_needed and not ffmpeg_path:
        print("\n❌ Error: ffmpeg is required for merging/conversion.")
        print("   Please install ffmpeg or add it to your PATH.")
        print("   - winget install ffmpeg")
        print("   - or download from: https://ffmpeg.org/download.html")
        return

    out_template = os.path.join(settings['save_path'], '%(title)s.%(ext)s')
    ydl_opts = {
        'format': build_video_format_option(settings['resolution'], settings['format']),
        'outtmpl': out_template,
        'merge_output_format': settings['format'],
        'ffmpeg_location': ffmpeg_path,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': True,
    }

    print(f"\n📥 Downloading VIDEO:")
    print(f"   Resolution: {settings['resolution']}")
    print(f"   Container:  {settings['format']}")
    print(f"   Save Path:  {settings['save_path']}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✓ Video download complete.")
    except Exception as e:
        print(f"Error downloading video: {e}")

def download_audio_mp3(url):
    settings = get_current_settings()
    if not url:
        print("Invalid URL.")
        return

    if not ensure_save_path(settings['save_path']):
        return

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("\n❌ Error: ffmpeg is required to extract/convert audio.")
        print("   Please install ffmpeg or add it to your PATH.")
        return

    out_template = os.path.join(settings['save_path'], '%(title)s.%(ext)s')
    bitrate = str(settings.get('mp3_bitrate', DEFAULT_CONFIG['mp3_bitrate']))

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_template,
        'ffmpeg_location': ffmpeg_path,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate
        }],
    }

    print(f"\n📥 Downloading AUDIO (MP3):")
    print(f"   Bitrate:   {bitrate} kbps")
    print(f"   Save Path: {settings['save_path']}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✓ Audio download complete.")
    except Exception as e:
        print(f"Error downloading audio: {e}")

# -------------------- Main --------------------
def main():
    print(" (By Utilizing This Software, You Agree To The Terms And Conditions. \n https://github.com/yosuf-e/OptiFetch/blob/main/README.md)")
    print("\n🎥 Welcome to OptiFetch!")

    while True:
        display_main_menu()
        choice = input("Select option (1-7): ").strip()
        if choice == '1':
            url = input("\nEnter video URL: ").strip()
            download_video(url)
        elif choice == '2':
            url = input("\nEnter video/audio URL (will produce MP3): ").strip()
            download_audio_mp3(url)
        elif choice == '3':
            display_settings(get_current_settings())
        elif choice == '4':
            temporary_settings_menu()
        elif choice == '5':
            permanent_settings_menu()
        elif choice == '6':
            confirm = input("\nReset to default settings? (y/n): ").strip().lower()
            if confirm == 'y':
                save_config(DEFAULT_CONFIG.copy())
                current_settings.clear()
                print("✓ Reset to defaults!")
        elif choice == '7':
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)