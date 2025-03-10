from story_elements.models import Character
from story_elements.repositories.base import BaseStoryElementRepository


class CharacterRepository(BaseStoryElementRepository[Character]):
    def __init__(self):
        super().__init__()
        self.special_token = Character.type
