from typing import Optional

from hors.partial_date.partial_datetime import PartialDateTime
from icecream import icecream

from preprocess.event import StoryEvent
from preprocess.modules.cleanup.pipeline import CleanupPipeline
from preprocess.modules.extraction.date.pipeline import DateExtractionPipeline
from preprocess.modules.extraction.direct_speech.pipeline import DirectSpeechExtractionPipeline
from preprocess.modules.extraction.entity.pipeline import EntityExtractionPipeline
from preprocess.modules.extraction.properties.pipeline import PropertiesExtractionPipeline
from preprocess.modules.markup.pipeline import MarkupPipeline
from preprocess.modules.rearrange.pipeline import SentenceRearrangePipeline
from preprocess.modules.special_tokens.pipeline import SpecialTokensPipeline
from preprocess.regex_templates.template import RegexTemplate
from story_elements.database import StoryElementsDatabase


class EventPreprocessor:
    def __init__(self, regex_template: RegexTemplate = RegexTemplate(),
                 story_elements_database: StoryElementsDatabase = StoryElementsDatabase()):
        self.elems_database = story_elements_database
        self.cleanup = CleanupPipeline(regex_template.cleanup_regexes)
        self.markup = MarkupPipeline()
        self.dates = DateExtractionPipeline(regex_template.dates_regex)
        self.entities = EntityExtractionPipeline(self.elems_database, regex_template.entities_regexes)
        self.properties = PropertiesExtractionPipeline(self.elems_database)
        self.rearrange = SentenceRearrangePipeline()
        self.direct_speech = DirectSpeechExtractionPipeline(regex_template.direct_speech_regexes)
        self.special_tokens = SpecialTokensPipeline()

    def preprocess(self, text: str, index=0, now: Optional[PartialDateTime] = None) -> StoryEvent:
        source_text = text
        text = self.cleanup.cleanup(text)
        block = self.markup.process(text)
        block, dates = self.dates.process(block, now)
        block, entities = self.entities.process(block)
        # text, markups = self.properties.process(text, markups, entities)
        block = self.special_tokens.process(block)
        block = self.rearrange.rearrange(block)
        # text = self.direct_speech.process(text)

        icecream.ic(block)
        event = StoryEvent(
            index=index,
            source_text=source_text,
            dates=dates,
            elements=entities,
            markups=block
        )
        return event
