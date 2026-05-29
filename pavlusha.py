# pavlusha.py — Публичный фаст-ран для тестирования бэкендов
# Запускай на телефоне друга для проверки связи, библиотек, путей

import sys, os, subprocess

print("=" * 60)
print("  PAVLUSHA — ТЕСТ БЭКЕНДОВ")
print("=" * 60)

# 1. Python
print(f"\n[1] Python: {sys.version}")

# 2. requests
print("\n[2] Библиотека requests:")
try:
    import requests
    print("  ✅ Установлена")
except ImportError:
    print("  ❌ НЕ установлена. Пробую поставить...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-i", "https://mirrors.aliyun.com/pypi/simple/", "-q"])
        import requests
        print("  ✅ Установлена (через зеркало)")
    except:
        print("  ❌ Не удалось установить")

# 3. Интернет
print("\n[3] Интернет:")
try:
    r = requests.get("https://google.com", timeout=5)
    print(f"  ✅ Google: {r.status_code}")
except:
    print("  ❌ Google недоступен")

# 4. GitHub
print("\n[4] GitHub:")
try:
    r = requests.get("https://github.com", timeout=5)
    print(f"  ✅ GitHub: {r.status_code}")
except:
    print("  ❌ GitHub недоступен")

# 5. PyPI
print("\n[5] PyPI (пакеты Python):")
try:
    r = requests.get("https://pypi.org", timeout=5)
    print(f"  ✅ PyPI: {r.status_code}")
except:
    print("  ❌ PyPI недоступен (зеркало может помочь)")

# 6. VPS
print("\n[6] VPS (Whisper):")
try:
    r = requests.get("http://157.22.202.232:5000/", timeout=5)
    print(f"  ✅ VPS: {r.status_code}")
except:
    print("  ❌ VPS недоступен")

# 7. Папки
print("\n[7] Папки:")
for path in [
    "/storage/emulated/0/Recordings/",
    "/storage/emulated/0/Download/",
    "/storage/emulated/0/MIUI/sound_recorder/",
]:
    exists = os.path.exists(path)
    print(f"  {'✅' if exists else '❌'} {path}")

# 8. Аудиофайлы
print("\n[8] Аудиофайлы в Recordings:")
rec = "/storage/emulated/0/Recordings/"
if os.path.exists(rec):
    audio = [f for f in os.listdir(rec) if f.endswith((".m4a", ".mp3", ".aac"))]
    print(f"  Найдено: {len(audio)}")
    for a in audio[:5]:
        print(f"    {a}")
else:
    print("  Папка не существует")

print("\n" + "=" * 60)
print("  ГОТОВО. Отправь этот вывод разработчику.")
print("=" * 60)
