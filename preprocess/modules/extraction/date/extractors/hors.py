from typing import List, Optional, Tuple

from hors import process_phrase
from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.modules.extraction.date.extractors.regex import RegexDateExtractor
from preprocess.modules.markup.pipeline import EventMarkup


class HorsDateExtractor:
    def extract(self,
                text: str,
                markups: List[EventMarkup],
                now: Optional[PartialDateTime] = None,
                token_counter: int = 1
                ) -> Tuple[str, List[DateTimeToken]]:
        result = process_phrase(text, now)
        orig = result.source if hasattr(result, 'source') and result.source else text
        if not result.dates:
            return orig, []

        # хотим в порядке встречаемости
        sorted_dates = sorted(result.dates, key=lambda d: d.start)
        new_text = ""
        idx = 0
        for d in sorted_dates:
            # берем фрагмент исходного
            frag = orig[d.start:d.end]
            placeholder = f"<|DATETIME_{token_counter}|>"
            # врезаем предыдущее и затем токен
            new_text += orig[idx:d.start] + placeholder
            # обновляем разметку по этому фрагменту
            self._replace_in_markups(frag, placeholder, markups)
            token_counter += 1
            idx = d.end
        new_text += orig[idx:]
        return new_text, sorted_dates

    @staticmethod
    def _replace_in_markups(*args, **kwargs):
        return RegexDateExtractor.replace_in_markups(*args, **kwargs)

    @staticmethod
    def _renumber(em: EventMarkup):
        return RegexDateExtractor.renumber(em)
