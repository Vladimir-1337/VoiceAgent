# updater.py — АВТООБНОВЛЕНИЕ v1.0.35
import os, shutil, zipfile

GITHUB_USER = "Vladimir-1337"
REPO = "VoiceAgent"

def check():
    try:
        import requests as _r
        
        # Читаем ЛОКАЛЬНУЮ версию
        local_path = "/storage/emulated/0/VoiceAgent/version.txt"
        try:
            with open(local_path, "r") as f:
                local_ver = f.read().strip()
        except:
            local_ver = "0.0"
        
        # Читаем УДАЛЁННУЮ версию
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
        
        # Качаем ZIP
        r_zip = _r.get(
            f"https://github.com/{GITHUB_USER}/{REPO}/archive/refs/heads/main.zip",
            timeout=30, allow_redirects=True
        )
        if r_zip.status_code != 200:
            return False
        
        zip_path = "/storage/emulated/0/Download/update.zip"
        with open(zip_path, "wb") as f:
            f.write(r_zip.content)
        
        tmp = "/storage/emulated/0/Download/update_tmp/"
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)
        
        target = "/storage/emulated/0/VoiceAgent/"
        
        # Сохраняем config.py
        backup_config = None
        config_path = os.path.join(target, "config.py")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                backup_config = f.read()
        
        # Копируем ВСЕ файлы
        for root, dirs, files in os.walk(tmp):
            for fname in files:
                if fname.endswith((".py", ".json", ".txt", ".md")):
                    src = os.path.join(root, fname)
                    dst = os.path.join(target, fname)
                    if fname == "config.py" and backup_config:
                        continue
                    try:
                        with open(src, "r") as fsrc:
                            with open(dst, "w") as fdst:
                                fdst.write(fsrc.read())
                    except:
                        pass
        
        # Восстанавливаем config.py
        if backup_config:
            with open(config_path, "w") as f:
                f.write(backup_config)
        
        # ОБНОВЛЯЕМ ЛОКАЛЬНЫЙ version.txt
        with open(local_path, "w") as f:
            f.write(remote)
        
        # Чистим
        shutil.rmtree(tmp, ignore_errors=True)
        os.remove(zip_path)
        
        print(f"  ✅ Обновлено до {remote}.")
        return True
    except:
        return False
