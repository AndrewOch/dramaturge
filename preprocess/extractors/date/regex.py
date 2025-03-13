import re
from typing import Tuple, List, Optional

from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime


class RegexDateExtractor:
    def __init__(self, regex: Optional[str] = None):
        self.regex = regex or r'(\d{2}\.\d{2}\.\d{4})'

    def extract(self, text: str, token_counter: int = 1) -> Tuple[str, List[DateTimeToken]]:
        dates = []

        def repl(match):
            nonlocal token_counter
            date_str = match.group(0)
            try:
                day, month, year = map(int, date_str.split('.'))
                dt = PartialDateTime(year=year, month=month, day=day)
                dates.append(dt)
            except ValueError:
                return date_str
            token = f"<|DATETIME_{token_counter}|>"
            token_counter += 1
            return token

        text = re.sub(self.regex, repl, text)
        return text, dates
