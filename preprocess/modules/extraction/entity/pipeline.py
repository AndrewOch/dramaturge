import re
import uuid
from typing import Dict, Tuple, List

from slovnet.markup import MorphToken, SyntaxToken

from preprocess.modules.extraction.entity.extractors.natasha import NatashaEntityExtractor
from preprocess.modules.extraction.entity.extractors.regex import RegexEntityExtractor
from preprocess.modules.markup.models import EventMarkup, EventToken, EventMarkupBlock
from story_elements.models import StoryElement


class EntityExtractionPipeline:
    def __init__(self, elems_database, regexes: Dict[str, str]):
        self.natasha_extractor = NatashaEntityExtractor()
        self.regex_extractor = RegexEntityExtractor(regexes)
        self.elems_database = elems_database

    def process(
            self,
            block: EventMarkupBlock
    ) -> Tuple[EventMarkupBlock, Dict[str, Dict[int, uuid.UUID]]]:
        # 1. собрали текст
        text = str(block)
        markups = block.markups
        token_counters: Dict[str, int] = {}
        entities_dict: Dict[str, List[StoryElement]] = {}

        # 2. regex-экстрактор
        text, res = self.regex_extractor.extract(text, markups, token_counters)
        for k, lst in res.items():
            entities_dict.setdefault(k, []).extend(lst)

        # 3. Natasha
        text, res = self.natasha_extractor.extract(text, token_counters)
        for k, lst in res.items():
            entities_dict.setdefault(k, []).extend(lst)

        # 4. сбор и замена в тексте
        combined = self._build_combined_tokens(entities_dict)
        text = self._apply_entity_replacement(text, combined)
        mapping, global_ids = self._build_combined_mapping(combined)
        text = self._update_tokens(text, mapping)
        text = self._merge_adjacent_tokens(text)

        # 5. обновляем разметку внутри блока
        self._update_markups(text, markups, combined, mapping)

        # 6. собираем элементы и отдаем
        final_map = self._build_final_index_mapping(global_ids)
        event_elements = self._build_event_elements(text, final_map)

        return block, event_elements

    def _build_combined_tokens(self, entities_dict: Dict[str, List[StoryElement]]
                               ) -> Dict[str, Dict[int, StoryElement]]:
        combined_tokens = {'PER': {}, 'LOC': {}, 'ORG': {}}
        for t_type in combined_tokens:
            for idx, elem in enumerate(entities_dict.get(t_type, []), 1):
                combined_tokens[t_type][idx] = elem
        return combined_tokens

    def _apply_entity_replacement(self, text: str,
                                  combined_tokens: Dict[str, Dict[int, StoryElement]]) -> str:

        def replace_word(match: re.Match) -> str:
            word = match.group(0)
            if not word[0].isupper() or len(word) <= 2:
                return word

            for t_type, tokens in combined_tokens.items():
                for idx, elem in tokens.items():
                    if word in elem.name.split():
                        return f"<|{t_type}_{idx}|>"

            return word

        return re.sub(r'(?<!<\|)\b\w+\b(?!\|>)', replace_word, text)

    def _update_tokens(self, text: str, combined_mapping: Dict[Tuple[str, int], int]) -> str:
        def repl(m: re.Match) -> str:
            t, i = m.group(1), int(m.group(2))
            final = combined_mapping.get((t, i), i)
            return f"<|{t}_{final}|>"

        return re.sub(r'<\|(\w+)_(\d+)\|>', repl, text)

    def _merge_adjacent_tokens(self, text: str) -> str:
        return re.sub(r'((?:<\|\w+_\d+\|>\s+){1,}<\|\w+_\d+\|>)',
                      lambda m: re.findall(r'<\|\w+_\d+\|>', m.group(0))[0],
                      text)

    def _build_combined_mapping(self, combined_tokens: Dict[str, Dict[int, StoryElement]]) -> Tuple[
        Dict[Tuple[str, int], int], Dict[str, Dict[uuid.UUID, int]]]:
        global_ids = {'PER': {}, 'LOC': {}, 'ORG': {}}
        mapping: Dict[Tuple[str, int], int] = {}
        for t_type, temp_map in combined_tokens.items():
            repo = self.elems_database.repositories[t_type]
            if temp_map:
                new_idxs, id_map = repo.add_elements(temp_map)
                for final_idx, eid in id_map.items():
                    global_ids[t_type][eid] = final_idx
                for temp_idx, final_idx in zip(sorted(temp_map), new_idxs):
                    mapping[(t_type, temp_idx)] = final_idx
        return mapping, global_ids

    def _build_final_index_mapping(self, global_final_id_to_index: Dict[str, Dict[uuid.UUID, int]]
                                   ) -> Dict[Tuple[str, int], uuid.UUID]:
        final: Dict[Tuple[str, int], uuid.UUID] = {}
        for t_type, id_map in global_final_id_to_index.items():
            for eid, idx in id_map.items():
                final[(t_type, idx)] = eid
        return final

    def _build_event_elements(self, text: str,
                              final_index_mapping: Dict[Tuple[str, int], uuid.UUID]
                              ) -> Dict[str, Dict[int, uuid.UUID]]:
        elems: Dict[str, Dict[int, uuid.UUID]] = {}
        for t, i in re.findall(r'<\|(\w+)_(\d+)\|>', text):
            idx = int(i)
            eid = final_index_mapping.get((t, idx))
            if eid:
                elems.setdefault(t, {})[idx] = eid
        return elems

    def _update_markups(self, text, markups, combined_tokens, combined_mapping):
        # Построим словарь: фраза сущности -> финальный спецтокен
        phrase_to_token = {}
        for t_type, temp_map in combined_tokens.items():
            for temp_idx, elem in temp_map.items():
                final_idx = combined_mapping.get((t_type, temp_idx), temp_idx)
                token = f"<|{t_type}_{final_idx}|>"
                phrase_to_token[elem.name] = token

        # Обрабатываем каждую маркировку
        for markup in markups:
            tokens = markup.tokens
            new_tokens = []
            original_ids_list = []
            i = 0
            while i < len(tokens):
                # Ищем самую длинную последовательность, которая соответствует сущности
                for k in range(len(tokens) - i, 0, -1):
                    phrase = ' '.join(t.text for t in tokens[i:i + k])
                    if phrase in phrase_to_token:
                        token = phrase_to_token[phrase]
                        # Находим головной токен: его head_id не в последовательности
                        seq_ids = {t.id for t in tokens[i:i + k]}
                        head_token = next(t for t in tokens[i:i + k] if t.head_id not in seq_ids)
                        # Создаем новый токен с текстом спецтокена и метками от головного токена
                        new_morph = MorphToken(text=token, pos=head_token.pos, feats=head_token.feats)
                        new_syntax = SyntaxToken(id=0, head_id=head_token.head_id, rel=head_token.rel, text=token)
                        new_token = EventToken(new_morph, new_syntax)
                        new_tokens.append(new_token)
                        original_ids_list.append([t.id for t in tokens[i:i + k]])
                        i += k
                        break
                else:
                    # Нет совпадения, добавляем оригинальный токен
                    new_tokens.append(tokens[i])
                    original_ids_list.append([tokens[i].id])
                    i += 1

            # Перенумеровываем id
            for idx, new_token in enumerate(new_tokens):
                new_token.id = idx + 1

            # Создаем отображение старых id на новые
            original_to_new = {}
            for new_id, orig_ids in enumerate(original_ids_list, 1):
                for orig_id in orig_ids:
                    original_to_new[orig_id] = new_id

            # Обновляем head_id
            for new_token in new_tokens:
                if new_token.head_id != 0:
                    new_token.head_id = original_to_new.get(new_token.head_id, 0)

            # Обновляем токены в маркировке
            markup.tokens = new_tokens
