# install_organizer.py — УСТАНОВЩИК ОРГАНАЙЗЕРА
import sys, os, subprocess, time, shutil, json, zipfile

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА")
print("=" * 60)

TARGET = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

def log(msg):
    print(f"  {msg}")

# ШАГ 1
log("[1/6] Сохраняю config.py...")
backup = None
config_path = os.path.join(TARGET, "config.py")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        backup = f.read()

# ШАГ 2
log("[2/6] Удаляю старую версию...")
if os.path.exists(TARGET):
    for root, dirs, files in os.walk(TARGET, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(TARGET)

# ШАГ 3
log("[3/6] Скачиваю новую версию...")
import requests as _r
r = _r.get(GITHUB_URL, timeout=30, allow_redirects=True)
if r.status_code != 200:
    log("Ошибка скачивания")
    sys.exit(1)

zip_path = "/storage/emulated/0/Download/install.zip"
with open(zip_path, "wb") as f:
    f.write(r.content)

tmp = "/storage/emulated/0/Download/install_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp)

# ШАГ 4
log("[4/6] Устанавливаю файлы...")
os.makedirs(TARGET, exist_ok=True)

for root, dirs, files in os.walk(tmp):
    for fname in files:
        if fname.endswith((".py", ".json", ".txt", ".md")):
            src = os.path.join(root, fname)
            dst = os.path.join(TARGET, fname)
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
    with open(config_path, "w") as f:
        f.write(backup)

vcp = os.path.join(TARGET, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
shutil.rmtree(tmp, ignore_errors=True)
os.remove(zip_path)

# ШАГ 5
log("[5/6] Запускаю диагностику...")
diag_path = os.path.join(TARGET, "diagnostics.py")
if os.path.exists(diag_path):
    try:
        subprocess.run([sys.executable, diag_path], timeout=30)
    except:
        pass

# ШАГ 6
log("[6/6] Готово!")
log("Установка завершена! Откройте main.py и нажмите Run.")
