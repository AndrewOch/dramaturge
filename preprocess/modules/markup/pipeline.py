from typing import List

from slovnet.markup import MorphMarkup, SyntaxMarkup

from preprocess.modules.markup.models import EventMarkup, EventToken
from preprocess.modules.markup.morph import MorphProcessor
from preprocess.modules.markup.syntax import SyntaxProcessor


class MarkupPipeline:
    def __init__(self):
        self.morph = MorphProcessor()
        self.syntax = SyntaxProcessor()

    def process(self, text) -> List[EventMarkup]:
        morph_markups = self.morph.process(text)
        syntax_markups = self.syntax.process(text)
        return self._merge(morph_markups, syntax_markups)

    def _merge(
            self,
            morph_markups: List[MorphMarkup],
            syntax_markups: List[SyntaxMarkup]
    ) -> List[EventMarkup]:
        if len(morph_markups) != len(syntax_markups):
            raise ValueError(
                f"Число morph-разметок ({len(morph_markups)}) "
                f"не совпадает с числом syntax-разметок ({len(syntax_markups)})"
            )

        event_markups: List[EventMarkup] = []

        for idx, (m_mkp, s_mkp) in enumerate(zip(morph_markups, syntax_markups), start=1):
            morph_tokens = m_mkp.tokens
            syntax_tokens = s_mkp.tokens

            if len(morph_tokens) != len(syntax_tokens):
                raise ValueError(
                    f"В предложении {idx} количество токенов morph ({len(morph_tokens)}) "
                    f"не совпадает с количеством токенов syntax ({len(syntax_tokens)})"
                )

            event_tokens = [
                EventToken(m, s) for m, s in zip(morph_tokens, syntax_tokens)
            ]

            event_markups.append(EventMarkup(event_tokens))

        return event_markups
