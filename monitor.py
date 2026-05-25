# monitor.py — Фоновый мониторинг папки Recordings (с логами)
# Без меню. Без ввода. Только цикл обработки.
# Запускается через MacroDroid при разблокировке экрана.

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, "/storage/emulated/0/VoiceAgent")

from main import process_new_files, show_summary

LOG_FILE = "/storage/emulated/0/VoiceAgent/monitor.log"
MAX_LOG_LINES = 500  # чтобы не раздувался

def log(msg):
    """Добавляет запись в лог-файл с временной меткой."""
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        # Обрезаем лог если слишком большой
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > MAX_LOG_LINES:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-MAX_LOG_LINES:])
    except:
        pass  # молча пропускаем ошибки записи лога

log("Фоновый мониторинг запущен")

print("=" * 50)
print("🟢 ФОНОВЫЙ МОНИТОРИНГ ЗАПУЩЕН")
print("=" * 50)

while True:
    try:
        processed, to_calendar, to_confirm, to_raw = process_new_files()
        if processed > 0:
            show_summary(processed, to_calendar, to_confirm, to_raw)
            log(f"Обработано: {processed} (календарь={to_calendar}, подтверждение={to_confirm}, сырые={to_raw})")
    except Exception as e:
        print(f"⚠️ Ошибка мониторинга: {e}")
        log(f"ОШИБКА: {e}")
    
    time.sleep(3)