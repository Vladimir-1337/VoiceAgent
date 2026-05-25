# profile.py
# Блок F.0: Профиль пользователя — БИНАРНАЯ КРЕПОСТЬ для точной матрицы слотов
# Все данные вводятся строго по регламенту. Никакой философии, только факты.





import json
import os

PROFILE_FILE = "user_profile.json"

import json
import os

PROFILE_FILE = "user_profile.json"

def load_profile():
    """Загружает профиль из файла. Если файла нет — возвращает словарь по умолчанию."""
    default_profile = {
        "city": "",
        "home_coords": "",
        "work_coords": "",
        "current_gastarbeiter_job": "",
        "current_business_calling": "",
        "slot_matrix": None,
        # Якоря МЕСТ
        "anchors": {
            "дом": {"address": "", "coords": ""},
            "работа": {"address": "", "coords": ""}
        },
        # Якоря ЛЮДЕЙ (новое)
        "people_anchors": {}
    }
    if not os.path.exists(PROFILE_FILE):
        return default_profile
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)
            for key, value in default_profile.items():
                if key not in profile:
                    profile[key] = value
            return profile
    except:
        return default_profile
        
        
















def save_profile(profile):
    """Сохраняет профиль в файл."""
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)



def edit_places(profile):
    """Подменю управления местами: город, дом, якорный словарь."""
    while True:
        p = load_profile()
        anchors = p.get("anchors", {})
        anchor_list = list(anchors.keys())
        
        print("\n=== 📍 МЕСТА ===")
        print(f"Город по умолчанию: {p.get('city', 'не указан')}")
        print(f"Координаты дома: {p.get('home_coords', 'не указаны')}")
        
        # --- ТАБЛИЦА ЯКОРЕЙ ---
        print("\n--- Якорные точки ---")
        if anchor_list:
            print(f"{'№':<4} {'Название':<18} {'Доп. названия':<22} {'Адрес':<22} {'Координаты':<18}")
            print("-" * 82)
            for i, name in enumerate(anchor_list, 1):
                a = anchors[name]
                aliases = a.get("aliases", "") or "—"
                addr = a.get("address", "") or "—"
                crd = a.get("coords", "") or "—"
                print(f"{i:<4} {name:<18} {aliases:<22} {addr:<22} {crd:<18}")
        else:
            print("(пусто)")
        
        print(f"\nДействия:")
        print("  1 — Редактировать город")
        print("  2 — Редактировать координаты дома")
        print("  3 — Редактировать якорь по номеру")
        print("  4 — Добавить якорь")
        print("  5 — Удалить якоря (номера через пробел)")
        print("  0 — Назад")
        
        choice = input("> ").strip()
        
        if choice == "0":
            save_profile(p)
            break
        elif choice == "1":
            city = input("Город по умолчанию: ").strip()
            p["city"] = city
            save_profile(p)
        elif choice == "2":
            coords = input("Координаты дома (lat,lon): ").strip()
            p["home_coords"] = coords
            save_profile(p)
        elif choice == "3":
            num_str = input("Номер якоря для редактирования: ").strip()
            if not num_str.isdigit():
                print("❌ Введите число.")
                continue
            idx = int(num_str) - 1
            if not (0 <= idx < len(anchor_list)):
                print("❌ Неверный номер.")
                continue
            
            old_name = anchor_list[idx]
            a = anchors[old_name]
            
            # Подменю выбора поля
            while True:
                print(f"\nРедактирование якоря «{old_name}»:")
                print(f"  1 — Название (ключ): {old_name}")
                print(f"  2 — Доп. названия: {a.get('aliases', '—')}")
                print(f"  3 — Адрес: {a.get('address', '—')}")
                print(f"  4 — Координаты: {a.get('coords', '—')}")
                print("  0 — Закончить")
                field_choice = input("Что изменить? ").strip()
                
                if field_choice == "0":
                    break
                elif field_choice == "1":
                    new_key = input("Новое название якоря: ").strip().lower()
                    if new_key and new_key != old_name:
                        if new_key not in anchors:
                            anchors[new_key] = anchors.pop(old_name)
                            old_name = new_key
                            anchor_list = list(anchors.keys())
                            idx = anchor_list.index(new_key)
                            a = anchors[new_key]
                            p["anchors"] = anchors
                            save_profile(p)
                            print(f"✅ Название изменено на «{new_key}».")
                        else:
                            print("❌ Такой ключ уже существует.")
                    elif not new_key:
                        print("❌ Название не может быть пустым.")
                elif field_choice == "2":
                    new_aliases = input("Доп. названия (через запятую): ").strip()
                    a["aliases"] = new_aliases
                    save_profile(p)
                    print("✅ Доп. названия обновлены.")
                elif field_choice == "3":
                    new_addr = input("Новый адрес: ").strip()
                    a["address"] = new_addr
                    save_profile(p)
                    print("✅ Адрес обновлён.")
                elif field_choice == "4":
                    new_coords = input("Новые координаты (lat,lon): ").strip()
                    a["coords"] = new_coords
                    save_profile(p)
                    print("✅ Координаты обновлены.")
                else:
                    print("❌ Неверный выбор.")
        
        elif choice == "4":
            name = input("Название якоря (основное): ").strip().lower()
            if name:
                if name in anchors:
                    print("❌ Такой якорь уже есть.")
                    continue
                aliases = input("Доп. названия (через запятую, Enter если нет): ").strip()
                addr = input("Адрес (Enter если не важно): ").strip()
                coords = input("Координаты (Enter если не важно): ").strip()
                anchors[name] = {"aliases": aliases, "address": addr, "coords": coords}
                p["anchors"] = anchors
                save_profile(p)
                print(f"✅ Якорь «{name}» добавлен.")
        elif choice == "5":
            nums_str = input("Номера якорей для удаления (через пробел): ").strip()
            if nums_str:
                nums = [int(x) for x in nums_str.split() if x.isdigit()]
                for n in sorted(nums, reverse=True):
                    idx = n - 1
                    if 0 <= idx < len(anchor_list):
                        del_name = anchor_list[idx]
                        del anchors[del_name]
                        print(f"🗑️ «{del_name}» удалён.")
                p["anchors"] = anchors
                save_profile(p)
        else:
            print("❌ Неверный выбор.")

