import regex as re
from base import Tokenizer  # базовый класс, см. ниже
import unicodedata

# Используем GPT-4 split pattern (как в оригинале)
GPT4_SPLIT_PATTERN = r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""


def get_pair_stats(seqs):
    """
    Вычисляет статистику пар для списка последовательностей.
    Каждый токен – это кортеж (например, (120,) или (120, 208)).
    Возвращает словарь: { (token1, token2): count }.
    """
    stats = {}
    for seq in seqs:
        for i in range(len(seq) - 1):
            pair = (seq[i], seq[i + 1])
            stats[pair] = stats.get(pair, 0) + 1
    return stats


class RegexTokenizer(Tokenizer):
    def __init__(self, pattern=None):
        """
        pattern: опциональная строка для переопределения дефолтного GPT-4 split pattern.
        special_tokens: словарь специальных токенов.
        """
        super().__init__()
        self.pattern = GPT4_SPLIT_PATTERN if pattern is None else pattern
        self.compiled_pattern = re.compile(self.pattern)
        self.special_tokens = {}
        self.inverse_special_tokens = {}

    def train(self, text, vocab_size, verbose=False):
        assert vocab_size >= 256
        num_merges = vocab_size - 256

        # Разбиваем текст на чанки по регулярке и кодируем в байтовые последовательности.
        text_chunks = re.findall(self.compiled_pattern, text)
        # Представляем каждую последовательность как список токенов: каждый базовый токен – кортеж из одного байта.
        seqs = [[(b,) for b in chunk.encode("utf-8")] for chunk in text_chunks]
        # Изначальный словарь – для базовых токенов (0..255)
        vocab = {idx: bytes([idx]) for idx in range(256)}
        # Выполняем обучение «в уме»: виртуальные последовательности остаются неизменными, а статистика обновляется инкрементально.
        merges_virtual, vocab, seqs = self.optimized_train(seqs, num_merges, vocab, verbose)
        # На данном этапе merges_virtual: { (A, B): new_token } – где все токены представлены как кортежи
        # Для финального словаря мы сопоставляем каждому виртуальному токену новый целочисленный id.
        merges_final, vocab = self.convert_merges(merges_virtual, vocab, verbose)
        self.merges = merges_final
        self.vocab = vocab

    def optimized_train(self, seqs, num_merges, vocab, verbose=False):
        """
        Обучение «в уме»: исходный текст не изменяется, а глобальная статистика (по парам, где токены – кортежи)
        обновляется инкрементально.

        При слиянии пары (A, B) (например, A=(a,b,c,d) и B=(e,f)) новый токен Z = A+B появляется с количеством count.
        Затем из глобальной статистики вычитается count для всех пар, где слева ровно B или справа ровно A встречаются.
        И добавляются новые пары, где Z стоит слева или справа.
        """
        # Вычисляем начальную глобальную статистику по парам
        global_stats = get_pair_stats(seqs)

        # Словарь виртуальных merge-правил (с токенами в виде кортежей)
        merges = {}

        for merge_iter in range(num_merges):
            if not global_stats:
                if verbose:
                    print("Нет пар для слияния. Завершаем обучение.")
                break

            # Выбираем пару с максимальной частотой
            best_pair = max(global_stats, key=global_stats.get)
            best_count = global_stats[best_pair]
            if best_count <= 0:
                if verbose:
                    print("Нет пар с ненулевой частотой. Завершаем обучение.")
                break

            # Новый виртуальный токен — конкатенация кортежей
            new_token = best_pair[0] + best_pair[1]
            merges[best_pair] = new_token

            if verbose:
                print(f"merge {merge_iter + 1}: {best_pair} -> {new_token} (count: {best_count})")

            # --- Инкрементальное обновление глобальной статистики ---
            # 1. Удаляем выбранную пару из global_stats (чтобы она не выбралась повторно)
            del global_stats[best_pair]

            # 2. Вычитаем best_count из всех пар, где встречается целиком A = best_pair[0] (как ВТОРАЯ часть)
            #    и из всех пар, где встречается целиком B = best_pair[1] (как ПЕРВАЯ часть)
            for key in list(global_stats.keys()):
                if key[1] == best_pair[0]:
                    global_stats[key] -= best_count
                    if global_stats[key] <= 0:
                        del global_stats[key]
                elif key[0] == best_pair[1]:
                    global_stats[key] -= best_count
                    if global_stats[key] <= 0:
                        del global_stats[key]

            # 3. Обновляем виртуальные последовательности: в каждом seq заменяем каждое вхождение best_pair на new_token
            #    и одновременно собираем новые соседние пары, которые включают new_token.
            # Для каждого affected места будем увеличивать счётчик новых пар на 1 (каждая замена – единичное вхождение)
            for seq in seqs:
                i = 0
                while i < len(seq) - 1:
                    if seq[i] == best_pair[0] and seq[i + 1] == best_pair[1]:
                        # Перед заменой запоминаем соседей (если есть)
                        left = seq[i - 1] if i > 0 else None
                        right = seq[i + 2] if i + 2 < len(seq) else None
                        # Замена: вместо (A, B) вставляем new_token
                        seq[i:i + 2] = [new_token]
                        # Обновляем global_stats: если слева был L, то пара (L, new_token) прибавляется на 1;
                        if left is not None:
                            key = (left, new_token)
                            global_stats[key] = global_stats.get(key, 0) + 1
                        # Если справа есть R, то пара (new_token, R) прибавляется на 1
                        if right is not None:
                            key = (new_token, right)
                            global_stats[key] = global_stats.get(key, 0) + 1
                        # После замены продолжаем со следующей позиции (не увеличиваем i, так как длина seq уменьшилась)
                    else:
                        i += 1
            # Конец обновления для текущей итерации

        return merges, vocab, seqs

    def convert_merges(self, merges_virtual, vocab, verbose=False):
        """
        Преобразует виртуальные merge‑правила (с токенами-туples) в правила с целочисленными id,
        как в обычном методе обучения.
        Каждому новому виртуальному токену присваиваем уникальный id, начиная с 256.
        При этом итоговый словарь модели будет иметь обычное представление: базовые токены – 0..255,
        новые – целые числа.
        """
        merges_final = {}
        next_id = 256
        # Создадим вспомогательный словарь для преобразования виртуального токена (tuple) в id.
        virtual2id = {}
        # Базовые токены: каждый кортеж из одного элемента (x,) сопоставляем с x
        for i in range(256):
            virtual2id[(i,)] = i

        # Для каждого правила в порядке обучения (порядок не гарантируется при итерации по словарю,
        # но для примера возьмём произвольный порядок)
        for pair, virtual_token in merges_virtual.items():
            # Преобразуем составные токены в их id с помощью virtual2id, затем создаём новый id
            # Здесь предполагается, что для всех составляющих virtual_token уже назначены id
            new_id = next_id
            next_id += 1
            merges_final[pair] = new_id
            virtual2id[virtual_token] = new_id
            # Можно также обновить vocab: новый токен = конкатенация базовых байтов
            # Но для финального словаря vocab должен быть записан через целочисленные id (как в обычном методе)
            # Поэтому здесь оставляем обновление vocab в базовом классе.
            if verbose:
                print(f"Converted virtual token {virtual_token} -> id {new_id}")
        return merges_final, vocab

    def register_special_tokens(self, special_tokens):
        self.special_tokens = special_tokens
        self.inverse_special_tokens = {v: k for k, v in special_tokens.items()}

    def decode(self, ids):
        part_bytes = []
        for token in ids:
            if isinstance(token, int):
                b = self.vocab.get(token, b"")
            else:
                # Если вдруг токен не целочисленный, пытаемся его развёрнуть
                flat = self.flatten_token(token)
                b = b"".join(self.vocab.get(t, b"") for t in flat)
            part_bytes.append(b)
        text_bytes = b"".join(part_bytes)
        return text_bytes.decode("utf-8", errors="replace")

    def flatten_token(self, token):
        """Рекурсивно разворачивает токен (если он кортеж) в список базовых id."""
        if not isinstance(token, tuple):
            return [token]
        else:
            result = []
            for t in token:
                result.extend(self.flatten_token(t))
            return result

    def encode_ordinary(self, text):
        # Для кодирования нового текста используем обычное разделение: базовые токены.
        text_chunks = re.findall(self.compiled_pattern, text)
        ids = []
        for chunk in text_chunks:
            chunk_bytes = chunk.encode("utf-8")
            ids.extend(list(chunk_bytes))
        return ids

    def encode(self, text, allowed_special="none_raise"):
        base_ids = self.encode_ordinary(text)
        # Представляем базовые токены в виде кортежей, чтобы можно было применять merge‑правила.
        seq = [(b,) for b in base_ids]
        # Применяем merge‑правила в порядке обучения (проходим по правилам в произвольном порядке)
        # Здесь для упрощения реализуем последовательное применение: ищем в последовательности вхождения пары и заменяем.
        for pair, new_id in self.merges.items():
            new_seq = []
            i = 0
            while i < len(seq):
                if i < len(seq) - 1 and seq[i] == pair[0] and seq[i + 1] == pair[1]:
                    # Для финального кодирования заменяем на новый целочисленный токен new_id
                    new_seq.append(new_id)
                    i += 2
                else:
                    new_seq.append(seq[i])
                    i += 1
            seq = new_seq
        return seq
