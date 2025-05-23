import re
from typing import Dict, List, Tuple

from preprocess.regex_templates.template import RegexTemplate


class HollywoodScriptTemplate(RegexTemplate):
    dates_regex: str = r'(\d{2}\.\d{2}\.\d{4})'
    entities_regexes: Dict[str, str] = {
        'PER': r'(?<!<\|)\b(?:[A-ZА-ЯЁ]{3,}(?:\s+[A-ZА-ЯЁ]{3,})*)\b(?!\|>)'
    }
    direct_speech_regexes: List[Tuple[str, bool, int]] = [
        (r'^(?P<speaker>[A-ZА-ЯЁ\s]{3,})\n(?P<quote>.+?)(?=\n{2,}|$)', True, re.M | re.S),
        (r'^(?P<speaker>[A-ZА-ЯЁ\s]{3,}):\s*(?P<quote>.+)$', True, re.M),
        (r'(?<!<\|)[“"\'”](?P<quote>.+?)[“"\'”](?!\|>)', False, 0),
        (r'^[\-–]\s*(?P<quote>.+)$', False, re.M),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cleanup_regexes = [
            (r'(?im)^(?:(?:INT\.|EXT\.|NAT\s+NAT\.)|(?:ИНТ(?:ЕРЬЕР)?|ЭКСТ(?:ЕРЬЕР)?|НАТ(?:\s+НАТ\.)?))\s.*$', ''),
            (r'\s{2,}', ' '),
            (r',\s*,', ','),
            (r'\s*,\s*', ', '),
        ]

        self.load_stopwords_from_csv('./regex_templates/resources/stopwords.csv', index=2)