def edit_people(profile):
    """Подменю управления людьми: список контактов для third_party."""
    while True:
        p = load_profile()
        people = p.get("people_anchors", {})
        people_list = list(people.keys())
        
        print("\n=== 👥 ЛЮДИ ===")
        
        # Таблица
        if people_list:
            print(f"{'№':<4} {'Имя':<18} {'Email':<28} {'Пригл (по умолч.)':<18}")
            print("-" * 68)
            for i, name in enumerate(people_list, 1):
                person = people[name]
                email = person.get("email", "") or "—"
                invite = "да" if person.get("invite_default", False) else "нет"
                print(f"{i:<4} {name:<18} {email:<28} {invite:<18}")
        else:
            print("(пусто)")
        
        print(f"\nДействия:")
        print("  1 — Добавить человека")
        print("  2 — Редактировать по номеру")
        print("  3 — Удалить (номера через пробел)")
        print("  0 — Назад")
        
        choice = input("> ").strip()
        
        if choice == "0":
            save_profile(p)
            break
        
        elif choice == "1":
            name = input("Имя (например, мама): ").strip().lower()
            if name:
                if name in people:
                    print("❌ Уже есть.")
                    continue
                email = input("Email (Enter если не нужно): ").strip()
                inv = input("Приглашать по умолчанию? (да/нет): ").strip().lower()
                invite_default = inv in ("да", "yes", "y", "1")
                people[name] = {"email": email, "invite_default": invite_default}
                p["people_anchors"] = people
                save_profile(p)
                print(f"✅ «{name}» добавлен.")
        
        elif choice == "2":
            num_str = input("Номер для редактирования: ").strip()
            if num_str.isdigit():
                idx = int(num_str) - 1
                if 0 <= idx < len(people_list):
                    old_name = people_list[idx]
                    person = people[old_name]
                    while True:
                        print(f"\nРедактирование: {old_name}")
                        print(f"  1 — Имя: {old_name}")
                        print(f"  2 — Email: {person.get('email', '—')}")
                        print(f"  3 — Приглашать: {'да' if person.get('invite_default', False) else 'нет'}")
                        print(f"  0 — Закончить")
                        fchoice = input("Что изменить? ").strip()
                        if fchoice == "0":
                            break
                        elif fchoice == "1":
                            new_name = input("Новое имя: ").strip().lower()
                            if new_name and new_name != old_name:
                                if new_name not in people:
                                    people[new_name] = people.pop(old_name)
                                    old_name = new_name
                                    people_list = list(people.keys())
                                    person = people[new_name]
                                    p["people_anchors"] = people
                                    save_profile(p)
                                    print(f"✅ Имя изменено на «{new_name}».")
                                else:
                                    print("❌ Такое имя уже есть.")
                        elif fchoice == "2":
                            new_email = input("Новый email: ").strip()
                            person["email"] = new_email
                            save_profile(p)
                            print("✅ Email обновлён.")
                        elif fchoice == "3":
                            current = person.get("invite_default", False)
                            new_val = input(f"Приглашать по умолчанию? (да/нет) [{'да' if current else 'нет'}]: ").strip().lower()
                            if new_val in ("да", "yes", "y", "1"):
                                person["invite_default"] = True
                            elif new_val in ("нет", "no", "n", "0"):
                                person["invite_default"] = False
                            save_profile(p)
                            print("✅ Обновлено.")
                        else:
                            print("❌ Неверный выбор.")
                else:
                    print("❌ Неверный номер.")
            else:
                print("❌ Введи число.")
        
        elif choice == "3":
            nums_str = input("Номера для удаления (через пробел): ").strip()
            if nums_str:
                nums = [int(x) for x in nums_str.split() if x.isdigit()]
                for n in sorted(nums, reverse=True):
                    idx = n - 1
                    if 0 <= idx < len(people_list):
                        del_name = people_list[idx]
                        del people[del_name]
                        print(f"🗑️ «{del_name}» удалён.")
                p["people_anchors"] = people
                save_profile(p)
        
        else:
            print("❌ Неверный выбор.")





