import uuid
from typing import Dict, List

from hors.models.parser_models import DateTimeToken
from pydantic import BaseModel, Field

from preprocess.modules.markup.pipeline import EventMarkup


class StoryEvent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    index: int
    source_text: str
    markups: List[EventMarkup] = Field(default_factory=list, exclude=True)
    dates: List[DateTimeToken]
    elements: Dict[str, Dict[int, uuid.UUID]]

    class Config:
        arbitrary_types_allowed = True

    def text(self):
        return str(self.block)
