# voice_sender.py — Отправка аудио на VPS
# Все настройки берутся из voice_config.py

import requests
import glob
import os
import struct

# Импортируем настройки из voice_config
from voice_config import SERVER_URL, RECORDINGS_DIR, REQUEST_TIMEOUT

# D.1: Максимальная длительность аудио в секундах (2 минуты)
MAX_AUDIO_DURATION = 120


def get_audio_duration(filepath):
    """
    Определяет длительность M4A/WAV/MP3 файла по заголовку.
    Возвращает длительность в секундах или 0 при ошибке.
    """
    try:
        size = os.path.getsize(filepath)
        with open(filepath, "rb") as f:
            header = f.read(12)
            if len(header) < 12:
                return 0

            # WAV: читаем заголовок RIFF
            if header[:4] == b"RIFF":
                f.seek(28)
                byte_rate_data = f.read(4)
                if len(byte_rate_data) == 4:
                    byte_rate = struct.unpack("<I", byte_rate_data)[0]
                    if byte_rate > 0:
                        return size / byte_rate

            # M4A/MP4: ищем moov/mdhd
            elif header[:4] == b"\x00\x00\x00" or b"ftyp" in header[:8]:
                f.seek(0)
                data = f.read()
                # Упрощённый поиск: берём размер файла / 16000 (типичный битрейт M4A)
                # Более точный метод требует парсинга moov-атома, что сложно
                estimated_duration = size / 16000
                return min(estimated_duration, 600)  # не больше 10 минут

            # Fallback: оценка по размеру файла (≈16 кбит/с для голоса)
            return size / 16000

    except Exception:
        return 0


def send_latest_recording():
    """
    Отправляет последний .m4a файл на VPS для распознавания.
    Возвращает (текст, ошибка).
    """
    m4a_files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    if not m4a_files:
        return None, "Нет файлов .m4a в папке Recordings"

    latest_file = max(m4a_files, key=os.path.getmtime)

    # D.1: Проверка длительности
    duration = get_audio_duration(latest_file)
    if duration > MAX_AUDIO_DURATION:
        return None, f"Слишком длинная запись ({duration:.0f} сек). Максимум {MAX_AUDIO_DURATION} сек."

    try:
        with open(latest_file, "rb") as f:
            response = requests.post(SERVER_URL, files={"audio": f}, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "")
            return text, None
        else:
            return None, f"Ошибка сервера: {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        return None, f"Таймаут ({REQUEST_TIMEOUT} сек) — VPS не отвечает"
    except requests.exceptions.ConnectionError:
        return None, "VPS недоступен. Проверь интернет или сервер."
    except Exception as e:
        return None, f"Ошибка при отправке: {str(e)}"