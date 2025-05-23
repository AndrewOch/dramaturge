import argparse
import json
import logging
import multiprocessing
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List
from uuid import UUID
import re

import nltk
from pydantic import BaseModel

from preprocess.preprocessor import EventPreprocessor
from preprocess.regex_templates.literary_prose import LiteraryProseTemplate
from story_elements.database import StoryElementsDatabase
from tokenizer.train import collect_txt_files

nltk.download('punkt')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ERROR_LOG_FILE = "failed_files.txt"
PROCESSED_LOG_FILE = "processed_files.txt"


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        if isinstance(obj, Enum):
            return obj.name
        return super().default(obj)


def log_failed_file(file_path: str, error: Exception):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_message = f"{timestamp} | {file_path} | {type(error).__name__}: {str(error)}\n"
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(error_message)


def log_processed_file(file_path: str):
    with open(PROCESSED_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{file_path}\n")


def get_processed_files() -> List[str]:
    if Path(PROCESSED_LOG_FILE).exists():
        with open(PROCESSED_LOG_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []


def split_paragraphs(text: str, max_words: int = 100) -> List[str]:
    # Разбиваем текст так, чтобы перед "ИНТ." или "НАТ." вставить разделитель
    scene_parts = re.split(r"(?=\b(?:ИНТ\.|НАТ\.))", text)
    paragraphs = []

    # Обрабатываем каждую часть отдельно
    for part in scene_parts:
        part = part.strip()
        if not part:
            continue

        # Токенизация на предложения
        sentences = nltk.sent_tokenize(part)
        current_paragraph = []
        current_word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            words = sentence.split()

            # Если предложение начинается с "ИНТ." или "НАТ." и уже есть накопленный текст,
            # завершаем текущий абзац и начинаем новый.
            if sentence.startswith(("ИНТ.", "НАТ.")) and current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
                current_word_count = 0

            # Если добавление предложения превышает лимит по количеству слов
            if current_word_count + len(words) > max_words:
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
                    current_word_count = 0
                # Если само предложение длинное, разбиваем его на части
                if len(words) > max_words:
                    for i in range(0, len(words), max_words):
                        paragraphs.append(' '.join(words[i:i + max_words]))
                else:
                    current_paragraph.extend(words)
                    current_word_count += len(words)
            else:
                current_paragraph.extend(words)
                current_word_count += len(words)

        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))

    return paragraphs


def process_file(file_path: str, output_dir: str) -> None:
    try:
        if Path(output_dir, f"{Path(file_path).stem}_processed.json").exists():
            logger.info(f"Файл уже обработан: {file_path}")
            return

        logger.info(f"Начата обработка файла: {file_path}")
        db = StoryElementsDatabase()
        preprocessor = EventPreprocessor(LiteraryProseTemplate(), db)

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        paragraphs = split_paragraphs(text)
        logger.info(f"Параграфы разделены: {file_path} {len(paragraphs)}")

        events = []
        index = 0

        for para in paragraphs:
            logger.info(f"Параграф {index} начинает обработку: {para}")
            event = preprocessor.preprocess(para, index=index)
            logger.info(f"Параграф {index} обработан: {file_path}")
            events.append(event)
            index += 1

        story_elements = {
            'PER': [elem.model_dump() for elem in db.characters.elements],
            'LOC': [elem.model_dump() for elem in db.locations.elements],
            'ORG': [elem.model_dump() for elem in db.organizations.elements]
        }

        result = {
            'events': [event.model_dump() for event in events],
            'story_elements': story_elements
        }

        output_path = Path(output_dir) / f"{Path(file_path).stem}_processed.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, cls=JSONEncoder)

        log_processed_file(file_path)
        logger.info(f"Файл успешно обработан: {file_path}")

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}:\n{traceback.format_exc()}")
        log_failed_file(file_path, e)


def process_all_files(input_dir: str = "../data", output_dir: str = "../data_preprocessed", resume: bool = False):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    file_paths = collect_txt_files(input_dir)

    if resume:
        processed = get_processed_files()
        file_paths = [fp for fp in file_paths if fp not in processed]
        logger.info(f"Возобновление обработки. Осталось файлов: {len(file_paths)}")

    logger.info(f"Найдено {len(file_paths)} файлов для обработки.")

    with multiprocessing.Pool() as pool:
        pool.starmap(process_file, [(file_path, output_dir) for file_path in file_paths])

    logger.info("Обработка всех файлов завершена.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Обработка текстовых файлов')
    parser.add_argument('--input', default='../data', help='Входная директория')
    parser.add_argument('--output', default='../data_preprocessed', help='Выходная директория')
    parser.add_argument('--resume', action='store_true', help='Продолжить с места остановки')
    args = parser.parse_args()

    process_all_files(input_dir=args.input, output_dir=args.output, resume=args.resume)
