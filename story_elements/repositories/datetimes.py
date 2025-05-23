from hors.partial_date.partial_datetime import PartialDateTime

from story_elements.repositories.base import BaseStoryElementRepository


class DatetimeRepository(BaseStoryElementRepository[PartialDateTime]):
    def __init__(self):
        super().__init__()
        self.special_token = 'DATETIME'
