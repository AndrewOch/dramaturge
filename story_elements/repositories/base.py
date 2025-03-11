import uuid
from typing import Generic, TypeVar, List, Optional, Dict

from icecream import icecream

from story_elements.models import StoryElement

T = TypeVar("T", bound=StoryElement)


class BaseStoryElementRepository(Generic[T]):
    def __init__(self):
        self.elements: List[T] = []
        self.special_token_head: str = ''

    def add(self, element: T, current_index: int = 1) -> str:
        self._insert_or_update(element)
        return f"<|{self.special_token_head}_{current_index + 1}|>"

    def add_elements(self, elements: Dict[int, T]) -> (List[int], Dict[int, uuid.UUID]):
        new_indexes = []
        id_mapping = {}
        id_mapped = {}
        next_index = 1

        for original_index, element in elements.items():
            final_id = self._insert_or_update(element)

            if final_id not in id_mapping:
                id_mapping[final_id] = next_index
                next_index += 1
            new_indexes.append(id_mapping[final_id])
            id_mapped[id_mapping[final_id]] = final_id
        return new_indexes, id_mapped

    def find_by_text(self, text: str) -> Optional[T]:
        for element in self.elements:
            if text == element.name or text in element.associated_names:
                return element
        return None

    def find_by_id(self, elem_id: uuid.UUID) -> Optional[T]:
        for element in self.elements:
            if element.id == elem_id:
                return element

    def _insert_or_update(self, element: T):
        for i, existing in enumerate(self.elements):
            if element == existing:
                merged = existing.merge(element)
                self.elements[i] = merged
                return merged.id

        element.associated_names = element.name.strip().split(' ')
        self.elements.append(element)
        return element.id
