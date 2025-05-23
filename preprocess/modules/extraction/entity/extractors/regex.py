import re
from typing import Tuple, List, Dict

from razdel import tokenize

from preprocess.modules.markup.pipeline import EventMarkup, EventToken
from story_elements.models import StoryElement, StoryElementExtractionOrigin


class RegexEntityExtractor:
    def __init__(self, regexes: Dict[str, str] = None):
        if regexes is None:
            regexes = {}
        self.regexes: Dict[str, str] = regexes

    def extract(
            self,
            text: str,
            event_markups: List[EventMarkup],
            token_counters: Dict[str, int] = None
    ) -> Tuple[str, Dict[str, List[StoryElement]]]:
        if token_counters is None:
            token_counters = {}
        # инициализируем счётчики для каждого типа сущности
        for etype in self.regexes.keys():
            token_counters.setdefault(etype, 1)

        entities: Dict[str, List[StoryElement]] = {}
        original_text = text

        # все токены разметки в один плоский список
        flat_tokens: List[EventToken] = []
        for markup in event_markups:
            flat_tokens.extend(markup.tokens)

        # токены для поиска по символам
        global_tokens = list(tokenize(original_text))

        # плейсхолдеры для падежей
        case_tokens = {
            'Gen': '<|C_GEN|>',
            'Dat': '<|C_DAT|>',
            'Acc': '<|C_ACC|>',
            'Ins': '<|C_INS|>',
            'Loc': '<|C_LOC|>',
            'Voc': '<|C_VOC|>'
        }

        allowed_punct = {',', '-', '—'}

        def is_desired_token(ev_token: EventToken) -> bool:
            # пунктуация
            if re.fullmatch(r'\W+', ev_token.text):
                return ev_token.text in allowed_punct

            if ev_token.rel == 'punct':
                return ev_token.text in allowed_punct

            # собственные имена только
            return ev_token.pos == 'PROPN'

        def repl(match: re.Match, etype: str) -> str:
            match_start, match_end = match.span()
            filtered = []
            entity_case = None

            # ищем все токены, чьи character offsets пересекаются с match
            for i, token in enumerate(global_tokens):
                if token.start < match_end and token.stop > match_start:
                    if i < len(flat_tokens):
                        ev = flat_tokens[i]
                        if is_desired_token(ev):
                            filtered.append(token.text)
                            if entity_case is None and ev.pos == 'PROPN':
                                entity_case = ev.feats.get('Case', 'Nom')

            # обрезаем лидирующую и конечную пунктуацию
            while filtered and filtered[0] in allowed_punct:
                filtered.pop(0)
            while filtered and filtered[-1] in allowed_punct:
                filtered.pop()

            filtered_entity = " ".join(filtered).strip()
            if not filtered_entity:
                return match.group(0)

            # формируем placeholder
            placeholder = f"<|{etype}_{token_counters[etype]}|>"
            if entity_case and entity_case != 'Nom' and entity_case in case_tokens:
                placeholder += case_tokens[entity_case]

            # сохраняем найденный элемент
            elem = StoryElement(
                name=filtered_entity,
                type=etype,
                extraction_origin=StoryElementExtractionOrigin.REGEX
            )
            entities.setdefault(etype, []).append(elem)
            token_counters[etype] += 1

            return placeholder

        # применяем все regex’ы к тексту
        for itype, pattern in self.regexes.items():
            text = re.sub(pattern, lambda m, etype=itype: repl(m, etype), text)

        return text, entities
