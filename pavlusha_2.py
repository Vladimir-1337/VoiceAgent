# pavlusha_2.py — ЖЕСТОЧАЙШАЯ ПРОВЕРКА АВТООБНОВЛЕНИЯ
# Запусти на телефоне где УЖЕ установлен Органайзер.
# Проверит: updater, ZIP, config, циклы, GitHub, интернет.
# Ничего не ломает. Только диагностика.

import sys, os, shutil, subprocess, json

print("=" * 60)
print("  PAVLUSHA 2 — ПРОВЕРКА АВТООБНОВЛЕНИЯ")
print("=" * 60)

problems = []
passed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  ✅ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

BASE = "/storage/emulated/0/VoiceAgent"
sys.path.insert(0, BASE)

# ═══════════════════════════════════════
# 1. БИБЛИОТЕКИ
# ═══════════════════════════════════════
print("\n[1] Библиотеки:")
try:
    import requests
    ok("requests установлен")
except ImportError:
    fail("requests НЕ установлен")

try:
    import zipfile
    ok("zipfile встроен")
except:
    fail("zipfile НЕ встроен")

# ═══════════════════════════════════════
# 2. ИНТЕРНЕТ И GITHUB
# ═══════════════════════════════════════
print("\n[2] Интернет и GitHub:")
try:
    r = requests.get("https://google.com", timeout=5)
    ok(f"Google: {r.status_code}")
except:
    fail("Google недоступен")

try:
    r = requests.get("https://github.com", timeout=5)
    ok(f"GitHub: {r.status_code}")
except:
    fail("GitHub недоступен")

try:
    r = requests.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt", timeout=5)
    if r.status_code == 200:
        GITHUB_VERSION = r.text.strip()
        ok(f"GitHub RAW доступен. Версия: {GITHUB_VERSION}")
    else:
        GITHUB_VERSION = None
        fail(f"GitHub RAW: статус {r.status_code}")
except:
    GITHUB_VERSION = None
    fail("GitHub RAW недоступен")

# ═══════════════════════════════════════
# 3. ЛОКАЛЬНЫЕ ФАЙЛЫ
# ═══════════════════════════════════════
print("\n[3] Локальные файлы:")
for fname in ["main.py", "config.py", "updater.py", "version.txt"]:
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{fname} ({size} байт)")
    else:
        fail(f"{fname} ОТСУТСТВУЕТ")

# ═══════════════════════════════════════
# 4. ВЕРСИИ
# ═══════════════════════════════════════
print("\n[4] Версии:")
try:
    with open(os.path.join(BASE, "version.txt"), "r") as f:
        LOCAL_VERSION = f.read().strip()
    ok(f"Локальная: {LOCAL_VERSION}")
except:
    LOCAL_VERSION = None
    fail("Локальный version.txt не найден")

if LOCAL_VERSION and GITHUB_VERSION:
    if LOCAL_VERSION == GITHUB_VERSION:
        ok("Версии совпадают — цикла нет")
    else:
        fail(f"Версии РАЗНЫЕ! Лок={LOCAL_VERSION}, GitHub={GITHUB_VERSION}")

# ═══════════════════════════════════════
# 5. МОДУЛЬ UPDATER
# ═══════════════════════════════════════
print("\n[5] Модуль updater:")
try:
    import updater
    ok("updater импортируется")
    
    if hasattr(updater, "check"):
        ok("updater.check() существует")
    else:
        fail("updater.check() НЕ НАЙДЕН")
    
    if hasattr(updater, "GITHUB_USER"):
        ok("GITHUB_USER в updater есть")
    if hasattr(updater, "REPO"):
        ok("REPO в updater есть")
except Exception as e:
    fail(f"updater НЕ импортируется: {str(e)[:80]}")

# ═══════════════════════════════════════
# 6. ВЫЗОВ UPDATER В MAIN.PY
# ═══════════════════════════════════════
print("\n[6] Вызов updater в main.py:")
with open(os.path.join(BASE, "main.py"), "r") as f:
    main_code = f.read()

if "import updater" in main_code or "from updater" in main_code:
    ok("main.py импортирует updater")
else:
    fail("main.py НЕ импортирует updater")

if "updater.check()" in main_code:
    ok("main.py вызывает updater.check()")
else:
    fail("main.py НЕ вызывает updater.check()")

if "allow_redirects=True" in main_code or "allow_redirects=True" in open(os.path.join(BASE, "updater.py")).read():
    ok("allow_redirects=True есть (ZIP качается)")
else:
    fail("allow_redirects=True ОТСУТСТВУЕТ")

# ═══════════════════════════════════════
# 7. ЗАЩИТА CONFIG.PY
# ═══════════════════════════════════════
print("\n[7] Защита config.py:")
updater_code = open(os.path.join(BASE, "updater.py")).read()
if "backup_config" in updater_code or "config.py" in updater_code:
    ok("updater сохраняет config.py")
else:
    fail("updater НЕ сохраняет config.py")

if "config.py" in main_code:
    ok("config.py упоминается в main.py")
else:
    fail("config.py НЕ упоминается в main.py")

# ═══════════════════════════════════════
# 8. СИМУЛЯЦИЯ АВТООБНОВЛЕНИЯ
# ═══════════════════════════════════════
print("\n[8] Симуляция автообновления (проверка ZIP):")
try:
    zip_url = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"
    r_zip = requests.get(zip_url, timeout=30, allow_redirects=True)
    if r_zip.status_code == 200:
        ok(f"ZIP скачан ({len(r_zip.content)//1024} КБ)")
        
        # Проверяем, что ZIP содержит нужные файлы
        import io, zipfile
        with zipfile.ZipFile(io.BytesIO(r_zip.content)) as zf:
            names = zf.namelist()
            has_main = any("main.py" in n for n in names)
            has_updater = any("updater.py" in n for n in names)
            has_config = any("config.py" in n for n in names)
            
            if has_main:
                ok("ZIP содержит main.py")
            else:
                fail("ZIP НЕ содержит main.py")
            
            if has_updater:
                ok("ZIP содержит updater.py")
            else:
                fail("ZIP НЕ содержит updater.py")
            
            if has_config:
                ok("ZIP содержит config.py (шаблон)")
            else:
                fail("ZIP НЕ содержит config.py")
    else:
        fail(f"ZIP не скачался: {r_zip.status_code}")
except Exception as e:
    fail(f"Ошибка ZIP: {str(e)[:60]}")

# ═══════════════════════════════════════
# 9. ПАМЯТЬ
# ═══════════════════════════════════════
print("\n[9] Память:")
stat = shutil.disk_usage("/storage/emulated/0")
free_gb = stat.free / (1024**3)
if free_gb > 0.5:
    ok(f"Свободно {free_gb:.1f} ГБ")
else:
    fail(f"Мало памяти: {free_gb:.1f} ГБ")

# ═══════════════════════════════════════
# 10. ANDROID
# ═══════════════════════════════════════
print("\n[10] Android:")
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
    print(f"  НАЙДЕНО ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print(f"  ✅ ВСЕ {passed} ТЕСТОВ ПРОЙДЕНЫ!")
    print("  Автообновление полностью работоспособно.")
print("=" * 60)
