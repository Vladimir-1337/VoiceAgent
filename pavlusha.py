# pavlusha.py — ПОЛНЫЙ ТЕСТ РАБОТОСПОСОБНОСТИ ОРГАНАЙЗЕРА
# Запусти в Pydroid. Он проверит ВСЁ под капотом.
# Никаких других файлов запускать не нужно.

import sys, os, subprocess, shutil

print("=" * 60)
print("  PAVLUSHA — ПОЛНЫЙ ТЕСТ ОРГАНАЙЗЕРА")
print("=" * 60)

problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    print(f"  ❌ {msg}")
    problems.append(msg)

# ═══════════════════════════════════════
# 1. Python и библиотеки
# ═══════════════════════════════════════
print("\n[1] Python и библиотеки:")
ok(f"Python {sys.version}")

try:
    import requests
    ok("requests установлена")
except ImportError:
    fail("requests HE установлена")
    print("  Пробую Яндекс-зеркало...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q", "--no-deps"], timeout=60)
        import requests
        ok("requests установлена через зеркало")
    except:
        fail("ВСЕ способы установки провалились")

# ═══════════════════════════════════════
# 2. Интернет и сервера
# ═══════════════════════════════════════
print("\n[2] Интернет и сервера:")
try:
    r = requests.get("https://google.com", timeout=5)
    ok(f"Google: {r.status_code}")
except:
    fail("Google недоступен")

try:
    r = requests.get("https://github.com", timeout=5)
    ok(f"GitHub: {r.status_code}")
except:
    fail("GitHub недоступен")

try:
    r = requests.get("http://157.22.202.232:5000/", timeout=5)
    ok(f"VPS (Whisper): {r.status_code}")
except:
    fail("VPS недоступен")

# ═══════════════════════════════════════
# 3. Папки программы
# ═══════════════════════════════════════
print("\n[3] Папки программы:")
base = "/storage/emulated/0/VoiceAgent"
rec = "/storage/emulated/0/Recordings"

for path, name in [(base, "VoiceAgent"), (rec, "Recordings")]:
    if os.path.exists(path):
        ok(f"Папка {name} существует")
    else:
        fail(f"Папка {name} HE существует")
        os.makedirs(path, exist_ok=True)
        if os.path.exists(path):
            ok(f"Папка {name} создана")
        else:
            fail(f"Папка {name} HE создалась")

# ═══════════════════════════════════════
# 4. Критичные файлы программы
# ═══════════════════════════════════════
print("\n[4] Файлы программы:")
critical = ["main.py", "config.py", "voice_config.py", "intent_parser.py"]
for fname in critical:
    path = os.path.join(base, fname)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{fname} ({size} байт)")
    else:
        fail(f"{fname} ОТСУТСТВУЕТ")

# ═══════════════════════════════════════
# 5. Поиск аудиозаписей диктофона
# ═══════════════════════════════════════
print("\n[5] Поиск аудиозаписей диктофона:")
user_dirs = [
    "/storage/emulated/0/Recordings/",
    "/storage/emulated/0/Download/",
    "/storage/emulated/0/DCIM/",
    "/storage/emulated/0/Music/",
    "/storage/emulated/0/Recorder/",
    "/storage/emulated/0/Sounds/",
    "/storage/emulated/0/Voice Recorder/",
    "/storage/emulated/0/MIUI/sound_recorder/",
]

found_audio = []
for d in user_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith((".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg")):
                found_audio.append(os.path.join(d, f))

if found_audio:
    ok(f"Найдено аудио: {len(found_audio)} файлов")
    dirs = set(os.path.dirname(f) for f in found_audio)
    for d in dirs:
        count = sum(1 for f in found_audio if os.path.dirname(f) == d)
        print(f"     📁 {d} ({count} файлов)")
else:
    fail("Аудиофайлы не найдены. СДЕЛАЙТЕ ЗАПИСЬ В ДИКТОФОНЕ И ПЕРЕЗАПУСТИТЕ ТЕСТ.")
    print("\n" + "=" * 60)
    print("  ТЕСТ ОСТАНОВЛЕН. Сделайте запись в диктофоне и перезапустите.")
    print("=" * 60)
    exit()

# ═══════════════════════════════════════
# 6. ТЕСТ МОСТА: копирование в Recordings
# ═══════════════════════════════════════
print("\n[6] Тест моста (копирование аудио в Recordings):")

