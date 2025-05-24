import re
from typing import Dict, List, Tuple
import uuid

from preprocess.modules.markup.pipeline import EventMarkup, EventToken
from story_elements.database import StoryElementsDatabase


class PropertiesExtractionPipeline:
    def __init__(self, story_elements_db: StoryElementsDatabase):
        self.db = story_elements_db
        # регэксп для спецтокенов вида <PER_1>, <LOC_2>, <ORG_3>
        self.token_pattern = re.compile(r'<(PER|LOC|ORG)_(\d+)>')

    def process(
            self,
            text: str,
            markups: List[EventMarkup],
            elements: Dict[str, Dict[int, uuid.UUID]]
    ) -> Tuple[str, List[EventMarkup]]:
        """
        Для каждого EventMarkup:
        1) Ищет спецтокены <TYPE_idx>.
        2) Собирает детей по amod/appos/cop/xcomp/advcl/advmod/acl:relcl/obj/nsubj.
        3) Сохраняет свойства в базе и помечает токены на удаление.
        4) Удаляет эти токены из markup и чистит текст.
        """
        for em in markups:
            to_remove_ids = set()
            token_map = {t.id: t for t in em.tokens}

            for tok in em.tokens:
                m = self.token_pattern.fullmatch(tok.text)
                if not m:
                    continue

                ent_type, ent_idx = m.group(1), int(m.group(2))
                ent_uuid = elements.get(ent_type, {}).get(ent_idx)
                if ent_uuid is None:
                    continue

                # 1) amod / appos → прилагательные/качественные признаки
                for child in self._children(em.tokens, tok.id, rels=('amod', 'appos')):
                    self._add_property(ent_type, ent_uuid, child.text)
                    to_remove_ids.add(child.id)

                # 2) cop → xcomp/advcl → ADJ/V
                for cop in self._children(em.tokens, tok.id, rels=('cop',)):
                    for ch in self._children(em.tokens, cop.id, rels=('xcomp', 'advcl')):
                        self._add_property(ent_type, ent_uuid, ch.text)
                        to_remove_ids.add(ch.id)

                # 3) глаголы, где сущность nsubj или obj
                if tok.rel in ('nsubj', 'obj'):
                    head = token_map.get(tok.head_id)
                    if head and head.pos and head.pos.startswith('V'):
                        # сам глагол
                        self._add_property(ent_type, ent_uuid, head.text)
                        to_remove_ids.add(head.id)
                        # все advmod → тип действия/манеры
                        for adv in self._children(em.tokens, head.id, rels=('advmod',)):
                            self._add_property(ent_type, ent_uuid, adv.text)
                            to_remove_ids.add(adv.id)

                # 4) относительные придаточные: acl:relcl
                for relcl in self._children(em.tokens, tok.id, rels=('acl:relcl',)):
                    subtree = self._collect_subtree(em.tokens, relcl.id)
                    phrase = ' '.join(token_map[i].text for i in sorted(subtree))
                    self._add_property(ent_type, ent_uuid, phrase)
                    to_remove_ids |= subtree

            # удаляем токены-характеристики из markup
            em.tokens = [t for t in em.tokens if t.id not in to_remove_ids]

            # Чистим текст (удаляем вхождения свойств)
            for tok_id in to_remove_ids:
                text = re.sub(
                    rf'\b{re.escape(token_map[tok_id].text)}\b',
                    '',
                    text
                )

        return text, markups

    def _add_property(self, ent_type: str, ent_uuid: uuid.UUID, prop: str):
        repo = {
            'PER': self.db.characters,
            'LOC': self.db.locations,
            'ORG': self.db.organizations
        }[ent_type]
        element = repo.find_by_id(ent_uuid)
        if element:
            element.properties.append(prop)
            repo.add(element)  # обновляем запись

    def _children(
            self,
            tokens: List[EventToken],
            head_id: int,
            rels: Tuple[str, ...]
    ) -> List[EventToken]:
        return [t for t in tokens if t.head_id == head_id and t.rel in rels]

    def _collect_subtree(self, tokens: List[EventToken], root_id: int) -> set:
        ids = {root_id}
        added = True
        while added:
            added = False
            for t in tokens:
                if t.head_id in ids and t.id not in ids:
                    ids.add(t.id)
                    added = True
        return ids
