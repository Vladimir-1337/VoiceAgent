# feedback_storage.py
# ============================================================
# ХРАНЕНИЕ ИСПРАВЛЕНИЙ КАТЕГОРИЙ ДЛЯ БУДУЩЕГО ОБУЧЕНИЯ ИИ
# ============================================================

import json
import os
import time
import sys

from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

FEEDBACK_FILE = "feedback.json"

def load_feedback():
    """Загружает все сохранённые исправления."""
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_feedback(original_text, wrong_category, correct_category):
    """
    Сохраняет одно исправление в feedback.json.
    В будущем эти данные можно использовать для дообучения AI.
    """
    feedback = load_feedback()
    feedback.append({
        "timestamp": time.time(),
        "original_text": original_text,
        "wrong_category": wrong_category,
        "correct_category": correct_category
    })
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)
    print(f"📝 Исправление сохранено в feedback.json (всего записей: {len(feedback)})")

def get_feedback_summary():
    """
    Возвращает краткую сводку исправлений для передачи в промпт AI.
    Пока заглушка – возвращает последние 5 примеров.
    В будущем можно улучшить: группировать, отбирать релевантные.
    """
    feedback = load_feedback()
    if not feedback:
        return "Нет исправлений."
    # Берём последние 5 записей
    last_five = feedback[-5:]
    summary = "История исправлений пользователя:\n"
    for item in last_five:
        summary += f"- \"{item['original_text']}\": было {item['wrong_category']} → стало {item['correct_category']}\n"
    return summary

def clear_feedback():
    """Очищает файл feedback.json (для отладки)."""
    if os.path.exists(FEEDBACK_FILE):
        os.remove(FEEDBACK_FILE)
        print("🗑️ feedback.json удалён.")
    else:
        print("❌ feedback.json не найден.")

# ==================== ЗАГЛУШКА ДЛЯ ИСПОЛЬЗОВАНИЯ В mode-1.py ====================
# (чтобы не менять mode-1.py, можно импортировать эту функцию вместо локальной заглушки)

def save_feedback_stub(original_text, wrong_category, correct_category):
    """Заглушка – просто вызывает реальную функцию сохранения."""
    save_feedback(original_text, wrong_category, correct_category)

if __name__ == "__main__":
    # Тест модуля
    print("=== ТЕСТ FEEDBACK_STORAGE ===")
    save_feedback("купить мёд", "деньги/гастарбайтер", "здоровье/физическое")
    save_feedback("не нервничать", "здоровье/психическое", "здоровье/физическое")
    print("\nСводка исправлений:")
    print(get_feedback_summary())
    print("\nОчистка...")
    clear_feedback()