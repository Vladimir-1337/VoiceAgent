# intent_parser.py — Парсер для режима «Напомни»
# Блок C.1: Стоп-слова глаголов


import re

from anchor_resolver import resolve_place, scan_person


STOP_VERBS = [
    # Покупки и финансы
    "купить", "купи", "заплатить", "заплати", "оплатить", "оплати",
    "снять", "сними", "пополнить", "пополни",
    
    # Здоровье и тело
    "вылечить", "вылечи", "записаться", "запишись", "сходить", "сходи",
    "принять", "прими", "сделать", "сделай",
    
    # Работа и дела
    "позвонить", "позвони", "написать", "напиши", "отправить", "отправь",
    "забрать", "забери", "отвезти", "отвези", "встретить", "встреть",
    "проверить", "проверь", "доделать", "доделай",
    "зарегистрировать", "зарегистрируй",
    
    # Дом и быт
    "убрать", "убери", "постирать", "постирай", "приготовить", "приготовь",
    "помыть", "помой", "починить", "почини",
    
    # Учёба и развитие
    "прочитать", "прочитай", "выучить", "выучи", "посмотреть", "посмотри",
    "послушать", "послушай", "узнать", "узнай",
    
    # Общее
    "зайти", "зайди", "найти", "найди", "взять", "возьми",
    "оформить", "оформи", "получить", "получи", "передать", "передай"
]


