# install_organizer.py — УСТАНОВЩИК ОРГАНАЙЗЕРА v2.0
# Сам находит папку диктофона. Сам прописывает config.py.
import sys, os, subprocess, time, threading

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА v2.0")
print("=" * 60)

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"
problems = []

def progress(text, pct):
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"  [{bar}] {pct}% — {text}")

# ═══════════════════════════════════════
# ШАГ 0: ПОИСК ПАПКИ ДИКТОФОНА
# ═══════════════════════════════════════
print("\n[0/7] Поиск папки диктофона...")
print("  📢 Запишите короткую фразу в ДИКТОФОНЕ и нажмите Enter.")
print("  (Не в Pydroid. В обычном приложении Диктофон на телефоне.)")
input("  ⏳ Нажмите Enter после записи...")

# Ищем самый свежий аудиофайл
found_audio = []
for root, dirs, files in os.walk("/storage/emulated/0/"):
    for f in files:
        if f.endswith((".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg")):
            found_audio.append(os.path.join(root, f))
    if len(found_audio) > 50:
        break

if found_audio:
    latest = max(found_audio, key=lambda f: os.path.getmtime(f))
    recorder_folder = os.path.dirname(latest)
    print(f"  ✅ Найдена папка: {recorder_folder}")
    print(f"     Файл: {os.path.basename(latest)}")
else:
    recorder_folder = "/storage/emulated/0/Recordings/"
    print(f"  ⚠️ Папка не найдена. Использую: {recorder_folder}")

progress("Папка диктофона найдена", 10)

# ═══════════════════════════════════════
# ШАГ 1: БИБЛИОТЕКИ
# ═══════════════════════════════════════
print("\n[1/7] Библиотеки...")
try:
    import requests
    print("  ✅ requests готов")
except ImportError:
    print("  ⏳ Устанавливаю...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q"], timeout=60)
        import requests
        print("  ✅ requests установлен")
    except:
        print("  ❌ Не удалось. Нужен VPN.")
        input("\n  Нажмите Enter...")
        exit()

progress("Библиотеки готовы", 20)

# ═══════════════════════════════════════
# ШАГ 2: ИНТЕРНЕТ
# ═══════════════════════════════════════
print("\n[2/7] Интернет...")
try:
    requests.get("https://github.com", timeout=5)
    print("  ✅ Интернет есть")
except:
    print("  ❌ Нет интернета.")
    input("\n  Нажмите Enter...")
    exit()

progress("Интернет проверен", 30)

# ═══════════════════════════════════════
# ШАГ 3: СКАЧИВАНИЕ
# ═══════════════════════════════════════
print("\n[3/7] Скачиваю архив...")
r = requests.get(GITHUB_URL)
zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
with open(zip_path, "wb") as f:
    f.write(r.content)
print(f"  ✅ Скачано ({len(r.content)//1024} КБ)")

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

# Восстанавливаем config.py если был
if backup:
    with open(old_config, "w") as f:
        f.write(backup)

# Прописываем правильную папку диктофона в config.py
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
