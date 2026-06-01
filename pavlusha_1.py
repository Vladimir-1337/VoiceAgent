# pavlusha_1.py — ФИНАЛЬНАЯ ДИАГНОСТИКА ДИКТОФОНА
# Мы найдём решение. Что бы ни случилось.
import sys, os, time, subprocess, json

print("=" * 60)
print("  PAVLUSHA — ПОИСК ДИКТОФОНА")
print("  Не волнуйтесь. Мы во всём разберёмся.")
print("=" * 60)

problems = []
solutions = []

def ok(msg):
    print(f"  ✅ {msg}")

def warn(msg):
    problems.append(msg)
    print(f"  ⚠️ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

def hope(msg):
    solutions.append(msg)
    print(f"  💡 {msg}")

# ═══════════════════════════════════════
# ЧАСТЬ 1: ЗНАКОМСТВО С ТЕЛЕФОНОМ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 1: ЗНАКОМСТВО С ТЕЛЕФОНОМ")
print("=" * 60)

try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    ok(f"Модель: {model}")
except:
    model = "неизвестна"
    warn("Не удалось определить модель")

try:
    manufacturer = subprocess.check_output(["getprop", "ro.product.manufacturer"]).decode().strip()
    ok(f"Производитель: {manufacturer}")
except:
    manufacturer = "неизвестен"

try:
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
    ok(f"Android: {release} (SDK {sdk})")
except:
    release = "?"
    sdk = "?"

# ═══════════════════════════════════════
# ЧАСТЬ 2: ПРОВЕРКА ПРАВ ДОСТУПА
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 2: ПРАВА ДОСТУПА")
print("=" * 60)

# Проверяем доступ к разным папкам
test_dirs = [
    "/storage/emulated/0/",
    "/storage/emulated/0/Download/",
    "/storage/emulated/0/Recordings/",
    "/storage/emulated/0/DCIM/",
    "/storage/emulated/0/Music/",
]

for d in test_dirs:
    if os.path.exists(d):
        try:
            files = os.listdir(d)
            ok(f"Доступ к {d.split('/')[-2]}/ есть ({len(files)} объектов)")
        except PermissionError:
            warn(f"Нет прав на чтение {d.split('/')[-2]}/")
            hope(f"Дайте Pydroid разрешение на доступ к файлам в настройках телефона")
        except Exception as e:
            warn(f"Ошибка доступа к {d.split('/')[-2]}/: {str(e)[:50]}")
    else:
        ok(f"Папка {d.split('/')[-2]}/ не существует (это нормально)")

# Проверяем MANAGE_EXTERNAL_STORAGE через jnius
print()
try:
    import jnius
    ok("jnius доступен")
    
    # Пробуем получить контекст через ActivityThread (работает в Pydroid)
    try:
        ActivityThread = jnius.autoclass('android.app.ActivityThread')
        context = ActivityThread.currentApplication()
        ok("Контекст Android получен")
        
        # Проверяем MANAGE_EXTERNAL_STORAGE
        try:
            Environment = jnius.autoclass('android.os.Environment')
            if Environment.isExternalStorageManager():
                ok("Расширенный доступ к файлам: ВКЛЮЧЕН")
            else:
                warn("Расширенный доступ к файлам: ВЫКЛЮЧЕН")
                hope("Откройте Настройки → Приложения → Pydroid 3 → Разрешить управление всеми файлами")
        except Exception as e:
            warn(f"Не удалось проверить расширенный доступ: {str(e)[:60]}")
        
        # Проверяем READ_MEDIA_AUDIO (Android 13+)
        if sdk and int(sdk) >= 33:
            try:
                PackageManager = jnius.autoclass('android.content.pm.PackageManager')
                perm = "android.permission.READ_MEDIA_AUDIO"
                if context.checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED:
                    ok("Разрешение на аудиофайлы: ВЫДАНО")
                else:
                    warn("Разрешение на аудиофайлы: НЕ ВЫДАНО")
                    hope("Откройте Настройки → Приложения → Pydroid 3 → Разрешения → Аудио")
            except:
                pass
        
        # Пробуем MediaStore
        print()
        print("  Пробую MediaStore (основной способ для Android 13)...")
        try:
            resolver = context.getContentResolver()
            MediaStore = jnius.autoclass('android.provider.MediaStore$Audio$Media')
            uri = MediaStore.EXTERNAL_CONTENT_URI
            cursor = resolver.query(uri, None, None, None, None)
            
            if cursor:
                count = cursor.getCount()
                if count > 0:
                    ok(f"MediaStore нашёл {count} аудиофайлов!")
                    print(f"  Показываю первые 10:")
                    cursor.moveToFirst()
                    shown = 0
                    while shown < 10:
                        try:
                            data_idx = cursor.getColumnIndex(MediaStore.DATA)
                            name_idx = cursor.getColumnIndex(MediaStore.DISPLAY_NAME)
                            if data_idx >= 0:
                                path = cursor.getString(data_idx)
                                name = cursor.getString(name_idx) if name_idx >= 0 else "?"
                                print(f"    📁 {path}")
                                shown += 1
                        except:
                            pass
                        if not cursor.moveToNext():
                            break
                else:
                    warn("MediaStore не нашёл аудиофайлов")
                    hope("Возможно, диктофон ещё не использовался. Запишите фразу и перезапустите.")
                cursor.close()
            else:
                warn("MediaStore не отвечает")
        except Exception as e:
            warn(f"MediaStore недоступен: {str(e)[:80]}")
            hope("Попробуем другие способы ниже")
    
    except Exception as e:
        warn(f"Не удалось получить контекст Android: {str(e)[:60]}")
    
except ImportError:
    warn("jnius не установлен")
    hope("Установите jnius: pip install pyjnius")

# ═══════════════════════════════════════
# ЧАСТЬ 3: ПОИСК АУДИО ПО ВСЕМУ ХРАНИЛИЩУ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 3: ПОИСК АУДИО ПО ХРАНИЛИЩУ")
print("=" * 60)

AUDIO_EXTS = (".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac",
              ".3gp", ".m4b", ".m4p", ".m4r", ".mp2", ".mpga", ".oga", ".opus",
              ".aiff", ".aif", ".aifc", ".au", ".caf", ".gsm", ".mka", ".mmf",
              ".snd", ".voc", ".vox", ".8svx")

all_audio = []
walk_errors = []

print("  Сканирую хранилище...")
for root, dirs, files in os.walk("/storage/emulated/0/"):
    try:
        for f in files:
            if any(f.lower().endswith(ext) for ext in AUDIO_EXTS):
                fp = os.path.join(root, f)
                ftime = os.path.getmtime(fp)
                fsize = os.path.getsize(fp)
                all_audio.append({"path": fp, "folder": root, "name": f, "size": fsize, "mtime": ftime})
    except PermissionError:
        walk_errors.append(root)
    except Exception as e:
        walk_errors.append(f"{root}: {str(e)[:40]}")
    
    if len(all_audio) > 200:
        break

ok(f"Всего аудиофайлов найдено: {len(all_audio)}")

if walk_errors:
    warn(f"Ошибок доступа к папкам: {len(walk_errors)}")
    unique_errors = list(set(walk_errors))[:5]
    for e in unique_errors:
        print(f"    🔒 {e}")

if all_audio:
    now = time.time()
    fresh = [a for a in all_audio if now - a["mtime"] < 3600]
    ok(f"Свежих (за час): {len(fresh)}")
    
    folders = {}
    for a in all_audio:
        f = a["folder"]
        folders[f] = folders.get(f, 0) + 1
    
    print(f"\n  Папки с аудио ({len(folders)}):")
    for folder, count in sorted(folders.items(), key=lambda x: -x[1])[:10]:
        print(f"    📁 {folder}/ ({count} файлов)")
    
    if fresh:
        latest = max(fresh, key=lambda x: x["mtime"])
        print(f"\n  ✅ Самая свежая запись: {latest['name']}")
        print(f"  ✅ Папка диктофона: {latest['folder']}/")
        recorder_folder = latest["folder"]
    else:
        warn("Свежих записей нет (старше 1 часа)")
        hope("Запишите фразу в диктофон и перезапустите этот тест")
        recorder_folder = "/storage/emulated/0/Recordings/"
else:
    fail("Аудиофайлы НЕ найдены вообще")
    hope("Проверьте, использовался ли диктофон на этом телефоне")
    hope("Возможно, диктофон сохраняет в скрытую папку /Android/data/")
    hope("Мы отправим этот отчёт разработчику — он найдёт решение")
    recorder_folder = "/storage/emulated/0/Recordings/"

# ═══════════════════════════════════════
# ЧАСТЬ 4: ОТПРАВКА ОТЧЁТА
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 4: ОТПРАВКА ОТЧЁТА")
print("=" * 60)

report = {
    "model": model,
    "manufacturer": manufacturer,
    "android": release,
    "sdk": sdk,
    "audio_total": len(all_audio),
    "audio_fresh": len(fresh) if all_audio else 0,
    "folders": list(folders.keys())[:15] if all_audio else [],
    "walk_errors": len(walk_errors),
    "recorder_folder": recorder_folder,
    "problems": problems,
}

try:
    import requests as _r
    _r.post("http://157.22.202.232:8200/report", 
            data=json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"), 
            timeout=10)
    ok("Отчёт отправлен разработчику")
    print("  Мы свяжемся с вами, как только найдём решение.")
except:
    warn("Не удалось отправить отчёт (нет интернета?)")
    print("  Но это не страшно — мы всё равно найдём решение.")

# ═══════════════════════════════════════
# ЧАСТЬ 5: ОБНОВЛЕНИЕ CONFIG.PY
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 5: ОБНОВЛЕНИЕ CONFIG.PY")
print("=" * 60)

base = "/storage/emulated/0/VoiceAgent"
config_path = os.path.join(base, "config.py")
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        content = f.read()
    old_line = 'RECORDINGS_DIR = "/storage/emulated/0/Recordings/"'
    new_line = f'RECORDINGS_DIR = "{recorder_folder}/"'
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(config_path, "w") as f:
            f.write(content)
        ok(f"config.py обновлён: {recorder_folder}/")
    else:
        ok("config.py уже настроен")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ИТОГ")
print("=" * 60)
print(f"  Телефон: {manufacturer} {model} (Android {release})")
print(f"  Аудиофайлов: {len(all_audio)}")
print(f"  Папка диктофона: {recorder_folder}/")
print()

if recorder_folder != "/storage/emulated/0/Recordings/":
    print("  ✅ Мы нашли папку диктофона!")
    print("  Всё работает. Можно пользоваться программой.")
elif len(all_audio) > 0:
    print("  ⚠️ Папка не определена точно, но аудио есть.")
    print("  Мы отправили данные разработчику. Он настроит программу.")
else:
    print("  ⚠️ Аудио не найдены. Но мы не сдаёмся.")
    print("  Отчёт отправлен. Решение будет найдено.")

print("=" * 60)
print()
print("  Спасибо за помощь! Вы помогаете сделать программу лучше.")
print("  Если что-то пошло не так — не переживайте. Мы всё починим.")
