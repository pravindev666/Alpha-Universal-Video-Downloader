import os
import requests
import zipfile
import io
import shutil
from pathlib import Path

def install_ffmpeg():
    print("Downloading FFmpeg (trying GitHub mirror)...")
    # Backup URL from BtbN (more reliable than gyan.dev sometimes)
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        print("Extracting...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Find the bin folder in the zip
            for file in z.namelist():
                if file.endswith("ffmpeg.exe") or file.endswith("ffprobe.exe"):
                    # Extract to current directory
                    filename = os.path.basename(file)
                    with z.open(file) as source, open(filename, "wb") as target:
                        shutil.copyfileobj(source, target)
                    print(f"Extracted: {filename}")
        
        print("\n✅ FFmpeg installed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error installing FFmpeg: {e}")
        # Try one more source if that fails
        try:
             print("Trying fallback source...")
             url2 = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
             r2 = requests.get(url2, stream=True)
             r2.raise_for_status()
             with zipfile.ZipFile(io.BytesIO(r2.content)) as z:
                for file in z.namelist():
                    if file.endswith("ffmpeg.exe") or file.endswith("ffprobe.exe"):
                        filename = os.path.basename(file)
                        with z.open(file) as source, open(filename, "wb") as target:
                            shutil.copyfileobj(source, target)
             print("\n✅ FFmpeg installed successfully from fallback!")
        except Exception as e2:
             print(f"Fallback failed too: {e2}")

if __name__ == "__main__":
    install_ffmpeg()
