# pavlusha_1.py - PEREUSTANOVKA + PROGRESS BAR
import sys, os, subprocess, time, threading

print("=" * 60)
print("  PAVLUSHA 1 - PEREUSTANOVKA")
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

# STEP 1
print("\n[1/5] Сохраняю config.py...")
if os.path.exists(CONFIG):
    try:
        with open(CONFIG, "r") as f:
            data = f.read()
        with open(CONFIG_BACKUP, "w") as f:
            f.write(data)
        ok("config.py сохранён")
    except:
        fail("Не могу сохранить config.py")
else:
    ok("config.py не найден")

# STEP 2
print("[2/5] Удаляю старую папку...")
if os.path.exists(BASE):
    for root, dirs, files in os.walk(BASE, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(BASE)
ok("Папка удалена" if not os.path.exists(BASE) else "Папка НЕ удалена")

# STEP 3 — ТОЛЬКО ПРОГРЕСС-БАР 0-100%
print("[3/5] Запускаю установщик...")

import requests as _r
r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
if r.status_code == 200:
    ipath = "/storage/emulated/0/Download/install_temp.py"
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(r.text)
    
    # Прогресс-бар в фоне
    done = False
    def progress():
        for pct in range(0, 101, 2):
            if done:
                break
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r  [{bar}] {pct}%", end="", flush=True)
            time.sleep(1.5)  # ~75 секунд до 100%
        if not done:
            print(f"\r  [{'█'*20}] 100%", flush=True)
    
    t = threading.Thread(target=progress)
    t.start()
    
    # Запускаем установщик молча
    result = subprocess.run([sys.executable, ipath], capture_output=True, text=True, timeout=180)
    done = True
    t.join()
    print(f"\r  [{'█'*20}] 100%", flush=True)
    
    if os.path.exists(os.path.join(BASE, "main.py")):
        ok("Установщик отработал!")
    else:
        fail("Установщик НЕ создал main.py")
    os.remove(ipath)
    
    # СРАЗУ восстанавливаем config.py поверх того что создал установщик
    if os.path.exists(CONFIG_BACKUP):
        try:
            with open(CONFIG_BACKUP, "r") as f:
                data = f.read()
            with open(CONFIG, "w") as f:
                f.write(data)
            os.remove(CONFIG_BACKUP)
        except:
            pass
else:
    fail(f"Не удалось скачать установщик: {r.status_code}")

# STEP 4
print("\n[4/5] Проверяю config.py...")
if os.path.exists(CONFIG):
    ok("config.py на месте. Регистрация сохранена.")
else:
    ok("config.py будет создан при первом запуске.")

# STEP 5
print("\n[5/5] Диагностика...")
try:
    import requests
    ok("requests OK")
except:
    fail("requests НЕ установлен")

for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com")]:
    try:
        r = requests.get(url, timeout=5)
        ok(f"{name}: {r.status_code}")
    except:
        fail(f"{name} НЕДОСТУПЕН")

for fname in ["main.py", "config.py", "updater.py", "version.txt"]:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        ok(f"{fname} ({os.path.getsize(path)} байт)")
    else:
        fail(f"{fname} ОТСУТСТВУЕТ")

sys.path.insert(0, BASE)
try:
    import updater
    ok("updater импортируется")
except:
    fail("updater НЕ импортируется")

for path, name in [(BASE, "VoiceAgent"), ("/storage/emulated/0/Recordings/", "Recordings")]:
    ok(f"Папка {name} существует" if os.path.exists(path) else f"Папка {name} ОТСУТСТВУЕТ")

import shutil
stat = shutil.disk_usage("/storage/emulated/0")
ok(f"Свободно {stat.free / (1024**3):.1f} ГБ")

try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    ok(f"Android {release}, {model}")
except:
    ok("Не удалось определить Android")

print("\n" + "=" * 60)
if problems:
    print(f"  ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ ПЕРЕУСТАНОВКА УСПЕШНА!")
    print("  Регистрация сохранена.")
    print("  Можно переходить к Заданию №2 (pavlusha_2.py).")
print("=" * 60)
