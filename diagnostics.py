# diagnostics.py — РАСШИРЕННАЯ ДИАГНОСТИКА
# Запускается из install_organizer.py после установки.
# Отправляет мега-отчёт разработчику.
import sys, os, time, subprocess, json, shutil

TARGET = "/storage/emulated/0/VoiceAgent"

report = {}

# Устройство
for prop, key in [
    ("ro.product.model", "model"),
    ("ro.product.manufacturer", "manufacturer"),
    ("ro.product.brand", "brand"),
    ("ro.build.version.release", "android"),
    ("ro.build.version.sdk", "sdk"),
    ("ro.build.type", "build_type"),
]:
    try: report[key] = subprocess.check_output(["getprop", prop]).decode().strip()
    except: report[key] = "?"

# Память
stat = shutil.disk_usage("/storage/emulated/0")
report["storage_free_gb"] = round(stat.free / (1024**3), 1)
report["storage_total_gb"] = round(stat.total / (1024**3), 1)
report["python_version"] = sys.version.split()[0]

# Права доступа
rights = {}
for path, name in [
    ("/storage/emulated/0/", "root"),
    ("/storage/emulated/0/Recordings/", "recordings"),
    ("/storage/emulated/0/Download/", "download"),
    ("/storage/emulated/0/DCIM/", "dcim"),
    ("/storage/emulated/0/Music/", "music"),
]:
    if os.path.exists(path):
        try:
            items = os.listdir(path)
            rights[name] = f"OK ({len(items)} объектов)"
        except:
            rights[name] = "DENIED"
    else:
        rights[name] = "NOT EXISTS"
report["access_rights"] = rights

# Разрешения
permissions = {}
try:
    import jnius
    ctx = jnius.autoclass('android.app.ActivityThread').currentApplication()
    pm = jnius.autoclass('android.content.pm.PackageManager')
    for perm in ["READ_MEDIA_AUDIO", "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE"]:
        try:
            ok = ctx.checkSelfPermission("android.permission." + perm) == pm.PERMISSION_GRANTED
            permissions[perm] = "GRANTED" if ok else "DENIED"
        except:
            permissions[perm] = "?"
    try:
        Environment = jnius.autoclass('android.os.Environment')
        permissions["MANAGE_EXTERNAL_STORAGE"] = "GRANTED" if Environment.isExternalStorageManager() else "DENIED"
    except:
        permissions["MANAGE_EXTERNAL_STORAGE"] = "?"
except:
    permissions["error"] = "jnius unavailable"
report["permissions"] = permissions

# Поиск аудио
AUDIO_EXTS = (".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac",
              ".3gp", ".m4b", ".m4p", ".m4r", ".mp2", ".mpga", ".oga", ".opus")
audio_all = []
audio_folders = {}
walk_errors = []

for root, dirs, files in os.walk("/storage/emulated/0/"):
    try:
        for f in files:
            if any(f.lower().endswith(ext) for ext in AUDIO_EXTS):
                fp = os.path.join(root, f)
                folder = os.path.dirname(fp)
                audio_all.append({"name": f, "folder": folder, "size": os.path.getsize(fp), "mtime": os.path.getmtime(fp)})
                audio_folders[folder] = audio_folders.get(folder, 0) + 1
    except PermissionError:
        walk_errors.append(f"DENIED: {root}")
    except Exception as e:
        walk_errors.append(f"ERROR: {root} - {str(e)[:40]}")
    if len(audio_all) > 200:
        break

report["audio_total"] = len(audio_all)
report["audio_folders_all"] = {k: v for k, v in sorted(audio_folders.items(), key=lambda x: -x[1])[:15]}
report["audio_fresh_1h"] = len([a for a in audio_all if time.time() - a["mtime"] < 3600])
report["walk_errors"] = walk_errors[:10]

# MediaStore
try:
    import jnius
    ctx = jnius.autoclass('android.app.ActivityThread').currentApplication()
    resolver = ctx.getContentResolver()
    MediaStore = jnius.autoclass('android.provider.MediaStore$Audio$Media')
    cursor = resolver.query(MediaStore.EXTERNAL_CONTENT_URI, None, None, None, None)
    if cursor:
        report["mediastore_count"] = cursor.getCount()
        cursor.close()
    else:
        report["mediastore_count"] = "null"
except:
    report["mediastore_count"] = "unavailable"

# Вердикт ADB
needs_adb = False
adb_reasons = []
if report["audio_total"] == 0:
    needs_adb = True
    adb_reasons.append("os.walk: 0 аудиофайлов")
if report.get("mediastore_count", 0) == 0 or report.get("mediastore_count") == "unavailable":
    needs_adb = True
    adb_reasons.append("MediaStore: недоступен или 0 файлов")
if permissions.get("MANAGE_EXTERNAL_STORAGE") == "DENIED":
    needs_adb = True
    adb_reasons.append("MANAGE_EXTERNAL_STORAGE не выдан")
if permissions.get("READ_MEDIA_AUDIO") == "DENIED":
    needs_adb = True
    adb_reasons.append("READ_MEDIA_AUDIO не выдан")
report["needs_adb"] = needs_adb
report["adb_reasons"] = adb_reasons

# Статус
report["install_success"] = os.path.exists(os.path.join(TARGET, "main.py"))
report["installed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

# Отправка
try:
    import requests as _r
    _r.post("http://157.22.202.232:8200/report",
            data=json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
            timeout=10)
except:
    pass
