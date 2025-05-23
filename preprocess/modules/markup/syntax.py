from navec import Navec
from razdel import sentenize, tokenize
from slovnet import Syntax
from slovnet.markup import SyntaxMarkup


class SyntaxProcessor:
    def __init__(self):
        self.navec = Navec.load('models/navec_news_v1_1B_250K_300d_100q.tar')
        self.syntax = Syntax.load('models/slovnet_syntax_news_v1.tar')
        self.syntax.navec(self.navec)

    def process(self, text) -> list[SyntaxMarkup]:
        chunk = []
        for sent in sentenize(text):
            tokens = [token.text for token in tokenize(sent.text)]
            chunk.append(tokens)
        markups = list(self.syntax.map(chunk))
        return markups
