import re

from preprocess.regex_templates.template import RegexTemplate


class RussianScriptTemplate(RegexTemplate):
    # Базовая очистка: удаляются заголовки сцен (варианты: ИНТ, ЭКСТ, НАТ NAT и т.д.)
    base_preprocess_regexes = [
        (r'^(?im)(ИНТ(?:ЕРЬЕР)?|ЭКСТ(?:ЕРЬЕР)?|ИНТ\.|ЭКСТ\.|НАТ(?:\s+НАТ\.)?)\s*[\s\-:]+.*$', ''),
        (r'\s{2,}', ' '),
    ]
    dates_regex = r'(\d{2}\.\d{2}\.\d{4})'
    # Сущности – имена персонажей (минимум 3 буквы) с двоеточием в начале строки,
    # также защищаем спецтокены.
    entities_regexes = {
        'PER': r'(?<!<\|)^(?P<speaker>[А-ЯЁ]{3,}):\s(?!\|>)'
    }
    # Паттерны для прямой речи:
    direct_speech_regexes = [
        # 1. Имя с двоеточием на отдельной строке, реплика на следующей (многострочный вариант).
        (r'^(?P<speaker>[А-ЯЁ]{3,}):\s*\n(?P<quote>.+?)(?=\n{2,}|$)', True, re.M | re.S),
        # 2. Имя и реплика на одной строке через двоеточие.
        (r'^(?P<speaker>[А-ЯЁ]{3,}):\s*(?P<quote>.+)$', True, re.M),
        # 3. Строка, начинающаяся с тире или длинного тире.
        (r'^[\-–—]\s*(?P<quote>.+)$', False, re.M),
        # 4. Прямая речь в кавычках без указания говорящего.
        (r'(?<!<\|)[«"“](?P<quote>.+?)[»"”](?!\|>)', False, 0),
        # 5. Формат: имя в скобках, затем прямая речь в кавычках.
        (r'\((?P<speaker>[А-ЯЁ][а-яё]{2,})\)\s*[«"“](?P<quote>.+?)[»"”]', True, 0),
        # 6. Формат с тире между именем и репликой: "АЛЕКС – Привет."
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s*[\-–—]\s*(?P<quote>.+)$', True, re.M),
        # 7. Имя и реплика, разделённые двоеточием с дополнительными пробелами.
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s*:\s*(?P<quote>.+)$', True, re.M),
        # 8. Вариант, когда имя указывается, а реплика начинается со строчной буквы.
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s+(?P<quote>[а-яё].+)$', True, re.M),
    ]
