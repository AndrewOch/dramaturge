import re
import uuid
from typing import Optional, Dict, List, Tuple

import icecream
from hors.models.parser_models import DateTimeToken
from hors.partial_date.partial_datetime import PartialDateTime

from preprocess.date_extractor import DateExtractor
from preprocess.event import StoryEvent
from preprocess.natasha_entity_extractor import NatashaEntityExtractor
from preprocess.regex_processor import RegexProcessor
from story_elements.database import StoryElementsDatabase
from story_elements.models import StoryElement, StoryElementExtractionOrigin


class EventPreprocessor:
    def __init__(self, regex_processor: RegexProcessor = RegexProcessor()):
        self.regex_processor = regex_processor
        self.date_extractor = DateExtractor()
        self.entity_extractor = NatashaEntityExtractor()

    def preprocess(self, text: str, index=0, now: Optional[PartialDateTime] = None) -> StoryEvent:
        source_text = text
        text = self._base_preprocess(text)
        text, dates = self._process_dates(text, now)
        text, entities = self._process_entities(text)
        text = self.regex_processor.process_direct_speech(text)

        event = StoryEvent(
            index=index,
            source_text=source_text,
            text=text,
            dates=dates,
            elements=entities
        )
        return event

    def _base_preprocess(self, text: str) -> str:
        text = self.regex_processor.apply_base_preprocess(text)
        return text.strip()

    def _process_dates(self, text: str, now: Optional[DateTimeToken]) -> Tuple[str, List]:
        dates = []
        token_counter = 1
        text, dates_res = self.regex_processor.extract_dates(text, token_counter)
        dates.extend(dates_res)
        text, dates_res = self.date_extractor.extract(text, now, token_counter)
        dates.extend(dates_res)
        return text, dates

    def _process_entities(self, text: str) -> Tuple[str, Dict[str, Dict[int, uuid.UUID]]]:

        entities_dict: Dict[str, List[StoryElement]] = {}
        token_counters = {}

        text, entities_res = self.regex_processor.extract_entities(text, token_counters)
        for key, elements in entities_res.items():
            entities_dict.setdefault(key, []).extend(elements)

        text, entities_res = self.entity_extractor.extract(text, token_counters)
        for key, elements in entities_res.items():
            entities_dict.setdefault(key, []).extend(elements)

        combined_tokens = self._build_combined_tokens(entities_dict)

        story_database = StoryElementsDatabase()

        text = self._apply_entity_replacement(text, combined_tokens, story_database)

        combined_mapping, global_final_id_to_index = self._build_combined_mapping(combined_tokens, story_database)
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
                                  combined_tokens: Dict[str, Dict[int, StoryElement]],
                                  story_database: StoryElementsDatabase) -> str:
        def replace_word(match: re.Match) -> str:
            word = match.group(0)
            if not word[0].isupper() or len(word) <= 2:
                return word

            for t_type in combined_tokens:
                for idx, existing in combined_tokens[t_type].items():
                    if existing.name == word:
                        return f"<|{t_type}_{idx}|>"

            found_element = None
            token_type = None
            for repo, t_type in [(story_database.characters, 'PER'),
                                 (story_database.locations, 'LOC'),
                                 (story_database.organizations, 'ORG')]:
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

    def _build_combined_mapping(self, combined_tokens: Dict[str, Dict[int, StoryElement]],
                                story_database: StoryElementsDatabase
                                ) -> Tuple[Dict[Tuple[str, int], int], Dict[str, Dict[uuid.UUID, int]]]:
        global_final_id_to_index = {'PER': {}, 'LOC': {}, 'ORG': {}}
        combined_mapping = {}
        for t_type in ['PER', 'LOC', 'ORG']:
            repo = {
                'PER': story_database.characters,
                'LOC': story_database.locations,
                'ORG': story_database.organizations
            }[t_type]
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
