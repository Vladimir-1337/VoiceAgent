# pavlusha.py — ДИАГНОСТИКА ТЕЛЕФОНА ДЛЯ ОРГАНАЙЗЕРА
# ЗАПУСТИ ЭТОТ ФАЙЛ В PYDROID
# ПОСЛЕ ЗАВЕРШЕНИЯ СКОПИРУЙ ВЕСЬ ТЕКСТ (ЛОГ) И СЛЕДУЙ ИНСТРУКЦИИ В КОНЦЕ

import sys, os, subprocess

print("=" * 60)
print("  ДИАГНОСТИКА ТЕЛЕФОНА ДЛЯ ОРГАНАЙЗЕРА")
print("=" * 60)

problems = []

def check(name, ok, detail=""):
    if ok:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name} {detail}")
        problems.append(name)

# 1. Python
print("\n[1] Python:")
print(f"  Версия: {sys.version}")

# 2. requests
print("\n[2] Библиотека requests:")
try:
    import requests
    print("  ✅ requests установлена")
except ImportError:
    print("  ❌ requests HE установлена (нужна для работы)")
    problems.append("requests HE установлена")
    print("  Пробую установить через Яндекс-зеркало...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q", "--no-deps"], timeout=60)
        import requests
        print("  ✅ requests установлена через зеркало")
    except:
        print("  Пробую установить из локального файла...")
        whl = "/storage/emulated/0/Download/requests-2.32.3-py3-none-any.whl"
        if os.path.exists(whl):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", whl, "-q", "--no-deps"], timeout=60)
                import requests
                print("  ✅ requests установлена из .whl")
            except:
                print("  ❌ ВСЕ СПОСОБЫ ПРОВАЛИЛИСЬ (нужен VPN для установки)")
                problems.append("Все способы установки requests провалились")

# 3. Интернет
print("\n[3] Интернет:")
sites = [
    ("Google", "https://google.com"),
    ("GitHub", "https://github.com"),
    ("Яндекс", "https://yandex.ru"),
]
for name, url in sites:
    try:
        r = requests.get(url, timeout=5)
        print(f"  ✅ {name}: {r.status_code}")
    except:
        print(f"  ❌ {name}: НЕДОСТУПЕН")
        problems.append(f"{name} недоступен")

# 4. PyPI (пакеты Python)
print("\n[4] PyPI (установка библиотек):")
mirrors = [
    ("Официальный PyPI", "https://pypi.org"),
    ("Яндекс-зеркало", "https://mirror.yandex.ru/mirrors/pypi/"),
]
for name, url in mirrors:
    try:
        r = requests.get(url, timeout=5)
        print(f"  ✅ {name}: {r.status_code}")
    except:
        print(f"  ❌ {name}: НЕДОСТУПЕН")
        problems.append(f"{name} недоступен")

# 5. VPS
print("\n[5] Сервер программы (VPS):")
try:
    r = requests.get("http://157.22.202.232:5000/", timeout=5)
    print(f"  ✅ VPS отвечает: {r.status_code}")
except:
    print("  ❌ VPS НЕДОСТУПЕН (распознавание голоса не будет работать)")
    problems.append("VPS недоступен")

# 6. Папки
print("\n[6] Папки:")
folders = [
    ("Recordings", "/storage/emulated/0/Recordings/"),
    ("Download", "/storage/emulated/0/Download/"),
    ("VoiceAgent", "/storage/emulated/0/VoiceAgent/"),
]
for name, path in folders:
    exists = os.path.exists(path)
    print(f"  {'✅' if exists else '❌'} {name}")
    if not exists:
        problems.append(f"Папка {name} не существует")

# 7. Поиск папки диктофона
print("\n[7] Поиск папки диктофона:")
found_audio = []
for root, dirs, files in os.walk("/storage/emulated/0/"):
    for f in files:
        if f.endswith((".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg")):
            found_audio.append(os.path.join(root, f))
    if len(found_audio) > 30:
        break

if found_audio:
    dirs = set(os.path.dirname(f) for f in found_audio)
    print(f"  Найдено аудио: {len(found_audio)} файлов в {len(dirs)} папках")
    for d in dirs:
        count = sum(1 for f in found_audio if os.path.dirname(f) == d)
        print(f"  📁 {d} ({count} файлов)")
else:
    print("  Аудиофайлы не найдены.")
    print("  Сделайте запись в диктофоне и запустите тест снова.")
    problems.append("Аудиофайлы не найдены")

# 8. Память
print("\n[8] Память:")
import shutil
stat = shutil.disk_usage("/storage/emulated/0")
free_gb = stat.free / (1024**3)
total_gb = stat.total / (1024**3)
print(f"  Свободно: {free_gb:.1f} ГБ из {total_gb:.1f} ГБ")
if free_gb < 0.5:
    problems.append(f"Мало памяти: {free_gb:.1f} ГБ")

# 9. Android
print("\n[9] Android:")
try:
    import subprocess as sp
    sdk = sp.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
    release = sp.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    model = sp.check_output(["getprop", "ro.product.model"]).decode().strip()
    print(f"  Версия: Android {release} (SDK {sdk}), модель: {model}")
except:
    print("  Не удалось определить версию")

# ИТОГ
print("\n" + "=" * 60)
if problems:
    print(f"  НАЙДЕНО ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    - {p}")
else:
    print("  ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
print("=" * 60)

# ИНСТРУКЦИЯ ДЛЯ БЕТА-ТЕСТЕРА
print("""

╔══════════════════════════════════════════════════════╗
║  ЧТО ДЕЛАТЬ ДАЛЬШЕ:                                 ║
║                                                      ║
║  1. СКОПИРУЙ ВЕСЬ ТЕКСТ ВЫШЕ (весь лог)              ║
║  2. Открой чат с ИИ (ChatGPT/DeepSeek/Claude)        ║
║  3. Включи режим "Поиск + Рассуждение"               ║
║  4. Вставь скопированный лог                         ║
║  5. Добавь в конец:                                  ║
║     "P.S. Загугли и составь отчёт для разработчика   ║
║      в чём вероятнее всего может быть ошибка"        ║
║  6. Скопируй ответ ИИ                                ║
║  7. Отправь мне на почту:                            ║
║     vovagubanov147@gmail.com                         ║
║     В письме пришли:                                 ║
║     - Лог из Pydroid (текст выше)                    ║
║     - Ответ ИИ (полностью)                           ║
║                                                      ║
║  Тема письма: "Бета-тест Органайзер"                 ║
╚══════════════════════════════════════════════════════╝
""")
