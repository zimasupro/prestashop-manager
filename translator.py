from nicegui import app

from settings import DEFAULT_LANGUAGE, TRANSLATIONS


def get_lang() -> str:
    return app.storage.user.get("lang", DEFAULT_LANGUAGE)


def translate(key: str) -> str:
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


def set_lang(lang: str):
    app.storage.user["lang"] = lang
