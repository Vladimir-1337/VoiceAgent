# pavlusha_1.py — ПЕРЕУСТАНОВКА + ПОЛНЫЙ ТЕСТ
# 1. Сохраняет config.py
# 2. Удаляет старую папку VoiceAgent
# 3. Запускает install_organizer.py (молча)
# 4. Восстанавливает config.py
# 5. Запускает полную диагностику
# НИЧЕГО НЕ СПРАШИВАЕТ. ВСЁ АВТОМАТОМ.

import sys, os, shutil, subprocess, time

print("=" * 60)
print("  PAVLUSHA 1 — ПЕРЕУСТАНОВКА + ТЕСТ")
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

# ═══════════════════════════════════════
# ШАГ 1: СОХРАНИТЬ config.py
# ═══════════════════════════════════════
print("\n[1/5] Сохраняю config.py...")
if os.path.exists(CONFIG):
    shutil.copy(CONFIG, CONFIG_BACKUP)
    ok("config.py сохранён")
else:
    ok("config.py не найден (новый пользователь)")

# ═══════════════════════════════════════
# ШАГ 2: УДАЛИТЬ СТАРУЮ ПАПКУ
# ═══════════════════════════════════════
print("\n[2/5] Удаляю старую папку VoiceAgent...")
if os.path.exists(BASE):
    shutil.rmtree(BASE, ignore_errors=True)
    ok("Папка VoiceAgent удалена")
else:
    ok("Папки VoiceAgent нет (первая установка)")

# ═══════════════════════════════════════
# ШАГ 3: ЗАПУСТИТЬ УСТАНОВЩИК
# ═══════════════════════════════════════
print("\n[3/5] Запускаю установщик...")
try:
    import requests as _r
    # Качаем install_organizer.py
    r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
    if r.status_code == 200:
        installer_path = "/storage/emulated/0/Download/install_organizer_temp.py"
        with open(installer_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        
        # Запускаем установщик молча
        result = subprocess.run([sys.executable, installer_path], capture_output=True, text=True, timeout=120)
        
        if os.path.exists(BASE) and os.path.exists(os.path.join(BASE, "main.py")):
            ok("Установщик отработал. main.py на месте.")
        else:
            fail("Установщик НЕ создал main.py")
        
        os.remove(installer_path)
    else:
        fail(f"Не удалось скачать установщик: {r.status_code}")
except Exception as e:
    fail(f"Ошибка установщика: {str(e)[:80]}")

# ═══════════════════════════════════════
# ШАГ 4: ВОССТАНОВИТЬ config.py
# ═══════════════════════════════════════
print("\n[4/5] Восстанавливаю config.py...")
if os.path.exists(CONFIG_BACKUP):
    shutil.copy(CONFIG_BACKUP, CONFIG)
    os.remove(CONFIG_BACKUP)
    ok("config.py восстановлен. Регистрация сохранена.")
else:
    ok("config.py не требует восстановления.")

# ═══════════════════════════════════════
# ШАГ 5: ПОЛНАЯ ДИАГНОСТИКА
# ═══════════════════════════════════════
print("\n[5/5] Полная диагностика...")

# 5.1 Python
try:
    import requests
    ok("requests установлен")
except ImportError:
    fail("requests НЕ установлен")

# 5.2 Интернет
for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com")]:
    try:
        r = requests.get(url, timeout=5)
        ok(f"{name}: {r.status_code}")
    except:
        fail(f"{name} недоступен")

# 5.3 GitHub RAW
try:
    r = requests.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt", timeout=5)
    if r.status_code == 200:
        GITHUB_VERSION = r.text.strip()
        ok(f"GitHub версия: {GITHUB_VERSION}")
    else:
        GITHUB_VERSION = None
        fail(f"GitHub RAW: {r.status_code}")
except:
    GITHUB_VERSION = None
    fail("GitHub RAW недоступен")

# 5.4 Локальные файлы
print("\nЛокальные файлы:")
for fname in ["main.py", "config.py", "updater.py", "version.txt"]:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        ok(f"{fname} ({os.path.getsize(path)} байт)")
    else:
        fail(f"{fname} ОТСУТСТВУЕТ")

# 5.5 Версии
try:
    with open(os.path.join(BASE, "version.txt"), "r") as f:
        LOCAL_VERSION = f.read().strip()
    ok(f"Локальная версия: {LOCAL_VERSION}")
    if LOCAL_VERSION == GITHUB_VERSION:
        ok("Версии совпадают")
    else:
        fail(f"Версии разные! Лок={LOCAL_VERSION}, GitHub={GITHUB_VERSION}")
except:
    fail("Локальный version.txt не найден")

# 5.6 updater
sys.path.insert(0, BASE)
try:
    import updater
    ok("updater импортируется")
except:
    fail("updater НЕ импортируется")

# 5.7 Папки
for path, name in [(BASE, "VoiceAgent"), ("/storage/emulated/0/Recordings/", "Recordings")]:
    if os.path.exists(path):
        ok(f"Папка {name} существует")
    else:
        fail(f"Папка {name} ОТСУТСТВУЕТ")

# 5.8 Память и Android
stat = shutil.disk_usage("/storage/emulated/0")
ok(f"Свободно {stat.free / (1024**3):.1f} ГБ")
try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    ok(f"Android {release}, {model}")
except:
    ok("Не удалось определить")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
if problems:
    print(f"  ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ ПЕРЕУСТАНОВКА УСПЕШНА!")
    print("  Регистрация сохранена.")
    print("  Программа готова к Заданию №2 (pavlusha_2.py).")
print("=" * 60)
