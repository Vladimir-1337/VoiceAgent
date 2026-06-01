# install_organizer.py v4.0 — УНИВЕРСАЛЬНЫЙ УСТАНОВЩИК
# Находит папку диктофона ЛЮБЫМ способом.
# Если не находит — полная диагностика + ADB-инструкция + отчёт разработчику.
import sys, os, subprocess, time, shutil, json

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА v4.0")
print("  Мы найдём решение. Что бы ни случилось.")
print("=" * 60)

TARGET_DIR = "/storage/emulated/0/VoiceAgent"
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"
REPORT = {}
PROBLEMS = []
SOLUTIONS = []

# Собираем данные об устройстве ВСЕГДА (до поиска аудио)
try:
    REPORT["model"] = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
except: REPORT["model"] = "?"
try:
    REPORT["manufacturer"] = subprocess.check_output(["getprop", "ro.product.manufacturer"]).decode().strip()
except: REPORT["manufacturer"] = "?"
try:
    REPORT["android_release"] = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    REPORT["android_sdk"] = subprocess.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
except:
    REPORT["android_release"] = "?"
    REPORT["android_sdk"] = "?"
try:
    REPORT["python_version"] = sys.version.split()[0]
except: pass
try:
    stat = shutil.disk_usage("/storage/emulated/0")
    REPORT["storage_free_gb"] = round(stat.free / (1024**3), 1)
    REPORT["storage_total_gb"] = round(stat.total / (1024**3), 1)
except: pass

# Права доступа к папкам
for d in ["/storage/emulated/0/", "/storage/emulated/0/Download/", "/storage/emulated/0/Recordings/", "/storage/emulated/0/DCIM/"]:
    key = "access_" + d.split("/")[-2]
    if os.path.exists(d):
        try:
            items = os.listdir(d)
            REPORT[key] = f"OK ({len(items)})"
        except:
            REPORT[key] = "DENIED"
    else:
        REPORT[key] = "NOT_EXISTS"

def ok(msg):
    print(f"  ✅ {msg}")

def warn(msg):
    PROBLEMS.append(msg)
    print(f"  ⚠️ {msg}")

def fail(msg):
    PROBLEMS.append(msg)
    print(f"  ❌ {msg}")

def hope(msg):
    SOLUTIONS.append(msg)
    print(f"  💡 {msg}")

def progress(text, pct):
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"  [{bar}] {pct}% — {text}")

def try_get(url, timeout=10, retries=3):
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

# ═══════════════════════════════════════
# ШАГ 0: СУПЕР-ДИАГНОСТИКА
# ═══════════════════════════════════════
print("\n[0/7] Супер-диагностика...")
print("  📢 Запишите короткую фразу в ДИКТОФОНЕ и нажмите Enter.")
input("  ⏳ Нажмите Enter после записи...")

recorder_folder = None
AUDIO_EXTS = (
    ".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac",
    ".3gp", ".m4b", ".m4p", ".m4r", ".mp2", ".mpga", ".oga", ".opus",
    ".aiff", ".aif", ".aifc", ".au", ".caf", ".gsm", ".mka", ".mmf",
    ".snd", ".voc", ".vox", ".8svx", ".mid", ".midi", ".xmf", ".mxmf",
    ".rtttl", ".rtx", ".ota", ".imy", ".mp4", ".m4v", ".mov", ".avi"
)

# --- Метод 1: MediaStore через jnius ---
print("\n  Метод 1: MediaStore API...")
mediastore_files = []
try:
    import jnius
    ActivityThread = jnius.autoclass('android.app.ActivityThread')
    context = ActivityThread.currentApplication()
    resolver = context.getContentResolver()
    MediaStore = jnius.autoclass('android.provider.MediaStore$Audio$Media')
    uri = MediaStore.EXTERNAL_CONTENT_URI
    cursor = resolver.query(uri, None, None, None, None)
    if cursor and cursor.getCount() > 0:
        count = cursor.getCount()
        ok(f"MediaStore: {count} файлов")
        REPORT["mediastore_count"] = count
        cursor.moveToFirst()
        for i in range(min(count, 100)):
            try:
                data_idx = cursor.getColumnIndex(MediaStore.DATA)
                name_idx = cursor.getColumnIndex(MediaStore.DISPLAY_NAME)
                date_idx = cursor.getColumnIndex(MediaStore.DATE_ADDED)
                if data_idx >= 0:
                    path = cursor.getString(data_idx)
                    name = cursor.getString(name_idx) if name_idx >= 0 else "?"
                    date = cursor.getLong(date_idx) if date_idx >= 0 else 0
                    mediastore_files.append({"path": path, "name": name, "date": date})
            except:
                pass
            if not cursor.moveToNext():
                break
        cursor.close()
        
        # Ищем свежие (за час)
        now = time.time()
        fresh_ms = [f for f in mediastore_files if now - f["date"] < 3600]
        if fresh_ms:
            recorder_folder = os.path.dirname(fresh_ms[0]["path"])
            ok(f"MediaStore: папка диктофона = {recorder_folder}/")
    else:
        warn("MediaStore: 0 файлов")
        REPORT["mediastore_count"] = 0
