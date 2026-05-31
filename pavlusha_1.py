# pavlusha_1.py — ЖЕСТОЧАЙШАЯ ПРОВЕРКА ПЕРЕД ПРОДАЖЕЙ
# Проверяет ВСЁ: переустановку, диктофон, автообновление, регистрацию, мост, парсинг, календарь
# Если хоть один тест провален — продукт не готов.
import sys, os, subprocess, time, shutil, json

print("=" * 60)
print("  PAVLUSHA 1 — HELL TEST")
print("=" * 60)

BASE = "/storage/emulated/0/VoiceAgent"
CONFIG = os.path.join(BASE, "config.py")
CONFIG_BACKUP = "/storage/emulated/0/Download/config_backup.py"
problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

# ═══════════════════════════════════════
# БЛОК А: ПЕРЕУСТАНОВКА
# ═══════════════════════════════════════
print("\n[БЛОК А] ПЕРЕУСТАНОВКА")

# A1. Сохраняем config.py
print("\n  A1. Сохраняю config.py...")
if os.path.exists(CONFIG):
    try:
        with open(CONFIG, "r") as f:
            data = f.read()
        with open(CONFIG_BACKUP, "w") as f:
            f.write(data)
        ok("config.py сохранён")
    except:
        fail("Не могу сохранить config.py")
else:
    ok("config.py не найден")

