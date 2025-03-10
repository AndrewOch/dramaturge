# natasha_entity_extractor.py
from typing import Tuple, List, Dict
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsNERTagger, Doc
from preprocess.regex_processor import RegexProcessor  # если нужны общие утилиты


class NatashaEntityExtractor:
    def __init__(self):
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.emb)

    def extract(self, text: str, token_counters: Dict[str, int] = None) -> Tuple[str, List[Dict[str, str]]]:
        if token_counters is None:
            token_counters = {}
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.ner_tagger)
        for span in doc.spans:
            span.normalize(self.morph_vocab)
        entities = []
        # Для согласованной замены сортируем спаны по убыванию позиции, чтобы индексы не смещались.
        spans_sorted = sorted(doc.spans, key=lambda s: s.start, reverse=True)
        for span in spans_sorted:
            etype = span.type  # например, PER, LOC, ORG и т.д.
            if etype not in token_counters:
                token_counters[etype] = 1
            token = f"<|{etype}_{token_counters[etype]}|>"
            token_counters[etype] += 1
            entities.append({
                'text': span.text,
                'type': etype,
                'normal': span.normal,
                'token': token
            })
            text = text[:span.start] + token + text[span.stop:]
        return text, entities
