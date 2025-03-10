import re
from typing import Tuple, List, Optional, Dict

import icecream
from hors.partial_date.partial_datetime import PartialDateTime


class RegexProcessor:
    def __init__(self, regex: Optional[str] = None):
        # Список кортежей (pattern, replacement) для базовой очистки текста.
        self.base_preprocess_regexes: List[Tuple[str, str]] = []
        # Паттерн для поиска дат (по умолчанию формат dd.mm.yyyy)
        self.dates_regex = regex or r'(\d{2}\.\d{2}\.\d{4})'
        # Словарь регулярных выражений для извлечения сущностей, например: {'PER': '...', 'LOC': '...', 'ORG': '...'}
        self.entities_regexes: Dict[str, str] = {}
        # Список кортежей для обработки прямой речи:
        # (pattern, with_speaker, flags)
        self.direct_speech_regexes: List[Tuple[str, bool, int]] = []

    def apply_base_preprocess(self, text: str) -> str:
        """Применяет паттерны базовой очистки текста."""
        for pattern, replacement in self.base_preprocess_regexes:
            text = re.sub(pattern, replacement, text)
        return text

    def process_direct_speech(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Ищет прямую речь в тексте по набору регулярных выражений.
        Каждый найденный фрагмент заменяется на стандартизированную форму:
            <|QUOTE_ST|>speaker<|QUOTE_MID|>quote<|QUOTE_END|>
        Если источник (speaker) не определён, между QUOTE_ST и QUOTE_MID остаётся пустая строка.
        Возвращает изменённый текст и список словарей с данными прямой речи.
        """
        direct_speech_entries: List[Dict[str, str]] = []
        for pattern, with_speaker, flags in self.direct_speech_regexes:
            regex = re.compile(pattern, flags)

            def repl(match):
                speaker = match.group("speaker").strip() if with_speaker and match.group("speaker") else "?"
                quote = match.group("quote").strip()
                direct_speech_entries.append({"speaker": speaker, "quote": quote})
                return f"<|QUOTE_ST|>{speaker}<|QUOTE_MID|>{quote}<|QUOTE_END|>"

            text = regex.sub(repl, text)
        return text, direct_speech_entries

    def extract_dates(self, text: str) -> Tuple[str, List[PartialDateTime]]:
        """
        Находит даты в тексте по заданному шаблону, заменяет каждую найденную дату на токен
        вида <|DATETIME_{i}|> (индекс i для дат начинается с 1) и возвращает изменённый текст
        и список объектов datetime.
        """
        dates = []
        date_index = 1

        def repl(match):
            nonlocal date_index
            date_str = match.group(0)
            try:
                dt = datetime.strptime(date_str, '%d.%m.%Y')
                dates.append(dt)
            except ValueError:
                return date_str
            token = f"<|DATETIME_{date_index}|>"
            date_index += 1
            return token

        text = re.sub(self.dates_regex, repl, text)
        return text, dates

    def extract_entities(self, text: str) -> Tuple[str, List[dict]]:
        """
        Ищет сущности по шаблонам из self.entities_regexes.
        Для каждой сущности заменяет найденный фрагмент на токен вида <|TYPE_{i}|>,
        где TYPE – тип сущности (например, PER, LOC, ORG) и i – порядковый номер для данного типа.
        Если совпадение находится внутри блока прямой речи (между <|QUOTE_ST|> и <|QUOTE_END|>),
        замена не производится.
        Возвращает изменённый текст и список найденных сущностей с информацией.
        """
        all_entities = []
        # Инициализируем счётчики для каждого типа сущности
        entity_counters = {etype: 1 for etype in self.entities_regexes.keys()}

        # Сохраним оригинальный текст для поиска токенов прямой речи (иначе, из-за замен, поиск может давать неверный результат)
        original_text = text

        for entity_type, pattern in self.entities_regexes.items():
            def repl(match, etype=entity_type):
                m = match.group(0)
                pos = match.start()
                # Если внутри уже обработанного прямого высказывания — пропускаем замену.
                # Определяем, находимся ли мы внутри блока, если последний токен <|QUOTE_ST|> до pos
                # и последний токен <|QUOTE_END|> до pos отсутствует или находится раньше.
                last_quote_st = original_text.rfind("<|QUOTE_ST|>", 0, pos)
                last_quote_end = original_text.rfind("<|QUOTE_END|>", 0, pos)
                if last_quote_st > last_quote_end:
                    return m  # не заменяем, если внутри блока прямой речи

                token = f"<|{etype}_{entity_counters[etype]}|>"
                all_entities.append({
                    'type': etype,
                    'value': m,
                    'token': token
                })
                entity_counters[etype] += 1
                return token

            text = re.sub(pattern, repl, text)
        return text, all_entities
