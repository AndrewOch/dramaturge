import re
from typing import List, Tuple, Dict

from preprocess.regex_templates.template import RegexTemplate


class LiteraryProseTemplate(RegexTemplate):
    dates_regex: str = r'(\d{2}\.\d{2}\.\d{4})'
    entities_regexes: Dict[str, str] = {
        'PER': r'(?<!<\|)\b[А-ЯЁ][а-яё]{2,}(?:\s+[А-ЯЁ][а-яё]{2,})?\b(?!\|>)'
    }
    direct_speech_regexes: List[Tuple[str, bool, int]] = [

        (r'(?P<speaker>[А-ЯЁ][а-яё]{2,}(?:\s+[А-ЯЁ][а-яё]{2,})*)\s*[:\-]\s*[«"“](?P<quote>.+?)[»"”]', True, 0),

        (r'(?P<speaker>[А-ЯЁ][а-яё]{2,}(?:\s+[А-ЯЁ][а-яё]{2,})*)\s*[:\-]\s*(?P<quote>.+?)(?=[\.\n])', True, 0),

        (r'^[\-\–\—]\s*(?P<quote>.+)$', False, re.M),

        (r'(?<!<\|)[«"“](?P<quote>.+?)[»"”](?!\|>)', False, 0),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cleanup_regexes = [
            (r'\s+', ' '),
            (r'-{2,}', '—'),
            (r',\s*,', ','),
            (r'\s*,\s*', ', '),
        ]

        self.load_stopwords_from_csv('./resources/stopwords.csv', index=2)
