# install_organizer.py v5.0 — МОЛЧАЛИВЫЙ УСТАНОВЩИК
# НЕ ждёт пользователя. НЕ задаёт вопросов.
# Вызывается из updater.py при автообновлении.
import sys, os, subprocess, time, shutil, json, zipfile

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

def try_get(url, timeout=10, retries=3):
    import requests
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r
        except:
            pass
        if attempt < retries - 1:
            time.sleep(2)
    return None

# Сохраняем config.py
backup = None
config_path = os.path.join(TARGET_DIR, "config.py")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        backup = f.read()

# Удаляем старую папку
if os.path.exists(TARGET_DIR):
    for root, dirs, files in os.walk(TARGET_DIR, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(TARGET_DIR)

# Качаем ZIP
r = try_get(GITHUB_URL, timeout=30)
if not r:
    sys.exit()

zip_path = "/storage/emulated/0/Download/update_silent.zip"
with open(zip_path, "wb") as f:
    f.write(r.content)

# Распаковываем
tmp = "/storage/emulated/0/Download/update_silent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp)

# Устанавливаем файлы
os.makedirs(TARGET_DIR, exist_ok=True)
for root, dirs, files in os.walk(tmp):
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

# Восстанавливаем config.py
if backup:
    with open(config_path, "w") as f:
        f.write(backup)

# Заглушка voice_config.py
vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)

# Чистим
shutil.rmtree(tmp, ignore_errors=True)
os.remove(zip_path)

# Запускаем новый main.py
subprocess.Popen([sys.executable, os.path.join(TARGET_DIR, "main.py")])
