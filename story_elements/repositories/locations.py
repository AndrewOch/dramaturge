from story_elements.models import Location
from story_elements.repositories.base import BaseStoryElementRepository


class LocationRepository(BaseStoryElementRepository[Location]):
    def __init__(self):
        super().__init__()
        self.special_token = Location.type
