import uuid
from typing import List

from hors.partial_date.partial_datetime import PartialDateTime
from pydantic import BaseModel

from utils.partial_dates import merge_dates


class StoryElement(BaseModel):
    id = uuid.uuid4()
    name: str
    type: str
    associated_names: List[str]
    birth_date: PartialDateTime
    last_date: PartialDateTime
    properties: List[str]

    def __eq__(self, other):
        if self.id == other.id:
            return True
        self_names = {self.name, self.associated_names}
        other_names = {other.name, other.associated_names}
        for name in self_names:
            for other_name in other_names:
                if name == other_name or name in other_name or other_name in name:
                    return True
        return False

    def merge(self, other):
        new_associated_names = {self.name, other.name, self.associated_names, other.associated_names}
        new_properties = {self.properties, other.properties}
        birth_date = merge_dates(self.birth_date, self.birth_date)
        last_date = merge_dates(self.last_date, self.last_date)
        return StoryElement(
            id=self.id,
            name=self.name,
            type=self.type,
            associated_names=new_associated_names,
            birth_date=birth_date,
            last_date=last_date,
            properties=new_properties
        )


class Character(StoryElement):
    type = "PER"


class Location(StoryElement):
    type = "LOC"


class Organization(StoryElement):
    type = "ORG"
