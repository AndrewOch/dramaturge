from typing import List, Tuple

import icecream

from preprocess.modules.markup.pipeline import EventMarkup, EventToken


class SentenceRearrangePipeline:
    # приоритеты рёбер (rel): меньший приоритет – раньше в предложении
    REL_PRIORITY = {
        'root': 0,
        'nsubj': 1,
        'obj': 2,
        'iobj': 3,
        'ccomp': 4,
        'xcomp': 5,
        'obl': 6,
        'advmod': 7,
        'amod': 8,
        'det': 9,
        'case': 10,
        'mark': 11,
        'punct': 12,
    }

    def rearrange(self, event_markups: List[EventMarkup]) -> Tuple[str, List[EventMarkup]]:
        new_sentences = []

        for em in event_markups:
            tokens = em.tokens

            children: dict[int, List[EventToken]] = {}
            for tok in tokens:
                children.setdefault(tok.head_id, []).append(tok)

            existing_ids = {tok.id for tok in tokens}
            roots = [tok for tok in tokens if tok.head_id not in existing_ids]
            if not roots:
                roots = [min(tokens, key=lambda t: t.id)]

            def traverse(node: EventToken) -> List[EventToken]:
                ordered = [node]
                kids = children.get(node.id, [])
                max_pr = max(self.REL_PRIORITY.values()) + 1
                kids_sorted = sorted(
                    kids,
                    key=lambda t: (
                        self.REL_PRIORITY.get(t.rel, max_pr),
                        t.id
                    )
                )
                for child in kids_sorted:
                    ordered.extend(traverse(child))
                return ordered

            max_pr = max(self.REL_PRIORITY.values()) + 1
            roots_sorted = sorted(
                roots,
                key=lambda t: (
                    self.REL_PRIORITY.get(t.rel, max_pr),
                    t.id
                )
            )
            ordered_tokens: List[EventToken] = []
            for root in roots_sorted:
                ordered_tokens.extend(traverse(root))

            old_to_new = {old.id: new_id
                          for new_id, old in enumerate(ordered_tokens, start=1)}
            for new_id, tok in enumerate(ordered_tokens, start=1):
                old_head = tok.head_id
                tok.id = new_id
                tok.head_id = old_to_new.get(old_head, 0)

            em.tokens = ordered_tokens
            new_sentences.append(str(em))

        new_text = "\n".join(new_sentences)
        icecream.ic(event_markups)
        return new_text, event_markups
