from typing import Optional, Tuple, List, Dict

from hors import process_phrase
from hors.partial_date.partial_datetime import PartialDateTime


class DateExtractor:
    def extract(self, text, now: Optional[PartialDateTime] = None, token_counters: Dict[str, int] = None) -> (
            Tuple)[str, List[PartialDateTime]]:
        result = process_phrase(text, now)
        orig_text = result.source if hasattr(result, 'source') and result.source else text
        if token_counters is None:
            token_counters = {"DATETIME": 1}
        elif "DATETIME" not in token_counters:
            token_counters["DATETIME"] = 1
        if not result.dates:
            return orig_text, result.dates
        sorted_dates = sorted(result.dates, key=lambda d: d.start)
        new_text = ""
        current_index = 0
        for d in sorted_dates:
            start = d.start
            end = d.end
            new_text += orig_text[current_index:start]
            new_text += f"<|DATETIME_{token_counters['DATETIME']}|>"
            token_counters["DATETIME"] += 1
            current_index = end
        new_text += orig_text[current_index:]
        return new_text, result.dates