except Exception as e:
    warn(f"MediaStore недоступен: {str(e)[:80]}")
    REPORT["mediastore_error"] = str(e)[:80]

# --- Метод 2: os.walk по хранилищу ---
if not recorder_folder:
    print("\n  Метод 2: поиск по файловой системе...")
    all_audio = []
    walk_errors = []
    for root, dirs, files in os.walk("/storage/emulated/0/"):
        try:
            for f in files:
                if any(f.lower().endswith(ext) for ext in AUDIO_EXTS):
                    fp = os.path.join(root, f)
                    try:
                        ftime = os.path.getmtime(fp)
                        all_audio.append({"path": fp, "folder": root, "name": f, "mtime": ftime})
                    except:
                        pass
        except PermissionError:
            walk_errors.append(root)
        except Exception as e:
            walk_errors.append(f"{root}: {str(e)[:40]}")
        if len(all_audio) > 500:
            break
    
    REPORT["audio_total"] = len(all_audio)
    REPORT["walk_errors"] = len(walk_errors)
    
    if all_audio:
        ok(f"Найдено аудио: {len(all_audio)}")
        fresh = [a for a in all_audio if time.time() - a["mtime"] < 3600]
        if fresh:
            recorder_folder = max(fresh, key=lambda x: x["mtime"])["folder"]
            ok(f"Папка диктофона: {recorder_folder}/")
        else:
            warn("Свежих записей нет (старше 1 часа)")
            recorder_folder = max(all_audio, key=lambda x: x["mtime"])["folder"]
            ok(f"Использую последнюю папку с аудио: {recorder_folder}/")
    else:
        fail("Аудиофайлы НЕ найдены вообще")
        REPORT["audio_total"] = 0

# --- Метод 3: Стандартные папки ---
if not recorder_folder:
    print("\n  Метод 3: проверка стандартных папок...")
    defaults = [
        "/storage/emulated/0/Recordings/",
        "/storage/emulated/0/Recorder/",
        "/storage/emulated/0/MIUI/sound_recorder/",
        "/storage/emulated/0/Sounds/",
        "/storage/emulated/0/Voice Recorder/",
        "/storage/emulated/0/record/",
        "/storage/emulated/0/Download/",
        "/storage/emulated/0/Music/",
        "/storage/emulated/0/DCIM/",
    ]
    for d in defaults:
        if os.path.exists(d):
            try:
                files = os.listdir(d)
                audio_in_dir = [f for f in files if any(f.lower().endswith(ext) for ext in AUDIO_EXTS)]
                if audio_in_dir:
                    recorder_folder = d
                    ok(f"Найдена папка с аудио: {d} ({len(audio_in_dir)} файлов)")
                    break
            except:
                pass
    
    if not recorder_folder:
        recorder_folder = "/storage/emulated/0/Recordings/"
        warn("Папка диктофона НЕ определена. Использую /Recordings/.")

REPORT["recorder_folder"] = recorder_folder
REPORT["method_found"] = "MediaStore" if recorder_folder and REPORT.get("mediastore_count",0) > 0 else ("os.walk" if recorder_folder and REPORT.get("audio_total",0) > 0 else ("defaults" if recorder_folder else "NOT_FOUND"))

# --- Если не нашли — глубокая диагностика ---
if not REPORT.get("audio_total", 0) and not REPORT.get("mediastore_count", 0):
    print("\n" + "=" * 60)
    print("  АУДИО НЕ НАЙДЕНЫ — ПОЛНАЯ ДИАГНОСТИКА")
    print("=" * 60)
    
    # Информация об устройстве
    for prop in ["ro.product.model", "ro.product.manufacturer", "ro.build.version.release", "ro.build.version.sdk"]:
        try:
            val = subprocess.check_output(["getprop", prop]).decode().strip()
            REPORT[prop.split(".")[-1]] = val
            print(f"  {prop.split('.')[-1]}: {val}")
        except:
            pass
    
    # Разрешения
    try:
        import jnius
        context = jnius.autoclass('android.app.ActivityThread').currentApplication()
        PackageManager = jnius.autoclass('android.content.pm.PackageManager')
        
        perms_to_check = [
            "android.permission.READ_MEDIA_AUDIO",
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
        ]
        for perm in perms_to_check:
            try:
                ok = context.checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED
                REPORT[f"perm_{perm.split('.')[-1]}"] = ok
                print(f"  {perm.split('.')[-1]}: {'✅' if ok else '❌'}")
                if not ok:
                    hope(f"ADB: adb shell pm grant ru.iiec.pydroid3 {perm}")
            except:
                pass
        
        # MANAGE_EXTERNAL_STORAGE
        try:
            Environment = jnius.autoclass('android.os.Environment')
            manage = Environment.isExternalStorageManager()
            REPORT["manage_external_storage"] = manage
            print(f"  MANAGE_EXTERNAL_STORAGE: {'✅' if manage else '❌'}")
            if not manage:
                hope("ADB: adb shell appops set ru.iiec.pydroid3 MANAGE_EXTERNAL_STORAGE allow")
        except:
            pass
    except:
        pass
    
    # Пути для ручного копирования
    print("\n  📂 Ручной метод (всегда работает):")
    print("     1. Диктофон → запись → Поделиться → Сохранить в Download")
    print("     2. Перезапустите установщик")
    
    # Беспроводная отладка
    sdk = REPORT.get("sdk", "0")
    try:
        if int(sdk) >= 30:
            print("\n  📡 Беспроводная отладка (Android 11+):")
            print("     1. Настройки → Для разработчиков → Беспроводная отладка")
            print("     2. Включить → IP и порт")
            print("     3. На ноутбуке: adb connect IP:порт")
            print("     4. Затем ADB-команды выше")
    except:
        pass

