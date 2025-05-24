from preprocess.modules.markup.models import EventMarkup, EventType


class EventTypeClassifier:
    DYNAMIC_POS = {"VERB", "AUX"}
    STATIC_POS = {"NOUN", "PROPN", "ADJ", "ADV"}

    DYNAMIC_RELS = {
        "nsubj", "csubj", "obj", "iobj",  # аргументы глагола
        "xcomp", "ccomp",  # комплементы
        "advcl", "advmod",  # придаточные/обстоятельства
        "obl"  # обстоятельства (включая временные/модальные)
    }
    STATIC_RELS = {
        "cop",  # связка «быть»
        "amod",  # атрибутивное прилагательное
        "compound",  # составной именительный
        "nmod"  # номинальный модификатор
    }

    @classmethod
    def classify(cls, markup: EventMarkup) -> EventType:
        dynamic_score = 0
        static_score = 0

        for tok in markup.tokens:
            pos = tok.pos
            rel = tok.rel
            feats = tok.feats or {}

            # 1) Сильные маркеры динамики
            # 1.1) Если корень‑глагол
            if tok.id == tok.head_id and pos in cls.DYNAMIC_POS:
                dynamic_score += 2
            # 1.2) Отношения, указывающие на аргументы действия / придаточные
            if rel in cls.DYNAMIC_RELS:
                dynamic_score += 1
            # 1.3) Морфо‑признаки времени/аспекта
            if feats.get("Aspect") == "Perf":
                dynamic_score += 1
            if feats.get("Tense") in {"Past", "Fut"}:
                dynamic_score += 1
            # 1.4) Императив
            if feats.get("Mood") == "Imp":
                dynamic_score += 1
            # 1.5) Пассивная конструкция
            if feats.get("Voice") == "Pass":
                dynamic_score += 1

            # 2) Сильные маркеры статики
            # 2.1) Если корень‑имя/прилагательное/наречие
            if tok.id == tok.head_id and pos in cls.STATIC_POS:
                static_score += 2
            # 2.2) Отношения атрибуции и номинальных модификаторов
            if rel in cls.STATIC_RELS:
                static_score += 1
        # 3) Классификация по набранным баллам
        required = 2
        if len(markup.tokens) < 3:
            required = 1
        if dynamic_score > required >= static_score:
            return EventType.DYNAMIC
        if static_score > required >= dynamic_score:
            return EventType.STATIC
        if dynamic_score > required and static_score > required:
            return EventType.MIXED
        return EventType.UNKNOWN