def save_profile(profile):
    """Сохраняет профиль в файл."""
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


# ---------- AI-КАЛЬКУЛЯТОР МАТРИЦЫ СЛОТОВ (С КЭШИРОВАНИЕМ) ----------
def calculate_slot_matrix(profile, force_recalc=False):
    """
    Отправляет ТОЛЬКО БИНАРНЫЕ ФАКТЫ в ИИ (Claude Haiku).
    ИИ должен УБРАТЬ невозможные комбинации, а не добавлять новые.
    Возвращает матрицу совместимости слотов.
    
    КЭШИРОВАНИЕ:
    - Перед вызовом AI вычисляется хэш всех данных профиля (кроме самой матрицы).
    - Если хэш совпадает с сохранённым profile_hash и матрица уже есть — возвращаем её из кэша.
    - Если данные изменились (или force_recalc=True) — вызываем AI заново.
    """
    import hashlib
    import json

    # --- 1. ВЫЧИСЛЯЕМ ХЭШ ТЕКУЩИХ ДАННЫХ ПРОФИЛЯ (без матрицы и старого хэша) ---
    profile_copy = {k: v for k, v in profile.items() if k not in ["slot_matrix", "profile_hash"]}
    profile_json = json.dumps(profile_copy, sort_keys=True, ensure_ascii=False)
    current_hash = hashlib.md5(profile_json.encode('utf-8')).hexdigest()

    # --- 2. ЕСЛИ ДАННЫЕ НЕ МЕНЯЛИСЬ И МАТРИЦА УЖЕ ЕСТЬ — ВОЗВРАЩАЕМ ИЗ КЭША ---
    if not force_recalc and profile.get("profile_hash") == current_hash and profile.get("slot_matrix"):
        print("✅ Матрица загружена из кэша (данные профиля не менялись).")
        return profile["slot_matrix"]

    print("🔄 Данные профиля изменились или матрица отсутствует. Вызываю AI...")

    # --- 3. ИНАЧЕ — ВЫЗЫВАЕМ AI (СТАРАЯ ЛОГИКА) ---
    from ai_helper import _call_agent_with_messages

    # --- СОБИРАЕМ СУХИЕ ФАКТЫ ДЛЯ ИИ ---
    city = profile.get("city", "не указан")
    home = profile.get("home_coords", "")
    work = profile.get("work_coords", "")
    self_employed = profile.get("self_employed", False)

    # Транспорт: только то, что РАЗРЕШЕНО (True)
    transport = []
    if profile.get("ready_walking"): transport.append("пешком")
    if profile.get("ready_car_driver"): transport.append("авто (водитель)")
    if profile.get("ready_car_passenger"): transport.append("авто (пассажир)")
    if profile.get("ready_taxi"): transport.append("такси")
    if profile.get("ready_public_transport"): transport.append("общественный")
    transport_str = ", ".join(transport) if transport else "НИКАКОЙ"

    # Оборудование: только то, что ЕСТЬ
    equip = []
    if profile.get("has_laptop"): equip.append("ноутбук")
    if profile.get("has_feature_phone"): equip.append("кнопочный телефон")
    if profile.get("has_smartphone"): equip.append("смартфон")
    equip_str = ", ".join(equip) if equip else "НИЧЕГО"

    # Работа: только факты
    work_ready = profile.get("work_ready_multitask", False)
    work_hours = profile.get("work_hours", "")
    work_days_off = profile.get("work_days_off", "")

    # Другие факты — строго как есть
    other = profile.get("other_features", "").strip()

    # --- ДИРЕКТИВНЫЙ ПРОМПТ ДЛЯ ИИ (ТОЛЬКО ИСКЛЮЧЕНИЯ) ---
    prompt = f"""
Ты — эксперт по эргономике. Твоя задача — ЗАПОЛНИТЬ матрицу совместимости слотов («ехать», «делать привычное», «уткнуться в экран») на основе ФАКТОВ о пользователе.

ФАКТЫ (НЕ ОБСУЖДАЮТСЯ):
- Город: {city}
- Координаты дома: {home if home else 'не указаны'}
- Координаты работы: {work if work else 'не указаны'}
- Самозанятый: {'ДА' if self_employed else 'НЕТ'}
- Готовность к транспорту: {transport_str}
- Наличие оборудования: {equip_str}
- Готовность к многозадачности на работе: {'ДА' if work_ready else 'НЕТ'}
- Часы работы: {work_hours if work_hours else 'не указаны'}
- Выходные: {work_days_off if work_days_off else 'не указаны'}
- ДРУГИЕ ФАКТЫ (только для ОГРАНИЧЕНИЙ): {other if other else 'нет'}

ПРАВИЛА ЗАПОЛНЕНИЯ (СТРОГО):
1. Ты НЕ ДОБАВЛЯЕШЬ новые возможности. Только УБИРАЕШЬ то, что противоречит фактам или здравому смыслу.
2. Базовые комбинации по умолчанию (если нет ограничений) считаются РАЗРЕШЁННЫМИ (true).
3. «Авто (водитель)» + «уткнуться в экран» = ВСЕГДА false (небезопасно).
4. Если оборудование не позволяет (нет наушников/смартфона), «уткнуться в экран» с аудио = false.
5. Любой факт из «ДРУГИЕ ФАКТЫ» должен ТОЛЬКО УМЕНЬШАТЬ количество true.
6. Если не уверен — ставь false (безопасный режим).

СЦЕНАРИИ ДЛЯ ЗАПОЛНЕНИЯ (только те, к которым пользователь ГОТОВ):
- пешком
- авто_водитель
- авто_пассажир
- такси
- общественный_стоя
- общественный_сидя_у_окна
- общественный_сидя_не_у_окна

Для каждого сценария верни объект с полями:
"ехать+делать_привычное": true/false,
"ехать+уткнуться_в_экран": true/false,
"делать_привычное+уткнуться_в_экран": true/false

Добавь блок "мультиустройства" с полем "возможно" (true/false) и "ограничения" (строка).
Добавь блок "общение_плюс_экран" с полем "совместимость" (true/false) и "ограничения" (строка).

ФОРМАТ ОТВЕТА: ТОЛЬКО валидный JSON, без пояснений.
"""

    messages = [
        {"role": "system", "content": "Ты — эксперт по эргономике. Отвечай только JSON."},
        {"role": "user", "content": prompt}
    ]

    result = _call_agent_with_messages(messages, temperature=0.1, max_retries=1)

    matrix = None
    if result:
        try:
            import json as json_module
            cleaned = result.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.replace("```", "").strip()
            matrix = json_module.loads(cleaned)
        except Exception as e:
            print(f"⚠️ Ошибка парсинга JSON от AI: {e}")

    # --- ПОСТ-ВАЛИДАЦИЯ: ПРИНУДИТЕЛЬНАЯ БЕЗОПАСНОСТЬ ---
    if matrix:
        # 1. Водитель не может уткнуться в экран
        if "авто_водитель" in matrix:
            matrix["авто_водитель"]["ехать+уткнуться_в_экран"] = False
        # 2. Если нет устройств с экраном — уткнуться некуда
        if not profile.get("has_smartphone") and not profile.get("has_laptop"):
            for scenario in matrix:
                if isinstance(matrix[scenario], dict) and "ехать+уткнуться_в_экран" in matrix[scenario]:
                    matrix[scenario]["ехать+уткнуться_в_экран"] = False
        print("✅ Матрица получена от AI и проверена.")
    else:
        # --- FALLBACK: МАТРИЦА ЗДРАВОГО СМЫСЛА (БЕЗОПАСНАЯ) ---
        print("⚠️ AI не ответил. Использую базовую матрицу здравого смысла.")
        matrix = {
            "пешком": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": True, "делать_привычное+уткнуться_в_экран": True},
            "авто_водитель": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": False, "делать_привычное+уткнуться_в_экран": False},
            "авто_пассажир": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": True, "делать_привычное+уткнуться_в_экран": True},
            "такси": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": True, "делать_привычное+уткнуться_в_экран": True},
            "общественный_стоя": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": False, "делать_привычное+уткнуться_в_экран": False},
            "общественный_сидя_у_окна": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": True, "делать_привычное+уткнуться_в_экран": True},
            "общественный_сидя_не_у_окна": {"ехать+делать_привычное": False, "ехать+уткнуться_в_экран": False, "делать_привычное+уткнуться_в_экран": False},
            "мультиустройства": {"возможно": False, "ограничения": "только при наличии двух экранов"},
            "общение_плюс_экран": {"совместимость": True, "ограничения": "только лёгкий контент"}
        }

    # --- 4. СОХРАНЯЕМ МАТРИЦУ И НОВЫЙ ХЭШ В ПРОФИЛЬ ---
    profile["slot_matrix"] = matrix
    profile["profile_hash"] = current_hash
    save_profile(profile)
    return matrix


