from story_elements.repositories.characters import CharacterRepository
from story_elements.repositories.datetimes import DatetimeRepository
from story_elements.repositories.locations import LocationRepository
from story_elements.repositories.organizations import OrganizationRepository


class StoryElementsDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StoryElementsDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.characters = CharacterRepository()
            self.locations = LocationRepository()
            self.organizations = OrganizationRepository()
            self.datetimes = DatetimeRepository()
            self._initialized = True  # Чтобы `__init__` не вызывался повторно

    @classmethod
    def reset_instance(cls):
        cls._instance = None
