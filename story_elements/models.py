import uuid
from enum import Enum, auto
from typing import List, Optional
from pydantic import BaseModel, Field
from hors.partial_date.partial_datetime import PartialDateTime


class StoryElementExtractionOrigin(Enum):
    MANUAL = auto()
    REGEX = auto()
    NATASHA = auto()


class StoryElement(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    type: str
    associated_names: List[str] = []
    birth_date: Optional[PartialDateTime] = None
    last_date: Optional[PartialDateTime] = None
    properties: List[str] = []
    extraction_origin: Optional[StoryElementExtractionOrigin] = None

    class Config:
        arbitrary_types_allowed = True

    def __eq__(self, other):
        intersection = (set(self.associated_names) | {self.name}) & (set(other.associated_names) | {other.name})
        return self.id == other.id or len(intersection) > 0

    def merge(self, other):
        other_new_associated_names = other.name.strip().split(' ')
        new_associated_names = (
                {self.name} |
                set(self.associated_names) |
                {other.name} |
                set(other.associated_names) |
                set(other_new_associated_names)
        )
        new_properties = set(self.properties) | set(other.properties)

        birth_date = self.birth_date
        if birth_date is None:
            birth_date = other.birth_date
        elif other.birth_date is not None:
            birth_date = birth_date.merge(other.birth_date)

        last_date = self.last_date
        if last_date is None:
            last_date = other.last_date
        elif other.last_date is not None:
            last_date = last_date.merge(other.last_date)

        return StoryElement(
            id=self.id,
            name=self.name,
            type=self.type,
            associated_names=list(new_associated_names),
            birth_date=birth_date,
            last_date=last_date,
            properties=list(new_properties),
            extraction_origin=self.extraction_origin,
        )


class Character(StoryElement):
    type: str = "PER"


class Location(StoryElement):
    type: str = "LOC"


class Organization(StoryElement):
    type: str = "ORG"
