"""
Pronoun Context Helper

Adds subject pronoun context to conjugated verbs before DeepL translation.
Uses spaCy morphological analysis to detect person/number, so it works
across Spanish, German, and Italian (and any language with a spaCy model).
"""

from typing import Dict, Optional, Tuple


_SPACY_MODELS: Dict[str, str] = {
    "es": "es_core_news_md",
    "de": "de_core_news_md",
    "it": "it_core_news_md",
}

_PRONOUN_MAP: Dict[str, Dict[Tuple[str, str], str]] = {
    "es": {
        ("1", "Sing"): "yo",
        ("2", "Sing"): "tú",
        ("3", "Sing"): "él",
        ("1", "Plur"): "nosotros",
        ("2", "Plur"): "vosotros",
        ("3", "Plur"): "ellos",
    },
    "de": {
        ("1", "Sing"): "ich",
        ("2", "Sing"): "du",
        ("3", "Sing"): "er",
        ("1", "Plur"): "wir",
        ("2", "Plur"): "ihr",
        ("3", "Plur"): "sie",
    },
    "it": {
        ("1", "Sing"): "io",
        ("2", "Sing"): "tu",
        ("3", "Sing"): "lui",
        ("1", "Plur"): "noi",
        ("2", "Plur"): "voi",
        ("3", "Plur"): "loro",
    },
}


class PronounContextHelper:
    """Prepend subject pronoun to conjugated verbs using spaCy morphology."""

    def __init__(self, language: str = "es") -> None:
        self._language = language.lower()[:2]
        model_name = _SPACY_MODELS.get(self._language)
        self._nlp = None
        if not model_name:
            return
        try:
            import spacy
            self._nlp = spacy.load(model_name)
        except (ImportError, OSError):
            pass

    def contextualize(self, word: str, sentence: Optional[str] = None) -> str:
        """Return word with pronoun prefix if it is a conjugated verb."""
        if self._nlp is None:
            return word
        target = self._find_token(word, sentence)
        if target is None or target.pos_ not in ("VERB", "AUX"):
            return word
        person = target.morph.get("Person")
        number = target.morph.get("Number")
        if not person or not number:
            return word
        pronoun_map = _PRONOUN_MAP.get(self._language, {})
        pronoun = pronoun_map.get((person[0], number[0]))
        if pronoun:
            return f"{pronoun} {word}"
        return word

    def _find_token(self, word: str, sentence: Optional[str] = None):
        """Find the spaCy token for word, using sentence context if available."""
        if sentence:
            doc = self._nlp(sentence)
            for token in doc:
                if token.text.lower() == word.lower():
                    return token
        doc = self._nlp(word)
        return doc[0] if doc else None