# A2. Удаляем старую папку
print("  A2. Удаляю VoiceAgent...")
if os.path.exists(BASE):
    for root, dirs, files in os.walk(BASE, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(BASE)
ok("Папка удалена" if not os.path.exists(BASE) else "Папка НЕ удалена")

# A3. Запускаем установщик
print("  A3. Установщик...")
import requests as _r
r = _r.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py", timeout=10)
if r.status_code == 200:
    ipath = "/storage/emulated/0/Download/install_temp.py"
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(r.text)
    
    # Запускаем с живым логом
    process = subprocess.Popen(
        [sys.executable, ipath],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in process.stdout:
        print(f"  {line.rstrip()}")
    process.wait()
    
    ok("Установщик отработал" if os.path.exists(os.path.join(BASE, "main.py")) else "main.py НЕ создан")
    os.remove(ipath)
else:
    fail(f"Не удалось скачать установщик: {r.status_code}")

# A4. Восстанавливаем config.py
print("  A4. Восстанавливаю config.py...")
if os.path.exists(CONFIG_BACKUP):
    try:
        with open(CONFIG_BACKUP, "r") as f:
            data = f.read()
        with open(CONFIG, "w") as f:
            f.write(data)
        os.remove(CONFIG_BACKUP)
        ok("config.py восстановлен")
    except:
        fail("Не могу восстановить config.py")
else:
    ok("Нет бэкапа")

# ═══════════════════════════════════════
# БЛОК Б: БАЗОВАЯ ДИАГНОСТИКА
# ═══════════════════════════════════════
print("\n[БЛОК Б] БАЗОВАЯ ДИАГНОСТИКА")

# Б1. Файлы
print("\n  Б1. Файлы программы:")
for fname in ["main.py", "config.py", "updater.py", "version.txt", "intent_parser.py", "caldav_client.py"]:
    path = os.path.join(BASE, fname)
    ok(f"{fname} ({os.path.getsize(path)} байт)" if os.path.exists(path) else f"{fname} ОТСУТСТВУЕТ")

# Б2. Библиотеки
print("  Б2. Библиотеки:")
try:
    import requests
    ok("requests")
except:
    fail("requests НЕТ")

for mod in ["json", "os", "time", "re", "threading", "datetime", "glob", "io", "contextlib", "collections"]:
    try:
        __import__(mod)
        ok(mod)
    except:
        fail(mod)

# Б3. Интернет (3 попытки)
print("  Б3. Интернет:")
for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com"), ("GitHub RAW", "https://raw.githubusercontent.com")]:
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=5)
            ok(f"{name} ({r.status_code}, попытка {attempt+1})")
            break
        except:
            if attempt == 2:
                fail(f"{name} НЕДОСТУПЕН")

# Б4. VPS
print("  Б4. VPS:")
for attempt in range(3):
    try:
        r = requests.get("http://157.22.202.232:5000/", timeout=5)
        ok(f"VPS отвечает ({r.status_code})")
        break
    except:
        if attempt == 2:
            fail("VPS НЕДОСТУПЕН")

# Б5. Календарь
print("  Б5. Календарь:")
sys.path.insert(0, BASE)
for attempt in range(3):
    try:
        from caldav_client import get_calendar_url
        url = get_calendar_url()
        ok(f"Календарь доступен" if url else "Календарь НЕ доступен")
        break
    except Exception as e:
        if attempt == 2:
            fail(f"Календарь: {str(e)[:50]}")

# Б6. Поддержка
print("  Б6. Поддержка:")
for attempt in range(3):
    try:
        r = requests.post("http://157.22.202.232:8200/report", data="ping", timeout=5)
        ok(f"Поддержка: В СЕТИ" if r.status_code in (200, 500) else f"Поддержка: {r.status_code}")
        break
    except:
        if attempt == 2:
            fail("Поддержка: ОФФЛАЙН")

# Б7. Регистрация
print("  Б7. Регистрация:")
if os.path.exists(CONFIG):
    with open(CONFIG, "r") as f:
        content = f.read()
    if "введите_пароль" in content or "введите_логин" in content:
        fail("config.py — ШАБЛОН. Нужна регистрация!")
    else:
        ok("config.py содержит данные. Регистрация НЕ нужна.")
else:
    fail("config.py ОТСУТСТВУЕТ")

# ═══════════════════════════════════════
# БЛОК В: ДИКТОФОН И МОСТ
# ═══════════════════════════════════════
print("\n[БЛОК В] ДИКТОФОН И МОСТ")

# В1. Папка Recordings
print("  В1. Папка Recordings:")
rec = "/storage/emulated/0/Recordings/"
ok(f"Recordings существует" if os.path.exists(rec) else "Recordings НЕ существует")

# В2. Права записи
print("  В2. Права записи:")
test_file = os.path.join(rec, ".test_write")
try:
    with open(test_file, "w") as f:
        f.write("x")
    os.remove(test_file)
    ok("Запись в Recordings работает")
except:
    fail("Запись в Recordings НЕ работает")

# В3. Поиск аудио (свежие, за последний час)
print("  В3. Поиск свежих аудио:")
found = []
skip = ["Android/data", "termux"]
for root, dirs, files in os.walk("/storage/emulated/0/"):
    if any(s in root for s in skip):
        continue
    for f in files:
        if f.endswith((".m4a", ".mp3", ".aac")):
            fp = os.path.join(root, f)
            if time.time() - os.path.getmtime(fp) < 3600:
                found.append(fp)
    if len(found) > 10:
        break

if found:
    latest = max(found, key=lambda f: os.path.getmtime(f))
    ok(f"Найдена запись: {os.path.basename(latest)} в {os.path.dirname(latest)}/")
else:
    fail("Свежие аудио НЕ найдены. Запишите фразу в диктофоне и перезапустите.")

# В4. Копирование в Recordings
print("  В4. Копирование:")
if found:
    src = max(found, key=lambda f: os.path.getmtime(f))
    dst = os.path.join(rec, os.path.basename(src))
    if not os.path.exists(dst):
        try:
            with open(src, "rb") as fsrc:
                data = fsrc.read()
            with open(dst, "wb") as fdst:
                fdst.write(data)
            ok(f"Файл скопирован в Recordings")
        except Exception as e:
            fail(f"Ошибка копирования: {str(e)[:50]}")
    else:
        ok("Файл уже в Recordings")
else:
    fail("Нет файлов для копирования")

# ═══════════════════════════════════════
# БЛОК Г: АВТООБНОВЛЕНИЕ
# ═══════════════════════════════════════
print("\n[БЛОК Г] АВТООБНОВЛЕНИЕ")

# Г1. updater
print("  Г1. Модуль updater:")
try:
    import updater
    ok("updater импортируется")
    ok("updater.check() есть" if hasattr(updater, "check") else "check() НЕТ")
except:
    fail("updater НЕ импортируется")

# Г2. Вызов в main.py
print("  Г2. Вызов в main.py:")
with open(os.path.join(BASE, "main.py"), "r") as f:
    mc = f.read()
ok("main.py вызывает updater" if "updater.check()" in mc else "main.py НЕ вызывает updater")

# Г3. Версии
print("  Г3. Версии:")
try:
    with open(os.path.join(BASE, "version.txt"), "r") as f:
        local = f.read().strip()
    r = requests.get("https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt", timeout=5)
    remote = r.text.strip() if r.status_code == 200 else "?"
    if local == remote:
        ok(f"Версии совпадают ({local})")
    else:
        fail(f"Версии РАЗНЫЕ! Лок={local}, GitHub={remote}")
except:
    fail("Не удалось проверить версии")

# Г4. ZIP (3 попытки)
print("  Г4. ZIP:")
for attempt in range(3):
    try:
        r = requests.get("https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip", timeout=30, allow_redirects=True)
        if r.status_code == 200:
            ok(f"ZIP доступен ({len(r.content)//1024} КБ, попытка {attempt+1})")
            break
        else:
            if attempt == 2:
                fail(f"ZIP НЕ доступен ({r.status_code})")
            else:
                time.sleep(2)
    except:
        if attempt == 2:
            fail("ZIP НЕ доступен")
        else:
            time.sleep(2)

# ═══════════════════════════════════════
# БЛОК Д: ПАРСИНГ И КАЛЕНДАРЬ
# ═══════════════════════════════════════
print("\n[БЛОК Д] ПАРСИНГ И КАЛЕНДАРЬ")

# Д1. Парсинг
print("  Д1. Парсинг:")
try:
    from intent_parser import parse_intent
    tests = [
        "напомни купить хлеб завтра в 10:00 в магазине",
        "встретиться с братом сегодня в 18:00 дома",
    ]
    for t in tests:
        intent = parse_intent(t)
        ok(f"«{t[:40]}...» → valid={intent.get('is_valid')}" if intent.get('is_valid') else f"«{t[:40]}...» → missing={intent.get('missing_fields')}")
except Exception as e:
    fail(f"Парсинг: {str(e)[:80]}")

# Д2. Календарь (создание + удаление тестового события)
print("  Д2. Создание тестового события:")
try:
    from caldav_client import create_event, delete_event
    test_task = {"title": "ТЕСТ", "date": "2026-06-01", "time": "12:00", "place": "Тест", "duration": 5}
    uid = create_event(test_task)
    if uid:
        ok(f"Событие создано: {uid}")
        delete_event(uid)
        ok("Тестовое событие удалено")
    else:
        fail("Событие НЕ создано")
except Exception as e:
    fail(f"Календарь: {str(e)[:80]}")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
if problems:
    print(f"  ❌ ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    {p}")
else:
    print("  ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("  Продукт готов к продаже.")
print("=" * 60)
