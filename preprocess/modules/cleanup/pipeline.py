from typing import List, Tuple

from preprocess.modules.cleanup.processors.regex import RegexCleanupProcessor


class CleanupPipeline:
    def __init__(self, regexes: List[Tuple[str, str]]):
        self.regex = RegexCleanupProcessor(regexes)

    def cleanup(self, text: str) -> str:
        text = self.regex.cleanup(text)
        return text.strip()
