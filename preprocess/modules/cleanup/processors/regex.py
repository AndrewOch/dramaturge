import re
from typing import Tuple, List


class RegexCleanupProcessor:
    def __init__(self, regexes=None):
        if regexes is None:
            regexes = []
        self._cleanup_regexes: List[Tuple[str, str]] = regexes

    def cleanup(self, text: str) -> str:
        for pattern, replacement in self._cleanup_regexes:
            text = re.sub(pattern, replacement, text)
        return text
