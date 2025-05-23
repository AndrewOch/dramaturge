import re
from typing import Tuple, List, Optional

from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.modules.markup.pipeline import EventMarkup


class RegexDateExtractor:
    def __init__(self, regex: Optional[str] = None):
        self.regex = regex or r'(\d{2}\.\d{2}\.\d{4})'

    def extract(self,
                text: str,
                markups: List[EventMarkup],
                token_counter: int = 1
                ) -> Tuple[str, List[DateTimeToken]]:
        dates: List[DateTimeToken] = []

        def repl(m: re.Match) -> str:
            nonlocal token_counter
            date_str = m.group(0)
            # парсим дату
            try:
                day, month, year = map(int, date_str.split('.'))
                dt = PartialDateTime(year=year, month=month, day=day)
                dates.append(dt)
            except ValueError:
                return date_str

            placeholder = f"<|DATETIME_{token_counter}|>"
            # актуализация разметки
            RegexDateExtractor.replace_in_markups(date_str, placeholder, markups)
            token_counter += 1
            return placeholder

        new_text = re.sub(self.regex, repl, text)
        return new_text, dates

    @staticmethod
    def replace_in_markups(date_str: str,
                           placeholder: str,
                           markups: List[EventMarkup]):
        words = date_str.split()
        for em in markups:
            tokens = em.tokens
            # ищем подпоследовательность по словам
            for i in range(len(tokens) - len(words) + 1):
                if all(tokens[i + j].text == words[j] for j in range(len(words))):
                    matched = tokens[i:i + len(words)]
                    ids = {t.id for t in matched}
                    # выбираем «корневой» элемент — тот, чей head_id вне вырезки
                    parent = next(t for t in matched if t.head_id not in ids)
                    # переназначаем детей удаляемых узлов на parent
                    for t in matched:
                        if t is parent: continue
                        for child in tokens:
                            if child.head_id == t.id:
                                child.head_id = parent.id
                        tokens.remove(t)
                    # меняем текст parent-а на токен
                    parent.text = placeholder
                    # пересчитываем id и head_id
                    RegexDateExtractor.renumber(em)
                    return

    @staticmethod
    def renumber(em: EventMarkup):
        old_to_new = {}
        for new_id, tok in enumerate(em.tokens, start=1):
            old_to_new[tok.id] = new_id
            tok.id = new_id
        for tok in em.tokens:
            tok.head_id = old_to_new.get(tok.head_id, 0)
