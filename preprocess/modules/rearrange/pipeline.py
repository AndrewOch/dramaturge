from typing import List, Tuple

from preprocess.modules.markup.pipeline import EventMarkup, EventToken


class SentenceRearrangePipeline:
    # приоритеты рёбер (rel): меньший — раньше в предложении
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
            before_count = len(tokens)

            # 1) разорвать самоссылки
            for tok in tokens:
                if tok.head_id == tok.id:
                    tok.head_id = 0

            # 2) разорвать циклы (поиск по head_id)
            by_id = {tok.id: tok for tok in tokens}
            for tok in tokens:
                visited = []
                cur = tok
                while True:
                    h = cur.head_id
                    if h == 0 or h not in by_id:
                        break
                    if h in visited:
                        # нашли цикл → разорвать только самую «малую» по id вершину цикла
                        cycle = visited[visited.index(h):] + [h]
                        root_id = min(cycle)
                        by_id[root_id].head_id = 0
                        break
                    visited.append(h)
                    cur = by_id[h]

            # 3) строим children
            children: dict[int, List[EventToken]] = {}
            for tok in tokens:
                children.setdefault(tok.head_id, []).append(tok)

            # 4) собираем корни
            existing = {tok.id for tok in tokens}
            roots = [tok for tok in tokens if tok.head_id == 0]
            if not roots:
                roots = [tok for tok in tokens if tok.head_id not in existing]
            if not roots:
                roots = [min(tokens, key=lambda t: t.id)]

            # вспомогательная функция обхода с visited
            def traverse(node: EventToken, visited: set[int]) -> List[EventToken]:
                if node.id in visited:
                    return []
                visited.add(node.id)
                seq = [node]
                kids = children.get(node.id, [])
                max_pr = max(self.REL_PRIORITY.values()) + 1
                # сортируем детей по rel, потом id
                kids_sorted = sorted(
                    kids,
                    key=lambda t: (self.REL_PRIORITY.get(t.rel, max_pr), t.id)
                )
                for ch in kids_sorted:
                    seq.extend(traverse(ch, visited))
                return seq

            # 5) обходим все ветки по порядку
            max_pr = max(self.REL_PRIORITY.values()) + 1
            roots_sorted = sorted(
                roots,
                key=lambda t: (self.REL_PRIORITY.get(t.rel, max_pr), t.id)
            )
            visited_ids = set()
            ordered = []
            # сначала по корням
            for r in roots_sorted:
                ordered.extend(traverse(r, visited_ids))
            # потом «висящие» остатки
            for tok in tokens:
                if tok.id not in visited_ids:
                    ordered.extend(traverse(tok, visited_ids))

            # 6) перенумерация
            old2new = {old.id: i for i, old in enumerate(ordered, start=1)}
            for new_id, tok in enumerate(ordered, start=1):
                old_h = tok.head_id
                tok.id = new_id
                tok.head_id = old2new.get(old_h, 0)

            em.tokens = ordered
            # контроль целостности
            assert len(em.tokens) == before_count, f"Token count mismatch: {before_count} → {len(em.tokens)}"

            new_sentences.append(str(em))

        text = "\n".join(new_sentences)
        return text, event_markups
