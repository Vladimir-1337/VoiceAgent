# install_organizer.py — УСТАНОВЩИК ОРГАНАЙЗЕРА (гарантированная установка requests)
import sys, os, subprocess

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА")
print("=" * 60)

# ШАГ 0: ГАРАНТИРОВАННАЯ УСТАНОВКА requests
print("\n[0/6] Устанавливаю requests (обязательно)...")
try:
    import requests
    print("  OK - уже есть")
except ImportError:
    print("  Устанавливаю...")
    # Пробуем несколько способов
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    except:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--break-system-packages", "-q"])
        except:
            try:
                os.system(f"{sys.executable} -m pip install requests -q")
            except:
                pass
    try:
        import requests
        print("  OK - установлен")
    except ImportError:
        print("  ОШИБКА: не удалось установить requests")
        print("  Проверьте интернет и перезапустите.")
        input("\nНажмите Enter...")
        exit()

import zipfile, shutil

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

# Шаг 1: Интернет
print("\n[1/6] Проверяю интернет...")
try:
    requests.get("https://github.com", timeout=5)
    print("  OK")
except:
    print("  ОШИБКА: Нет интернета.")
    exit()

# Шаг 2: Скачивание
print("\n[2/6] Скачиваю архив...")
zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
r = requests.get(GITHUB_URL)
with open(zip_path, "wb") as f:
    f.write(r.content)
print(f"  OK ({len(r.content)//1024} КБ)")

# Шаг 3: Распаковка
print("\n[3/6] Распаковываю...")
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
print("  OK")

# Шаг 4: Установка файлов
print("\n[4/6] Устанавливаю файлы...")
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

vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
print("  OK")

# Шаг 5: Очистка
print("\n[5/6] Очищаю...")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
print("  OK")

print(f"\n{'='*60}")
print("  ОРГАНАЙЗЕР УСТАНОВЛЕН!")
print(f"  Откройте Pydroid -> {TARGET_DIR}/main.py -> Run")
print(f"{'='*60}")
input("\nНажмите Enter...")
