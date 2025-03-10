from tokenizers import Tokenizer


def test_tokenizer(tokenizer, samples):
    for text in samples:
        # Кодируем текст
        encoding = tokenizer.encode(text)
        tokens = encoding.tokens
        ids = encoding.ids

        # Декодируем обратно из идентификаторов
        decoded_text = tokenizer.decode(ids)

        print("Исходный текст:", text)
        print("Токены:", tokens)
        print("ID токенов:", ids)
        print("Декодированный текст:", decoded_text)
        print("-" * 50)


if __name__ == '__main__':
    # Загружаем токенизатор из файла
    tokenizer = Tokenizer.from_file("tokenizer.json")

    # Примеры для тестирования
    test_samples = [
        "Привет, как дела?\nЭто тестовая строка для токенизации.",
        "Это тестовая строка для токенизации.",
        "Еще один пример текста, чтобы проверить работу токенизатора!"
    ]

    test_tokenizer(tokenizer, test_samples)
