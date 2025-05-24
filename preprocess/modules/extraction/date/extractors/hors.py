from typing import List, Optional, Tuple

from hors import process_phrase
from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.modules.extraction.date.extractors.regex import RegexDateExtractor
from preprocess.modules.markup.models import EventMarkupBlock


class HorsDateExtractor:
    def extract(
            self,
            text: str,
            block: EventMarkupBlock,
            now: Optional[PartialDateTime] = None,
            token_counter: int = 1
    ) -> Tuple[EventMarkupBlock, List[DateTimeToken]]:
        result = process_phrase(text, now)
        orig = result.source_text or text
        if not result.dates:
            return block, []

        dates = sorted(result.dates, key=lambda d: d.start)
        idx = 0
        new_text = ""
        for d in dates:
            frag = orig[d.start:d.end]
            placeholder = f"<|DATETIME_{token_counter}|>"
            new_text += orig[idx:d.start]
            RegexDateExtractor.replace_in_block(frag, placeholder, block)
            new_text += placeholder
            token_counter += 1
            idx = d.end
        new_text += orig[idx:]
        return block, dates