# ---------- ИНТЕРФЕЙС ПРОФИЛЯ (С ПОДМЕНЮ) ----------

def show_charter():
    """Показывает БЕСПОЩАДНЫЙ РЕГЛАМЕНТ заполнения профиля."""
    print("""
================================================================================
                    РЕГЛАМЕНТ ЗАПОЛНЕНИЯ ПРОФИЛЯ (ОБЯЗАТЕЛЕН)
================================================================================

Точность Матрицы Слотов зависит от точности твоих данных. Никакой философии.

[1] ГОРОД
    Указывай фактический город проживания. Если пригород — укажи через запятую.
    Пример: "Инкерман, Севастополь"

[2] КООРДИНАТЫ ДОМА
    Открой Яндекс.Карты, найди свой дом, нажми на него и выбери "Копировать
    координаты". Вставь сюда. Формат: "44.123456, 33.654321"
    Если нет постоянного дома — оставь пустым.

[3] КООРДИНАТЫ РАБОТЫ
    Аналогично дому. Скопируй координаты с Яндекс.Карт и вставь.
    Если работа удалённая — напиши "удалённо".
    Если работаешь на себя — включи "Режим самозанятого" в подменю "Работа".

[4] ТРАНСПОРТ (в подменю)
    Отметь ТОЛЬКО те виды транспорта, в которых ты РЕАЛЬНО готов совмещать
    слоты (например, слушать аудио или читать). Если сомневаешься — НЕ отмечай.

[5] ОБОРУДОВАНИЕ (в подменю)
    Отметь ТОЛЬКО те устройства, которые у тебя ЕСТЬ и которыми ты можешь
    пользоваться для задач. Нет устройства — не отмечай.

[6] ДРУГИЕ ФАКТЫ (свободное поле)
    Вводи ТОЛЬКО проверяемые факты, которые МЕШАЮТ совмещать слоты.
    Формат: "Факт: описание". Разделяй факты ЗАПЯТОЙ.
    Пример: "Факт: быстро укачивает при чтении, Факт: в автобусе всегда стою"
    НЕ пиши эмоции или предположения. Только то, что можно проверить.

[7] О СЕБЕ (новый раздел)
    · Гастарбайтерское дело — чем зарабатываешь на хлеб и крышу.
    · Призвание / бизнес — что развиваешь как своё дело.

================================================================================
Заполнил неточно — получил неработающую матрицу. Ответственность на тебе.
================================================================================
""")


