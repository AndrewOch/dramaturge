import re
from typing import Tuple, List, Optional

from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.modules.markup.models import EventMarkupBlock
from preprocess.modules.markup.pipeline import EventMarkup


class RegexDateExtractor:
    def __init__(self, regex: Optional[str] = None):
        self.regex = regex or r'(\d{2}\.\d{2}\.\d{4})'

    def extract(
            self,
            text: str,
            block: EventMarkupBlock,
            token_counter: int = 1
    ) -> Tuple[EventMarkupBlock, List[DateTimeToken]]:
        dates: List[DateTimeToken] = []

        def repl(m: re.Match) -> str:
            nonlocal token_counter
            s = m.group(0)
            try:
                d, m_, y = map(int, s.split('.'))
                dt = PartialDateTime(year=y, month=m_, day=d)
                dates.append(dt)
            except ValueError:
                return s
            placeholder = f"<|DATETIME_{token_counter}|>"
            token_counter += 1
            # патчим только разметку внутри блока
            self.replace_in_block(s, placeholder, block)
            return placeholder

        re.sub(self.regex, repl, text)
        return block, dates

    @staticmethod
    def replace_in_block(
            date_str: str,
            placeholder: str,
            block: EventMarkupBlock
    ):
        words = date_str.split()
        for em in block:
            tokens = em.tokens
            for i in range(len(tokens) - len(words) + 1):
                if all(tokens[i + j].text == words[j] for j in range(len(words))):
                    # вырезаем matched, переносим детей, меняем parent.text
                    matched = tokens[i:i + len(words)]
                    ids = {t.id for t in matched}
                    parent = next(t for t in matched if t.head_id not in ids)
                    for t in matched:
                        if t is parent: continue
                        for child in tokens:
                            if child.head_id == t.id:
                                child.head_id = parent.id
                        tokens.remove(t)
                    parent.text = placeholder
                    # пересчёт id/head_id
                    RegexDateExtractor.renumber(em)
                    return

    @staticmethod
    def renumber(em):
        old2new = {}
        for new_id, t in enumerate(em.tokens, start=1):
            old2new[t.id] = new_id
            t.id = new_id
        for t in em.tokens:
            t.head_id = old2new.get(t.head_id, 0)
