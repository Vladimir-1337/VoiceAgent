# pavlusha_1.py - PEREUSTANOVKA + TEST (with progress bar)
import sys, os, subprocess, time, threading

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

# Прогресс-бар (бегает пока установщик работает)
def progress_bar():
    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not progress_bar.done:
        print(f"\r  ⏳ Установка... {chars[i % len(chars)]} (может занять до 2 минут)", end="", flush=True)
        i += 1
        time.sleep(0.2)
    print("\r" + " " * 60 + "\r", end="")

progress_bar.done = False

# STEP 1: Save config.py
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
    ok("config.py не найден (новый пользователь)")

# STEP 2: Delete old folder
print("[2/5] Удаляю старую папку...")
if os.path.exists(BASE):
    for root, dirs, files in os.walk(BASE, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(BASE)
ok("Папка удалена" if not os.path.exists(BASE) else "Папка НЕ удалена")

# STEP 3: Run installer (с прогресс-баром и таймаутом 180 сек)
print("[3/5] Запускаю установщик...")
import requests as _r
r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
if r.status_code == 200:
    ipath = "/storage/emulated/0/Download/install_temp.py"
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(r.text)
    
    # Запускаем прогресс-бар в фоне
    t = threading.Thread(target=progress_bar)
    t.start()
    
    try:
        result = subprocess.run([sys.executable, ipath], capture_output=True, text=True, timeout=180)
        progress_bar.done = True
        t.join()
    except subprocess.TimeoutExpired:
        progress_bar.done = True
        t.join()
        fail("Установщик завис (таймаут 3 мин)")
        print("\n  Возможные причины:")
        print("    1. Нет интернета")
        print("    2. PyPI заблокирован (нужен VPN)")
        print("    3. Мало памяти")
        print("\n  Решение: включите VPN и перезапустите pavlusha_1.py")
        exit()
    
    if os.path.exists(os.path.join(BASE, "main.py")):
        ok("Установщик отработал!")
    else:
        fail("Установщик НЕ создал main.py")
    os.remove(ipath)
else:
    fail(f"Не удалось скачать установщик: {r.status_code}")

# STEP 4: Restore config.py
print("[4/5] Восстанавливаю config.py...")
if os.path.exists(CONFIG_BACKUP):
    try:
        with open(CONFIG_BACKUP, "r") as f:
            data = f.read()
        with open(CONFIG, "w") as f:
            f.write(data)
        os.remove(CONFIG_BACKUP)
        ok("config.py восстановлен. Регистрация сохранена.")
    except:
        fail("Не могу восстановить config.py")
else:
    ok("Нечего восстанавливать")

# STEP 5: Diagnostics
print("[5/5] Диагностика...")
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
