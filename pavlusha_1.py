# pavlusha_1.py - PEREUSTANOVKA + TEST (NO shutil.copy)
import sys, os, subprocess

print("=" * 60)
print("  PAVLUSHA 1 - PEREUSTANOVKA + TEST")
print("=" * 60)

BASE = "/storage/emulated/0/VoiceAgent"
CONFIG = os.path.join(BASE, "config.py")
CONFIG_BACKUP = "/storage/emulated/0/Download/config_backup.py"
problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

# STEP 1: Save config.py (read/write, no shutil)
print("\n[1/5] Save config.py...")
if os.path.exists(CONFIG):
    try:
        with open(CONFIG, "r") as f:
            data = f.read()
        with open(CONFIG_BACKUP, "w") as f:
            f.write(data)
        ok("config.py saved")
    except:
        fail("Cannot save config.py")
else:
    ok("config.py not found (new user)")

# STEP 2: Delete old folder
print("\n[2/5] Delete old VoiceAgent...")
for root, dirs, files in os.walk(BASE, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
if os.path.exists(BASE):
    os.rmdir(BASE)
ok("VoiceAgent deleted" if not os.path.exists(BASE) else "VoiceAgent NOT deleted")

# STEP 3: Run installer
print("\n[3/5] Run installer...")
import requests as _r
r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
if r.status_code == 200:
    ipath = "/storage/emulated/0/Download/install_temp.py"
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(r.text)
    subprocess.run([sys.executable, ipath], capture_output=True, text=True, timeout=120)
    if os.path.exists(os.path.join(BASE, "main.py")):
        ok("Installer OK")
    else:
        fail("Installer FAILED")
    os.remove(ipath)
else:
    fail(f"Download failed: {r.status_code}")

# STEP 4: Restore config.py (read/write, no shutil)
print("\n[4/5] Restore config.py...")
if os.path.exists(CONFIG_BACKUP):
    try:
        with open(CONFIG_BACKUP, "r") as f:
            data = f.read()
        with open(CONFIG, "w") as f:
            f.write(data)
        os.remove(CONFIG_BACKUP)
        ok("config.py restored")
    except:
        fail("Cannot restore config.py")
else:
    ok("No backup")

# STEP 5: Diagnostics
print("\n[5/5] Diagnostics...")
try:
    import requests
    ok("requests OK")
except:
    fail("requests MISSING")

for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com")]:
    try:
        r = requests.get(url, timeout=5)
        ok(f"{name}: {r.status_code}")
    except:
        fail(f"{name} FAILED")

for fname in ["main.py", "config.py", "updater.py", "version.txt"]:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        ok(f"{fname} OK")
    else:
        fail(f"{fname} MISSING")

sys.path.insert(0, BASE)
try:
    import updater
    ok("updater OK")
except:
    fail("updater FAILED")

for path, name in [(BASE, "VoiceAgent"), ("/storage/emulated/0/Recordings/", "Recordings")]:
    ok(f"{name} exists" if os.path.exists(path) else f"{name} MISSING")

import shutil
stat = shutil.disk_usage("/storage/emulated/0")
ok(f"Free {stat.free / (1024**3):.1f} GB")

try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    ok(f"Android {release}, {model}")
except:
    ok("Android unknown")

print("\n" + "=" * 60)
if problems:
    print(f"  PROBLEMS: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ PEREUSTANOVKA SUCCESS!")
    print("  Registration saved.")
print("=" * 60)
