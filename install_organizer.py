# install_organizer.py - УСТАНОВЩИК ОРГАНАЙЗЕРА (для чайников)
# ЧТО ДЕЛАТЬ: открой этот файл в Pydroid и нажми Run ▶
# ОН САМ всё скачает, распакует и установит. Ты просто жди.
# После установки открой main.py в папке VoiceAgent и нажми Run.

import requests, os, zipfile, shutil, sys, subprocess

print("=" * 60)
print("  УСТАНОВЩИК ОРГАНАЙЗЕРА")
print("  Сейчас программа сама всё установит. Просто жди.")
print("=" * 60)

# Куда всё установится
TARGET_DIR = "/storage/emulated/0/VoiceAgent"
# Откуда скачиваем
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"

# -------------------------------------------------------
# ШАГ 1 из 6: проверяем, что есть библиотека requests
# Она нужна чтобы скачивать файлы из интернета
# -------------------------------------------------------
print("\n[1/6] Проверяю библиотеки (нужны для скачивания)...")
try:
    import requests
    print("  OK - всё на месте")
except ImportError:
    print("  Скачиваю недостающую библиотеку...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests
    print("  OK - библиотека установлена")

# -------------------------------------------------------
# ШАГ 2 из 6: проверяем интернет
# -------------------------------------------------------
print("\n[2/6] Проверяю интернет (нужен для скачивания)...")
try:
    requests.get("https://github.com", timeout=5)
    print("  OK - интернет работает")
except:
    print("  ОШИБКА: Нет интернета.")
    print("  Включите Wi-Fi или мобильные данные и перезапустите программу.")
    input("\nНажмите Enter чтобы выйти...")
    exit()

# -------------------------------------------------------
# ШАГ 3 из 6: скачиваем архив с программой
# -------------------------------------------------------
print("\n[3/6] Скачиваю архив с программой...")
print("  Это как скачать файл из интернета, только автоматически.")
zip_path = "/storage/emulated/0/Download/VoiceAgent_install.zip"
r = requests.get(GITHUB_URL)
with open(zip_path, "wb") as f:
    f.write(r.content)
print(f"  OK - скачано {len(r.content)//1024} КБ (размер архива)")

# -------------------------------------------------------
# ШАГ 4 из 6: распаковываем архив
# -------------------------------------------------------
print("\n[4/6] Распаковываю архив...")
print("  Это как открыть ZIP-файл на телефоне, только автоматически.")
tmp_dir = "/storage/emulated/0/Download/VoiceAgent_tmp/"
with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(tmp_dir)
print("  OK - архив распакован")

# -------------------------------------------------------
# ШАГ 5 из 6: копируем файлы в нужную папку
# -------------------------------------------------------
print("\n[5/6] Устанавливаю файлы в папку VoiceAgent...")
print("  Копирую все файлы программы в нужное место.")
os.makedirs(TARGET_DIR, exist_ok=True)

# Если у вас уже был config.py с настройками - сохраняем его
old_config = os.path.join(TARGET_DIR, "config.py")
backup = None
if os.path.exists(old_config):
    print("  Нашёл ваш старый config.py - сохраняю ваши настройки.")
    with open(old_config, "r") as f:
        backup = f.read()

# Копируем все файлы программы
for root, dirs, files in os.walk(tmp_dir):
    for fname in files:
        if fname.endswith((".py", ".json", ".txt", ".md")):
            src = os.path.join(root, fname)
            dst = os.path.join(TARGET_DIR, fname)
            # Не перезаписываем настройки пользователя
            if fname == "config.py" and backup:
                continue
            shutil.copy2(src, dst)

# Восстанавливаем настройки пользователя
if backup:
    with open(old_config, "w") as f:
        f.write(backup)
    print("  Ваши настройки сохранены.")

# Создаём вспомогательный файл для совместимости
vcp = os.path.join(TARGET_DIR, "voice_config.py")
if not os.path.exists(vcp):
    with open(vcp, "w") as f:
        f.write("# voice_config.py - вспомогательный файл\nfrom config import *\n")

# Создаём папку для аудиозаписей
os.makedirs("/storage/emulated/0/Recordings/", exist_ok=True)
print("  OK - все файлы на своих местах")

# -------------------------------------------------------
# ШАГ 6 из 6: убираем временные файлы
# -------------------------------------------------------
print("\n[6/6] Убираю временные файлы...")
print("  Удаляю то, что уже не нужно (архив и временную папку).")
shutil.rmtree(tmp_dir, ignore_errors=True)
os.remove(zip_path)
print("  OK - чисто")

# -------------------------------------------------------
# ГОТОВО!
# -------------------------------------------------------
print(f"\n{'='*60}")
print("  ОРГАНАЙЗЕР УСТАНОВЛЕН!")
print(f"\n  Что делать дальше:")
print(f"  1. Откройте Pydroid")
print(f"  2. Нажмите на иконку папки (Открыть)")
print(f"  3. Зайдите в папку VoiceAgent")
print(f"  4. Выберите файл main.py")
print(f"  5. Нажмите Run (треугольник внизу)")
print(f"\n  При первом запуске программа попросит ввести")
print(f"  логин и пароль приложения Яндекс.Календарь.")
print(f"  Это нужно для выгрузки задач в ваш календарь.")
print(f"{'='*60}")
input("\nНажмите Enter чтобы выйти...")
