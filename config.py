# config.py — Настройки Органайзера
# ЗАПОЛНИТЕ СВОИ ДАННЫЕ ПЕРЕД ЗАПУСКОМ

import sys
import os
sys.path.insert(0, "/storage/emulated/0/VoiceAgent")

# ========== БАЗОВЫЙ ПУТЬ ==========
BASE_DIR = "/storage/emulated/0/VoiceAgent"

# ========== ПУТИ К ФАЙЛАМ ==========
RECORDINGS_DIR = "/storage/emulated/0/Recordings/"
READY_FILE = os.path.join(BASE_DIR, "ready_tasks.json")
RAW_FILE = os.path.join(BASE_DIR, "raw_tasks.json")
SEEN_FILE = os.path.join(BASE_DIR, "seen_files.json")
PROFILE_FILE = os.path.join(BASE_DIR, "user_profile.json")
LOG_FILE = os.path.join(BASE_DIR, "monitor.log")
AUDIO_EXT = ".m4a"

# ========== СЕРВЕР ==========
SERVER_URL = "http://157.22.202.232:5000/voice"

# ========== ЯНДЕКС КАЛЕНДАРЬ ==========
# Впишите свои данные ниже
YANDEX_LOGIN = "введите_логин@yandex.ru"
YANDEX_APP_PASSWORD = "введите_пароль_приложения"
CALDAV_URL = "https://caldav.yandex.ru"

# ========== НАСТРОЙКИ УВЕДОМЛЕНИЙ ==========
DEFAULT_REMINDER_MINUTES = 0

# ========== РАСПОЗНАВАНИЕ ==========
SPEECH_LANGUAGE = "ru-RU"

# ========== ПРОЧИЕ НАСТРОЙКИ ==========
REQUEST_TIMEOUT = 30

# ========== ЯНДЕКС SEARCH API ==========
YANDEX_SEARCH_API_KEY = ""
YANDEX_FOLDER_ID = ""