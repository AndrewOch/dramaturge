from typing import List

from slovnet.markup import MorphMarkup, SyntaxMarkup

from preprocess.modules.markup.models import EventMarkup, EventToken, EventMarkupBlock
from preprocess.modules.markup.processors.event_type import EventTypeClassifier
from preprocess.modules.markup.processors.morph import MorphProcessor
from preprocess.modules.markup.processors.syntax import SyntaxProcessor


class MarkupPipeline:
    def __init__(self):
        self.morph = MorphProcessor()
        self.syntax = SyntaxProcessor()
        self.type_classifier = EventTypeClassifier()

    def process(self, text: str) -> EventMarkupBlock:
        morph_markups: List[MorphMarkup] = self.morph.process(text)
        syntax_markups: List[SyntaxMarkup] = self.syntax.process(text)

        if len(morph_markups) != len(syntax_markups):
            raise ValueError(f"...")

        markups: List[EventMarkup] = []
        for m_mkp, s_mkp in zip(morph_markups, syntax_markups):
            if len(m_mkp.tokens) != len(s_mkp.tokens):
                raise ValueError(f"...")
            tokens = [EventToken(m, s) for m, s in zip(m_mkp.tokens, s_mkp.tokens)]
            em = EventMarkup(tokens)
            em.type = self.type_classifier.classify(em)
            markups.append(em)

        return EventMarkupBlock(markups)

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
