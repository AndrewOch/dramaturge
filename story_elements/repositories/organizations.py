from story_elements.models import Organization
from story_elements.repositories.base import BaseStoryElementRepository


class OrganizationRepository(BaseStoryElementRepository[Organization]):
    def __init__(self):
        super().__init__()
        self.special_token = 'ORG'
