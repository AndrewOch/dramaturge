# regex_processor.py
import re
from datetime import datetime
from typing import Tuple, List, Optional, Dict
from hors.partial_date.partial_datetime import PartialDateTime


class RegexProcessor:
    def __init__(self, regex: Optional[str] = None):
        # Список кортежей (pattern, replacement) для базовой очистки текста.
        self.base_preprocess_regexes: List[Tuple[str, str]] = []
        # Паттерн для поиска дат (по умолчанию формат dd.mm.yyyy)
        self.dates_regex = regex or r'(\d{2}\.\d{2}\.\d{4})'
        # Словарь регулярных выражений для извлечения сущностей, например: {'PER': '...'}
        self.entities_regexes: Dict[str, str] = {}
        # Список кортежей для обработки прямой речи: (pattern, with_speaker, flags)
        self.direct_speech_regexes: List[Tuple[str, bool, int]] = []

    def apply_base_preprocess(self, text: str) -> str:
        for pattern, replacement in self.base_preprocess_regexes:
            text = re.sub(pattern, replacement, text)
        return text

    def process_direct_speech(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
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

    def extract_dates(self, text: str, token_counters: Dict[str, int] = None) -> Tuple[str, List[PartialDateTime]]:
        if token_counters is None:
            token_counters = {"DATETIME": 1}
        elif "DATETIME" not in token_counters:
            token_counters["DATETIME"] = 1

        dates = []

        def repl(match):
            nonlocal token_counters
            date_str = match.group(0)
            try:
                # Вместо datetime создаём PartialDateTime
                day, month, year = map(int, date_str.split('.'))
                dt = PartialDateTime(year=year, month=month, day=day)
                dates.append(dt)
            except ValueError:
                return date_str
            token = f"<|DATETIME_{token_counters['DATETIME']}|>"
            token_counters["DATETIME"] += 1
            return token

        text = re.sub(self.dates_regex, repl, text)
        return text, dates

    def extract_entities(self, text: str, token_counters: Dict[str, int] = None) -> Tuple[str, List[dict]]:
        if token_counters is None:
            token_counters = {}
        # Инициализируем счётчики для каждого типа, если ещё не созданы.
        for etype in self.entities_regexes.keys():
            if etype not in token_counters:
                token_counters[etype] = 1

        all_entities = []
        # Сохраняем оригинальный текст для проверки токенов прямой речи.
        original_text = text

        for entity_type, pattern in self.entities_regexes.items():
            def repl(match, etype=entity_type):
                m = match.group(0)
                pos = match.start()
                last_quote_st = original_text.rfind("<|QUOTE_ST|>", 0, pos)
                last_quote_end = original_text.rfind("<|QUOTE_END|>", 0, pos)
                if last_quote_st > last_quote_end:
                    return m
                token = f"<|{etype}_{token_counters[etype]}|>"
                all_entities.append({
                    'type': etype,
                    'value': m,
                    'token': token
                })
                token_counters[etype] += 1
                return token

            text = re.sub(pattern, repl, text)
        return text, all_entities
