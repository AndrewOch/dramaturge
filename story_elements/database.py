from story_elements.repositories.characters import CharacterRepository
from story_elements.repositories.datetimes import DatetimeRepository
from story_elements.repositories.locations import LocationRepository
from story_elements.repositories.organizations import OrganizationRepository


class StoryElementsDatabase:
    def __init__(self):
        self.characters = CharacterRepository()
        self.locations = LocationRepository()
        self.organizations = OrganizationRepository()
        self.datetimes = DatetimeRepository()
