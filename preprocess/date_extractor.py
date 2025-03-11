from typing import Optional, Tuple, List, Dict

from hors import process_phrase
from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime


class DateExtractor:
    def extract(self, text, now: Optional[PartialDateTime] = None, token_counter: int = 1) -> (
            Tuple)[str, List[DateTimeToken]]:
        result = process_phrase(text, now)
        orig_text = result.source if hasattr(result, 'source') and result.source else text
        if not result.dates:
            return orig_text, result.dates
        sorted_dates = sorted(result.dates, key=lambda d: d.start)
        new_text = ""
        current_index = 0
        for d in sorted_dates:
            start = d.start
            end = d.end
            new_text += orig_text[current_index:start]
            new_text += f"<|DATETIME_{token_counter}|>"
            token_counter += 1
            current_index = end
        new_text += orig_text[current_index:]
        return new_text, result.dates
