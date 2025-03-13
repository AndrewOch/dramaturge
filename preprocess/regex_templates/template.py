from typing import List, Tuple, Dict, Optional

from pydantic import BaseModel


class RegexTemplate(BaseModel):
    cleanup_regexes: List[Tuple[str, str]] = []
    dates_regex = Optional[str]
    entities_regexes: Dict[str, str] = {}
    direct_speech_regexes: List[Tuple[str, bool, int]] = []
