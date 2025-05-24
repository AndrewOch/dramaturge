import os
from typing import Dict, List

import pandas as pd

from preprocess.modules.markup.models import EventToken, EventMarkupBlock


class SpecialTokensPipeline:
    def __init__(self, mapping_path: str = './modules/special_tokens/resources/special_token_mappings.csv'):
        # делаем все ключи в lower()
        self.special_tokens: Dict[str, str] = {
            k.lower(): v
            for k, v in self._load_special_tokens(mapping_path).items()
        }
        # сортируем фразы по длине (числу слов), чтобы сначала шли самые длинные
        self.sorted_phrases: List[str] = sorted(
            self.special_tokens.keys(),
            key=lambda s: len(s.split()),
            reverse=True
        )

    def process(self, block: EventMarkupBlock) -> EventMarkupBlock:
        for markup in block:
            tokens = markup.tokens
            i = 0
            while i < len(tokens):
                matched = False
                for phrase in self.sorted_phrases:
                    words = phrase.split()
                    L = len(words)
                    if i + L <= len(tokens) and all(
                            tokens[i + j].text.lower() == words[j] for j in range(L)
                    ):
                        parent = tokens[i]
                        new_tok = EventToken.__new__(EventToken)
                        new_tok.id = parent.id
                        new_tok.head_id = parent.head_id
                        new_tok.rel = parent.rel
                        new_tok.text = self.special_tokens[phrase]
                        new_tok.pos = parent.pos
                        new_tok.feats = parent.feats
                        tokens[i: i + L] = [new_tok]
                        matched = True
                        break
                if not matched:
                    i += 1
            markup.tokens = tokens
        return block

    def _load_special_tokens(self, path: str) -> Dict[str, str]:
        if not os.path.exists(path):
            return {}
        df = pd.read_csv(path)
        return {row['Text']: row['SpecialToken'] for _, row in df.iterrows()}
