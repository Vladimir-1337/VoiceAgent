# voice_sender.py — Отправка аудио на VPS (Whisper)
import requests, glob, os, struct, time
from voice_config import SERVER_URL, RECORDINGS_DIR, REQUEST_TIMEOUT

MAX_AUDIO_DURATION = 120

def get_audio_duration(filepath):
    try:
        size = os.path.getsize(filepath)
        with open(filepath, "rb") as f:
            header = f.read(12)
            if len(header) < 12:
                return 0
            if header[:4] == b"RIFF":
                f.seek(28)
                byte_rate_data = f.read(4)
                if len(byte_rate_data) == 4:
                    byte_rate = struct.unpack("<I", byte_rate_data)[0]
                    if byte_rate > 0:
                        return size / byte_rate
            elif header[:4] == b"\x00\x00\x00" or b"ftyp" in header[:8]:
                estimated_duration = size / 16000
                return min(estimated_duration, 600)
            return size / 16000
    except:
        return 0

def send_latest_recording():
    """Отправляет последний .m4a файл на VPS. До 3 попыток. Возвращает (text, error)."""
    m4a_files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    if not m4a_files:
        return (None, "Нет файлов .m4a в папке Recordings")
    
    latest_file = max(m4a_files, key=os.path.getmtime)
    
    duration = get_audio_duration(latest_file)
    if duration > MAX_AUDIO_DURATION:
        return (None, f"Слишком длинная запись ({duration:.0f} сек). Максимум {MAX_AUDIO_DURATION} сек.")
    
    for attempt in range(3):
        try:
            with open(latest_file, "rb") as f:
                response = requests.post(SERVER_URL, files={"audio": f}, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "")
                return (text, None)
            
            if attempt < 2:
                time.sleep(2)
                continue
            return (None, f"Ошибка сервера: {response.status_code}")
        
        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(2)
                continue
            return (None, f"Таймаут ({REQUEST_TIMEOUT} сек)")
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                time.sleep(2)
                continue
            return (None, "VPS недоступен")
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            return (None, str(e)[:200])
    
    return (None, "Все попытки исчерпаны")