# Находим самый свежий аудиофайл
latest_file = max(found_audio, key=lambda f: os.path.getmtime(f))
latest_name = os.path.basename(latest_file)
ok(f"Самый свежий файл: {latest_name}")

# Копируем в Recordings
dest = os.path.join(rec, latest_name)
if not os.path.exists(dest):
    with open(latest_file, 'rb') as fsrc:\n    with open(dest, 'wb') as fdst:\n        fdst.write(fsrc.read())
    ok(f"Файл скопирован в Recordings: {latest_name}")
else:
    ok(f"Файл уже в Recordings: {latest_name}")

# Проверяем размер
src_size = os.path.getsize(latest_file)
dst_size = os.path.getsize(dest)
if src_size == dst_size:
    ok(f"Размер совпадает: {src_size} байт")
else:
    fail(f"Размеры различаются! Источник: {src_size}, копия: {dst_size}")

# ═══════════════════════════════════════
# 7. ТЕСТ ИМПОРТА МОДУЛЕЙ ПРОГРАММЫ
# ═══════════════════════════════════════
print("\n[7] Тест модулей программы:")
sys.path.insert(0, base)

modules = [
    ("config", "config"),
    ("intent_parser", "intent_parser"),
    ("task_data", "task_data"),
    ("caldav_client", "caldav_client"),
    ("profile", "profile"),
]

for mod_name, file_name in modules:
    try:
        __import__(mod_name)
        ok(f"Модуль {file_name} импортируется")
    except Exception as e:
        fail(f"Модуль {file_name}: {str(e)[:80]}")

# ═══════════════════════════════════════
# 8. ТЕСТ ПАРСИНГА (сердце программы)
# ═══════════════════════════════════════
print("\n[8] Тест парсинга (сердце программы):")
try:
    from intent_parser import parse_intent
    
    test_phrases = [
        "напомни купить хлеб завтра в 10:00 в магазине",
        "встретиться с братом сегодня в 18:00 дома",
        "приказываю позвонить Вове в пятницу в 15:00 на складе",
    ]
    
    for phrase in test_phrases:
        intent = parse_intent(phrase)
        has_remind = intent.get("has_remind", False)
        is_valid = intent.get("is_valid", False)
        date_val = intent.get("date") or "—"
        time_val = intent.get("time") or "—"
        place_val = intent.get("place") or "—"
        title_val = intent.get("title") or "—"
        
        status = "✅" if is_valid else "⚠️"
        print(f"  {status} «{phrase[:50]}...»")
        print(f"     Напомни={has_remind}, Дата={date_val}, Время={time_val}")
        print(f"     Место={place_val}, Задача={title_val}")
        
        if not is_valid:
            print(f"     Не хватает: {intent.get('missing_fields', [])}")
    
    ok("Парсинг работает")
except Exception as e:
    fail(f"Парсинг: {str(e)[:80]}")

# ═══════════════════════════════════════
# 9. ТЕСТ КАЛЕНДАРЯ (если есть интернет)
# ═══════════════════════════════════════
print("\n[9] Тест календаря:")
try:
    from caldav_client import get_calendar_url
    url = get_calendar_url()
    if url:
        ok(f"Календарь доступен: {url[:50]}...")
    else:
        fail("Календарь HE доступен (проверьте пароль приложения)")
except Exception as e:
    fail(f"Календарь: {str(e)[:80]}")

# ═══════════════════════════════════════
# 10. ПАМЯТЬ И АNDROID
# ═══════════════════════════════════════
print("\n[10] Память и Android:")
stat = shutil.disk_usage("/storage/emulated/0")
free_gb = stat.free / (1024**3)
total_gb = stat.total / (1024**3)
ok(f"Память: свободно {free_gb:.1f} ГБ из {total_gb:.1f} ГБ")

try:
    sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    ok(f"Android {release} (SDK {sdk}), {model}")
except:
    fail("Не удалось определить Android")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
if problems:
    print(f"  НАЙДЕНО ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    ❌ {p}")
else:
    print("  ✅ ВСЕ 10 ТЕСТОВ ПРОЙДЕНЫ!")
    print("  Органайзер полностью работоспособен на этом телефоне.")
print("=" * 60)