ORG_MARKERS = [
    # =================================================================
    # 1. ОРГАНЫ ВЛАСТИ И УПРАВЛЕНИЯ (на основе ОКОПФ и КЛАДР)
    # =================================================================
    "администрация", "управа", "мэрия", "правительство", "дума",
    "совет федерации", "госдума", "заксобрание", "парламент",
    "министерство", "департамент", "комитет", "управление",
    "инспекция", "надзор", "служба", "агентство", "комиссия",
    "избирком", "счетная палата", "омбудсмен", "уполномоченный",
    "префектура", "посольство", "консульство",

    # =================================================================
    # 2. ПРАВООХРАНИТЕЛЬНЫЕ И СИЛОВЫЕ СТРУКТУРЫ
    # =================================================================
    "полиция", "дпс", "гаи", "гибдд", "мвд", "фсб", "мчс",
    "прокуратура", "суд", "трибунал", "следственный комитет",
    "таможня", "фссп", "приставы", "росгвардия", "военкомат",
    "воинская часть", "исправительная колония", "сизо", "тюрьма",
    "фсин", "фсо", "фельдъегерская служба",

    # =================================================================
    # 3. МЕДИЦИНСКИЕ ОРГАНИЗАЦИИ (СП 136.13330.2012)
    # =================================================================
    "поликлиника", "больница", "госпиталь", "клиника", "диспансер",
    "роддом", "травмпункт", "скорая помощь", "амбулатория",
    "санэпидемстанция", "санэпиднадзор", "роспотребнадзор",
    "медсанчасть", "хоспис", "санаторий", "профилакторий",
    "диагностический центр", "лаборатория", "аптека", "оптика",
    "ветеринарная клиника", "ветеринарная станция",

    # =================================================================
    # 4. ОБРАЗОВАТЕЛЬНЫЕ УЧРЕЖДЕНИЯ
    # =================================================================
    "школа", "гимназия", "лицей", "детсад", "садик", "ясли",
    "университет", "институт", "академия", "колледж", "техникум",
    "училище", "музыкальная школа", "музшкола", "художественная школа",
    "художка", "спортивная школа", "спортшкола", "автошкола",
    "центр дополнительного образования", "дом творчества",
    "школа искусств", "вечерняя школа", "коррекционная школа",
    "интернат", "кадетский корпус", "суворовское училище",

    # =================================================================
    # 5. СОЦИАЛЬНЫЕ УЧРЕЖДЕНИЯ
    # =================================================================
    "соцзащита", "собес", "пенсионный фонд", "социальный фонд",
    "мфц", "паспортный стол", "загс", "центр занятости",
    "биржа труда", "дом престарелых", "дом инвалидов",
    "реабилитационный центр", "приют", "ночлежка",
    "центр социального обслуживания", "собеседование",
    "бюро медико-социальной экспертизы", "мсэ",

    # =================================================================
    # 6. ФИНАНСОВЫЕ И БАНКОВСКИЕ УЧРЕЖДЕНИЯ
    # =================================================================
    "банк", "сбербанк", "втб", "россельхозбанк", "страховая компания",
    "страховой дом", "пенсионный фонд", "негосударственный пенсионный фонд",
    "ломбард", "обменник", "платежный терминал", "кредитный союз",
    "микрофинансовая организация", "мфо", "расчетный центр",

    # =================================================================
    # 7. КУЛЬТУРНЫЕ И ДОСУГОВЫЕ УЧРЕЖДЕНИЯ
    # =================================================================
    "библиотека", "музей", "театр", "кинотеатр", "дк", "дом культуры",
    "филармония", "цирк", "планетарий", "выставочный зал", "галерея",
    "концертный зал", "зоопарк", "океанариум", "дельфинарий",
    "парк аттракционов", "аквапарк", "клуб", "дискотека",

    # =================================================================
    # 8. СПОРТИВНЫЕ И ФИЗКУЛЬТУРНЫЕ ОБЪЕКТЫ
    # =================================================================
    "стадион", "бассейн", "спорткомплекс", "спортивный комплекс",
    "фитнес", "тренажерный зал", "каток", "ледовая арена",
    "теннисный корт", "гольф-клуб", "ипподром", "автодром",
    "мотодром", "велотрек", "спортзал", "фок", "физкультурно-оздоровительный комплекс",

    # =================================================================
    # 9. ТОРГОВЫЕ И БЫТОВЫЕ ОРГАНИЗАЦИИ
    # =================================================================
    "рынок", "ярмарка", "тц", "торговый центр", "торговый комплекс",
    "молл", "гипермаркет", "супермаркет", "универмаг", "универсам",
    "магазин", "аптека", "оптика", "автосалон", "авторынок",
    "химчистка", "прачечная", "ателье", "ремонт обуви",
    "парикмахерская", "салон красоты", "спа", "баня", "сауна",
    "гостиница", "отель", "хостел", "общежитие",

    # =================================================================
    # 10. ТРАНСПОРТНЫЕ И ЛОГИСТИЧЕСКИЕ ОБЪЕКТЫ
    # =================================================================
    "вокзал", "аэропорт", "автостанция", "автовокзал",
    "железнодорожная станция", "жд станция", "платформа",
    "депо", "метро", "станция метро", "порт", "причал",
    "таможенный пост", "склад", "терминал", "логистический центр",
    "почта", "почтамт", "отделение связи",

    # =================================================================
    # 11. РЕЛИГИОЗНЫЕ ОРГАНИЗАЦИИ
    # =================================================================
    "церковь", "храм", "мечеть", "синагога", "собор",
    "монастырь", "часовня", "костел", "кирха", "дацан",

    # =================================================================
    # 12. ПРОЧИЕ УЧРЕЖДЕНИЯ И ОРГАНИЗАЦИИ
    # =================================================================
    "кладбище", "крематорий", "колумбарий",
    "типография", "издательство", "редакция",
    "телестудия", "радиостанция", "телецентр",
    "обсерватория", "метеостанция", "сейсмостанция",
    "заповедник", "заказник", "национальный парк",
    "питомник", "ветеринарная станция", "станция по борьбе с болезнями животных",
    "общество", "союз", "ассоциация", "фонд", "гильдия",
    "палата", "коллегия", "партия", "движение",
    "гаражный кооператив", "гараж", "автостоянка", "парковка",
    "жилконтора", "жэк", "тсж", "управляющая компания",
    "общежитие", "хостел", "мини-отель"
]









# ---------------------------------------------------------------------------
# Блок C.2: Сканер «Напомни»
# ---------------------------------------------------------------------------

def scan_remind(text):
    """
    Ищет в тексте слово 'напомни' (любой регистр).
    Если находит — активирует флаг has_remind и ВЫРЕЗАЕТ слово из текста.
    
    Вход:  строка (например, "Напомни купить носки")
    Выход: (has_remind, clean_text)
           has_remind = True/False
           clean_text = текст без слова 'напомни'
    """
    # Приводим к нижнему регистру для поиска, но оригинал сохраняем для вырезания
    text_lower = text.lower()
    
    # Ищем точное вхождение слова "напомни"
    idx = text_lower.find("напомни")
    
    if idx == -1:
        # Слово не найдено — возвращаем флаг False и исходный текст без изменений
        return (False, text)
    
    # Слово найдено — вырезаем его из исходного текста
    # [0:idx] — всё до слова, [idx+7:] — всё после слова (длина "напомни" = 7 символов)
    before = text[:idx]
    after = text[idx + 7:]
    clean_text = before + after
    
    # Убираем возможный двойной пробел на месте склейки
    clean_text = " ".join(clean_text.split())
    
    return (True, clean_text)
    
    
    
    
    
    
    
    
    
    
