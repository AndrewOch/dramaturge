import uuid
from typing import Dict, List

from hors.models.parser_models import DateTimeToken
from pydantic import BaseModel, Field


class StoryEvent(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    index: int
    source_text: str
    text: str
    dates: List[DateTimeToken]
    elements: Dict[str, Dict[int, uuid.UUID]]

    class Config:
        arbitrary_types_allowed = True
