# updater.py v1.0.40 — ТЕНЕВОЙ АГЕНТ
# Не обновляет сам себя. Запускает установщик, который делает всё.
import os, sys, subprocess

GITHUB_USER = "Vladimir-1337"
REPO = "VoiceAgent"

def check():
    try:
        import requests as _r
        
        # Читаем локальную версию
        local_path = "/storage/emulated/0/VoiceAgent/version.txt"
        try:
            with open(local_path, "r") as f:
                local_ver = f.read().strip()
        except:
            local_ver = "0.0"
        
        # Читаем удалённую версию
        r_ver = _r.get(
            f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO}/main/version.txt",
            timeout=5
        )
        if r_ver.status_code != 200:
            return False
        
        remote = r_ver.text.strip()
        if remote == local_ver:
            return False
        
        print(f"\n  ⚠️ Новая версия: {remote}. Обновляю...")
        
        # Качаем свежий установщик
        r_inst = _r.get(
            f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO}/main/install_organizer.py",
            timeout=10
        )
        if r_inst.status_code != 200:
            return False
        
        # Сохраняем установщик
        installer_path = "/storage/emulated/0/Download/update_installer.py"
        with open(installer_path, "w", encoding="utf-8") as f:
            f.write(r_inst.text)
        
        # Запускаем установщик и выходим
        print("  Запускаю установщик...")
        subprocess.Popen([sys.executable, installer_path])
        return True  # Выходим — установщик всё сделает
    
    except:
        return False
