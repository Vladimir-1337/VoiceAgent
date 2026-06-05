# install_organizer.py — УСТАНОВЩИК ОРГАНАЙЗЕРА (v2.1 — с телеметрией)
import sys
import os
import subprocess
import time
import shutil
import zipfile
import re
import json

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
TARGET = "/storage/emulated/0/VoiceAgent"
TARGET_NEW = "/storage/emulated/0/VoiceAgent_NEW"
TARGET_OLD = "/storage/emulated/0/VoiceAgent_OLD"
BACKUP_DIR = "/storage/emulated/0/Download"
BACKUP_FILE = os.path.join(BACKUP_DIR, "voiceagent_config_backup.py")
GITHUB_URL = "https://github.com/Vladimir-1337/VoiceAgent/archive/refs/heads/main.zip"
VERSION_URL = "https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt"
MIN_FREE_SPACE_MB = 50
VPS_URL = "http://157.22.202.232:8200/report"

REMOTE_VER = "?"
RETRY_COUNT = 3
RETRY_DELAY = [1, 2, 4]


# ============================================================
# ТЕЛЕМЕТРИЯ
# ============================================================
def collect_device_info():
    """Собирает информацию об устройстве. Возвращает dict."""
    info = {}

    # Модель, производитель, Android, SDK
    for prop, key in [
        ("ro.product.model", "model"),
        ("ro.product.manufacturer", "manufacturer"),
        ("ro.build.version.release", "android"),
        ("ro.build.version.sdk", "sdk"),
    ]:
        try:
            info[key] = subprocess.check_output(["getprop", prop], timeout=3).decode().strip()
        except:
            try:
                with open("/system/build.prop", "r") as f:
                    content = f.read()
                match = re.search(rf'{prop.split(".")[-1]}=(.+)', content)
                info[key] = match.group(1).strip() if match else "?"
            except:
                info[key] = "?"

    # Память
    try:
        stat = shutil.disk_usage("/storage/emulated/0")
        info["free_space_mb"] = stat.free // (1024 ** 2)
        info["total_space_mb"] = stat.total // (1024 ** 2)
    except:
        info["free_space_mb"] = -1
        info["total_space_mb"] = -1

    # Python
    info["python"] = sys.version.split()[0]

    # Время начала установки
    info["install_start"] = time.time()
    info["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    return info


def send_telemetry(event, info, reason=None):
    """Тихо отправляет телеметрию. НЕ прерывает установку."""
    info["event"] = event
    if reason:
        info["reason"] = reason
    try:
        import requests as _r
        _r.post(VPS_URL,
                data=json.dumps(info, ensure_ascii=False).encode("utf-8"),
                timeout=3)
    except:
        pass  # Тихо — VPS недоступен, установка продолжается


# ============================================================
# УТИЛИТЫ
# ============================================================
def log(msg):
    print(f"  {msg}")


def abort(msg, code=1):
    print(f"\n  ❌ {msg}")
    print("  Старая версия НЕ тронута.")
    sys.exit(code)


def get_remote_version():
    try:
        import requests as _rv
        rv = _rv.get(VERSION_URL, timeout=10)
        if rv.status_code == 200:
            return rv.text.strip()
    except:
        pass
    return "?"


def parse_version(v_str):
    if not v_str:
        return (0, 0, 0)
    m = re.match(r'^(\d+)\.(\d+)\.(\d+)', str(v_str).strip())
    if m:
        return tuple(map(int, m.groups()))
    return (0, 0, 0)


def download_with_retries(url, max_retries=3):
    import requests as _r
    for attempt in range(max_retries):
        try:
            log(f"  Попытка {attempt + 1}/{max_retries}...")
            r = _r.get(url, timeout=30, allow_redirects=True)
            if r.status_code == 200:
                return r.content
            else:
                log(f"  HTTP {r.status_code}, пробую снова...")
        except Exception as e:
            log(f"  Ошибка: {e}")
        if attempt < max_retries - 1:
            delay = RETRY_DELAY[min(attempt, len(RETRY_DELAY) - 1)]
            time.sleep(delay)
    return None


def check_disk_space(path, min_mb):
    try:
        stat = shutil.disk_usage(path)
        free_mb = stat.free / (1024 * 1024)
        return free_mb >= min_mb
    except:
        return False


def check_write_permission(path):
    test_file = os.path.join(path, ".test_write")
    try:
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return True
    except:
        return False


def check_python_syntax(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, filepath, "exec")
        return (True, "")
    except SyntaxError as e:
        return (False, f"SyntaxError: {e}")
    except Exception as e:
        return (False, f"Ошибка: {e}")


def cleanup_crash_remnants():
    for d in [TARGET_NEW, TARGET_OLD]:
        if os.path.exists(d):
            log(f"Очищаю остатки после краша: {d}")
            shutil.rmtree(d, ignore_errors=True)
    if os.path.exists(BACKUP_FILE):
        log(f"Найден backup config.py: {BACKUP_FILE}")
        config_path = os.path.join(TARGET, "config.py")
        if os.path.exists(TARGET) and not os.path.exists(config_path):
            shutil.copy(BACKUP_FILE, config_path)
            log("config.py восстановлен из backup!")
            os.remove(BACKUP_FILE)


# ============================================================
# ГЛАВНЫЙ ПРОЦЕСС
# ============================================================
def main():
    global REMOTE_VER

    # --- ТЕЛЕМЕТРИЯ: СТАРТ ---
    device_info = collect_device_info()

    REMOTE_VER = get_remote_version()
    local_ver = "?"
    version_path = os.path.join(TARGET, "version.txt")
    if os.path.exists(version_path):
        with open(version_path, "r") as f:
            local_ver = f.read().strip()

    print("=" * 60)
    print(f"  УСТАНОВЩИК ОРГАНАЙЗЕРА v{REMOTE_VER}")
    print(f"  Локальная версия: {local_ver}")
    print(f"  Устройство: {device_info.get('model', '?')} (Android {device_info.get('android', '?')})")
    print("=" * 60)

    if parse_version(local_ver) >= parse_version(REMOTE_VER) and REMOTE_VER != "?":
        log(f"Версия уже актуальна ({local_ver}). Обновление не требуется.")
        sys.exit(0)

    cleanup_crash_remnants()

    config_path = os.path.join(TARGET, "config.py")
    config_backup_content = None

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_backup_content = f.read()
            log("config.py прочитан успешно")
        except Exception as e:
            send_telemetry("install_fail", device_info, f"config.py не читается: {e}")
            abort(f"Не могу прочитать config.py: {e}", 4)
    else:
        log("config.py не найден. После обновления потребуется регистрация.")

    if not check_disk_space("/storage/emulated/0", MIN_FREE_SPACE_MB):
        send_telemetry("install_fail", device_info, "недостаточно места")
        abort(f"Недостаточно места (нужно минимум {MIN_FREE_SPACE_MB} МБ).", 4)
    log(f"Свободного места достаточно (>{MIN_FREE_SPACE_MB} МБ)")

    test_dir = TARGET if os.path.exists(TARGET) else "/storage/emulated/0"
    if not check_write_permission(test_dir):
        send_telemetry("install_fail", device_info, "нет прав на запись")
        abort("Нет прав на запись в целевую папку.", 4)
    log("Права на запись есть")

    log("Скачиваю новую версию...")
    zip_content = download_with_retries(GITHUB_URL, max_retries=RETRY_COUNT)
    if zip_content is None:
        send_telemetry("install_fail", device_info, "не удалось скачать архив после 3 попыток")
        abort("Не удалось скачать архив после 3 попыток.", 4)

    zip_path = os.path.join(BACKUP_DIR, "organizer_update.zip")
    with open(zip_path, "wb") as f:
        f.write(zip_content)

    if not zipfile.is_zipfile(zip_path):
        os.remove(zip_path)
        send_telemetry("install_fail", device_info, "битый ZIP")
        abort("Скачанный файл повреждён (не является ZIP-архивом).", 4)
    log("Архив скачан и проверен")

    if config_backup_content:
        try:
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                f.write(config_backup_content)
            log(f"Backup config.py сохранён: {BACKUP_FILE}")
        except Exception as e:
            send_telemetry("install_fail", device_info, f"не удалось сохранить backup: {e}")
            abort(f"Не удалось сохранить backup config.py: {e}", 4)

    tmp_extract = os.path.join(BACKUP_DIR, "organizer_extract")
    if os.path.exists(tmp_extract):
        shutil.rmtree(tmp_extract, ignore_errors=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        root_in_zip = names[0].split("/")[0] if names else ""
        zf.extractall(tmp_extract)

    src_dir = os.path.join(tmp_extract, root_in_zip)

    if os.path.exists(TARGET_NEW):
        shutil.rmtree(TARGET_NEW, ignore_errors=True)
    os.makedirs(TARGET_NEW, exist_ok=True)

    for fname in os.listdir(src_dir):
        src = os.path.join(src_dir, fname)
        dst = os.path.join(TARGET_NEW, fname)
        if os.path.isdir(src):
            continue
        if fname == "config.py" and config_backup_content:
            continue
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            shutil.rmtree(TARGET_NEW, ignore_errors=True)
            send_telemetry("install_fail", device_info, f"ошибка копирования {fname}: {e}")
            abort(f"Ошибка копирования {fname}: {e}", 4)

    new_main = os.path.join(TARGET_NEW, "main.py")
    if os.path.exists(new_main):
        ok, err = check_python_syntax(new_main)
        if not ok:
            shutil.rmtree(TARGET_NEW, ignore_errors=True)
            send_telemetry("install_fail", device_info, f"SyntaxError в main.py: {err}")
            abort(f"Новая версия main.py содержит ошибку:\n  {err}", 4)
        log("main.py проверен (синтаксис корректен)")

    if config_backup_content:
        dst_config = os.path.join(TARGET_NEW, "config.py")
        try:
            with open(dst_config, "w", encoding="utf-8") as f:
                f.write(config_backup_content)
            log("config.py восстановлен из backup")
            with open(dst_config, "r", encoding="utf-8") as f:
                restored = f.read()
            if restored != config_backup_content:
                shutil.rmtree(TARGET_NEW, ignore_errors=True)
                send_telemetry("install_fail", device_info, "ошибка восстановления config.py — содержимое не совпадает")
                abort("Ошибка восстановления config.py — содержимое не совпадает.", 4)
            if os.path.exists(BACKUP_FILE):
                os.remove(BACKUP_FILE)
                log("Backup-файл удалён (восстановление успешно)")
        except Exception as e:
            shutil.rmtree(TARGET_NEW, ignore_errors=True)
            send_telemetry("install_fail", device_info, f"не удалось восстановить config.py: {e}")
            abort(f"Не удалось восстановить config.py: {e}", 4)

    if os.path.exists(TARGET):
        if os.path.exists(TARGET_OLD):
            shutil.rmtree(TARGET_OLD, ignore_errors=True)
        os.rename(TARGET, TARGET_OLD)
    os.rename(TARGET_NEW, TARGET)
    if os.path.exists(TARGET_OLD):
        shutil.rmtree(TARGET_OLD, ignore_errors=True)
    log("Файлы установлены")

    if REMOTE_VER and REMOTE_VER != "?":
        try:
            version_path = os.path.join(TARGET, "version.txt")
            with open(version_path, "w") as f:
                f.write(REMOTE_VER)
            log(f"version.txt обновлён: {REMOTE_VER}")
        except Exception as e:
            log(f"Не удалось обновить version.txt: {e}")

    if os.path.exists(tmp_extract):
        shutil.rmtree(tmp_extract, ignore_errors=True)
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # --- ТЕЛЕМЕТРИЯ: УСПЕХ ---
    device_info["install_time_sec"] = round(time.time() - device_info["install_start"], 1)
    device_info["version"] = REMOTE_VER
    send_telemetry("install_success", device_info)

    print("\n" + "=" * 60)
    log(f"ОБНОВЛЕНО ДО v{REMOTE_VER}!")
    log("Запустите main.py и нажмите Run.")
    print("=" * 60)


if __name__ == "__main__":
    main()
