# pavlusha.py — ДИАГНОСТИКА ТЕЛЕФОНА ДЛЯ ОРГАНАЙЗЕРА
# Запусти в Pydroid и скопируй весь вывод разработчику

import sys, os, subprocess

print("=" * 60)
print("  ДИАГНОСТИКА ТЕЛЕФОНА ДЛЯ ОРГАНАЙЗЕРА")
print("=" * 60)

problems = []

def check(name, ok):
    if ok:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name}")
        problems.append(name)

# 1. Python
print("\n[1] Python:")
print(f"  Версия: {sys.version}")

# 2. requests
print("\n[2] Библиотека requests:")
try:
    import requests
    print("  ✅ Установлена")
except ImportError:
    print("  ❌ НЕ установлена. Пробую Яндекс-зеркало...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirror.yandex.ru/mirrors/pypi/simple/", "-q", "--no-deps"], timeout=60)
        import requests
        print("  ✅ Установлена через зеркало")
    except:
        print("  Пробую из локального файла...")
        whl = "/storage/emulated/0/Download/requests-2.32.3-py3-none-any.whl"
        if os.path.exists(whl):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", whl, "-q", "--no-deps"], timeout=60)
                import requests
                print("  ✅ Установлена из .whl")
            except:
                print("  ❌ ВСЕ СПОСОБЫ ПРОВАЛИЛИСЬ")
                problems.append("requests не установлена")

# 3. Интернет
print("\n[3] Интернет:")
for name, url in [("Google", "https://google.com"), ("GitHub", "https://github.com"), ("Яндекс", "https://yandex.ru")]:
    try:
        r = requests.get(url, timeout=5)
        print(f"  ✅ {name}: {r.status_code}")
    except:
        print(f"  ❌ {name}: НЕДОСТУПЕН")
        problems.append(f"{name} недоступен")

# 4. PyPI
print("\n[4] PyPI (установка библиотек):")
for name, url in [("Официальный PyPI", "https://pypi.org"), ("Яндекс-зеркало", "https://mirror.yandex.ru/mirrors/pypi/")]:
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
    print(f"  ✅ Отвечает: {r.status_code}")
except:
    print("  ❌ НЕДОСТУПЕН")
    problems.append("VPS недоступен")

# 6. Папки
print("\n[6] Папки:")
for name, path in [("Recordings", "/storage/emulated/0/Recordings/"), ("Download", "/storage/emulated/0/Download/"), ("VoiceAgent", "/storage/emulated/0/VoiceAgent/")]:
    print(f"  {'✅' if os.path.exists(path) else '❌'} {name}")
    if not os.path.exists(path):
        problems.append(f"Папка {name} не существует")

# 7. Поиск папки диктофона (только пользовательские папки)
print("\n[7] Поиск папки диктофона:")
user_dirs = [
    "/storage/emulated/0/Recordings/",
    "/storage/emulated/0/Download/",
    "/storage/emulated/0/DCIM/",
    "/storage/emulated/0/Music/",
    "/storage/emulated/0/Movies/",
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
    dirs = set(os.path.dirname(f) for f in found_audio)
    print(f"  Найдено: {len(found_audio)} файлов в {len(dirs)} папках")
    for d in dirs:
        count = sum(1 for f in found_audio if os.path.dirname(f) == d)
        print(f"  📁 {d} ({count} файлов)")
else:
    print("  Аудиофайлы не найдены. Сделайте запись в диктофоне и перезапустите.")
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
    sdk = subprocess.check_output(["getprop", "ro.build.version.sdk"]).decode().strip()
    release = subprocess.check_output(["getprop", "ro.build.version.release"]).decode().strip()
    model = subprocess.check_output(["getprop", "ro.product.model"]).decode().strip()
    print(f"  Версия: Android {release} (SDK {sdk}), модель: {model}")
except:
    print("  Не удалось определить")

# ИТОГ
print("\n" + "=" * 60)
if problems:
    print(f"  НАЙДЕНО ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    - {p}")
else:
    print("  ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
print("=" * 60)
