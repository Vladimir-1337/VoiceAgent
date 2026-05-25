# split_tasks.py — ФИНАЛЬНАЯ ВЕРСИЯ
# Разделение текста на задачи по слову "ПРИКАЗЫВАЮ".
# Защита от искажений Whisper + все краевые случаи.

import re

def split_tasks(text: str):
    """
    Делит очищенный текст на задачи по разделителю "ПРИКАЗЫВАЮ".
    
    Вход:  строка после ai_clean_text
    Выход: список строк — отдельные задачи (без пустых и мусора)
    """
    if not text or not text.strip():
        return []
    
    # Нормализация: склеиваем разорванные пробелом части разделителя
    text = re.sub(r'приказ\s+ываю', 'приказываю', text, flags=re.IGNORECASE)
    text = re.sub(r'приказы\s+ваю', 'приказываю', text, flags=re.IGNORECASE)
    text = re.sub(r'приказыва\s+ю', 'приказываю', text, flags=re.IGNORECASE)
    
    # Ищем все вхождения корня "приказ"
    pattern = r'приказ\w*'
    
    # Если ВЕСЬ текст — это только разделитель, возвращаем []
    if re.fullmatch(pattern, text.strip(), flags=re.IGNORECASE):
        return []
    
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    
    # Очищаем каждую часть
    tasks = []
    for part in parts:
        part = part.strip().strip('.').strip(',').strip('!').strip('?').strip()
        # Убираем одиночные союзы-остатки и мусорные одиночные точки
        if part.lower() in ('и', 'а', 'потом', 'затем', 'и ещё', 'а также'):
            continue
        if part in ('.', '..', '...', ',', '!', '?'):
            continue
        if part:
            tasks.append(part)
    
    if not tasks:
        text = text.strip().strip('.').strip(',').strip()
        if text and text not in ('.', '..', '...'):
            return [text]
        return []
    
    return tasks