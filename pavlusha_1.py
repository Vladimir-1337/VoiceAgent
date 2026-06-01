# pavlusha_1.py — ПОИСК ПАПКИ ДИКТОФОНА (специализированный)
# Только один блок: найти, куда телефон сохраняет аудиозаписи.
# Запусти после того как запишешь фразу в диктофон.
import sys, os, time

print("=" * 60)
print("  PAVLUSHA 1 — ПОИСК ДИКТОФОНА")
print("=" * 60)

problems = []

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg):
    problems.append(msg)
    print(f"  ❌ {msg}")

# ═══════════════════════════════════════
# ШАГ 1: ПРОВЕРКА ЗАПИСИ
# ═══════════════════════════════════════
print("\n[1/4] Проверяю, есть ли свежая запись...")
print("  (Если вы ещё не записали фразу в диктофон — сделайте это сейчас)")
print("  (Потом перезапустите этот тест)")
print()

# Все возможные расширения
AUDIO_EXTS = (
    ".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac",
    ".3gp", ".m4b", ".m4p", ".m4r", ".mp2", ".mpga", ".oga", ".opus",
    ".ra", ".rm", ".wv", ".webm", ".aiff", ".aif", ".aifc", ".au",
    ".caf", ".gsm", ".mka", ".mmf", ".snd", ".voc", ".vox", ".8svx"
)

# Ищем по ВСЕМУ хранилищу, исключая только явный мусор
found_all = []
skip_keywords = ["cache", ".thumbnails", "termux-app-master", "com.google.", "com.android."]

print("  Сканирую хранилище...")
for root, dirs, files in os.walk("/storage/emulated/0/"):
    # Пропускаем только кэш и исходники
    dir_lower = root.lower()
    if any(s in dir_lower for s in skip_keywords):
        continue
    
    for f in files:
        f_lower = f.lower()
        if any(f_lower.endswith(ext) for ext in AUDIO_EXTS):
            full_path = os.path.join(root, f)
            file_time = os.path.getmtime(full_path)
            file_size = os.path.getsize(full_path)
            found_all.append((full_path, file_time, file_size))
    
    # Ограничиваем глубину
    if len(found_all) > 100:
        break

ok(f"Всего найдено аудиофайлов: {len(found_all)}")

# ═══════════════════════════════════════
# ШАГ 2: ФИЛЬТР — ТОЛЬКО СВЕЖИЕ (за последние 30 минут)
# ═══════════════════════════════════════
print(f"\n[2/4] Фильтрую свежие (за последние 30 минут)...")
now = time.time()
fresh = [(p, t, s) for p, t, s in found_all if now - t < 1800]  # 30 минут

if fresh:
    ok(f"Свежих файлов: {len(fresh)}")
else:
    fail(f"Свежих файлов НЕТ")
    print()
    print("  Возможные причины:")
    print("    1. Вы не записали фразу в диктофон перед запуском")
    print("    2. Диктофон сохраняет в скрытую папку")
    print("    3. Формат файла не поддерживается")
    print()
    print("  ЧТО ДЕЛАТЬ:")
    print("    1. Откройте обычный Диктофон на телефоне")
    print("    2. Запишите короткую фразу (например «тест»)")
    print("    3. НЕ закрывая этот тест, перезапустите его")
    print("    4. Если всё равно не находит — смотрите Шаг 4 ниже")
    print()
    print("=" * 60)
    print("  ❌ ТЕСТ ОСТАНОВЛЕН. Запишите фразу и перезапустите.")
    print("=" * 60)
    exit()

# ═══════════════════════════════════════
# ШАГ 3: ПОКАЗАТЬ ВСЕ СВЕЖИЕ ФАЙЛЫ
# ═══════════════════════════════════════
print(f"\n[3/4] Свежие аудиофайлы:")
fresh.sort(key=lambda x: x[1], reverse=True)  # Сортируем по времени (новые сверху)

for i, (path, ftime, fsize) in enumerate(fresh[:10], 1):
    folder = os.path.dirname(path)
    fname = os.path.basename(path)
    minutes_ago = int((now - ftime) / 60)
    size_kb = fsize / 1024
    print(f"  [{i}] {fname}")
    print(f"      Папка: {folder}/")
    print(f"      {minutes_ago} мин назад, {size_kb:.1f} КБ")

# Определяем папку самого свежего файла
latest = fresh[0]
recorder_folder = os.path.dirname(latest[0])
print(f"\n  ✅ Папка диктофона: {recorder_folder}/")
print(f"     Файл: {os.path.basename(latest[0])}")

# ═══════════════════════════════════════
# ШАГ 4: ЕСЛИ НЕ НАШЛОСЬ — ПОМОЩЬ
# ═══════════════════════════════════════
print(f"\n[4/4] Проверка config.py...")
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
        ok(f"config.py уже содержит: {recorder_folder}/" if recorder_folder in content else "config.py НЕ обновлён (старая версия?)")
else:
    fail("config.py не найден")

# ═══════════════════════════════════════
# ИТОГ
# ═══════════════════════════════════════
print("\n" + "=" * 60)
if problems:
    print(f"  ПРОБЛЕМ: {len(problems)}")
    for p in problems:
        print(f"    {p}")
else:
    print(f"  ✅ Папка диктофона найдена: {recorder_folder}/")
    print(f"  config.py обновлён.")
    print(f"  Отправьте этот лог разработчику.")
print("=" * 60)
