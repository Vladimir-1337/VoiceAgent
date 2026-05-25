# display_module.py — Блок 2: Отображение таблицы и меню Режима 3
# Подблок 2.1: sort_tasks() — сортировка задач по дате, времени, индексу

from datetime import datetime


def sort_tasks(tasks):
    """
    Принимает список задач.
    Возвращает новый список, отсортированный:
    1. Дата (возрастание)
    2. Время (возрастание)
    3. Исходный порядок в списке (стабильная сортировка)
    Задачи с битой датой или временем падают в конец списка.
    Исходный список НЕ меняется.
    """
    def parse_date(task):
        """Вытащить дату как объект datetime. Кривая дата -> 9999-12-31 (в конец)."""
        d = task.get("date", "")
        try:
            return datetime.strptime(d, "%Y-%m-%d")
        except (ValueError, TypeError):
            return datetime(9999, 12, 31)

    def parse_time(task):
        """Вытащить время как объект datetime. Кривое время -> 23:59 (в конец дня)."""
        t = task.get("time", "")
        try:
            return datetime.strptime(t, "%H:%M")
        except (ValueError, TypeError):
            return datetime(1900, 1, 1, 23, 59)

    # Нумеруем задачи (индекс для стабильности при одинаковых дате+времени)
    indexed = list(enumerate(tasks))

    # Сортируем: дата -> время -> индекс
    indexed.sort(key=lambda pair: (parse_date(pair[1]), parse_time(pair[1]), pair[0]))

    # Достаём задачи без индексов
    return [task for _, task in indexed]
    
    
    
    
    
    
    
    
    # display_module.py — продолжение
# Подблок 2.2: format_repeat() — читаемый вид повторяемости


def format_repeat(repeat):
    """
    Принимает словарь repeat из задачи.
    Возвращает строку для колонки 'Повтор' в таблице.
    none      -> "" (пусто)
    daily     -> "daily"
    weekly    -> "weekly:пн,ср,пт"
    interval  -> "interval:5 мин"
    Битый/отсутствующий -> "" (не падаем)
    """
    if not isinstance(repeat, dict):
        return ""

    rtype = repeat.get("type", "none")

    if rtype == "none":
        return ""

    if rtype == "daily":
        return "daily"

    if rtype == "weekly":
        days = repeat.get("days", [])
        if not days:
            return "weekly:—"
        days_map = {1: "пн", 2: "вт", 3: "ср", 4: "чт", 5: "пт", 6: "сб", 7: "вс"}
        day_strs = []
        for d in days:
            if isinstance(d, int) and 1 <= d <= 7:
                day_strs.append(days_map[d])
        if not day_strs:
            return "weekly:—"
        return f"weekly:{','.join(day_strs)}"

    if rtype == "interval":
        mins = repeat.get("interval_minutes", 0)
        if isinstance(mins, int) and mins > 0:
            return f"interval:{mins} мин"
        return "interval:? мин"

    # Неизвестный тип — просто показываем как есть
    return rtype
    
    
    
    
    
    
# display_module.py — продолжение
# Подблок ST.3: колонка «Статус» добавлена


