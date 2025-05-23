from typing import Optional, Tuple, List

from hors.models.parser_models import DateTimeToken

from preprocess.modules.extraction.date.extractors.hors import HorsDateExtractor
from preprocess.modules.extraction.date.extractors.regex import RegexDateExtractor


class DateExtractionPipeline:
    def __init__(self, regexes: Optional[str]):
        self.regex_extractor = RegexDateExtractor(regexes)
        self.hors_extractor = HorsDateExtractor()

    def process(self, text: str, markups, now: Optional[DateTimeToken]) -> Tuple[str, List]:
        dates = []
        token_counter = 1
        text, dates_res = self.regex_extractor.extract(text, markups, token_counter)
        dates.extend(dates_res)
        text, dates_res = self.hors_extractor.extract(text, markups, now, token_counter)
        dates.extend(dates_res)
        return text, dates
