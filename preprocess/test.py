import icecream

from preprocess.preprocessor import EventPreprocessor
from preprocess.regex_processors.literary_prose import LiteraryProseRegexProcessor
from preprocess.regex_processors.hollywood_script import HollywoodScriptRegexProcessor
from preprocess.regex_processors.russian_script import RussianScriptRegexProcessor

if __name__ == '__main__':
    preprocessor = EventPreprocessor(regex_processor=LiteraryProseRegexProcessor())
    preprocessor1 = EventPreprocessor(regex_processor=HollywoodScriptRegexProcessor())
    preprocessor2 = EventPreprocessor(regex_processor=RussianScriptRegexProcessor())

    texts = [
        "После венчания не было даже легкой закуски; молодые выпили по бокалу, переоделись и поехали на вокзал. Вместо веселого свадебного бала и ужина, вместо музыки и танцев — поездка на богомолье за двести верст. Многие одобрили это, говоря, что Модест Алексеич уже в чинах и не молод, и шумная свадьба могла бы, пожалуй, показаться не совсем приличной; да и скучно слушать музыку, когда чиновник 52 лет женится на девушке, которой едва минуло 18. Говорили также, что эту поездку в монастырь Модест Алексеич, как человек с правилами, затеял, собственно, для того, чтобы дать понять своей молодой жене, что и в браке он отдает первое место религии и нравственности."
        ,
        "Молодых провожали. Толпа сослуживцев и родных стояла с бокалами и ждала, когда пойдет поезд, чтобы крикнуть ура, и Петр Леонтьич, отец, в цилиндре, в учительском фраке, уже пьяный и уже очень бледный, всё тянулся к окну со своим бокалом и говорил умоляюще:"
        ,
        "— Анюта! Аня! Аня, на одно слово! Подойди завтра"
        , "У меня уже дежурство закончилось."
    ]
    d = "=" * 25
    icecream.ic(f"{d} Литература {d}")

    for text in texts:
        result = preprocessor.preprocess(text, )
        icecream.ic(result)

    icecream.ic(f"{d} Голливуд {d}")

    for text in texts:
        result = preprocessor1.preprocess(text, )
        icecream.ic(result)

    icecream.ic(f"{d} Русский сценарий {d}")

    for text in texts:
        result = preprocessor2.preprocess(text, )
        icecream.ic(result)
