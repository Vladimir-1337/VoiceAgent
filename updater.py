# updater.py — АВТООБНОВЛЕНИЕ (отдельный модуль)
# Вызывается из main.py при старте.
# Проверяет GitHub, сравнивает версии, обновляет ВСЕ файлы.
# config.py НЕ трогает. Регистрация сохраняется.

import os, shutil, zipfile

LOCAL_VERSION = "1.0.33"
GITHUB_USER = "Vladimir-1337"
REPO = "VoiceAgent"

def check():
    """Проверяет обновления. Если есть — обновляет и возвращает True."""
    try:
        import requests as _r
        r_ver = _r.get(
            f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO}/main/version.txt",
            timeout=5
        )
        if r_ver.status_code != 200:
            return False
        
        remote = r_ver.text.strip()
        if remote == LOCAL_VERSION:
            return False  # Версии совпадают
        
        print(f"\n  ⚠️ Новая версия: {remote}. Обновляю...")
        
        # Качаем ZIP
        zip_url = f"https://github.com/{GITHUB_USER}/{REPO}/archive/refs/heads/main.zip"
        r_zip = _r.get(zip_url, timeout=30, allow_redirects=True)
        if r_zip.status_code != 200:
            print("  ❌ Не удалось скачать обновление.")
            return False
        
        # Сохраняем ZIP
        zip_path = "/storage/emulated/0/Download/update.zip"
        with open(zip_path, "wb") as f:
            f.write(r_zip.content)
        
        # Распаковываем
        tmp = "/storage/emulated/0/Download/update_tmp/"
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp)
        
        # Сохраняем config.py
        target = "/storage/emulated/0/VoiceAgent/"
        backup_config = None
        config_path = os.path.join(target, "config.py")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                backup_config = f.read()
        
        # Копируем ВСЕ файлы (config.py не трогаем)
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
        
        # Чистим
        shutil.rmtree(tmp, ignore_errors=True)
        os.remove(zip_path)
        
        # Фиксируем версию
        with open(os.path.join(target, "version.txt"), "w") as f:
            f.write(remote)
        
        print(f"  ✅ Обновлено до {remote}. Регистрация сохранена.")
        return True
    
    except:
        return False  # GitHub недоступен — работаем на текущей версии
