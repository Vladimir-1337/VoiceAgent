# updater.py v1.0.41 — ТЕНЕВОЙ АГЕНТ
import os, sys, subprocess, time

GITHUB_USER = "Vladimir-1337"
REPO = "VoiceAgent"

def check():
    try:
        import requests as _r
        
        local_path = "/storage/emulated/0/VoiceAgent/version.txt"
        try:
            with open(local_path, "r") as f:
                local_ver = f.read().strip()
        except:
            local_ver = "0.0"
        
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
        
        installer_path = "/storage/emulated/0/Download/update_installer.py"
        with open(installer_path, "w", encoding="utf-8") as f:
            f.write(r_inst.text)
        
        # Запускаем установщик и ЖДЁМ его завершения
        print("  Установка...")
        subprocess.run([sys.executable, installer_path], timeout=180)
        
        # Установщик сам запустит новый main.py
        return True
    
    except:
        return False
