import os
import re
from typing import Dict

import pandas as pd


class SpecialTokensPipeline:
    def __init__(self):
        self.special_tokens_dict = self._load_special_tokens('./resources/special_token_mappings.csv')

    def replace_with_special_tokens(self, text: str) -> str:
        sorted_items = sorted(self.special_tokens_dict.items(), key=lambda x: len(x[0]), reverse=True)

        for word, token in sorted_items:
            pattern = re.escape(word)

            pattern = r'\s*' + pattern + r'\s*'

            text = re.sub(pattern, f' {token} ', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _load_special_tokens(self, path: str) -> Dict[str, str]:
        if not os.path.exists(path):
            return {}

        df = pd.read_csv(path)
        special_tokens_dict = {}
        for _, row in df.iterrows():
            text = row['Text']
            token = row['SpecialToken']
            special_tokens_dict[text] = token
        return special_tokens_dict