def display_table(tasks):
    """
    Выводит таблицу задач в консоль.
    Ширина колонок подгоняется под содержимое автоматически.
    """
    if not tasks:
        print("=== Режим 3: Управление задачами ===")
        print("Нет задач для отображения.")
        return

    # Заголовки колонок (ключ: имя колонки)
    headers = {
        "num": "№",
        "date": "Дата",
        "time": "Время",
        "place": "Место",
        "title": "Название",
        "duration": "Длит",
        "repeat": "Повтор",
        "slot": "Слот",
        "description": "Описание",
        "third_party": "Лицо",
        "invite": "Пригл",
        "status": "Статус"         # ← ST.3: новая колонка
    }

    # Считаем максимальную ширину для каждой колонки
    widths = {key: len(headers[key]) for key in headers}

    for i, task in enumerate(tasks, start=1):
        widths["num"] = max(widths["num"], len(str(i)))
        widths["date"] = max(widths["date"], len(task.get("date", "")))
        widths["time"] = max(widths["time"], len(task.get("time", "")))
        widths["place"] = max(widths["place"], len(task.get("place", "")))
        widths["title"] = max(widths["title"], len(task.get("title", "")))
        widths["duration"] = max(widths["duration"], len(str(task.get("duration", ""))))
        repeat_str = format_repeat(task.get("repeat", {}))
        widths["repeat"] = max(widths["repeat"], len(repeat_str))
        widths["slot"] = max(widths["slot"], len(task.get("slot", "")))
        widths["description"] = max(widths["description"], len(task.get("description", "")))
        widths["third_party"] = max(widths["third_party"], len(task.get("third_party", "")))
        invite_str = "✓" if task.get("invite", False) else ""
        widths["invite"] = max(widths["invite"], len(invite_str))
        # ST.3: форматирование статуса
        status_str = build_status(task)
        widths["status"] = max(widths["status"], len(status_str))

    # Шапка
    print("=== Режим 3: Управление задачами ===")

    # Строка заголовков с выравниванием
    header_line = (
        f"{headers['num']:>{widths['num']}} | "
        f"{headers['date']:<{widths['date']}} | "
        f"{headers['time']:<{widths['time']}} | "
        f"{headers['place']:<{widths['place']}} | "
        f"{headers['title']:<{widths['title']}} | "
        f"{headers['duration']:>{widths['duration']}} | "
        f"{headers['repeat']:<{widths['repeat']}} | "
        f"{headers['slot']:<{widths['slot']}} | "
        f"{headers['description']:<{widths['description']}} | "
        f"{headers['third_party']:<{widths['third_party']}} | "
        f"{headers['invite']:<{widths['invite']}} | "
        f"{headers['status']:<{widths['status']}}"
    )
    print(header_line)
    print("-" * len(header_line))

    # Строки данных
    for i, task in enumerate(tasks, start=1):
        repeat_str = format_repeat(task.get("repeat", {}))
        invite_str = "✓" if task.get("invite", False) else ""
        status_str = build_status(task)
        line = (
            f"{i:>{widths['num']}} | "
            f"{task.get('date', ''):<{widths['date']}} | "
            f"{task.get('time', ''):<{widths['time']}} | "
            f"{task.get('place', ''):<{widths['place']}} | "
            f"{task.get('title', ''):<{widths['title']}} | "
            f"{task.get('duration', ''):>{widths['duration']}} | "
            f"{repeat_str:<{widths['repeat']}} | "
            f"{task.get('slot', ''):<{widths['slot']}} | "
            f"{task.get('description', ''):<{widths['description']}} | "
            f"{task.get('third_party', ''):<{widths['third_party']}} | "
            f"{invite_str:<{widths['invite']}} | "
            f"{status_str:<{widths['status']}}"
        )
        print(line)


# Вспомогательная функция для колонки «Статус»
def build_status(task):
    """
    Формирует строку статуса:
      ✅ — выгружено
      ❌ — не выгружено
      Если last_edited не пустое — добавляет дату в скобках.
    """
    exported = task.get("exported", False)
    last_edited = task.get("last_edited", "")

    if exported:
        base = "✅"
    else:
        base = "❌"

    if last_edited:
        return f"{base} ({last_edited})"
    return base
        
        
        
        
# display_module.py — show_main_menu()
# Правка 6: добавлена выгрузка выбранных задач
def show_main_menu(tasks):
    """
    Показывает таблицу задач и цифровое меню.
    Команды:
      0 — выход
      1 — выгрузить ВСЕ задачи
      5 — выгрузить выбранные (по номерам через пробел)
      2 — добавить задачу
      3 — редактировать задачу
      4 — удалить задачу
    """
    display_table(tasks)

    print("\nКоманды:")
    print("  0 — Выход")
    print("  1 — Выгрузить всё в календарь")
    print("  2 — Добавить задачу")
    print("  3 — Редактировать задачу")
    print("  4 — Удалить задачу")
    print("  5 — Выгрузить выбранные")
    print()

    raw = input("> ").strip()

    if raw == "0":
        return ("exit", None)
    if raw == "1":
        return ("export_all", None)
    if raw == "2":
        return ("add", None)
    if raw == "3":
        return ("edit", None)
    if raw == "4":
        return ("delete", None)
    if raw == "5":
        return ("export_selected", None)

    return ("unknown", raw)