# Отправка отчёта
REPORT["problems"] = PROBLEMS
REPORT["solutions"] = SOLUTIONS
REPORT["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

print("\n  Отправляю диагностику разработчику...")
try:
    import requests as _r2
    _r2.post("http://157.22.202.232:8200/report",
             data=json.dumps(REPORT, indent=2, ensure_ascii=False).encode("utf-8"),
             timeout=10)
    ok("Отчёт отправлен")
except:
    warn("Отчёт не отправлен (нет интернета)")

progress("Диагностика завершена", 15)

# Отправляем отчёт при ЛЮБОЙ установке (успешной или нет)
REPORT["recorder_folder"] = recorder_folder
REPORT["success"] = recorder_folder != "/storage/emulated/0/Recordings/"
try:
    import requests as _r3
    _r3.post("http://157.22.202.232:8200/report",
             data=json.dumps(REPORT, indent=2, ensure_ascii=False).encode("utf-8"),
             timeout=10)
except:
    pass

# ═══════════════════════════════════════
# ШАГ 1: БИБЛИОТЕКИ
# ═══════════════════════════════════════
print("\n[1/7] Библиотеки...")
try:
    import requests
    ok("requests готов")
except ImportError:
    print("  ⏳ Устанавливаю...")
    for attempt in range(3):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q"], timeout=60)
            import requests
            ok(f"requests установлен (попытка {attempt+1})")
            break
        except:
            if attempt == 2:
                fail("Нужен VPN для установки requests")
                exit()
            time.sleep(2)
progress("Библиотеки готовы", 25)

# ═══════════════════════════════════════
# ШАГ 2: ИНТЕРНЕТ
# ═══════════════════════════════════════
print("\n[2/7] Интернет...")
r = try_get("https://github.com")
if r:
    ok("Интернет есть")
else:
    fail("Нет интернета")
    exit()
progress("Интернет проверен", 35)

# ═══════════════════════════════════════
# ШАГ 3: СКАЧИВАНИЕ
# ═══════════════════════════════════════
print("\n[3/7] Скачиваю архив...")
r = try_get(GITHUB_URL, timeout=30)
if r:
    zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
    with open(zip_path, "wb") as f:
        f.write(r.content)
    ok(f"Скачано ({len(r.content)//1024} КБ)")
else:
    fail("Не удалось скачать архив")
    exit()
progress("Архив скачан", 55)

# ═══════════════════════════════════════
# ШАГ 4: РАСПАКОВКА
# ═══════════════════════════════════════
print("\n[4/7] Распаковываю...")
import zipfile
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
ok("Распаковано")
progress("Архив распакован", 70)

# ═══════════════════════════════════════
# ШАГ 5: УСТАНОВКА + ПРАВКА CONFIG
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

# Прописываем папку диктофона
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
    ok(f"config.py: {recorder_folder}/")

# Заглушка voice_config.py
vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - stub\nfrom config import *\n")

os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
ok("Файлы установлены")
progress("Файлы установлены", 85)

# ═══════════════════════════════════════
# ШАГ 6: ОЧИСТКА
# ═══════════════════════════════════════
print("\n[6/7] Очищаю...")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
ok("Временные файлы удалены")
progress("Очистка завершена", 95)

# ═══════════════════════════════════════
# ШАГ 7: ГОТОВО
# ═══════════════════════════════════════
print(f"\n[7/7] Готово!")
progress("Установка завершена", 100)

print(f"\n{'='*60}")
print("  ОРГАНАЙЗЕР УСТАНОВЛЕН!")
print(f"  Папка диктофона: {recorder_folder}/")
if PROBLEMS:
    print(f"  Мы отправили отчёт разработчику ({len(PROBLEMS)} замечаний).")
print(f"  Откройте: {TARGET_DIR}/main.py → Run")
print(f"{'='*60}")
