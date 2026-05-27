# install_organizer.py - UNIVERSAL INSTALLER
# Run once in Pydroid. It will do everything automatically.

import requests
import os
import zipfile
import shutil
import sys
import subprocess

print("=" * 60)
print("  ORGANIZER INSTALLER v1.0")
print("=" * 60)

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

# STEP 1: Check libraries
print("\n[1/6] Checking libraries...")
try:
    import requests
    print("  OK requests ready")
except ImportError:
    print("  Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    print("  OK requests installed")

# STEP 2: Internet
print("\n[2/6] Checking internet...")
try:
    requests.get("https://github.com", timeout=5)
    print("  OK internet connected")
except:
    print("  ERROR No internet. Turn on Wi-Fi and restart.")
    input("\nPress Enter to exit...")
    exit()

# STEP 3: Download
print("\n[3/6] Downloading archive...")
zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
r = requests.get(GITHUB_URL)
with open(zip_path, "wb") as f:
    f.write(r.content)
print(f"  OK Downloaded ({len(r.content)//1024} KB)")

# STEP 4: Extract
print("\n[4/6] Extracting...")
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
print("  OK Extracted")

# STEP 5: Install files
print("\n[5/6] Installing files...")
os.makedirs(TARGET_DIR, exist_ok=True)

old_config = os.path.join(TARGET_DIR, "config.py")
backup = None
if os.path.exists(old_config):
    with open(old_config, "r") as f:
        backup = f.read()

for root, dirs, files in os.walk(tmp_dir):
    for fname in files:
        if fname.endswith((".py", ".json", ".txt", ".md")):
            src = os.path.join(root, fname)
            dst = os.path.join(TARGET_DIR, fname)
            if fname == "config.py" and backup:
                continue
            shutil.copy2(src, dst)

if backup:
    with open(old_config, "w") as f:
        f.write(backup)

vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
print("  OK Files installed")

# STEP 6: Cleanup
print("\n[6/6] Cleaning temporary files...")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
print("  OK Done")

print(f"\n{'='*60}")
print("  ORGANIZER INSTALLED!")
print(f"\n  Open Pydroid -> {TARGET_DIR}/main.py -> Run")
print(f"{'='*60}")
input("\nPress Enter to exit...")
