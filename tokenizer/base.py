import unicodedata


def replace_control_characters(s: str) -> str:
    chars = []
    for ch in s:
        if unicodedata.category(ch)[0] != "C":
            chars.append(ch)
        else:
            chars.append(f"\\u{ord(ch):04x}")
    return "".join(chars)


def render_token(t: bytes) -> str:
    s = t.decode("utf-8", errors="replace")
    return replace_control_characters(s)


class Tokenizer:
    def __init__(self):
        self.merges = {}  # Будет содержать финальные merge‑правила: (token1, token2) -> id
        self.pattern = ""
        self.special_tokens = {}
        self.vocab = self._build_vocab()

    def train(self, text, vocab_size, verbose=False):
        raise NotImplementedError

    def encode(self, text):
        raise NotImplementedError

    def decode(self, ids):
        raise NotImplementedError

    def _build_vocab(self):
        # Начальный словарь для базовых токенов: числа 0..255 как байты
        vocab = {i: bytes([i]) for i in range(256)}
        # Для новых токенов, полученных по merge, мы будем записывать их байтовое представление
        for (x, y), new_id in self.merges.items():
            # Здесь предполагается, что мы можем получить базовое представление, объединив базовые токены.
            # Для простоты оставляем это преобразование как есть.
            flat = self.flatten_token(new_id)
            vocab[new_id] = b"".join(vocab[t] for t in flat)
        for special, idx in self.special_tokens.items():
            vocab[idx] = special.encode("utf-8")
        return vocab

    def save(self, file_prefix):
        model_file = file_prefix + ".model"
        with open(model_file, "w") as f:
            f.write("minbpe v1\n")
            f.write(f"{self.pattern}\n")
            f.write(f"{len(self.special_tokens)}\n")
            for special, idx in self.special_tokens.items():
                f.write(f"{special} {idx}\n")
            for (x, y), new_id in self.merges.items():
                f.write(f"{x} {y} -> {new_id}\n")
        vocab_file = file_prefix + ".vocab"
        with open(vocab_file, "w", encoding="utf-8") as f:
            for idx, token in self.vocab.items():
                s = render_token(token)
                f.write(f"[{s}] {idx}\n")

    def load(self, model_file):
        # Реализация загрузки оставлена для краткости.
        pass

    def flatten_token(self, token):
        if not isinstance(token, tuple):
            return [token]
        else:
            result = []
            for t in token:
                result.extend(self.flatten_token(t))
            return result
