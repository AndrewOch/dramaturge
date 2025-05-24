from typing import Optional, Tuple, List

from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.modules.extraction.date.extractors.hors import HorsDateExtractor
from preprocess.modules.extraction.date.extractors.regex import RegexDateExtractor
from preprocess.modules.markup.models import EventMarkupBlock


class DateExtractionPipeline:
    def __init__(self, regexes: Optional[str]):
        self.regex_extractor = RegexDateExtractor(regexes)
        self.hors_extractor = HorsDateExtractor()

    def process(self, block: EventMarkupBlock, now: Optional[PartialDateTime] = None) \
            -> Tuple[EventMarkupBlock, List[DateTimeToken]]:
        text = str(block)

        dates: List[DateTimeToken] = []
        block, dates_res = self.regex_extractor.extract(text, block)
        dates.extend(dates_res)
        block, dates_res = self.hors_extractor.extract(text, block, now)
        dates.extend(dates_res)

        return block, dates