def edit_work(profile):
    """Подменю настройки работы — только гастарбайтер и призвание."""
    while True:
        print("\n--- 💼 РАБОТА ---")
        print(f"1. Гастарбайтерское дело (хлеб и крыша): {profile.get('current_gastarbeiter_job', '') or 'не указано'}")
        print(f"2. Призвание / своё дело: {profile.get('current_business_calling', '') or 'не указано'}")
        print("0. Назад")
        
        choice = input("Выберите пункт (1-2): ").strip()
        if choice == "0":
            break
        elif choice == "1":
            val = input("Введите гастарбайтерское дело (например, разнорабочий): ").strip()
            profile["current_gastarbeiter_job"] = val
            save_profile(profile)
            print("✅ Сохранено.")
        elif choice == "2":
            val = input("Введите призвание / бизнес (например, аниматор): ").strip()
            profile["current_business_calling"] = val
            save_profile(profile)
            print("✅ Сохранено.")
        else:
            print("❌ Неверный выбор.")
                
                
                

def edit_transport(profile):
    """Подменю настройки транспорта (галочки)."""
    while True:
        print("\n--- ГОТОВНОСТЬ К ТРАНСПОРТУ (отметь только то, где готов совмещать) ---")
        items = [
            ("Пешком", "ready_walking"),
            ("Авто (водитель)", "ready_car_driver"),
            ("Авто (пассажир)", "ready_car_passenger"),
            ("Такси", "ready_taxi"),
            ("Общественный транспорт", "ready_public_transport")
        ]
        for i, (label, key) in enumerate(items, 1):
            status = "✅" if profile.get(key, False) else "❌"
            print(f"{i}. {label}: {status}")
        print("0. Назад")
        choice = input("Выберите пункт для переключения (1-5): ").strip()
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                key = items[idx][1]
                profile[key] = not profile.get(key, False)
                save_profile(profile)
            else:
                print("❌ Неверный номер.")
        except:
            print("❌ Неверный ввод.")

