# pavlusha_1.py — ГЛУБОКАЯ ДИАГНОСТИКА ДИКТОФОНА
# Соберите ВСЕ данные о телефоне и аудиозаписях для поддержки.
# Запустите ПОСЛЕ того как запишете фразу в диктофон.
import sys, os, time, subprocess, shutil

print("=" * 60)
print("  PAVLUSHA 1 — ДИАГНОСТИКА ДИКТОФОНА")
print("=" * 60)

problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

def info(msg):
    print(f"  📋 {msg}")

# ═══════════════════════════════════════
# ЧАСТЬ 1: ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 1: ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ")
print("=" * 60)

try:
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    info(f"Модель: {model}")
except:
    info("Модель: неизвестна")

try:
    manufacturer = subprocess.check_output(["getprop", "ro.product.manufacturer"]).decode().strip()
    info(f"Производитель: {manufacturer}")
except:
    info("Производитель: неизвестен")

try:
    brand = subprocess.check_output(["getprop", "ro.product.brand"]).decode().strip()
    info(f"Бренд: {brand}")
except:
    info("Бренд: неизвестен")

try:
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
    info(f"Android: {release} (SDK {sdk})")
except:
    info("Android: неизвестен")

try:
    build_type = subprocess.check_output(["getprop", "ro.build.type"]).decode().strip()
    info(f"Тип сборки: {build_type}")
except:
    pass

try:
    import requests as _r
    r = _r.get("https://httpbin.org/ip", timeout=5)
    if r.status_code == 200:
        ip = r.json().get("origin", "?")
        info(f"Внешний IP: {ip}")
except:
    pass

stat = shutil.disk_usage("/storage/emulated/0")
info(f"Память: свободно {stat.free / (1024**3):.1f} ГБ из {stat.total / (1024**3):.1f} ГБ")

# ═══════════════════════════════════════
# ЧАСТЬ 2: ПРОВЕРКА ДИКТОФОНА
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 2: ПРОВЕРКА ДИКТОФОНА")
print("=" * 60)

# Проверяем, установлено ли приложение Диктофон
recorder_packages = [
    "com.android.soundrecorder",
    "com.mediatek.soundrecorder",
    "com.sec.android.app.voicenote",
    "com.android.voicerecorder",
    "com.samsung.android.app.notes",
    "com.xiaomi.voicerecorder",
    "com.coloros.soundrecorder",
    "com.huawei.multimedia.recorder",
]

