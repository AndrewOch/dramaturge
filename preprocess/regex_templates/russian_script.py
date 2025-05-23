import re
from typing import List, Tuple, Dict

from preprocess.regex_templates.template import RegexTemplate


class RussianScriptTemplate(RegexTemplate):
    dates_regex: str = r'(\d{2}\.\d{2}\.\d{4})'
    entities_regexes: Dict[str, str] = {
        'PER': r'(?<!<\|)^(?P<speaker>[А-ЯЁ]{3,}):\s(?!\|>)'
    }
    direct_speech_regexes: List[Tuple[str, bool, int]] = [
        (r'^(?P<speaker>[А-ЯЁ]{3,}):\s*\n(?P<quote>.+?)(?=\n{2,}|$)', True, re.M | re.S),
        (r'^(?P<speaker>[А-ЯЁ]{3,}):\s*(?P<quote>.+)$', True, re.M),
        (r'^[\-–—]\s*(?P<quote>.+)$', False, re.M),
        (r'(?<!<\|)[«"“](?P<quote>.+?)[»"”](?!\|>)', False, 0),
        (r'\((?P<speaker>[А-ЯЁ][а-яё]{2,})\)\s*[«"“](?P<quote>.+?)[»"”]', True, 0),
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s*[\-–—]\s*(?P<quote>.+)$', True, re.M),
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s*:\s*(?P<quote>.+)$', True, re.M),
        (r'^(?P<speaker>[А-ЯЁ]{3,})\s+(?P<quote>[а-яё].+)$', True, re.M),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cleanup_regexes = [
            (r'^(?im)(ИНТ(?:ЕРЬЕР)?|ЭКСТ(?:ЕРЬЕР)?|ИНТ\.|ЭКСТ\.|НАТ(?:\s+НАТ\.)?)\s*[\s\-:]+.*$', ''),
            (r'\s{2,}', ' '),
            (r',\s*,', ','),
            (r'\s*,\s*', ', '),
        ]

        self.load_stopwords_from_csv('./regex_templates/resources/stopwords.csv', index=2)
