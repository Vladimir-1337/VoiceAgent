# mode_3.py — Скелет Режима 3: Управление задачами (слот добавлен)
# Каждая функция пока содержит упрощённую логику, которую позже заменим на реальную.

import sys
# Добавляем корень проекта в пути импорта, чтобы находить модули
from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

# task_data.py — работа с ready_tasks.json
from task_data import load_tasks, save_tasks, validate_task

from display_module import sort_tasks, format_repeat, display_table, show_main_menu

from caldav_client import create_event, delete_event, create_interval_events



def add_task_interactive():
    """Ручной ввод новой задачи с немедленной проверкой обязательных полей."""
    print("\n=== Добавление новой задачи ===")

    from datetime import datetime, timedelta
    today = datetime.now()

    # ------------------------------------------------------------
    # Вспомогательные проверки
    # ------------------------------------------------------------
    def _is_valid_date(d):
        try:
            datetime.strptime(d, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _is_valid_time(t):
        try:
            datetime.strptime(t, "%H:%M")
            return True
        except ValueError:
            return False

    def _has_verb(title_str):
        try:
            from intent_parser import STOP_VERBS
        except ImportError:
            STOP_VERBS = []
        words = title_str.strip().split()
        for word in words:
            clean = word.strip(",.!?;:«»\"'()[]").lower()
            if not clean:
                continue
            if clean in STOP_VERBS:
                return True
            if clean.endswith(("ть", "ти", "чь", "тся", "ться")):
                return True
            if clean.endswith(("и", "й")) and len(clean) <= 4:
                return True
        return False

    def _is_valid_place(p):
        if not p or not p.strip():
            return False, "Место обязательно для выполнения задачи (например, 'Дом', 'Работа', 'Озон')."
        forbidden = ["везде", "где угодно", "любое место", "когда-нибудь",
                     "не важно", "без разницы", "где попало", "где-то"]
        if p.strip().lower() in forbidden:
            return False, f"Слишком абстрактное место: '{p}'. Укажи конкретное."
        return True, ""

    # ------------------------------------------------------------
    # ДАТА
    # ------------------------------------------------------------
    while True:
        raw_date = input(f"Дата (ДД, ММ-ДД, сегодня/завтра, Enter = сегодня {today.strftime('%Y-%m-%d')}): ").strip()
        if raw_date == "" or raw_date.lower() in ("сегодня", "today"):
            date = today.strftime("%Y-%m-%d")
        elif raw_date.lower() in ("завтра", "tomorrow"):
            date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif raw_date.lower() == "послезавтра":
            date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        elif "-" in raw_date:
            parts = raw_date.split("-")
            if len(parts) == 2:
                date = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            else:
                date = raw_date
        else:
            date = f"{today.year}-{today.month:02d}-{raw_date.zfill(2)}"

        if _is_valid_date(date):
            break
        print(f"❌ Некорректная дата: '{date}'. Попробуй ещё раз.")

    # ------------------------------------------------------------
    # ВРЕМЯ
    # ------------------------------------------------------------
    while True:
        time_val = input("Время (ЧЧ:ММ или ЧЧ): ").strip()
        if time_val and ":" not in time_val and time_val.isdigit():
            time_val = f"{int(time_val):02d}:00"
        if _is_valid_time(time_val):
            break
        print(f"❌ Некорректное время: '{time_val}'. Введи в формате ЧЧ:ММ (например, 15:00 или 15).")

    # ------------------------------------------------------------
    # НАЗВАНИЕ
    # ------------------------------------------------------------
    while True:
        title = input("Название (глагол + объект, например 'купить хлеб'): ").strip()
        if title and _has_verb(title):
            break
        if not title:
            print("❌ Название не может быть пустым.")
        else:
            print("❌ Название должно содержать конкретное действие (глагол): купить, позвонить, сделать, забрать…")

    # ------------------------------------------------------------
    # МЕСТО
    # ------------------------------------------------------------
    while True:
        place = input("Место (обязательно, например 'Дом', 'Магазин', 'Работа'): ").strip()
        ok, err = _is_valid_place(place)
        if ok:
            break
        print(f"❌ {err}")

    # ------------------------------------------------------------
    # ДЛИТЕЛЬНОСТЬ
    # ------------------------------------------------------------
    while True:
        duration_str = input("Длительность в минутах (по умолчанию 5): ").strip()
        if duration_str == "":
            duration = 5
            break
        try:
            duration = int(duration_str)
            if duration < 1:
                print("❌ Длительность должна быть не меньше 1 минуты.")
                continue
            break
        except ValueError:
            print("❌ Введи целое число минут.")

    # ------------------------------------------------------------
    # ОПИСАНИЕ, СЛОТ
    # ------------------------------------------------------------
    desc = input("Описание (Enter если пусто): ")
    slot = input("Слот (состояние, когда выполнять, Enter если не важно): ")

    # ------------------------------------------------------------
    # ТРЕТЬЕ ЛИЦО (опционально)
    # ------------------------------------------------------------
    third_party = ""
    invite = False
    tp = input("Третье лицо (с кем связана задача, Enter если нет): ").strip()
    if tp:
        third_party = tp
        inv_choice = input("Пригласить как участника в календарь? (да/нет): ").strip().lower()
        invite = inv_choice in ("да", "yes", "y", "1")

    # ------------------------------------------------------------
    # ПОВТОРЯЕМОСТЬ
    # ------------------------------------------------------------
    print("\nПовторяемость:")
    print("  0 — Нет (один раз)")
    print("  1 — Каждый день (daily)")
    print("  2 — По дням недели (weekly)")
    print("  3 — Каждые N минут (interval)")
    repeat_choice = input("> ").strip()

    repeat = {"type": "none", "days": [], "interval_minutes": 0, "until": ""}

    if repeat_choice == "1":
        repeat["type"] = "daily"
        print("\nОстановить серию в определённый день?")
        print("  1 — Да")
        print("  2 — Нет (бесконечно)")
        end_choice = input("> ").strip()
        if end_choice == "1":
            while True:
                end_date_str = input("Какого числа закончить? (ДД или ММ-ДД): ").strip()
                if not end_date_str:
                    print("❌ Нужно указать дату окончания.")
                    continue
                if "-" in end_date_str:
                    parts = end_date_str.split("-")
                    if len(parts) == 2:
                        end_date = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    else:
                        end_date = end_date_str
                else:
                    end_date = f"{today.year}-{today.month:02d}-{end_date_str.zfill(2)}"
                if _is_valid_date(end_date):
                    break
                print(f"❌ Некорректная дата окончания: {end_date}")
            repeat["until"] = f"{end_date}T23:59:59Z"

    elif repeat_choice == "2":
        repeat["type"] = "weekly"
        days_str = input("Дни недели через пробел (1=пн 2=вт ... 7=вс): ").strip()
        if days_str:
            repeat["days"] = [int(d) for d in days_str.split() if d.isdigit() and 1 <= int(d) <= 7]
        print("\nОстановить серию в определённый день?")
        print("  1 — Да")
        print("  2 — Нет (бесконечно)")
        end_choice = input("> ").strip()
        if end_choice == "1":
            while True:
                end_date_str = input("Какого числа закончить? (ДД или ММ-ДД): ").strip()
                if not end_date_str:
                    print("❌ Нужно указать дату окончания.")
                    continue
                if "-" in end_date_str:
                    parts = end_date_str.split("-")
                    if len(parts) == 2:
                        end_date = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    else:
                        end_date = end_date_str
                else:
                    end_date = f"{today.year}-{today.month:02d}-{end_date_str.zfill(2)}"
                if _is_valid_date(end_date):
                    break
                print(f"❌ Некорректная дата окончания: {end_date}")
            repeat["until"] = f"{end_date}T23:59:59Z"

    elif repeat_choice == "3":
        repeat["type"] = "interval"
        while True:
            mins_str = input("Интервал в минутах: ").strip()
            if mins_str and mins_str.isdigit():
                repeat["interval_minutes"] = int(mins_str)
                break
            else:
                print("❌ Введи целое число минут.")

        print("\nОстановить серию в определённое время?")
        print("  1 — Да")
        print("  2 — Нет (бесконечно)")
        end_choice = input("> ").strip()
        if end_choice == "2":
            print("Внимание: для интервала обязательно указывать время окончания.")
            end_choice = "1"
        if end_choice == "1":
            while True:
                end_time_str = input("Во сколько закончить? (ЧЧ:ММ): ").strip()
                if not end_time_str:
                    print("❌ Нужно указать время окончания.")
                    continue
                try:
                    end_h, end_m = map(int, end_time_str.split(":"))
                    start_h, start_m = map(int, time_val.split(":"))
                    if end_h < start_h or (end_h == start_h and end_m <= start_m):
                        task_date_dt = datetime.strptime(date, "%Y-%m-%d")
                        next_day = task_date_dt + timedelta(days=1)
                        end_date = next_day.strftime("%Y-%m-%d")
                    else:
                        end_date = date
                    repeat["until"] = f"{end_date}T{end_h:02d}:{end_m:02d}:00Z"
                    break
                except:
                    print("❌ Неверный формат времени. Используй ЧЧ:ММ.")

    # ------------------------------------------------------------
    # СБОРКА
    # ------------------------------------------------------------
    new_task = {
        "date": date,
        "time": time_val,
        "place": place,
        "title": title,
        "duration": duration,
        "repeat": repeat,
        "description": desc,
        "slot": slot.strip(),
        "third_party": third_party,
        "invite": invite,
        "caldav_uid": "",
        "exported": False
    }
    return new_task





def edit_task_interactive(task):
    """Редактирование задачи: выбор конкретного поля."""
    while True:
        print(f"\nРедактирование: {task['title']}")
        print(f"  1 — Дата:        {task['date']}")
        print(f"  2 — Время:       {task['time']}")
        print(f"  3 — Место:       {task['place'] or '(пусто)'}")
        print(f"  4 — Название:    {task['title']}")
        print(f"  5 — Длительность: {task['duration']} мин")
        print(f"  6 — Повтор:       {format_repeat(task.get('repeat', {})) or '(нет)'}")
        print(f"  7 — Описание:    {task['description'] or '(пусто)'}")
        print(f"  8 — Слот:        {task.get('slot', '') or '(пусто)'}")
        print(f"  9 — Третье лицо: {task.get('third_party', '') or '(нет)'}")
        print(f" 10 — Пригласить:  {'да' if task.get('invite', False) else 'нет'}")
        print(f"  0 — Закончить редактирование")

        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            from datetime import datetime
            today = datetime.now()
            new_val = input(f"Новая дата (ДД, ММ-ДД или ГГГГ-ММ-ДД, Enter без изменений) [{task['date']}]: ").strip()
            if new_val:
                if "-" in new_val:
                    parts = new_val.split("-")
                    if len(parts) == 2:
                        task["date"] = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                    elif len(parts) == 3:
                        task["date"] = new_val
                    else:
                        task["date"] = new_val
                else:
                    task["date"] = f"{today.year}-{today.month:02d}-{new_val.zfill(2)}"
        elif choice == "2":
            new_val = input(f"Новое время ({task['time']}): ").strip()
            if new_val:
                task["time"] = new_val
        elif choice == "3":
            new_val = input(f"Новое место ({task['place'] or 'пусто'}): ").strip()
            task["place"] = new_val
        elif choice == "4":
            new_val = input(f"Новое название ({task['title']}): ").strip()
            if new_val:
                task["title"] = new_val
        elif choice == "5":
            new_val = input(f"Новая длительность в минутах ({task['duration']}): ").strip()
            if new_val and new_val.isdigit():
                task["duration"] = int(new_val)
        elif choice == "6":
            print("Типы повтора:")
            print("  0 — Нет (none)")
            print("  1 — Каждый день (daily)")
            print("  2 — По дням недели (weekly)")
            print("  3 — Каждые N минут (interval)")
            rchoice = input(f"Тип (0-3, Enter без изменений): ").strip()
            
            if rchoice == "0":
                task["repeat"] = {"type": "none", "days": [], "interval_minutes": 0, "until": ""}
            
            elif rchoice == "1":
                task["repeat"] = {"type": "daily", "days": [], "interval_minutes": 0, "until": ""}
                print("\nОстановить серию в определённый день?")
                print("  1 — Да")
                print("  2 — Нет (бесконечно)")
                end_choice = input("> ").strip()
                if end_choice == "1":
                    from datetime import datetime
                    today = datetime.now()
                    end_date_str = input("Какого числа закончить? (ДД или ММ-ДД): ").strip()
                    if "-" in end_date_str:
                        parts = end_date_str.split("-")
                        if len(parts) == 2:
                            end_date = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        else:
                            end_date = end_date_str
                    else:
                        end_date = f"{today.year}-{today.month:02d}-{end_date_str.zfill(2)}"
                    task["repeat"]["until"] = f"{end_date}T23:59:59Z"
            
            elif rchoice == "2":
                task["repeat"] = {"type": "weekly", "days": [], "interval_minutes": 0, "until": ""}
                days_str = input("Дни через пробел (1=пн..7=вс): ").strip()
                if days_str:
                    task["repeat"]["days"] = [int(d) for d in days_str.split() if d.isdigit() and 1 <= int(d) <= 7]
                print("\nОстановить серию в определённый день?")
                print("  1 — Да")
                print("  2 — Нет (бесконечно)")
                end_choice = input("> ").strip()
                if end_choice == "1":
                    from datetime import datetime
                    today = datetime.now()
                    end_date_str = input("Какого числа закончить? (ДД или ММ-ДД): ").strip()
                    if "-" in end_date_str:
                        parts = end_date_str.split("-")
                        if len(parts) == 2:
                            end_date = f"{today.year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                        else:
                            end_date = end_date_str
                    else:
                        end_date = f"{today.year}-{today.month:02d}-{end_date_str.zfill(2)}"
                    task["repeat"]["until"] = f"{end_date}T23:59:59Z"
            
            elif rchoice == "3":
                mins_str = input("Интервал в минутах: ").strip()
                interval_mins = int(mins_str) if mins_str and mins_str.isdigit() else 5
                task["repeat"] = {"type": "interval", "days": [], "interval_minutes": interval_mins, "until": ""}
                print("\nОстановить серию в определённое время?")
                print("  1 — Да")
                print("  2 — Нет (бесконечно)")
                end_choice = input("> ").strip()
                if end_choice == "2":
                    print("Внимание: для интервала обязательно указывать время окончания. Укажите.")
                    end_choice = "1"
                if end_choice == "1":
                    end_time_str = input("Во сколько закончить? (ЧЧ:ММ): ").strip()
                    if end_time_str:
                        from datetime import datetime, timedelta
                        try:
                            end_h, end_m = map(int, end_time_str.split(":"))
                            start_h, start_m = map(int, task["time"].split(":"))
                            if end_h < start_h or (end_h == start_h and end_m <= start_m):
                                task_date = datetime.strptime(task["date"], "%Y-%m-%d")
                                next_day = task_date + timedelta(days=1)
                                end_date = next_day.strftime("%Y-%m-%d")
                            else:
                                end_date = task["date"]
                            task["repeat"]["until"] = f"{end_date}T{end_h:02d}:{end_m:02d}:00Z"
                        except:
                            task["repeat"]["until"] = f"{task['date']}T{end_time_str}:00Z"
        
        elif choice == "7":
            new_val = input(f"Новое описание ({task['description'] or 'пусто'}): ").strip()
            task["description"] = new_val
        elif choice == "8":
            new_val = input(f"Новый слот ({task.get('slot', '') or 'пусто'}): ").strip()
            task["slot"] = new_val
        elif choice == "9":
            new_val = input(f"Новое третье лицо ({task.get('third_party', '') or 'нет'}): ").strip()
            task["third_party"] = new_val
        elif choice == "10":
            current = task.get("invite", False)
            new_val = input(f"Пригласить как участника? (да/нет) [{'да' if current else 'нет'}]: ").strip().lower()
            if new_val in ("да", "yes", "y", "1"):
                task["invite"] = True
            elif new_val in ("нет", "no", "n", "0"):
                task["invite"] = False
        else:
            print("Неверный выбор.")

        errors = validate_task(task)
        if errors:
            print("Предупреждение: после изменения есть ошибки:")
            for e in errors:
                print(f"  - {e}")
        else:
            print("OK.")
            # СТ.2: запоминаем дату последнего редактирования
            from datetime import datetime
            task["last_edited"] = datetime.now().strftime("%d.%m %H:%M")

    # --- ОБНОВЛЕНИЕ В КАЛЕНДАРЕ ---
    if task.get("exported") and task.get("caldav_uid"):
        print("Обновляю событие в календаре...")
        old_uid = task["caldav_uid"]
        ok_del = delete_event(old_uid)
        if ok_del:
            print(f"Старое событие удалено ({old_uid})")
        else:
            print("Предупреждение: не удалось удалить старое событие")
        
        if task["repeat"].get("type") == "interval":
            new_uids = create_interval_events(task)
            if new_uids:
                task["caldav_uid"] = new_uids[0]
                print(f"Создана серия из {len(new_uids)} событий.")
            else:
                print("Ошибка: серия не создана. Задача осталась без календаря.")
                task["caldav_uid"] = ""
                task["exported"] = False
        else:
            new_uid = create_event(task)
            if new_uid:
                task["caldav_uid"] = new_uid
                print(f"Новое событие создано: {new_uid}")
            else:
                print("Ошибка: новое событие не создано. Задача осталась без календаря.")
                task["caldav_uid"] = ""
                task["exported"] = False

        # СТ.2: после обновления календаря тоже фиксируем дату
        from datetime import datetime
        task["last_edited"] = datetime.now().strftime("%d.%m %H:%M")

    print("Редактирование завершено.")
    return task
    
    





# ---------- БЛОК 5: УДАЛЕНИЕ ЗАДАЧИ ----------
def delete_task(task):
    """Удаление задачи: сначала из календаря (все события серии), потом из списка."""
    if task["repeat"].get("type") == "interval" and task.get("caldav_uid"):
        # Ищем все события с таким же названием и датой (серия)
        calendar_url = get_calendar_url()
        if calendar_url:
            ok, result = _call_mcp("list-events", {
                "start": task["date"] + "T00:00:00+03:00",
                "end": task["date"] + "T23:59:59+03:00",
                "calendarUrl": calendar_url
            }, timeout=15)
            if ok:
                try:
                    events = json.loads(result['content'][0]['text'])
                    for ev in events:
                        if ev.get("summary") == task["title"]:
                            _call_mcp("delete-event", {"uid": ev["uid"], "calendarUrl": calendar_url}, timeout=10)
                    print(f"Серия удалена.")
                except:
                    print("Не удалось удалить серию — удаляю только из списка.")
    
    elif task.get("caldav_uid"):
        # Одиночное событие или daily/weekly
        delete_event(task["caldav_uid"])
    
    return True





# ---------- БЛОК 6: ВЫГРУЗКА В КАЛЕНДАРЬ ----------
def export_to_calendar(task):
    """Выгрузка одной задачи в Яндекс.Календарь."""
    from datetime import datetime
    
    if task["repeat"].get("type") == "interval":
        uids = create_interval_events(task)
        if uids:
            task["caldav_uid"] = uids[0]
            task["exported"] = True
            task["exported_at"] = datetime.now().isoformat()   # ← V.1 для ручной выгрузки
            print(f"Серия создана: {len(uids)} событий.")
            return True
        else:
            print("Ошибка выгрузки интервальной задачи.")
            return False
    else:
        uid = create_event(task)
        if uid:
            task["caldav_uid"] = uid
            task["exported"] = True
            task["exported_at"] = datetime.now().isoformat()   # ← V.1 для ручной выгрузки
            print(f"Событие создано: {uid}")
            return True
        else:
            print("Ошибка выгрузки задачи.")
            return False


# ---------- БЛОК 7: МАССОВАЯ ВЫГРУЗКА ----------
def export_all_tasks(tasks):
    """Выгрузить все неэкспортированные задачи с паузой."""
    import time
    count = 0
    for task in tasks:
        if not task.get("exported", False):
            if export_to_calendar(task):
                count += 1
                time.sleep(2)
    print(f"Массовая выгрузка завершена. Выгружено: {count} задач.")






# ---------- ГЛАВНАЯ ФУНКЦИЯ РЕЖИМА 3 (цифровое меню) ----------
def run_mode_3():
    """Точка входа в Режим 3. Управление задачами через цифровое меню."""
    from task_data import cleanup_exported_tasks
    cleanup_exported_tasks()
    
    tasks = load_tasks()

    while True:
        sorted_tasks = sort_tasks(tasks)
        command, arg = show_main_menu(sorted_tasks)

        if command == "exit":
            print("Выход из Режима 3.")
            break

        elif command == "export_all":
            export_all_tasks(tasks)
            save_tasks(tasks)

        elif command == "export_selected":
            # Правка 6: выгрузка выбранных задач
            nums_str = input("Номера задач для выгрузки (через пробел): ").strip()
            if not nums_str:
                print("❌ Не введены номера.")
                continue
            
            nums = []
            for part in nums_str.split():
                if part.isdigit():
                    nums.append(int(part))
            
            if not nums:
                print("❌ Нет корректных номеров.")
                continue
            
            exported = 0
            for n in nums:
                if 1 <= n <= len(sorted_tasks):
                    task = sorted_tasks[n - 1]
                    # Ищем в исходном списке
                    for i, t in enumerate(tasks):
                        if t is task or (t.get("title") == task.get("title") and t.get("date") == task.get("date") and t.get("time") == task.get("time")):
                            if export_to_calendar(tasks[i]):
                                exported += 1
                            break
                else:
                    print(f"⚠️ Номер {n} вне диапазона.")
            
            if exported > 0:
                save_tasks(tasks)
                print(f"✅ Выгружено задач: {exported}")

        elif command == "add":
            new_task = add_task_interactive()
            if new_task:
                errors = validate_task(new_task)
                if errors:
                    print("Ошибки валидации:")
                    for e in errors:
                        print(f"  - {e}")
                else:
                    tasks.append(new_task)
                    save_tasks(tasks)
                    print("Задача добавлена.")

        elif command == "edit":
            num_str = input("Номер задачи для редактирования: ").strip()
            if num_str.isdigit():
                n = int(num_str)
                if 1 <= n <= len(sorted_tasks):
                    task = sorted_tasks[n - 1]
                    for i, t in enumerate(tasks):
                        if t is task or (t.get("title") == task.get("title") and t.get("date") == task.get("date") and t.get("time") == task.get("time")):
                            edit_task_interactive(tasks[i])
                            save_tasks(tasks)
                            break
                else:
                    print(f"Номер {n} вне диапазона.")
            else:
                print("Введите число.")

        elif command == "delete":
            nums_str = input("Номера задач для удаления (через пробел): ").strip()
            if not nums_str:
                print("❌ Не введены номера.")
                continue
            
            nums = []
            for part in nums_str.split():
                if part.isdigit():
                    nums.append(int(part))
            
            if not nums:
                print("❌ Нет корректных номеров.")
                continue
            
            removed = 0
            for n in sorted(nums, reverse=True):
                if 1 <= n <= len(sorted_tasks):
                    task = sorted_tasks[n - 1]
                    found = False
                    for i, t in enumerate(tasks):
                        if t is task or (t.get("title") == task.get("title") and t.get("date") == task.get("date") and t.get("time") == task.get("time")):
                            if delete_task(tasks[i]):
                                del tasks[i]
                                print(f"🗑️ Задача №{n} удалена.")
                                removed += 1
                                found = True
                            break
                    if not found:
                        print(f"⚠️ Задача №{n} не найдена.")
                else:
                    print(f"⚠️ Номер {n} вне диапазона.")
            
            if removed > 0:
                save_tasks(tasks)
                print(f"✅ Удалено задач: {removed}")

        elif command == "unknown":
            print(f"Неизвестная команда: {arg}")