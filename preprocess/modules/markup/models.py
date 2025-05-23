from enum import Enum, auto
from typing import List

from slovnet.markup import MorphToken, SyntaxToken


class EventType(Enum):
    UNKNOWN = auto()
    STATIC = auto()
    DYNAMIC = auto()
    MIXED = auto()


class EventToken:
    def __init__(self, morph: MorphToken, syntax: SyntaxToken):
        if morph.text != syntax.text:
            raise ValueError(
                f"morph.text ({morph.text}) != syntax.text ({syntax.text})"
            )
        self.id = syntax.id
        self.head_id = syntax.head_id
        self.rel = syntax.rel
        self.text = morph.text
        self.pos = morph.pos
        self.feats = morph.feats

    def __repr__(self) -> str:
        return (
            f"EventToken(id={self.id}, head_id={self.head_id}, rel='{self.rel}', "
            f"text='{self.text}', pos='{self.pos}', feats={self.feats})"
        )

    def __str__(self) -> str:
        return self.text


class EventMarkup:
    __attributes__ = ['type', 'tokens']
    __annotations__ = {
        'type': EventType,
        'tokens': List[EventToken]
    }

    def __init__(self, tokens: List[EventToken], event_type: EventType = EventType.UNKNOWN):
        self.type = event_type
        self.tokens = tokens

    def __repr__(self) -> str:
        return (f"EventMarkup(text={self.__str__()}\n"
                f"type={self.type} tokens=[{', '.join(repr(t) for t in self.tokens)}])")

    def __str__(self) -> str:
        # вернёт саму фразу, восстановленную из токенов
        parts: List[str] = []
        for tok in self.tokens:
            if parts and tok.text in {'.', ',', '!', '?', ';', ':'}:
                parts[-1] += tok.text
            else:
                parts.append(tok.text)
        return " ".join(parts)
