import re
from typing import Tuple, List, Dict

from razdel import tokenize

from story_elements.models import StoryElement, StoryElementExtractionOrigin


class RegexEntityExtractor:
    def __init__(self, regexes=None):
        if regexes is None:
            regexes = {}
        self.regexes: Dict[str, str] = regexes

    def extract(self, text: str, morph_markups, syntax_markups, token_counters: Dict[str, int] = None) -> \
            Tuple[str, Dict[str, List[StoryElement]]]:
        if token_counters is None:
            token_counters = {}
        for etype in self.regexes.keys():
            if etype not in token_counters:
                token_counters[etype] = 1

        entities = {}
        original_text = text

        global_tokens = list(tokenize(original_text))

        flat_morph_tokens = []
        for markup in morph_markups:
            flat_morph_tokens.extend(markup.tokens)
        flat_syntax_tokens = []
        for markup in syntax_markups:
            flat_syntax_tokens.extend(markup.tokens)

        case_tokens = {
            'Gen': '<|C_GEN|>',
            'Dat': '<|C_DAT|>',
            'Acc': '<|C_ACC|>',
            'Ins': '<|C_INS|>',
            'Loc': '<|C_LOC|>',
            'Voc': '<|C_VOC|>'
        }

        allowed_punct = {',', '-', '—'}

        def is_desired_token(morph_token, syntax_token):

            if re.fullmatch(r'\W+', morph_token.text):
                if morph_token.text in allowed_punct:
                    return True
                else:
                    return False

            if hasattr(syntax_token, 'rel') and syntax_token.rel == 'punct':
                if syntax_token.text in allowed_punct:
                    return True
                else:
                    return False

            if morph_token.pos != 'PROPN':
                return False
            return True

        def repl(match, etype):
            match_start = match.start()
            match_end = match.end()
            m = match.group(0)

            filtered_tokens = []
            entity_case = None

            for i, token in enumerate(global_tokens):

                if token.start < match_end and token.stop > match_start:
                    if i < len(flat_morph_tokens) and i < len(flat_syntax_tokens):
                        morph_token = flat_morph_tokens[i]
                        syntax_token = flat_syntax_tokens[i]
                        if is_desired_token(morph_token, syntax_token):
                            filtered_tokens.append(token.text)

                            if entity_case is None and morph_token.pos == 'PROPN':
                                entity_case = morph_token.feats.get('Case', 'Nom')

            while filtered_tokens and filtered_tokens[0] in allowed_punct:
                filtered_tokens.pop(0)
            while filtered_tokens and filtered_tokens[-1] in allowed_punct:
                filtered_tokens.pop()
            filtered_entity = " ".join(filtered_tokens).strip()

            if not filtered_entity:
                return m

            token_placeholder = f"<|{etype}_{token_counters[etype]}|>"

            if entity_case is not None and entity_case != 'Nom' and entity_case in case_tokens:
                token_placeholder += case_tokens[entity_case]
            element = StoryElement(
                name=filtered_entity,
                type=etype,
                extraction_origin=StoryElementExtractionOrigin.REGEX
            )
            if etype not in entities:
                entities[etype] = []
            entities[etype].append(element)
            token_counters[etype] += 1
            return token_placeholder

        for entity_type, pattern in self.regexes.items():
            text = re.sub(pattern, lambda m, etype=entity_type: repl(m, etype), text)
        return text, entities
