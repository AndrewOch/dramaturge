import icecream

from preprocess.preprocessor import EventPreprocessor
from preprocess.regex_templates.literary_prose import LiteraryProseTemplate
from preprocess.regex_templates.hollywood_script import HollywoodScriptTemplate
from preprocess.regex_templates.russian_script import RussianScriptTemplate
from story_elements.database import StoryElementsDatabase

if __name__ == '__main__':
    preprocessors = {
        "Литература": EventPreprocessor(LiteraryProseTemplate()),
        "Голливуд": EventPreprocessor(HollywoodScriptTemplate()),
        "Русский сценарий": EventPreprocessor(RussianScriptTemplate())
    }

    texts = [
        # "После венчания Ани, короче говоря, не было даже легкой закуски; молодые выпили по бокалу, переоделись "
        # "и поехали на вокзал. "
        # "Вместо веселого свадебного бала и ужина, вместо музыки и танцев — поездка на богомолье за двести верст. "
        # "Многие одобрили это, говоря, что Модест Алексеич может быть уже в чинах и не молод, и шумная свадьба могла бы, пожалуй, "
        # "показаться не совсем приличной; да и скучно слушать музыку, когда чиновник 52 лет женится на девушке, которой "
        # "едва минуло 18. Говорили также, что эту поездку в монастырь Модест Алексеич, как человек с правилами, затеял, "
        # "собственно, для того, чтобы дать понять своей молодой жене, что и в браке он отдает первое место религии "
        # "и нравственности."
        # ,
        # "Молодых провожали. Толпа сослуживцев и родных стояла с бокалами и ждала, когда пойдет поезд, чтобы крикнуть "
        # "ура, и Петр Леонтьич, отец, в цилиндре, в учительском фраке, уже пьяный и уже очень бледный, всё тянулся к "
        # "окну со своим бокалом и говорил умоляюще:"
        # ,
        # "— Анюта! Аня! Аня, на одно слово! Подойди завтра",
        # "У меня уже дежурство закончилось.",
        "Гуров отрезал себе ломоть и стал есть не спеша. Прошло, по крайней мере, полчаса в молчании. "
        "Анна Сергеевна была трогательна, от нее веяло чистотой порядочной, наивной, мало жившей женщины; одинокая "
        "свеча, горевшая на столе, едва освещала ее лицо, но было видно, что у нее нехорошо на душе. – Отчего бы я "
        "мог перестать уважать тебя? – спросил Гуров. – Ты сама не знаешь, что говоришь. – Пусть бог меня простит! – "
        "сказала она, и глаза у нее наполнились слезами. – Это ужасно. – Ты точно оправдываешься. – Чем мне "
        "оправдаться?"
    ]

    d = "=" * 25

    for key, preprocessor in preprocessors.items():
        icecream.ic(f"{d} {key} {d}")
        for text in texts:
            database = StoryElementsDatabase()
            preprocessor.database = database
            result = preprocessor.preprocess(text)
            icecream.ic(result.model_dump())
            if "PER" in result.elements:
                for elem_id in result.elements["PER"].values():
                    icecream.ic(database.characters.find_by_id(elem_id).model_dump())
            if "LOC" in result.elements:
                for elem_id in result.elements["LOC"].values():
                    icecream.ic(database.locations.find_by_id(elem_id).model_dump())
            if "ORG" in result.elements:
                for elem_id in result.elements["ORG"].values():
                    icecream.ic(database.organizations.find_by_id(elem_id).model_dump())
