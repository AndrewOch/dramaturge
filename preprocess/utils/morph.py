from navec import Navec
from razdel import sentenize, tokenize
from slovnet import Morph
from slovnet.markup import MorphMarkup


class MorphProcessor:
    def __init__(self):
        self.navec = Navec.load('../models/navec_news_v1_1B_250K_300d_100q.tar')
        self.morph = Morph.load('../models/slovnet_morph_news_v1.tar')
        self.morph.navec(self.navec)

    def process(self, text) -> list[MorphMarkup]:
        chunk = []
        for sent in sentenize(text):
            tokens = [token.text for token in tokenize(sent.text)]
            chunk.append(tokens)
        markups = list(self.morph.map(chunk))
        return markups
