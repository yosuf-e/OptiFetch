# Hey there! Thank you for choosing OptiFetch. 🙏🏻


## Key Capabilities ✨✨:

- **Destination Control**: Seamlessly direct your media to any local or network directory of your choice. (This could be both permanent and temporary)

- **Multi-Format Versatility**: Export in multiple video formats, including MP4 and MKV.

- **Cinematic Resolution Scaling**: Complete control over visual fidelity, from data-saving 480p to the best/highest resolution available.

There are 2 ways to run the program: the easy way (through the exe file; or the hard way through the python script).

#### METHOD #1 OF INSTALLATION (EASY): Use the EXE. File

- After unzipping the zip file, you will find an exe. file named "OptiFetch_2026.exe", you can just run the code from there and even move it to your desktop. However, if the app's logo becomes corrupted, you can try either restarting your PC/Laptop, or creating a shortcut for the app and then changing its logo in the properties menu (by selecting the "App_Logo.ico" file.) **Moreover, if you experince any errors in the code, you will be promted to download "ffmpeg" via winget on you Windows PC.**


#### METHOD #2 OF INSTALLATION (HARD): Use the Py. File

1. Install Python
This script primarily runs on Python; thus, you will need it for both running it and making it workable. You can install it from: 
https://www.python.org/downloads/

2. Install yt-dlp
This script requires the yt-dlp library. Install it via your Python directory by running:
pip install yt-dlp

3. Install FFmpeg
FFmpeg is required for processing high-quality video and audio. Install it via Windows PowerShell using:
winget install ffmpeg



## Troubleshooting ⚙️⚙️

- **If Windows-Defender blocks the app**, you can resolve the issue with the following steps:

1. **Add an exclusion**: You can add the specific file or, more conveniently, the entire folder containing the executable, to the Windows Defender exclusion list.
2. Open Windows Security from the taskbar or Start menu.
3. Go to Virus & threat protection.
4. Under "Virus & threat protection settings," click Manage settings.
5. Scroll down to Exclusions and click Add or remove exclusions.
6. Click + Add an exclusion, then select File or Folder and browse to your application's location.


- Make sure that Python is properly installed and that you have created a PATH environment.

- FFmpeg Not Found: If the application reports that FFmpeg does not exist, verify the installation by typing-- ffmpeg -version or winget list -- in your terminal. If it is not listed, please repeat the installation step above.

- Module Errors: If you encounter a ModuleNotFoundError regarding yt-dlp, verify that it is installed in your active Python environment by typing 
pip show yt-dlp

- After installing FFmpeg, you may need to restart your terminal or computer for the changes to take effect.

- Update Command: In 2026, APIs change frequently; thus, if downloads fail, try updating your library with: 
pip install -U yt-dlp

- Check Python Version: Ensure you are on a modern version (Python 3.10 or higher for compatibility)

- Admin Rights: If winget fails run PowerShell as Administrator to install system-level dependencies.

# ⭕⚠️ Terms and Conditions ⭕⚠️:

### By utilizing this software, you agree to the following legally binding terms:

- **LIMITATION OF LIABILITY**: TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, OptiFetch SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM (A) YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE SERVICES; (B) ANY CONDUCT OR CONTENT OF ANY THIRD PARTY; OR (C) ANY LEGAL CONSEQUENCES ARISING FROM YOUR ACTIONS WHILE USING THE SERVICE.

- Assumption of Risk: Your **use of OptiFetch is at your sole risk**. The service is provided on an "AS IS" and "AS AVAILABLE" basis. OptiFetch expressly disclaims all warranties of any kind. You agree that any legal or negative consequences resulting from your use of the service are your sole responsibility, and you waive any right to bring a claim against OptiFetch  for such outcomes.

- Permitted Use: This tool is provided for **PERSONAL USE ONLY**. You agree NOT to use this software for any illicit activities, including the unauthorized distribution or PIRACY of copyrighted material.

- Distribution Prohibitions: You shall not sell, lease, or sublicense this product.

- Intellectual Property: **MODIFICATION OF AUTHORSHIP** or removal of original metadata from this program bundle is **strictly PROHIBITED**.

### The App's UI:

<img width="643" height="412" alt="image" src="https://github.com/user-attachments/assets/604ba367-24d9-47f0-bb0c-dd0cdff78f1e" />

