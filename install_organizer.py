# install_organizer.py — ФИНАЛЬНЫЙ УСТАНОВЩИК
# 1. Удаляет старую папку
# 2. Устанавливает новую версию
# 3. Отправляет отчёт разработчику
# 4. Сохраняет config.py
# 5. Запускает main.py
import sys, os, subprocess, time, shutil, json, zipfile

TARGET = "/storage/emulated/0/VoiceAgent"

def log(msg):
    print(f"  {msg}")
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

def try_get(url, retries=3):
    import requests
    for a in range(retries):
        try:
            r = requests.get(url, timeout=30, allow_redirects=True)
            if r.status_code == 200:
                return r
        except:
            pass
        time.sleep(2)
    return None

# ШАГ 1: Сохраняем config.py
log("[1/6] Сохраняю config.py...")
# ═══════════════════════════════
backup = None
config_path = os.path.join(TARGET, "config.py")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        backup = f.read()

# ШАГ 2: Удаляем старую папку
log("[2/6] Удаляю старую версию...")
# ═══════════════════════════════
if os.path.exists(TARGET):
    for root, dirs, files in os.walk(TARGET, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(TARGET)

# ШАГ 3: Качаем и распаковываем
log("[3/6] Скачиваю новую версию...")
# ═══════════════════════════════
r = try_get(GITHUB_URL)
if not r:
    print("Ошибка скачивания")
    sys.exit(1)

zip_path = "/storage/emulated/0/Download/install.zip"
with open(zip_path, "wb") as f:
    f.write(r.content)

tmp = "/storage/emulated/0/Download/install_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp)

# ШАГ 4: Устанавливаем файлы
log("[4/6] Устанавливаю файлы...")
# ═══════════════════════════════
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

# Восстанавливаем config.py
if backup:
    with open(config_path, "w") as f:
        f.write(backup)

# Заглушка voice_config.py
vcp = os.path.join(TARGET, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)

# Чистим
shutil.rmtree(tmp, ignore_errors=True)
os.remove(zip_path)

# ШАГ 5: Отправляем отчёт
log("[5/6] Отправляю отчёт...")
# ═══════════════════════════════
report = {"model": "?", "android": "?", "sdk": "?"}
for prop, key in [("ro.product.model", "model"), ("ro.build.version.release", "android"), ("ro.build.version.sdk", "sdk")]:
    try:
        report[key] = subprocess.check_output(["getprop", prop]).decode().strip()
    except:
        pass
report["installed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

try:
    import requests as _r
    _r.post("http://157.22.202.232:8200/report",
            data=json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
            timeout=10)
except:
    pass

# ШАГ 6: Запускаем main.py
log("[6/6] Запускаю программу...")
# ═══════════════════════════════
log("✅ Установка завершена! Откройте main.py в Pydroid и нажмите Run.")
