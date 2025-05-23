from typing import List, Tuple, Dict, Optional
from pydantic import BaseModel, Field
import re
import csv


class RegexTemplate(BaseModel):
    cleanup_regexes: List[Tuple[str, str]] = Field(default_factory=list)
    dates_regex: Optional[str] = None
    entities_regexes: Dict[str, str] = Field(default_factory=dict)
    direct_speech_regexes: List[Tuple[str, bool, int]] = Field(default_factory=list)

    def add_regex(self, pattern: str, replacement: str, index: Optional[int] = None) -> None:
        """
        Добавляет регулярное выражение в cleanup_regexes.
        :param pattern: Регулярное выражение.
        :param replacement: Замена.
        :param index: Позиция, куда вставить регулярное выражение (по умолчанию в конец).
        """
        if index is not None:
            self.cleanup_regexes.insert(index, (pattern, replacement))
        else:
            self.cleanup_regexes.append((pattern, replacement))

    def load_stopwords_from_csv(self, csv_path: str, index: Optional[int] = None) -> None:
        """
        Загружает ненужные слова из CSV-файла и добавляет их в cleanup_regexes.
        :param csv_path: Путь к CSV-файлу.
        :param index: Позиция, куда вставить регулярное выражение (по умолчанию в конец).
        """
        stopwords = self._load_stopwords(csv_path)
        regex_pattern = self._build_stopwords_regex(stopwords)
        self.add_regex(regex_pattern, ' ', index)

    def _load_stopwords(self, csv_path: str) -> List[str]:
        """
        Загружает ненужные слова из CSV-файла (одно слово на строку).
        :param csv_path: Путь к CSV-файлу.
        :return: Список ненужных слов.
        """
        stopwords = []
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:  # Проверяем, что строка не пустая
                    word = row[0].strip()  # Берем первое значение из строки
                    if word:  # Проверяем, что слово не пустое
                        stopwords.append(word)
        return stopwords

    def _build_stopwords_regex(self, stopwords: List[str]) -> str:
        """
        Создает регулярное выражение для удаления ненужных слов.
        :param stopwords: Список ненужных слов.
        :return: Регулярное выражение.
        """
        if not stopwords:
            return ''
        # Экранируем специальные символы в словах
        escaped_words = [re.escape(word) for word in stopwords]
        # Собираем регулярное выражение
        return r'\s*,?\s*\b(' + '|'.join(escaped_words) + r')\b\s*,?\s*'