info("Поиск приложений диктофона:")
found_recorders = []
for pkg in recorder_packages:
    try:
        result = subprocess.run(["pm", "list", "packages", pkg], capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            found_recorders.append(result.stdout.strip())
            info(f"  Найден: {result.stdout.strip()}")
    except:
        pass

if not found_recorders:
    fail("НИ ОДНО приложение диктофона не найдено!")
    info("  Возможно, диктофон не установлен или используется стороннее приложение.")
else:
    ok(f"Найдено приложений диктофона: {len(found_recorders)}")

# ═══════════════════════════════════════
# ЧАСТЬ 3: ПОИСК АУДИОФАЙЛОВ (БЕЗ ФИЛЬТРОВ)
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 3: ПОИСК ВСЕХ АУДИОФАЙЛОВ")
print("=" * 60)

AUDIO_EXTS = (
    ".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac",
    ".3gp", ".m4b", ".m4p", ".m4r", ".mp2", ".mpga", ".oga", ".opus",
    ".ra", ".rm", ".wv", ".webm", ".aiff", ".aif", ".aifc", ".au",
    ".caf", ".gsm", ".mka", ".mmf", ".snd", ".voc", ".vox", ".8svx"
)

all_audio = []
scan_start = time.time()

info("Сканирую ВСЁ хранилище без фильтров...")
for root, dirs, files in os.walk("/storage/emulated/0/"):
    for f in files:
        f_lower = f.lower()
        if any(f_lower.endswith(ext) for ext in AUDIO_EXTS):
            full_path = os.path.join(root, f)
            try:
                stat_info = os.stat(full_path)
                all_audio.append({
                    "path": full_path,
                    "folder": root,
                    "name": f,
                    "size": stat_info.st_size,
                    "mtime": stat_info.st_mtime,
                    "ctime": stat_info.st_ctime,
                })
            except:
                pass
    
    if len(all_audio) > 200:
        break

scan_time = time.time() - scan_start
ok(f"Сканирование завершено за {scan_time:.1f} сек")
ok(f"Всего аудиофайлов на устройстве: {len(all_audio)}")

if not all_audio:
    fail("АУДИОФАЙЛЫ ПОЛНОСТЬЮ ОТСУТСТВУЮТ!")
    info("  На этом устройстве нет НИ ОДНОГО аудиофайла.")
    info("  Возможно, диктофон не работает или память не читается.")
    print("\n" + "=" * 60)
    print("  ДИАГНОСТИКА ЗАВЕРШЕНА (аудио не найдены)")
    print("=" * 60)
    exit()

# ═══════════════════════════════════════
# ЧАСТЬ 4: ПОКАЗАТЬ ВСЕ ФАЙЛЫ И ПАПКИ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 4: ВСЕ НАЙДЕННЫЕ АУДИОФАЙЛЫ")
print("=" * 60)

# Сортируем по времени (новые сверху)
all_audio.sort(key=lambda x: x["mtime"], reverse=True)

# Уникальные папки
folders = {}
for a in all_audio:
    f = a["folder"]
    if f not in folders:
        folders[f] = 0
    folders[f] += 1

info(f"Уникальных папок с аудио: {len(folders)}")
for folder, count in sorted(folders.items()):
    print(f"  📁 {folder}/ ({count} файлов)")

# Показываем 15 самых свежих
print(f"\n  Самые свежие файлы (топ-15):")
now = time.time()
for i, a in enumerate(all_audio[:15], 1):
    minutes_ago = int((now - a["mtime"]) / 60)
    hours_ago = minutes_ago // 60
    size_kb = a["size"] / 1024
    time_str = f"{minutes_ago} мин назад" if minutes_ago < 120 else f"{hours_ago} ч назад"
    print(f"  [{i}] {a['name']}")
    print(f"      Папка: {a['folder']}/")
    print(f"      Время: {time_str}, Размер: {size_kb:.1f} КБ")

# Самый свежий
latest = all_audio[0]
info(f"\n  САМЫЙ СВЕЖИЙ: {latest['name']}")
info(f"  Папка: {latest['folder']}/")
info(f"  Время: {int((now - latest['mtime']) / 60)} мин назад")

# ═══════════════════════════════════════
# ЧАСТЬ 5: ПРОВЕРКА ПРАВ ДОСТУПА
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 5: ПРАВА ДОСТУПА")
print("=" * 60)

# Проверяем права на папку самого свежего файла
test_folder = latest["folder"]
info(f"Проверяю права на: {test_folder}/")

# Можем ли читать?
try:
    files_in_folder = os.listdir(test_folder)
    ok(f"Чтение разрешено ({len(files_in_folder)} файлов)")
except PermissionError:
    fail(f"Чтение ЗАПРЕЩЕНО! Нет прав на {test_folder}/")
except Exception as e:
    fail(f"Ошибка чтения: {str(e)[:50]}")

# Можем ли копировать?
try:
    test_src = latest["path"]
    test_dst = "/storage/emulated/0/Recordings/_diag_test." + latest["name"].split(".")[-1]
    with open(test_src, "rb") as fsrc:
        data = fsrc.read()
    with open(test_dst, "wb") as fdst:
        fdst.write(data)
    os.remove(test_dst)
    ok("Копирование работает")
except Exception as e:
    fail(f"Копирование НЕ работает: {str(e)[:50]}")

# Проверяем доступ к /storage/emulated/0/
info("Проверка доступа к корню хранилища:")
try:
    root_files = os.listdir("/storage/emulated/0/")
    ok(f"Доступ к /storage/emulated/0/ есть ({len(root_files)} папок/файлов)")
except:
    fail("Доступ к /storage/emulated/0/ ЗАПРЕЩЁН!")

# ═══════════════════════════════════════
# ЧАСТЬ 6: ОБНОВЛЕНИЕ CONFIG.PY
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ЧАСТЬ 6: ОБНОВЛЕНИЕ CONFIG.PY")
print("=" * 60)

recorder_folder = latest["folder"]
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
        ok(f"config.py уже содержит правильный путь" if recorder_folder in content else "config.py НЕ обновлён")
else:
    fail("config.py не найден")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("  ИТОГ ДИАГНОСТИКИ")
print("=" * 60)
print(f"  Устройство: {model if 'model' in dir() else '?'}")
print(f"  Аудиофайлов всего: {len(all_audio)}")
print(f"  Папка диктофона: {recorder_folder}/")
print(f"  Проблем: {len(problems)}")
if problems:
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ Все проверки пройдены.")
print("=" * 60)
print()
print("  Отправьте этот лог разработчику + в чат с ИИ.")
print("  В чате ИИ включите режим «Поиск + Рассуждение».")
print("  Добавьте: «P.S. Загугли и составь отчёт: в чём проблема с диктофоном на этом устройстве?»")
