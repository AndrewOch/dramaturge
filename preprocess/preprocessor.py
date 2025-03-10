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

        text, dates = self._process_dates(text, now)
        text, entities = self._process_entities(text)
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

    def _process_dates(self, text: str, now: Optional[PartialDateTime] = None):
        dates = []
        text, dates_res = self.regex_processor.extract_dates(text)
        dates.extend(dates_res)

        text, dates_res = self.date_extractor.extract(text, now)
        dates.extend(dates_res)
        return text, dates

    def _process_entities(self, text: str):
        entities = []
        text, entities_res = self.regex_processor.extract_entities(text)
        entities.extend(entities_res)
        text, entities_res = self.entity_extractor.extract(text)
        entities.extend(entities_res)
        return text, entities
