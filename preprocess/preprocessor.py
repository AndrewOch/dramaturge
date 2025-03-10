# event_preprocessor.py
from typing import Optional
from hors.partial_date.partial_datetime import PartialDateTime
from preprocess.date_extractor import DateExtractor
from preprocess.natasha_entity_extractor import NatashaEntityExtractor
from preprocess.regex_processor import RegexProcessor


class EventPreprocessor:
    def __init__(self, regex_processor: RegexProcessor = RegexProcessor()):
        self.regex_processor = regex_processor
        self.date_extractor = DateExtractor()
        self.entity_extractor = NatashaEntityExtractor()

    def preprocess(self, text: str, index=0, now: Optional[PartialDateTime] = None) -> dict:
        original_text = text
        text = self._base_preprocess(text)

        # Создаём один общий словарь-счётчик токенов
        token_counters = {"DATETIME": 1}
        # Для сущностей можно использовать отдельные ключи (например, PER)
        # Если их не создаём отдельно, то они будут инициированы в экстракторах.

        text, dates = self._process_dates(text, now, token_counters)
        text, entities = self._process_entities(text, token_counters)
        text, quotes = self.regex_processor.process_direct_speech(text)

        return {
            'original_text': original_text,
            'processed_text': text,
            'dates': dates,
            'entities': entities,
            'direct_speech': quotes
        }

    def _base_preprocess(self, text: str) -> str:
        text = self.regex_processor.apply_base_preprocess(text)
        return text.strip()

    def _process_dates(self, text: str, now: Optional[PartialDateTime], token_counters: dict):
        dates = []
        text, dates_res = self.regex_processor.extract_dates(text, token_counters)
        dates.extend(dates_res)
        text, dates_res = self.date_extractor.extract(text, now, token_counters)
        dates.extend(dates_res)
        return text, dates

    def _process_entities(self, text: str, token_counters: dict):
        entities = []
        text, entities_res = self.regex_processor.extract_entities(text, token_counters)
        entities.extend(entities_res)
        text, entities_res = self.entity_extractor.extract(text, token_counters)
        entities.extend(entities_res)
        return text, entities