def edit_equipment(profile):
    """Подменю настройки оборудования (галочки)."""
    while True:
        print("\n--- НАЛИЧИЕ ОБОРУДОВАНИЯ (отметь только то, что есть) ---")
        items = [
            ("Ноутбук", "has_laptop"),
            ("Кнопочный телефон", "has_feature_phone"),
            ("Смартфон", "has_smartphone")
        ]
        for i, (label, key) in enumerate(items, 1):
            status = "✅" if profile.get(key, False) else "❌"
            print(f"{i}. {label}: {status}")
        print("0. Назад")
        choice = input("Выберите пункт для переключения (1-3): ").strip()
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                key = items[idx][1]
                profile[key] = not profile.get(key, False)
                save_profile(profile)
            else:
                print("❌ Неверный номер.")
        except:
            print("❌ Неверный ввод.")

def edit_profile():
    """Главное меню профиля — простое. 0 = Назад."""
    while True:
        p = load_profile()
        print("\n=== ПРОФИЛЬ ===")
        print(f"1. 📍 Места (город, дом, якоря)")
        print(f"2. 👥 Люди (контакты)")
        print(f"3. 💼 Работа (гастарбайтер / призвание)")
        print("0. Назад")

        choice = input("Выберите поле (0-3): ").strip()
        if choice == "0":
            break
        elif choice == "1":
            edit_places(p)
        elif choice == "2":
            edit_people(p)
        elif choice == "3":
            # Простая форма: только гастарбайтер и призвание
            while True:
                print("\n--- 💼 РАБОТА ---")
                print(f"1. Гастарбайтерское дело: {p.get('current_gastarbeiter_job', '') or 'не указано'}")
                print(f"2. Призвание / своё дело: {p.get('current_business_calling', '') or 'не указано'}")
                print("0. Назад")
                c = input("Выберите пункт (1-2): ").strip()
                if c == "0":
                    break
                elif c == "1":
                    val = input("Введите гастарбайтерское дело (например, разнорабочий): ").strip()
                    p["current_gastarbeiter_job"] = val
                    save_profile(p)
                    print("✅ Сохранено.")
                elif c == "2":
                    val = input("Введите призвание / бизнес (например, аниматор): ").strip()
                    p["current_business_calling"] = val
                    save_profile(p)
                    print("✅ Сохранено.")
                else:
                    print("❌ Неверный выбор.")
        else:
            print("❌ Неверный выбор.")