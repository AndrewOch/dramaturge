import os
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import BpeTrainer


def special_tokens():
    tokens = ["<|UNK|>", "<|QUOTE_ST|>", "<|QUOTE_MID|>", "<|QUOTE_END|>"]
    elements_heads = ["PER", "LOC", "ORG", "DATETIME"]
    for element in elements_heads:
        for i in range(10):
            tokens.append(f"<|{element}-{i}|>")
    return tokens


def collect_txt_files(root_dir):
    """
    Рекурсивно обходит папку root_dir и возвращает список путей ко всем .txt файлам.
    """
    txt_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.txt'):
                txt_files.append(os.path.join(dirpath, filename))
    return txt_files


def load_texts(file_list):
    """
    Загружает содержимое файлов из списка file_list, заменяя некорректные байты на символ замены.
    """
    texts = []
    for file in file_list:
        with open(file, 'r', encoding='utf-8', errors='replace') as f:
            texts.append(f.read())
    return texts


if __name__ == '__main__':
    root_dir = "../data"
    # Собираем пути к .txt файлам
    txt_files = collect_txt_files(root_dir)
    print(f"Найдено {len(txt_files)} .txt файлов.")

    # Определяем размер словаря (например, 256 + 3 специальных токена)
    vocab_size = 256 + 30000

    # Создаем токенизатор с моделью BPE и задаем токен для неизвестных символов
    tokenizer = Tokenizer(BPE(unk_token="<|UNK|>"))
    # Устанавливаем препроцессор для разбиения текста по пробельным символам
    tokenizer.pre_tokenizer = Whitespace()

    # Определяем тренера с нужными специальными токенами
    trainer = BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=special_tokens()
    )

    # Загружаем тексты с обработкой ошибок декодирования
    texts = load_texts(txt_files)

    # Обучаем токенизатор, используя итератор текстов
    tokenizer.train_from_iterator(texts, trainer=trainer, length=len(texts))

    # Сохраняем обученный токенизатор в формате JSON
    tokenizer.save("tokenizer.json")
    print("Обучение токенизатора завершено.")
