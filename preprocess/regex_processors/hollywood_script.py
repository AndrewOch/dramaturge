import re

from preprocess.regex_processor import RegexProcessor


class HollywoodScriptRegexProcessor(RegexProcessor):
    def __init__(self):
        super().__init__()
        # Базовая очистка: удаляются заголовки сцен (английские, русские, а также "НАТ NAT.")
        self.base_preprocess_regexes = [
            (r'(?im)^(?:(?:INT\.|EXT\.|NAT\s+NAT\.)|(?:ИНТ(?:ЕРЬЕР)?|ЭКСТ(?:ЕРЬЕР)?|НАТ(?:\s+НАТ\.)?))\s.*$', ''),
            (r'\s{2,}', ' '),
        ]
        self.dates_regex = r'(\d{2}\.\d{2}\.\d{4})'
        # Имена персонажей – минимум 3 символа (латиница или кириллица), защищены от повторной обработки внутри спецтокенов.
        self.entities_regexes = {
            'PER': r'(?<!<\|)\b(?:[A-ZА-ЯЁ]{3,}(?:\s+[A-ZА-ЯЁ]{3,})*)\b(?!\|>)'
        }
        # Паттерны для прямой речи.
        self.direct_speech_regexes = [
            # 1. Многострочный формат: имя на отдельной строке, затем реплика.
            (r'^(?P<speaker>[A-ZА-ЯЁ\s]{3,})\n(?P<quote>.+?)(?=\n{2,}|$)', True, re.M | re.S),
            # 2. Формат с двоеточием: "ALEX: Hello, world." или "АЛЕКС: Привет, мир."
            (r'^(?P<speaker>[A-ZА-ЯЁ\s]{3,}):\s*(?P<quote>.+)$', True, re.M),
            # 3. Прямая речь в кавычках без указания говорящего.
            (r'(?<!<\|)[“"\'”](?P<quote>.+?)[“"\'”](?!\|>)', False, 0),
            # 4. Строка, начинающаяся с тире.
            (r'^[\-–]\s*(?P<quote>.+)$', False, re.M),
        ]