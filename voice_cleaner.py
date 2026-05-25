
# voice_cleaner.py
import os
import glob

import sys

from voice_config import RECORDINGS_DIR



def delete_file(file_path):
    """Удаляет конкретный файл."""
    try:
        os.remove(file_path)
        print(f"🗑️ Удалён файл: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при удалении {file_path}: {e}")
        return False

def delete_latest_recording():
    """Удаляет самый свежий .m4a файл из папки Recordings (старая логика)."""
    files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    if not files:
        print("Нет файлов .m4a для удаления")
        return False
    latest = max(files, key=os.path.getmtime)
    return delete_file(latest)

def delete_all_recordings():
    """Удаляет ВСЕ .m4a файлы из папки Recordings."""
    files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    count = 0
    for f in files:
        if delete_file(f):
            count += 1
    print(f"Удалено {count} файлов .m4a")
    return count

def delete_feedback():
    """Удаляет файл feedback.json."""
    feedback_file = "/storage/emulated/0/VoiceAgent/feedback.json"
    if os.path.exists(feedback_file):
        os.remove(feedback_file)
        print("🗑️ Удалён feedback.json")
    else:
        print("❌ feedback.json не найден")

if __name__ == "__main__":
    delete_latest_recording()