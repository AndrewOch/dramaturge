from typing import List

from slovnet.markup import MorphToken, SyntaxToken


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
        # подробное представление для отладки
        return (
            f"EventToken(id={self.id}, head_id={self.head_id}, rel='{self.rel}', "
            f"text='{self.text}', pos='{self.pos}', feats={self.feats})"
        )

    def __str__(self) -> str:
        # краткое «человеческое» представление — просто текст токена
        return self.text


class EventMarkup:
    __attributes__ = ['tokens']
    __annotations__ = {
        'tokens': List[EventToken]
    }

    def __init__(self, tokens: List[EventToken]):
        self.tokens = tokens

    def __repr__(self) -> str:
        # подробный repr: покажем список токенов
        return f"EventMarkup(tokens=[{', '.join(repr(t) for t in self.tokens)}])"

    def __str__(self) -> str:
        # вернёт саму фразу, восстановленную из токенов
        parts: List[str] = []
        for tok in self.tokens:
            if parts and tok.text in {'.', ',', '!', '?', ';', ':'}:
                # «прилипшая» пунктуация
                parts[-1] += tok.text
            else:
                parts.append(tok.text)
        return " ".join(parts)
