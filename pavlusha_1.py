# pavlusha_1.py - PEREUSTANOVKA + ASK ENTER ONCE
import sys, os, subprocess

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

# 1. Сохраняем config.py
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

# 2. Удаляем старую папку
print("[2/5] Удаляю старую папку...")
if os.path.exists(BASE):
    for root, dirs, files in os.walk(BASE, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(BASE)
ok("Папка удалена" if not os.path.exists(BASE) else "Папка НЕ удалена")

# 3. Установщик
print("[3/5] Установщик...")
print("-" * 50)

import requests as _r
r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
if r.status_code == 200:
    ipath = "/storage/emulated/0/Download/install_temp.py"
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(r.text)
    
    process = subprocess.Popen(
        [sys.executable, ipath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        print(f"  {line.rstrip()}")
    
    process.wait()
    print("-" * 50)
    
    if os.path.exists(os.path.join(BASE, "main.py")):
        ok("main.py создан!")
        # Сразу восстанавливаем config.py
        if os.path.exists(CONFIG_BACKUP):
            try:
                with open(CONFIG_BACKUP, "r") as f:
                    data = f.read()
                with open(CONFIG, "w") as f:
                    f.write(data)
                os.remove(CONFIG_BACKUP)
                ok("config.py восстановлен! Регистрация сохранена.")
            except:
                fail("Не могу восстановить config.py")
        else:
            ok("Нет бэкапа config.py. Нужна регистрация при первом запуске.")
    else:
        fail("main.py НЕ создан!")
    os.remove(ipath)
else:
    fail(f"Не удалось скачать установщик: {r.status_code}")

# 4. Проверка config.py
print("\n[4/5] Проверяю config.py...")
if os.path.exists(CONFIG):
    with open(CONFIG, "r") as f:
        content = f.read()
    if "введите_пароль" in content or "введите_логин" in content:
        ok("config.py — шаблон. Нужна регистрация.")
    else:
        ok("config.py содержит данные. Регистрация НЕ нужна.")
else:
    ok("config.py отсутствует.")

# 5. Диагностика
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
    print("  Теперь нажмите Enter чтобы закрыть этот тест.")
    input()
print("=" * 60)
