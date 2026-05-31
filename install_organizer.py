# install_organizer.py — УСТАНОВЩИК ОРГАНАЙЗЕРА v2.1 (с повторами)
# Каждый сетевой шаг — 3 попытки. Не падает с первого раза.
import sys, os, subprocess, time, threading

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА v2.1")
print("=" * 60)

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

def progress(text, pct):
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"  [{bar}] {pct}% — {text}")

def try_get(url, timeout=10, retries=3):
    """GET-запрос с повторами."""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r
            else:
                print(f"    Попытка {attempt+1}/{retries}: статус {r.status_code}")
        except Exception as e:
            print(f"    Попытка {attempt+1}/{retries}: {str(e)[:50]}")
        if attempt < retries - 1:
            time.sleep(2)
    return None

# ═══════════════════════════════════════
# ШАГ 0: ПОИСК ПАПКИ ДИКТОФОНА
# ═══════════════════════════════════════
print("\n[0/7] Поиск папки диктофона...")
print("  📢 Запишите короткую фразу в ДИКТОФОНЕ и нажмите Enter.")
print("  (Не в Pydroid. В обычном приложении Диктофон на телефоне.)")
input("  ⏳ Нажмите Enter после записи...")

found_audio = []
skip_dirs = ["Android/data", "termux", "Download/termux"]
for root, dirs, files in os.walk("/storage/emulated/0/"):
    if any(skip in root for skip in skip_dirs):
        continue
    for f in files:
        if f.endswith((".m4a", ".mp3", ".aac", ".amr", ".wav")):
            full_path = os.path.join(root, f)
            if time.time() - os.path.getmtime(full_path) < 3600:
                found_audio.append(full_path)
    if len(found_audio) > 20:
        break

if found_audio:
    latest = max(found_audio, key=lambda f: os.path.getmtime(f))
    recorder_folder = os.path.dirname(latest)
    print(f"  ✅ Найдена свежая запись: {os.path.basename(latest)}")
    print(f"  ✅ Папка диктофона: {recorder_folder}/")
else:
    defaults = [
        "/storage/emulated/0/Recordings/",
        "/storage/emulated/0/Recorder/",
        "/storage/emulated/0/MIUI/sound_recorder/",
        "/storage/emulated/0/Download/",
    ]
    recorder_folder = "/storage/emulated/0/Recordings/"
    for d in defaults:
        if os.path.exists(d):
            recorder_folder = d
            break
    print(f"  ⚠️ Свежая запись не найдена. Использую: {recorder_folder}/")
    print(f"  (Если неверно — удалите папку VoiceAgent и запустите снова)")

progress("Папка диктофона найдена", 10)

# ═══════════════════════════════════════
# ШАГ 1: БИБЛИОТЕКИ
# ═══════════════════════════════════════
print("\n[1/7] Библиотеки...")
try:
    import requests
    print("  ✅ requests готов")
except ImportError:
    print("  ⏳ Устанавливаю (3 попытки)...")
    for attempt in range(3):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q"], timeout=60)
            import requests
            print(f"  ✅ requests установлен (попытка {attempt+1})")
            break
        except:
            if attempt == 2:
                print("  ❌ Не удалось. Нужен VPN.")
                input("\n  Нажмите Enter...")
                exit()
            else:
                time.sleep(2)

progress("Библиотеки готовы", 20)

# ═══════════════════════════════════════
# ШАГ 2: ИНТЕРНЕТ
# ═══════════════════════════════════════
print("\n[2/7] Интернет...")
r = try_get("https://github.com")
if r:
    print("  ✅ Интернет есть")
else:
    print("  ❌ Нет интернета.")
    input("\n  Нажмите Enter...")
    exit()

progress("Интернет проверен", 30)

# ═══════════════════════════════════════
# ШАГ 3: СКАЧИВАНИЕ (3 попытки)
# ═══════════════════════════════════════
print("\n[3/7] Скачиваю архив...")
r = try_get(GITHUB_URL, timeout=30)
if r:
    zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
    with open(zip_path, "wb") as f:
        f.write(r.content)
    print(f"  ✅ Скачано ({len(r.content)//1024} КБ)")
else:
    print("  ❌ Не удалось скачать архив.")
    input("\n  Нажмите Enter...")
    exit()

progress("Архив скачан", 50)

# ═══════════════════════════════════════
# ШАГ 4: РАСПАКОВКА
# ═══════════════════════════════════════
print("\n[4/7] Распаковываю...")
import zipfile, shutil
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
print("  ✅ Распаковано")

progress("Архив распакован", 65)

# ═══════════════════════════════════════
# ШАГ 5: УСТАНОВКА ФАЙЛОВ + ПРАВКА config.py
# ═══════════════════════════════════════
print("\n[5/7] Устанавливаю файлы...")
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
            try:
                with open(src, "r", encoding="utf-8") as fsrc:
                    content = fsrc.read()
                with open(dst, "w", encoding="utf-8") as fdst:
                    fdst.write(content)
            except:
                pass

if backup:
    with open(old_config, "w") as f:
        f.write(backup)

config_path = os.path.join(TARGET_DIR, "config.py")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config_content = f.read()
    config_content = config_content.replace(
        'RECORDINGS_DIR = "/storage/emulated/0/Recordings/"',
        f'RECORDINGS_DIR = "{recorder_folder}/"'
    )
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"  ✅ config.py обновлён: RECORDINGS_DIR = {recorder_folder}/")

vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
print("  ✅ Файлы установлены")

progress("Файлы установлены", 85)

# ═══════════════════════════════════════
# ШАГ 6: ОЧИСТКА
# ═══════════════════════════════════════
print("\n[6/7] Очищаю...")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
print("  ✅ Временные файлы удалены")

progress("Очистка завершена", 95)

# ═══════════════════════════════════════
# ШАГ 7: ГОТОВО
# ═══════════════════════════════════════
print(f"\n[7/7] Готово!")
progress("Установка завершена", 100)

print(f"\n{'='*60}")
print("  ОРГАНАЙЗЕР УСТАНОВЛЕН!")
print(f"  Папка диктофона: {recorder_folder}/")
print(f"  Откройте: {TARGET_DIR}/main.py → Run")
print(f"{'='*60}")
