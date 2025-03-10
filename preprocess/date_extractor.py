from typing import Optional
from hors import process_phrase
from hors.partial_date.partial_datetime import PartialDateTime


class DateExtractor:
    def extract(self, text, now: Optional[PartialDateTime] = None):
        result = process_phrase(text, now)
        # Используем исходный текст из результата, если он есть, иначе переданный текст.
        orig_text = result.source if hasattr(result, 'source') and result.source else text

        if not result.dates:
            return orig_text, result.dates

        # Сортируем даты по атрибуту start
        sorted_dates = sorted(result.dates, key=lambda d: d.start)
        new_text = ""
        current_index = 0

        for i, d in enumerate(sorted_dates):
            start = d.start  # обращаемся к атрибуту start
            end = d.end  # обращаемся к атрибуту end
            new_text += orig_text[current_index:start]
            new_text += f"<|DATETIME_{i + 1}|>"
            current_index = end

        new_text += orig_text[current_index:]
        return new_text, result.dates
