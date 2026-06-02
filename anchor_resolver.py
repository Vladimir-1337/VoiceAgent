# anchor_resolver.py — Блок B.1: Загрузка якорей из профиля
# Превращает user_profile.json в словарь для парсера

import json
import os

from voice_config import PROFILE_FILE

# Кеш — чтобы не читать файл при каждом запросе
_cache = None
_cache_mtime = None


def load_anchors():
    """
    Загружает якоря из user_profile.json.
    
    Вход:  файл user_profile.json (с полями city, anchors)
    Выход: словарь {ключ: адрес}
           Пример: {"озон": "склад Ozon, Севастополь", "у петра": "ул. Ленина, 5, Севастополь"}
    
    Кеширует результат. Если файл не менялся — возвращает кеш.
    """
    global _cache, _cache_mtime
    
    # Проверяем, изменился ли файл
    try:
        mtime = os.path.getmtime(PROFILE_FILE)
        if _cache is not None and _cache_mtime == mtime:
            return _cache
        _cache_mtime = mtime
    except OSError:
        pass
    
    # Загружаем профиль
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
    city = profile.get("city", "").strip()
    anchors = profile.get("anchors", {})
    
    result = {}
    
    for main_name, data in anchors.items():
        address = data.get("address", "").strip()
        
        # Если адрес не содержит город — добавляем город по умолчанию
        if address and city and city.lower() not in address.lower():
            address = f"{address}, {city}"
        elif not address:
            coords = data.get("coords", "").strip()
            if coords:
                address = coords  # используем координаты как адрес
            else:
                address = city  # только город, если и координат нет
        
        # Основное название → адрес
        if main_name and address:
            result[main_name.lower()] = address
        
        # Дополнительные названия (через запятую) → тот же адрес
        aliases_str = data.get("aliases", "")
        if aliases_str:
            for alias in aliases_str.split(","):
                alias = alias.strip().lower()
                if alias and alias not in result:
                    result[alias] = address
    
    _cache = result
    return result


def reload_anchors():
    """Сбрасывает кеш и перечитывает якоря из файла."""
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = None
    return load_anchors()
    
    
    
def resolve_place(text):
    """
    Ищет в тексте якорное место и возвращает его адрес + очищенный текст.
    
    Вход:  строка (например, "купить носки в озон")
    Выход: (address или None, текст без места)
    
    Ищет точное вхождение ключа. Если нашлось — вырезает и возвращает адрес.
    Если не нашлось — возвращает (None, исходный текст).
    """
    anchors = load_anchors()
    
    if not anchors:
        return (None, text)
    
    text_lower = text.lower()
    
    # Ищем самое длинное совпадение (чтобы "в покровском" нашлось раньше, чем "в")
    found_key = None
    found_address = None
    
    for key, address in anchors.items():
        if key in text_lower:
            # Выбираем самое длинное совпадение
            if found_key is None or len(key) > len(found_key):
                found_key = key
                found_address = address
    
    if found_key:
        # Вырезаем ключ из текста (с учётом регистра)
        idx = text_lower.find(found_key)
        clean_text = text[:idx] + text[idx + len(found_key):]
        # Убираем двойные пробелы и обрезаем
        clean_text = " ".join(clean_text.split())
        return (found_address, clean_text)
    
    return (None, text)
    
    
    
def load_people():
    """
    Загружает якоря людей из user_profile.json.
    
    Вход:  файл user_profile.json (поле people_anchors)
    Выход: словарь {имя: {"email": ..., "invite_default": ...}}
    """
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
    return profile.get("people_anchors", {})


def resolve_person(text):
    """
    Ищет в тексте имя человека из people_anchors.
    
    Вход:  строка (например, "купить хлеб маме")
    Выход: (name, email, invite_default)
           name — имя человека или None
           email — email или ""
           invite_default — True/False
    
    Ищет точное вхождение имени. Если нашлось — возвращает данные.
    Если не нашлось — возвращает (None, "", False).
    """
    people = load_people()
    
    if not people:
        return (None, "", False)
    
    text_lower = text.lower()
    
    # Ищем самое длинное совпадение
    found_name = None
    found_data = None
    
    for name, data in people.items():
        if name in text_lower:
            if found_name is None or len(name) > len(found_name):
                found_name = name
                found_data = data
    
    if found_name:
        email = found_data.get("email", "")
        invite_default = found_data.get("invite_default", False)
        return (found_name, email, invite_default)
    
    return (None, "", False)
    
    
# anchor_resolver.py — продолжение
# F.1: scan_person() — поиск и вырезание имён из текста


def scan_person(text):
    """
    Ищет в тексте якорное имя и вырезает его.
    Аналог resolve_place, но для людей.
    
    Вход:  строка (например, "купить хлеб маме завтра в 16 дома")
    Выход: (name, email, invite_default, clean_text)
           name — имя человека или None
           email — email или ""
           invite_default — True/False
           clean_text — текст без имени
    
    Ищет точное вхождение имени из people_anchors.
    Если нашлось — вырезает и возвращает данные + чистый текст.
    Если не нашлось — возвращает (None, "", False, text).
    """
    people = load_people()
    
    if not people:
        return (None, "", False, text)
    
    text_lower = text.lower()
    
    # Ищем самое длинное совпадение
    found_name = None
    found_data = None
    
    for name, data in people.items():
        if name in text_lower:
            if found_name is None or len(name) > len(found_name):
                found_name = name
                found_data = data
    
    if found_name:
        # Вырезаем имя из текста
        idx = text_lower.find(found_name)
        clean_text = text[:idx] + text[idx + len(found_name):]
        clean_text = " ".join(clean_text.split())
        
        email = found_data.get("email", "")
        invite_default = found_data.get("invite_default", False)
        return (found_name, email, invite_default, clean_text)
    
    return (None, "", False, text)