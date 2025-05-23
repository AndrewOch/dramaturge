import re
import uuid
from typing import Dict, Tuple, List

from preprocess.modules.extraction.entity.extractors.natasha import NatashaEntityExtractor
from preprocess.modules.extraction.entity.extractors.regex import RegexEntityExtractor
from story_elements.models import StoryElement


class EntityExtractionPipeline:
    def __init__(self, elems_database, regexes: Dict[str, str]):
        self.natasha_extractor = NatashaEntityExtractor()
        self.regex_extractor = RegexEntityExtractor(regexes)
        self.elems_database = elems_database

    def process(self, text: str, markups) -> Tuple[
        str, Dict[str, Dict[int, uuid.UUID]]]:

        entities_dict: Dict[str, List[StoryElement]] = {}
        token_counters = {}

        text, entities_res = self.regex_extractor.extract(text, markups, token_counters)
        for key, elements in entities_res.items():
            entities_dict.setdefault(key, []).extend(elements)

        text, entities_res = self.natasha_extractor.extract(text, token_counters)
        for key, elements in entities_res.items():
            entities_dict.setdefault(key, []).extend(elements)

        combined_tokens = self._build_combined_tokens(entities_dict)

        text = self._apply_entity_replacement(text, combined_tokens)

        combined_mapping, global_final_id_to_index = self._build_combined_mapping(combined_tokens)
        text = self._update_tokens(text, combined_mapping)

        text = self._merge_adjacent_tokens(text)

        final_index_mapping = self._build_final_index_mapping(global_final_id_to_index)
        event_elements = self._build_event_elements(text, final_index_mapping)

        return text, event_elements

    def _build_combined_tokens(self, entities_dict: Dict[str, List[StoryElement]]
                               ) -> Dict[str, Dict[int, StoryElement]]:
        combined_tokens = {'PER': {}, 'LOC': {}, 'ORG': {}}
        for t_type in ['PER', 'LOC', 'ORG']:
            for i, element in enumerate(entities_dict.get(t_type, []), start=1):
                combined_tokens[t_type][i] = element
        return combined_tokens

    def _apply_entity_replacement(self, text: str,
                                  combined_tokens: Dict[str, Dict[int, StoryElement]]) -> str:
        def replace_word(match: re.Match) -> str:
            word = match.group(0)
            if not word[0].isupper() or len(word) <= 2:
                return word

            for t_type in combined_tokens:
                for idx, existing in combined_tokens[t_type].items():
                    if word in existing.name.split(' '):
                        return f"<|{t_type}_{idx}|>"

            found_element = None
            token_type = None
            for repo, t_type in [(self.elems_database.characters, 'PER'),
                                 (self.elems_database.locations, 'LOC'),
                                 (self.elems_database.organizations, 'ORG')]:
                element = repo.find_by_text(word)
                if element is not None:
                    found_element = element
                    token_type = t_type
                    break
            if found_element is not None:
                for idx, existing in combined_tokens[token_type].items():
                    if existing.name == found_element.name:
                        return f"<|{token_type}_{idx}|>"
                new_index = len(combined_tokens[token_type]) + 1
                combined_tokens[token_type][new_index] = found_element
                return f"<|{token_type}_{new_index}|>"
            return word

        return re.sub(r'(?<!<\|)\b\w+\b(?!\|>)', replace_word, text)

    def _build_combined_mapping(self, combined_tokens: Dict[str, Dict[int, StoryElement]]) -> Tuple[
        Dict[Tuple[str, int], int], Dict[str, Dict[uuid.UUID, int]]]:
        global_final_id_to_index = {'PER': {}, 'LOC': {}, 'ORG': {}}
        combined_mapping = {}
        for t_type in ['PER', 'LOC', 'ORG']:
            repo = self.elems_database.repositories[t_type]
            mapping_for_type = combined_tokens[t_type]
            if mapping_for_type:
                new_indexes, id_mapped = repo.add_elements(mapping_for_type)
                for final_idx, story_elem_id in id_mapped.items():
                    global_final_id_to_index[t_type][story_elem_id] = final_idx
                for temp_idx, final_index in zip(sorted(mapping_for_type.keys()), new_indexes):
                    combined_mapping[(t_type, temp_idx)] = final_index
        return combined_mapping, global_final_id_to_index

    def _update_tokens(self, text: str, combined_mapping: Dict[Tuple[str, int], int]) -> str:
        def update_token(match: re.Match) -> str:
            token_full = match.group(0)
            m = re.match(r'<\|(\w+)_(\d+)\|>', token_full)
            if m:
                t_type = m.group(1)
                temp_idx = int(m.group(2))
                final_index = combined_mapping.get((t_type, temp_idx), temp_idx)
                return f"<|{t_type}_{final_index}|>"
            return token_full

        return re.sub(r'<\|\w+_\d+\|>', update_token, text)

    def _merge_adjacent_tokens(self, text: str) -> str:
        def merge_adjacent(match: re.Match) -> str:
            group = match.group(0)
            tokens = re.findall(r'<\|\w+_\d+\|>', group)
            if len(set(tokens)) == 1:
                return tokens[0]
            return group

        return re.sub(r'((?:<\|\w+_\d+\|>\s+){1,}<\|\w+_\d+\|>)', merge_adjacent, text)

    def _build_final_index_mapping(self, global_final_id_to_index: Dict[str, Dict[uuid.UUID, int]]
                                   ) -> Dict[Tuple[str, int], uuid.UUID]:
        final_index_mapping = {}
        for t_type in ['PER', 'LOC', 'ORG']:
            for story_elem_id, final_idx in global_final_id_to_index[t_type].items():
                final_index_mapping[(t_type, final_idx)] = story_elem_id
        return final_index_mapping

    def _build_event_elements(self, text: str,
                              final_index_mapping: Dict[Tuple[str, int], uuid.UUID]
                              ) -> Dict[str, Dict[int, uuid.UUID]]:
        event_elements: Dict[str, Dict[int, uuid.UUID]] = {}
        tokens_in_text = re.findall(r'<\|(\w+)_(\d+)\|>', text)
        for t_type, idx_str in tokens_in_text:
            final_idx = int(idx_str)
            elem_id = final_index_mapping.get((t_type, final_idx))
            if elem_id is None:
                continue
            event_elements.setdefault(t_type, {})[final_idx] = elem_id
        return event_elements
