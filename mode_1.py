# mode_1.py — РЕЖИМ 1: СЫРЫЕ ЗАДАЧИ (с контекстом профиля)
# ============================================================
# Принимает невалидные остатки из main.py (через raw_tasks.json).
# При добавлении задачи AI сразу категоризирует её автоматически,
# учитывая твои поля "гастарбайтерское дело" и "призвание/свой бизнес"
# из Профиля.
# ============================================================

import sys
import time
import os

from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

from ai_helper import categorize
from task_storage import get_raw_tasks, _save_tasks
from feedback_storage import save_feedback
from profile import load_profile   # чтобы знать, чем ты занимаешься

# ============================================================
# АВТОМАТИЧЕСКАЯ КАТЕГОРИЗАЦИЯ С УЧЁТОМ ПРОФИЛЯ
# ============================================================
def auto_categorize(text):
    """
    Отправляет текст в AI, возвращает категорию.
    Перед отправкой добавляет контекст из Профиля:
      - current_gastarbeiter_job (хлеб и крыша)
      - current_business_calling (призвание / свой бизнес)
    Это помогает AI точнее отличать «деньги/гастарбайтер» от «деньги/своё дело».
    
    Вход:  строка текста
    Выход: строка категории
    """
    profile = load_profile()
    gast = profile.get("current_gastarbeiter_job", "").strip()
    biz = profile.get("current_business_calling", "").strip()

    # Собираем контекст
    context_parts = []
    if gast:
        context_parts.append(f"Текущая работа для хлеба и крыши: {gast}")
    if biz:
        context_parts.append(f"Своё дело / призвание: {biz}")

    if context_parts:
        # Добавляем контекст к тексту задачи
        enhanced_text = f"{text}\n\nКонтекст из профиля:\n" + "\n".join(context_parts)
    else:
        enhanced_text = text

    result = categorize(enhanced_text)
    if result and len(result) > 0:
        return result[0].get("category", "не категоризировано")
    return "не категоризировано"


# ============================================================
# ТАБЛИЦА СЫРЫХ ЗАДАЧ (главный экран)
# ============================================================
def show_raw_tasks():
    """
    Показывает таблицу сырых задач и меню действий.
    
    Вход:  raw_tasks.json (через get_raw_tasks())
    Выход: изменения сохраняются в raw_tasks.json
    """
    while True:
        all_tasks = get_raw_tasks()
        
        print("\n=== РЕЖИМ 1: СЫРЫЕ ЗАДАЧИ ===")
        
        if not all_tasks:
            print("📭 Сырых задач нет.")
        else:
            # Шапка таблицы
            print(f"{'№':<4} {'Текст':<40} {'Категория':<22} {'Дата':<12}")
            print("-" * 78)
            for i, t in enumerate(all_tasks, 1):
                text = t.get("text", "")[:38]
                category = t.get("category", "не категоризировано")
                created = ""
                if "created_at" in t:
                    created = time.strftime("%d.%m %H:%M", time.localtime(t["created_at"]))
                print(f"{i:<4} {text:<40} {category:<22} {created:<12}")
        
        print(f"\nДействия:")
        print("  1 — Редактировать задачу")
        print("  2 — Удалить задачу")
        print("  0 — Назад")
        
        choice = input("> ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            edit_existing_tasks()
        elif choice == "2":
            delete_tasks()
        else:
            print("❌ Неверный выбор.")


# ============================================================
# РЕДАКТИРОВАНИЕ ЗАДАЧИ
# ============================================================
def edit_existing_tasks():
    """
    Подменю редактирования: изменить текст (→ авто-категоризация)
    или сменить категорию вручную.
    """
    all_tasks = get_raw_tasks()
    if not all_tasks:
        print("📭 Нет задач для редактирования.")
        return
    
    print("\n📋 Список сырых задач:")
    for i, t in enumerate(all_tasks, 1):
        print(f"  {i}. {t['text'][:50]} → [{t.get('category', '?')}]")
    
    try:
        idx = int(input("\nНомер задачи: ").strip()) - 1
        if not (0 <= idx < len(all_tasks)):
            print("❌ Неверный номер.")
            return
    except ValueError:
        print("❌ Введи число.")
        return
    
    task = all_tasks[idx]
    print(f"\nРедактирование: «{task['text']}»")
    print(f"  Текущая категория: {task.get('category', 'не категоризировано')}")
    print(f"  1 — Изменить текст (авто-категоризация)")
    print(f"  2 — Изменить категорию вручную")
    print(f"  0 — Назад")
    
    choice = input("> ").strip()
    
    if choice == "0":
        return
    elif choice == "1":
        new_text = input("Новый текст: ").strip()
        if not new_text:
            print("❌ Пустой текст.")
            return
        new_cat = auto_categorize(new_text)
        save_feedback(task["text"], task["category"], new_cat)
        all_tasks[idx]["text"] = new_text
        all_tasks[idx]["category"] = new_cat
        _save_tasks(all_tasks)
        print(f"✅ Обновлено: {new_text} → {new_cat}")
    elif choice == "2":
        print("\nКатегории:")
        print("  1. деньги/своё дело")
        print("  2. деньги/гастарбайтер")
        print("  3. здоровье/физическое")
        print("  4. здоровье/психическое")
        cat_choice = input("> ").strip()
        cat_map = {
            "1": "деньги/своё дело",
            "2": "деньги/гастарбайтер",
            "3": "здоровье/физическое",
            "4": "здоровье/психическое"
        }
        new_cat = cat_map.get(cat_choice)
        if not new_cat:
            print("❌ Неверный выбор.")
            return
        old_cat = task.get("category", "не категоризировано")
        if old_cat != new_cat:
            save_feedback(task["text"], old_cat, new_cat)
        all_tasks[idx]["category"] = new_cat
        _save_tasks(all_tasks)
        print(f"✅ Категория изменена: {new_cat}")
    else:
        print("❌ Неверный выбор.")


# ============================================================
# УДАЛЕНИЕ ЗАДАЧ
# ============================================================
def delete_tasks():
    """Удаление задач по номерам."""
    all_tasks = get_raw_tasks()
    if not all_tasks:
        print("📭 Нет задач для удаления.")
        return
    
    print("\n📋 Список сырых задач:")
    for i, t in enumerate(all_tasks, 1):
        print(f"  {i}. {t['text'][:50]} → [{t.get('category', '?')}]")
    
    nums_str = input("\nНомера через пробел: ").strip()
    if not nums_str:
        return
    
    nums = [int(x) for x in nums_str.split() if x.isdigit()]
    if not nums:
        print("❌ Нет корректных номеров.")
        return
    
    for n in sorted(nums, reverse=True):
        idx = n - 1
        if 0 <= idx < len(all_tasks):
            removed = all_tasks.pop(idx)
            print(f"🗑️ Удалена: {removed['text'][:50]}")
    
    _save_tasks(all_tasks)
    print("✅ Готово.")


# ============================================================
# ТОЧКА ВХОДА
# ============================================================
def run_mode1():
    """Вызывает главный экран сырых задач."""
    show_raw_tasks()