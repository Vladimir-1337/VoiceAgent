# install_organizer.py — УНИВЕРСАЛЬНЫЙ УСТАНОВЩИК ОРГАНАЙЗЕРА
# Запусти один раз в Pydroid. Он всё сделает сам.

import requests
import os
import zipfile
import shutil
import sys
import subprocess

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА v1.0")
print("=" * 60)

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

# ШАГ 1: Проверка библиотек
print("
[1/6] Проверяю библиотеки...")
try:
    import requests
    print("  ✅ requests готов")
except ImportError:
    print("  ⏳ Устанавливаю requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    print("  ✅ requests установлен")

# ШАГ 2: Интернет
print("
[2/6] Проверяю интернет...")
try:
    requests.get("https://github.com", timeout=5)
    print("  ✅ Интернет есть")
except:
    print("  ❌ Нет интернета. Включите Wi-Fi и перезапустите.")
    input("
Нажмите Enter...")
    exit()

# ШАГ 3: Скачивание
print("
[3/6] Скачиваю архив...")
zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
r = requests.get(GITHUB_URL)
with open(zip_path, "wb") as f:
    f.write(r.content)
print(f"  ✅ Скачано ({len(r.content)//1024} КБ)")

# ШАГ 4: Распаковка
print("
[4/6] Распаковываю...")
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
print("  ✅ Распаковано")

# ШАГ 5: Установка файлов
print("
[5/6] Устанавливаю файлы...")
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
            shutil.copy2(src, dst)

if backup:
    with open(old_config, "w") as f:
        f.write(backup)

# Заглушка voice_config.py
vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py — заглушка\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
print("  ✅ Файлы установлены")

# ШАГ 6: Очистка
print("
[6/6] Очищаю временные файлы...")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
print("  ✅ Готово")

print(f"\n{'='*60}")
print("  ✅ ОРГАНАЙЗЕР УСТАНОВЛЕН!")
print(f"\n  Откройте Pydroid → {TARGET_DIR}/main.py → Run")
print(f"{'='*60}")
input("\nНажмите Enter...")