# ---------------------------------------------------------------------------
# Блок C.3: Сканер смещения напоминания
# ---------------------------------------------------------------------------

def scan_reminder_offset(text):
    """
    Ищет конструкцию 'за X часов Y минут' (составную) или простую 'за X минут/часов'.
    Возвращает смещение в формате ISO 8601 duration и чистый текст.
    """
    # Сначала ищем составной интервал: за X час(ов) Y минут
    pattern_complex = r'за\s+(\d+)\s*(час|часа|часов)\s+(\d+)\s*(минут|минуту|минуты)'
    match = re.search(pattern_complex, text, re.IGNORECASE)
    if match:
        hours = int(match.group(1))
        mins = int(match.group(3))
        total_minutes = hours * 60 + mins
        clean_text = text[:match.start()] + text[match.end():]
        clean_text = " ".join(clean_text.split())
        if total_minutes >= 60:
            h = total_minutes // 60
            m = total_minutes % 60
            offset = f"-PT{h}H{m}M" if m else f"-PT{h}H"
        else:
            offset = f"-PT{total_minutes}M"
        return (offset, clean_text)

    # Простой интервал: за X минут/часов или за час/минуту
    pattern_simple = r'за\s+(\d+)?\s*(минут|минуту|час|часа|часов)'
    match = re.search(pattern_simple, text, re.IGNORECASE)
    if not match:
        return (None, text)

    number_str = match.group(1)
    unit = match.group(2)
    amount = int(number_str) if number_str else 1
    if unit in ("час", "часа", "часов"):
        total_minutes = amount * 60
    else:
        total_minutes = amount

    clean_text = text[:match.start()] + text[match.end():]
    clean_text = " ".join(clean_text.split())
    if total_minutes >= 60:
        h = total_minutes // 60
        m = total_minutes % 60
        offset = f"-PT{h}H{m}M" if m else f"-PT{h}H"
    else:
        offset = f"-PT{total_minutes}M"
    return (offset, clean_text)
    
    
    
    
    
    
# ---------------------------------------------------------------------------
# Блок C.4: Сканер абсолютного времени
# ---------------------------------------------------------------------------

