from typing import Tuple, List, Dict

from icecream import icecream
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsNERTagger, Doc


class NatashaEntityExtractor:
    def __init__(self):
        # Инициализация компонентов Natasha
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.emb = NewsEmbedding()
        self.ner_tagger = NewsNERTagger(self.emb)

    def extract(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Извлекает именованные сущности из текста с использованием Natasha.
        Для каждой найденной сущности заменяет исходный фрагмент на токен вида:
            <|TYPE_{i}|>
        где TYPE – тип сущности (например, PER, LOC, ORG) и i – порядковый номер для данного типа.
        Возвращает изменённый текст и список сущностей с дополнительной информацией.
        """
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_ner(self.ner_tagger)
        for span in doc.spans:
            span.normalize(self.morph_vocab)
        entities = []
        # Словарь для счёта токенов по типам сущностей
        entity_counters = {}
        # Сортируем найденные сущности по убыванию позиции, чтобы замена не нарушала индексы
        spans_sorted = sorted(doc.spans, key=lambda s: s.start, reverse=True)
        for span in spans_sorted:
            etype = span.type  # например, PER, LOC, ORG и т.д.
            if etype not in entity_counters:
                entity_counters[etype] = 1
            token = f"<|{etype}_{entity_counters[etype]}|>"
            entity_counters[etype] += 1
            entities.append({
                'text': span.text,
                'type': etype,
                'normal': span.normal,
                'token': token
            })
            # Замена найденной сущности в тексте на токен.
            text = text[:span.start] + token + text[span.stop:]
        return text, entities
