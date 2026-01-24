import yt_dlp
import os
import json
import shutil

# Configuration file for storing permanent settings
CONFIG_FILE = "youtube_downloader_config.json"
DEFAULT_SAVE_PATH = os.path.expanduser("~/Downloads")

# Find ffmpeg path
def find_ffmpeg():
    """Find ffmpeg executable in system PATH"""
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✓ ffmpeg found at: {ffmpeg_path}")
    else:
        print("⚠️  WARNING: ffmpeg not found in PATH!")
        print("   Please install ffmpeg or add it to your system PATH")
    return ffmpeg_path

# Default configuration
DEFAULT_CONFIG = {
    "save_path": DEFAULT_SAVE_PATH,
    "resolution": "best",
    "format": "mp4"
}

# Current session settings (can be overridden temporarily)
current_settings = {}

# ==================== Configuration Management ====================
def load_config():
    """Load permanent configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save permanent configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print("✓ Configuration saved permanently!")

def get_current_settings():
    """Get current settings (temporary overrides permanent)"""
    config = load_config()
    # Merge permanent config with temporary session overrides
    config.update(current_settings)
    return config

# ==================== User Interface ====================
def display_main_menu():
    """Display main menu options"""
    print(" (By Utilizing This Software, You Agree To The Terms And Conditions Mentiond in The File.)")
    print("\n" + "="*60)
    print("          OptiFetch 2026 - YouTube Downloader")
    print("="*60)
    print("1. Download Video")
    print("2. View Current Settings")
    print("3. Change Settings (Temporary)")
    print("4. Change Settings (Permanent)")
    print("5. Reset to Default Settings")
    print("6. Exit")
    print("Side Note: The default save path is C:\\Users\\<Username>\\Downloads".)
    print("="*60)

def display_settings(settings):
    """Display current settings"""
    print("\n" + "-"*60)
    print("       CURRENT SETTINGS")
    print("-"*60)
    print(f"Save Path:    {settings['save_path']}")
    print(f"Resolution:   {settings['resolution']}")
    print(f"Format:       {settings['format']}")
    print("-"*60)

def change_resolution():
    """Allow user to select resolution"""
    print("\nResolution Options:")
    resolutions = {
        '1': ('best', 'Best Quality (auto-select)'),
        '2': ('1080', '1080p (Full HD)'),
        '3': ('720', '720p (HD)'),
        '4': ('480', '480p (SD)'),
        '5': ('360', '360p (Low)'),
    }
    
    for key, (res_code, res_name) in resolutions.items():
        print(f"  {key}. {res_name}")
    
    choice = input("Select resolution (1-5): ").strip()
    if choice in resolutions:
        return resolutions[choice][0]
    else:
        print("Invalid choice. Using 'best' quality.")
        return 'best'

def change_format():
    """Allow user to select output format"""
    print("\nFormat Options:")
    formats = {
        '1': ('mp4', 'MP4 (Most Compatible)'),
        '2': ('mkv', 'MKV (Higher Quality)'),
        '3': ('webm', 'WEBM (Web Format)'),
    }
    
    for key, (fmt, fmt_name) in formats.items():
        print(f"  {key}. {fmt_name}")
    
    choice = input("Select format (1-3): ").strip()
    if choice in formats:
        return formats[choice][0]
    else:
        print("Invalid choice. Using 'mp4'.")
        return 'mp4'

def change_save_path():
    """Allow user to specify save path"""
    print("\nCurrent save path:", DEFAULT_SAVE_PATH)
    path = input("Enter new save path (or press Enter to keep current): ").strip()
    
    if not path:
        return None
    
    if not os.path.exists(path):
        create = input(f"Path doesn't exist. Create it? (y/n): ").strip().lower()
        if create == 'y':
            try:
                os.makedirs(path)
                return path
            except Exception as e:
                print(f"Error creating path: {e}")
                return None
        else:
            return None
    return path

def temporary_settings_menu():
    """Menu for temporary (session-only) settings changes"""
    global current_settings
    
    print("\n" + "="*50)
    print("       TEMPORARY SETTINGS (This Session Only)")
    print("="*50)
    
    while True:
        settings = get_current_settings()
        print(f"\n1. Resolution: {settings['resolution']}")
        print(f"2. Format: {settings['format']}")
        print(f"3. Save Path: {settings['save_path']}")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect option to change (1-4): ").strip()
        
        if choice == '1':
            current_settings['resolution'] = change_resolution()
        elif choice == '2':
            current_settings['format'] = change_format()
        elif choice == '3':
            path = change_save_path()
            if path:
                current_settings['save_path'] = path
        elif choice == '4':
            break
        else:
            print("Invalid choice!")

def permanent_settings_menu():
    """Menu for permanent settings changes"""
    config = load_config()
    
    print("\n" + "="*50)
    print("       PERMANENT SETTINGS (Saved for Future Use)")
    print("="*50)
    
    while True:
        print(f"\n1. Resolution: {config['resolution']}")
        print(f"2. Format: {config['format']}")
        print(f"3. Save Path: {config['save_path']}")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect option to change (1-4): ").strip()
        
        if choice == '1':
            config['resolution'] = change_resolution()
            save_config(config)
        elif choice == '2':
            config['format'] = change_format()
            save_config(config)
        elif choice == '3':
            path = change_save_path()
            if path:
                config['save_path'] = path
                save_config(config)
        elif choice == '4':
            break
        else:
            print("Invalid choice!")

# ==================== Download Functions ====================
def build_format_option(resolution, format_type):
    """Build yt-dlp format string based on resolution and format"""
    if resolution == 'best':
        return f'bestvideo[ext={format_type}]+bestaudio[ext=m4a]/best[ext={format_type}]/best'
    else:
        return f'bestvideo[height<={resolution}][ext={format_type}]+bestaudio/best[height<={resolution}]/best'

def my_hook(d):
    """Progress hook function"""
    if d['status'] == 'finished':
        print('\n✓ Done downloading!')

def download_video(url):
    """Download video with current settings"""
    settings = get_current_settings()
    
    # Check for ffmpeg
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("\n❌ Error: ffmpeg is required to merge video and audio.")
        print("   Please install ffmpeg:")
        print("   - winget install ffmpeg")
        print("   - or download from: https://ffmpeg.org/download.html")
        return
    
    # Ensure save path exists
    if not os.path.exists(settings['save_path']):
        os.makedirs(settings['save_path'])
    
    output_template = os.path.join(settings['save_path'], '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': build_format_option(settings['resolution'], settings['format']),
        'outtmpl': output_template,
        'merge_output_format': settings['format'],
        'ffmpeg_location': ffmpeg_path,
        'noplaylist': True,
        'progress_hooks': [my_hook],
    }
    
    print(f"\n📥 Downloading with settings:")
    print(f"   Resolution: {settings['resolution']}")
    print(f"   Format: {settings['format']}")
    print(f"   Save Path: {settings['save_path']}\n")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error downloading: {e}")

# ==================== Main Program ====================
def main():
    """Main program loop"""
    print("\n🎥 Welcome to YouTube Downloader!")
    
    while True:
        display_main_menu()
        choice = input("Select option (1-6): ").strip()
        
        if choice == '1':
            url = input("\nEnter YouTube URL: ").strip()
            if url:
                download_video(url)
            else:
                print("Invalid URL!")
        
        elif choice == '2':
            settings = get_current_settings()
            display_settings(settings)
        
        elif choice == '3':
            temporary_settings_menu()
        
        elif choice == '4':
            permanent_settings_menu()
        
        elif choice == '5':
            confirm = input("\nReset to default settings? (y/n): ").strip().lower()
            if confirm == 'y':
                save_config(DEFAULT_CONFIG.copy())
                current_settings.clear()
                print("✓ Reset to defaults!")
        
        elif choice == '6':
            print("\nGoodbye! 👋")
            break
        
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":

    main()

