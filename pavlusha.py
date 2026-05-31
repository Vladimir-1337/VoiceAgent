# pavlusha.py - TEST AVTOOBNOVLENIA NA CHUZHOM TELEFONE
import sys, os, shutil, subprocess

print("=" * 60)
print("  PAVLUSHA - TEST")
print("=" * 60)

problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    print(f"  ❌ {msg}")
    problems.append(msg)

# 1. Python
print("\n[1] Python:")
ok(f"Python {sys.version.split()[0]}")

# 2. requests
print("\n[2] requests:")
try:
    import requests
    ok("requests OK")
except ImportError:
    fail("requests NET")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q"], timeout=60)
        import requests
        ok("requests ustanovlen")
    except:
        fail("requests NE USTANOVLEN")

# 3. Internet
print("\n[3] Internet:")
for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com")]:
    try:
        r = requests.get(url, timeout=5)
        ok(f"{name}: {r.status_code}")
    except:
        fail(f"{name} nedostupen")

# 4. GitHub RAW
print("\n[4] GitHub RAW:")
try:
    r = requests.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt", timeout=5)
    if r.status_code == 200:
        ok(f"GitHub RAW OK. Version: {r.text.strip()}")
    else:
        fail(f"GitHub RAW: {r.status_code}")
except:
    fail("GitHub RAW nedostupen")

# 5. Local files
print("\n[5] Local files:")
base = "/storage/emulated/0/VoiceAgent"
for fname in ["main.py", "config.py", "updater.py", "version.txt"]:
    path = os.path.join(base, fname)
    if os.path.exists(path):
        ok(f"{fname} OK")
    else:
        fail(f"{fname} NET")

# 6. Versions
print("\n[6] Versions:")
try:
    with open(os.path.join(base, "version.txt"), "r") as f:
        local_ver = f.read().strip()
    ok(f"Local: {local_ver}")
except:
    local_ver = "NET"
    fail("Local version NET")

try:
    r = requests.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt", timeout=5)
    remote_ver = r.text.strip() if r.status_code == 200 else "NET"
    ok(f"GitHub: {remote_ver}")
except:
    remote_ver = "NET"

if local_ver != "NET" and remote_ver != "NET":
    if local_ver == remote_ver:
        ok("Versions match")
    else:
        fail(f"Versions RAZNYE! Local={local_ver} GitHub={remote_ver}")

# 7. updater
print("\n[7] updater:")
sys.path.insert(0, base)
try:
    import updater
    ok("updater OK")
except:
    fail("updater NET")

# 8. main calls updater?
print("\n[8] main.py:")
with open(os.path.join(base, "main.py"), "r") as f:
    main_code = f.read()
if "updater.check()" in main_code:
    ok("main calls updater.check()")
else:
    fail("main NE calls updater.check()")

# 9. Memory
print("\n[9] Memory:")
stat = shutil.disk_usage("/storage/emulated/0")
free_gb = stat.free / (1024**3)
ok(f"Free {free_gb:.1f} GB")

# 10. Android
print("\n[10] Android:")
try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    ok(f"Android {release}, {model}")
except:
    ok("Cannot detect")

# ITÖG
print("\n" + "=" * 60)
if problems:
    print(f"  PROBLEMS: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
