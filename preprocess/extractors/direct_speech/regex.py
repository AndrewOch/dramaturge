import re
from typing import Tuple, List


class RegexDirectSpeechProcessor:
    def __init__(self, regexes=None):
        if regexes is None:
            regexes = []
        self.regexes: List[Tuple[str, bool, int]] = regexes

    def process(self, text: str) -> str:
        for pattern, with_speaker, flags in self.regexes:
            regex = re.compile(pattern, flags)

            def repl(match):
                speaker = match.group("speaker").strip() if with_speaker and match.group("speaker") else "?"
                quote = match.group("quote").strip()
                return f"<|QUOTE_ST|>{speaker}<|QUOTE_MID|>{quote}<|QUOTE_END|>"

            text = regex.sub(repl, text)
        return text