def scan_absolute_time(text):
    """
    Ищет в тексте конструкции абсолютного времени и возвращает ЧЧ:ММ.
    Умеет понимать "пол второго", "четверть пятого" как дневное время (12–17 часов),
    а "пол первого" как 12:30, "пол двенадцатого" как 11:30 и т.д.
    """
    ordinals = {
        "первого": 1, "второго": 2, "третьего": 3, "четвертого": 4,
        "пятого": 5, "шестого": 6, "седьмого": 7, "восьмого": 8,
        "девятого": 9, "десятого": 10, "одиннадцатого": 11, "двенадцатого": 12
    }

    text_lower = text.lower()
    found_time = None
    found_start = None
    found_end = None

    # 1. "в HH:MM" или "в HH.MM"
    match = re.search(r'в\s+(\d{1,2})[:.](\d{2})', text_lower)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
    else:
        # "в HH часов/час/часа"
        match = re.search(r'в\s+(\d{1,2})\s*(?:часов|час|часа)?', text_lower)
        if match:
            hour = int(match.group(1))
            minute = 0
        else:
            match = None

    if match:
        found_time = f"{hour:02d}:{minute:02d}"
        found_start = match.start()
        found_end = match.end()

    # 2. "пол первого", "пол второго" и т.д.
    if not found_time:
        match = re.search(r'пол\s+(первого|второго|третьего|четвертого|пятого|шестого|седьмого|восьмого|девятого|десятого|одиннадцатого|двенадцатого)', text_lower)
        if match:
            ordinal_word = match.group(1)
            base_hour = ordinals[ordinal_word] - 1   # "пол первого" – это 12:30, "пол второго" – 1:30 и т.д.
            if base_hour == -1:
                base_hour = 11  # "пол первого" превращается в 12:30, а base_hour берём 11, потом прибавим 12
            # Если время похоже на день/вечер (с 10 утра до 11 вечера), добавляем 12 часов,
            # чтобы "пол второго" стало 13:30, "пол пятого" – 16:30 и т.д.
            # Для ночных/ранних утренних (до 10 утра) оставляем как есть.
            # "пол двенадцатого" = 11:30 – остаётся.
            hour = base_hour
            if 10 <= (hour % 12) <= 11:   # 10, 11 утра — уже светло, не трогаем
                pass
            elif hour < 10:               # 0–9 часов утра – добавляем 12, если это не "пол первого"
                hour += 12
            # "пол первого" (base_hour=11) даёт 11 + 12 = 23? Нет, для "пол первого" особая логика:
            if ordinal_word == "первого":
                hour = 12  # 12:30
            found_time = f"{hour:02d}:30"
            found_start = match.start()
            found_end = match.end()

    # 3. "четверть пятого" и т.д.
    if not found_time:
        match = re.search(r'четверть\s+(первого|второго|третьего|четвертого|пятого|шестого|седьмого|восьмого|девятого|десятого|одиннадцатого|двенадцатого)', text_lower)
        if match:
            ordinal_word = match.group(1)
            base_hour = ordinals[ordinal_word] - 1
            if base_hour == -1:
                base_hour = 11
            hour = base_hour
            if ordinal_word == "первого":
                hour = 12
            elif hour < 10:
                hour += 12
            found_time = f"{hour:02d}:15"
            found_start = match.start()
            found_end = match.end()

    # 4. "ровно 12", "ровно в 12"
    if not found_time:
        match = re.search(r'ровно\s+(?:в\s+)?(\d{1,2})', text_lower)
        if match:
            hour = int(match.group(1))
            found_time = f"{hour:02d}:00"
            found_start = match.start()
            found_end = match.end()

    # 5. Голое "HH:MM" (без предлога)
    if not found_time:
        match = re.search(r'\b(\d{1,2}):(\d{2})\b', text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                found_time = f"{hour:02d}:{minute:02d}"
                found_start = match.start()
                found_end = match.end()

    if not found_time:
        return (None, text)

    clean_text = text[:found_start] + text[found_end:]
    clean_text = " ".join(clean_text.split())
    return (found_time, clean_text)    
    
    
    
    
# intent_parser.py — Блок C.5: Сканер даты (финал с падежами)

def scan_date(text):
    from datetime import datetime, timedelta
    
    today = datetime.now()
    text_lower = text.lower()
    found_date = None
    found_start = None
    found_end = None
    
    # --- 1. "сегодня", "завтра", "послезавтра" ---
    for word, delta in [("послезавтра", 2), ("завтра", 1), ("сегодня", 0)]:
        match = re.search(r'\b' + word + r'\b', text_lower)
        if match:
            target = today + timedelta(days=delta)
            found_date = target.strftime("%Y-%m-%d")
            found_start = match.start()
            found_end = match.end()
            break
    
    # --- 2. ДНИ НЕДЕЛИ (с падежами) ---
    if not found_date:
        # Словарь: все падежные формы → номер дня недели
        day_forms = {
            # понедельник
            "понедельник": 0, "понедельника": 0, "понедельнику": 0, "понедельником": 0, "понедельнике": 0,
            # вторник
            "вторник": 1, "вторника": 1, "вторнику": 1, "вторником": 1, "вторнике": 1,
            # среда
            "среда": 2, "среды": 2, "среде": 2, "среду": 2, "средой": 2,
            # четверг
            "четверг": 3, "четверга": 3, "четвергу": 3, "четвергом": 3, "четверге": 3,
            # пятница
            "пятница": 4, "пятницы": 4, "пятнице": 4, "пятницу": 4, "пятницей": 4,
            # суббота
            "суббота": 5, "субботы": 5, "субботе": 5, "субботу": 5, "субботой": 5,
            # воскресенье
            "воскресенье": 6, "воскресенья": 6, "воскресенью": 6, "воскресеньем": 6, "воскресенье": 6,
        }
        
        # 2.1 "в следующий понедельник", "в следующий вторник"...
        match = re.search(r'в следующий\s+(' + '|'.join(day_forms.keys()) + r')', text_lower)
        if not match:
            # 2.2 "на этой неделе в пятницу"...
            match = re.search(r'на этой неделе\s+в\s+(' + '|'.join(day_forms.keys()) + r')', text_lower)
        if not match:
            # 2.3 просто "в субботу", "в понедельник"...
            match = re.search(r'\bв\s+(' + '|'.join(day_forms.keys()) + r')\b', text_lower)
        
        if match:
            day_form = match.group(1)
            target_wd = day_forms[day_form]
            current_wd = today.weekday()
            days_ahead = (target_wd - current_wd) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            found_date = target.strftime("%Y-%m-%d")
            found_start = match.start()
            found_end = match.end()
    
    # --- 3. "25 мая" (число + название месяца) ---
    if not found_date:
        months = {
            "января": 1, "янв": 1, "февраля": 2, "фев": 2,
            "марта": 3, "мар": 3, "апреля": 4, "апр": 4,
            "мая": 5, "май": 5, "июня": 6, "июн": 6,
            "июля": 7, "июл": 7, "августа": 8, "авг": 8,
            "сентября": 9, "сен": 9, "октября": 10, "окт": 10,
            "ноября": 11, "ноя": 11, "декабря": 12, "дек": 12
        }
        match = re.search(r'(\d{1,2})\s*(?:\.|\s+)?(' + '|'.join(months.keys()) + r')', text_lower)
        if match:
            day = int(match.group(1))
            month_name = match.group(2)
            month = months[month_name]
            try:
                target = datetime(today.year, month, day)
                if target < today:
                    target = datetime(today.year + 1, month, day)
                found_date = target.strftime("%Y-%m-%d")
                found_start = match.start()
                found_end = match.end()
            except ValueError:
                pass
    
    # --- 4. "25.05" или "25.5" ---
    if not found_date:
        match = re.search(r'\b(\d{1,2})\.(\d{1,2})\b', text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    target = datetime(today.year, month, day)
                    if target < today:
                        target = datetime(today.year + 1, month, day)
                    found_date = target.strftime("%Y-%m-%d")
                    found_start = match.start()
                    found_end = match.end()
                except ValueError:
                    pass
    
    # --- 5. "2026-05-25" (ISO) ---
    if not found_date:
        match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', text)
        if match:
            found_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            found_start = match.start()
            found_end = match.end()
    
    if not found_date:
        return (None, text)
    
    clean_text = text[:found_start] + text[found_end:]
    clean_text = " ".join(clean_text.split())
    return (found_date, clean_text)
    
    
# ---------------------------------------------------------------------------
# Блок C.6: Сканер места — НОВАЯ ВЕРСИЯ (с фиксом типов улиц)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Блок C.6: Сканер места — НОВАЯ ВЕРСИЯ (фикс: время не ломает поиск места)
# ---------------------------------------------------------------------------


def _result_matches(result, place_word):
    """Проверяет, что хотя бы одно значимое слово из place_word есть в result."""
    words = place_word.lower().split()
    significant = [w for w in words if not w.isdigit() and len(w) > 2]
    if not significant:
        significant = [w for w in words if not w.isdigit()] or words
    return any(w in result.lower() for w in significant)


def scan_place(text):
    """
    Ищет место: якорь → маркер → Nominatim → xmlriver → fallback.
    Возвращает (place, clean_text).
    """
    city = "Севастополь"
    try:
        from profile import load_profile
        profile = load_profile()
        city = profile.get("city", "").strip() or "Севастополь"
    except:
        pass

    print(f"  [SCAN_PLACE] Старт: «{text[:60]}»")

    # ФИКС: Вырезаем время ("в 10:23", "в 10.23"), чтобы не ломало поиск предлога
    text = re.sub(r'\b(?:в|к|во)\s+\d{1,2}[.:]\d{2}\b', '', text)
    text = " ".join(text.split())

    # Шаг 1: Якорь
    try:
        from anchor_resolver import resolve_place
        address, clean = resolve_place(text)
        if address:
            print(f"  [SCAN_PLACE] ✅ Якорь: {address}")
            return (address, clean)
    except:
        pass

    print(f"  [SCAN_PLACE] Якорь не найден")

    # Шаг 2: Предлог + слово
    match = re.search(
        r'(?:в|на|у|возле|рядом с|около)\s+'
        r'([А-Яа-яЁёA-Za-z0-9\-]+(?:\s*(?:номер\s*)?\d+)?)',
        text,
        re.IGNORECASE
    )
    if not match:
        print(f"  [SCAN_PLACE] ⚠️ Предлог не найден")
        return (None, text)

    place_word = match.group(1)
    start_idx = match.start()
    end_idx = match.end()

    # ФИКС: если place_word — это тип улицы, берём следующее слово как название
    street_types = [
        "улице", "улица", "ул", "проспект", "проспекте", "пр",
        "переулок", "переулке", "бульвар", "бульваре", "шоссе",
        "площадь", "площади", "набережная", "набережной",
        "проезд", "проезде", "тупик", "тупике"
    ]
    if place_word.lower() in street_types:
        rest = text[end_idx:].strip()
        next_match = re.match(r'([А-Яа-яЁёA-Za-z0-9\-]+(?:\s*\d+[а-я]?)?)', rest)
        if next_match:
            place_word = next_match.group(1)
            end_idx += next_match.end()
            print(f"  [SCAN_PLACE] Тип улицы «{match.group(1)}» → название: «{place_word}»")

    clean_text = text[:start_idx] + text[end_idx:]
    clean_text = " ".join(clean_text.split())

    print(f"  [SCAN_PLACE] Предлог + слово: «{place_word}»")

    # Шаг 3: Маркер или «номер»
    is_org = _check_marker(place_word)
    has_nomer = "номер" in place_word.lower()

    if is_org or has_nomer:
        print(f"  [SCAN_PLACE] Маркер/номер → xmlriver")
        result = _xmlriver_search(place_word, city)
        if result:
            if _result_matches(result, place_word):
                print(f"  [SCAN_PLACE] ✅ xmlriver: {result}")
                return (result, clean_text)
            else:
                print(f"  [SCAN_PLACE] ⚠️ xmlriver: '{result}' не совпадает с '{place_word}'")
        else:
            print(f"  [SCAN_PLACE] ❌ xmlriver не нашёл")

    # Шаг 4: Цифры
    digits = re.findall(r'\d+', place_word)
    if digits:
        print(f"  [SCAN_PLACE] Цифры {digits} → Nominatim")
        result = _nominatim_search(place_word, city)
        if result:
            print(f"  [SCAN_PLACE] ✅ Nominatim: {result}")
            return (result, clean_text)
        else:
            print(f"  [SCAN_PLACE] Nominatim не нашёл → xmlriver")
            result = _xmlriver_search(place_word, city)
            if result:
                if _result_matches(result, place_word):
                    print(f"  [SCAN_PLACE] ✅ xmlriver: {result}")
                    return (result, clean_text)
                else:
                    print(f"  [SCAN_PLACE] ⚠️ xmlriver: '{result}' не совпадает с '{place_word}'")
    else:
        print(f"  [SCAN_PLACE] Нет цифр")
        if _has_street(place_word):
            print(f"  [SCAN_PLACE] Улица найдена → xmlriver")
            result = _xmlriver_search(place_word, city)
            if result:
                if _result_matches(result, place_word):
                    print(f"  [SCAN_PLACE] ✅ xmlriver: {result}")
                    return (result, clean_text)
                else:
                    print(f"  [SCAN_PLACE] ⚠️ xmlriver: '{result}' не совпадает с '{place_word}'")
        else:
            print(f"  [SCAN_PLACE] Улица не найдена → fallback")

    # Шаг 5: Fallback
    if city.lower() not in place_word.lower():
        place = f"{place_word}, {city}"
    else:
        place = place_word
    print(f"  [SCAN_PLACE] ⚠️ Fallback: {place}")
    return (place, clean_text)


# ======================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ scan_place
# ======================================================================

def _check_marker(word):
    """Проверяет, есть ли слово в маркерах организаций (по корню)."""
    word_lower = word.lower()
    for marker in ORG_MARKERS:
        root = marker[:-2] if len(marker) > 4 else marker
        if root and root in word_lower:
            return True
    return False


def _has_street(word):
    """Проверяет, есть ли в слове указание на улицу."""
    street_markers = [
        "улица", "проспект", "бульвар", "переулок", "площадь",
        "набережная", "шоссе", "проезд", "тупик", "аллея",
        "октябрьск", "ленина", "пушкин", "хрусталёв", "остряков",
    ]
    word_lower = word.lower()
    for s in street_markers:
        if s in word_lower:
            return True
    return False


def _nominatim_search(place_word, city):
    """Быстрый поиск адреса через Nominatim."""
    try:
        import requests as _req
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{place_word}, {city}",
            "format": "json", "limit": 3, "addressdetails": 1,
            "accept-language": "ru",
            "bounded": 1,
            "viewbox": "33.35,44.55,33.65,44.65"
        }
        r = _req.get(url, params=params, timeout=5,
                      headers={"User-Agent": "Organizer/1.0"})
        data = r.json()
        if not data:
            return None
        digits = re.findall(r'\d+', place_word)
        for item in data:
            addr = item.get("address", {})
            road = addr.get("road", "")
            house = addr.get("house_number", "")
            full = f"{road} {house}".strip()
            if digits:
                if any(d in full for d in digits):
                    return f"{full}, {city}"
            else:
                return f"{full}, {city}"
        return None
    except:
        return None


def _xmlriver_search(full_text, city):
    """Поиск организации/адреса через xmlriver."""
    try:
        import requests as _req
        import xml.etree.ElementTree as ET
        from collections import Counter

        USER = "20826"
        KEY = "8e4f11bb7912d7b3bbf35ed58a1b5345406e3611"

        url = "http://xmlriver.com/search_yandex/xml"
        params = {
            "user": USER,
            "key": KEY,
            "query": f"{full_text} {city} адрес",
            "lr": "959",
            "groupby": "attr=d.mode=deep.groups-on-page=3.docs-in-group=3"
        }
        r = _req.get(url, params=params, timeout=20)
        root = ET.fromstring(r.text)
        docs = root.findall(".//doc")
        if not docs:
            return None

        patterns = [
            r'(?:пр|просп|проспект)\.?\s*[А-Яа-яёЁ\s]+Революции\s*,?\s*\d+\s*[а-я]?',
            r'ул\.?\s*[А-Яа-яёЁ\s]+\s*,?\s*\d+\s*[а-я]?',
            r'улица\s+[А-Яа-яёЁ\s]+\s*,?\s*\d+\s*[а-я]?',
            r'Севастополь\s*,?\s*(?:ул|пр|проспект|улица)\.?\s*[^,.]+\s*,?\s*\d+',
            r'проспект\s+Октябрьской\s+Революции\s*,?\s*\d+\s*[а-я]?',
            r'Октябрьской\s+Революции\s*,?\s*\d+\s*[а-я]?',
            r'Хрусталёва\s*,?\s*\d+\s*[а-я]?',
            r'Пушкина\s*,?\s*\d+\s*[а-я]?',
            r'Острякова\s*,?\s*\d+\s*[а-я]?',
            r'д\.\s*\d+\s*[а-я]?',
        ]
        all_addresses = []
        for doc in docs[:3]:
            url_el = doc.find("url")
            if url_el is None or not url_el.text:
                continue
            try:
                page = _req.get(url_el.text, timeout=5,
                                 headers={"User-Agent": "Mozilla/5.0"})
                clean = re.sub(r'<[^>]+>', ' ', page.text)
                clean = re.sub(r'\s+', ' ', clean)
                for pat in patterns:
                    for m in re.findall(pat, clean, re.IGNORECASE):
                        m_clean = m.strip()
                        if len(m_clean) > 5:
                            all_addresses.append(m_clean)
            except:
                pass
        if not all_addresses:
            return None
        counter = Counter(all_addresses)
        best = counter.most_common(1)[0][0]
        return f"{best}, {city}"
    except:
        return None
    
    


def parse_intent(text):
    """
    Главная функция парсинга.
    Работает как с триггером «напомни», так и без него.
    """
    raw_text = text

    # 1. Режим «Напомни»
    has_remind, text = scan_remind(text)

    # 2. Смещение напоминания
    reminder_offset, text = scan_reminder_offset(text)

    # 3. Абсолютное время
    time_val, text = scan_absolute_time(text)

    # 4. Дата
    date_val, text = scan_date(text)

    # 5. Место (якоря)
    place_val, text = scan_place(text)

    # 6. Люди (F.2: вырезаем имена из текста)
    person_val, person_email, person_invite, text = scan_person(text)

    # 7. Предметы «с собой»
    items, text = scan_items(text)

    # 8. Название задачи (остаток)
    title_val = extract_title(text)

    # === СБОРКА РЕЗУЛЬТАТА ===
    intent = {
        "has_remind": has_remind,
        "reminder_offset": reminder_offset,
        "date": date_val,
        "time": time_val,
        "place": place_val,
        "title": title_val,
        "items": items,
        "third_party": person_val or "",        # F.3
        "invite": person_invite,                 # F.3
        "invite_email": person_email or "",      # F.3
        "raw_text": raw_text
    }

    # === ВАЛИДАЦИЯ ===
    is_valid = validate_intent(intent)
    intent["is_valid"] = is_valid

    # === КАКИХ ПОЛЕЙ НЕ ХВАТАЕТ ===
    missing = []
    if not date_val:
        missing.append("date")
    if not time_val:
        missing.append("time")
    if not place_val:
        missing.append("place")
    if not title_val:
        missing.append("title")
    intent["missing_fields"] = missing

    return intent


    
# ---------------------------------------------------------------------------
# Блок C.7: Сканер предметов «с собой»
# ---------------------------------------------------------------------------

def scan_items(text):
    """
    Ищет в тексте конструкцию 'с собой' и забирает предметы после неё.
    Останавливается перед стоп-глаголом или в конце текста.
    
    Вход:  строка (например, "купить хлеб с собой паспорт СНИЛС")
    Выход: (items, clean_text)
           items = ["паспорт", "СНИЛС"] / []
           clean_text = текст без конструкции 'с собой ...'
    
    Правило отсечки:
      - После 'с собой' забираем ВСЕ слова
      - НО останавливаемся, если встретили стоп-глагол из STOP_VERBS
      - Если глагол не найден — забираем до конца текста
    """
    import re
    
    text_lower = text.lower()
    
    # Ищем "с собой"
    match = re.search(r'\bс собой\b', text_lower)
    if not match:
        return ([], text)
    
    # Всё, что после "с собой"
    after_idx = match.end()  # позиция сразу после "с собой"
    before = text[:match.start()]  # текст до "с собой"
    after = text[after_idx:]      # текст после "с собой"
    
    # Разбиваем остаток на слова
    words = after.split()
    
    # Ищем первое вхождение стоп-глагола
    stop_idx = None
    for i, word in enumerate(words):
        # Очищаем слово от знаков препинания для сравнения
        clean_word = re.sub(r'[^\w]', '', word).lower()
        if clean_word in STOP_VERBS:
            stop_idx = i
            break
    
    if stop_idx is not None:
        # Глагол найден — предметы до него, остальное (включая глагол) остаётся в тексте
        item_words = words[:stop_idx]      # слова до глагола = предметы
        rest_words = words[stop_idx:]      # слова от глагола = остаток текста
    else:
        # Глагол не найден — все слова после "с собой" = предметы
        item_words = words
        rest_words = []
    
    # Формируем список предметов (убираем пустые, знаки препинания)
    items = []
    for w in item_words:
        # Убираем знаки препинания
        clean = re.sub(r'[^\w]', '', w).strip()
        if clean:
            items.append(clean)
    
    # Собираем чистый текст обратно
    clean_text = before.strip()
    if rest_words:
        clean_text += " " + " ".join(rest_words)
    clean_text = " ".join(clean_text.split())
    
    return (items, clean_text)
    
    
    
    
# ---------------------------------------------------------------------------
# Блок C.8: Сборщик title
# ---------------------------------------------------------------------------

def extract_title(text):
    """
    Берёт остаток текста после всех сканеров и возвращает его как title.
    
    Вход:  строка (например, "купить хлеб")
    Выход: title (str) — название задачи
    
    Если текст пустой — возвращает пустую строку.
    Убирает лишние пробелы.
    """
    title = text.strip()
    return title
    
    
    
    
# ---------------------------------------------------------------------------
# Блок C.9: Валидатор готовности
# ---------------------------------------------------------------------------

def validate_intent(intent):
    """
    Проверяет, что все 4 обязательных поля заполнены.
    
    Вход:  словарь intent с полями date, time, place, title
    Выход: True (все поля заполнены) / False (чего-то не хватает)
    
    Обязательные поля:
      - date  (ГГГГ-ММ-ДД)
      - time  (ЧЧ:ММ)
      - place (непустая строка, не абстракция)
      - title (непустая строка)
    
    Дополнительная проверка для place:
      - Не должен быть в списке запрещённых абстракций
    """
    
    # Список запрещённых абстрактных мест
    FORBIDDEN_PLACES = [
        "везде", "где угодно", "любое место", "когда-нибудь",
        "не важно", "без разницы", "где попало", "где-то"
    ]
    
    # Проверка date
    date = intent.get("date")
    if not date or not isinstance(date, str) or date.strip() == "":
        return False
    
    # Проверка time
    time_val = intent.get("time")
    if not time_val or not isinstance(time_val, str) or time_val.strip() == "":
        return False
    
    # Проверка place
    place = intent.get("place")
    if not place or not isinstance(place, str) or place.strip() == "":
        return False
    if place.strip().lower() in FORBIDDEN_PLACES:
        return False
    
    # Проверка title
    title = intent.get("title")
    if not title or not isinstance(title, str) or title.strip() == "":
        return False
    
    return True
    
    
    
    
