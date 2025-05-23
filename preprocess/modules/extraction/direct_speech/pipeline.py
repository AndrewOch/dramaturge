from typing import Tuple, List

from preprocess.modules.extraction.direct_speech.extractors.regex import RegexDirectSpeechExtractor


class DirectSpeechExtractionPipeline:
    def __init__(self, regexes: List[Tuple[str, bool, int]]):
        self.regex_extractor = RegexDirectSpeechExtractor(regexes)

    def process(self, text: str) -> str:
        return self.regex_extractor.process(text)
