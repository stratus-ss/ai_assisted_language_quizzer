"""
Lemma Grouper Module

Groups surface word forms (conjugations, plurals, etc.) under their
dictionary lemma using spaCy's Spanish morphological analyzer.
"""

from dataclasses import dataclass
from typing import Dict
import spacy


@dataclass
class LemmaGroup:
    """Represents a group of surface forms sharing the same lemma."""
    lemma: str
    total_freq: int
    forms: Dict[str, int]  # surface_form -> frequency
    representative: str     # highest-frequency surface form


class LemmaGrouper:
    """Group surface word forms under their lemma using spaCy."""

    def __init__(self, language_model: str = "es_core_news_sm"):
        """
        Initialize the lemma grouper with a spaCy language model.

        Args:
            language_model: spaCy model name for the target language.

        Raises:
            OSError: If the spaCy model is not installed.
        """
        try:
            self._nlp = spacy.load(language_model)
        except OSError as e:
            raise OSError(
                f"spaCy model '{language_model}' is not installed. "
                f"To fix, run: python -m spacy download {language_model}"
            ) from e

    def group_by_lemma(self, frequencies: Dict[str, int]) -> Dict[str, LemmaGroup]:
        """
        Group surface forms under their lemmas.

        Args:
            frequencies: Dict mapping surface form -> frequency count.

        Returns:
            Dict mapping lemma string -> LemmaGroup.
        """
        lemma_map: Dict[str, LemmaGroup] = {}

        for surface_form, freq in frequencies.items():
            lemma = self._get_lemma(surface_form)

            if lemma not in lemma_map:
                lemma_map[lemma] = LemmaGroup(
                    lemma=lemma,
                    total_freq=0,
                    forms={},
                    representative=surface_form
                )

            lemma_map[lemma].forms[surface_form] = freq
            lemma_map[lemma].total_freq += freq

            # Update representative if this form has higher frequency
            current_rep_freq = lemma_map[lemma].forms.get(
                lemma_map[lemma].representative, 0
            )
            if freq > current_rep_freq:
                lemma_map[lemma].representative = surface_form

        # Compute statistics for get_statistics()
        self._stats = {
            "total_surface_forms": len(frequencies),
            "unique_lemmas": len(lemma_map),
            "largest_group_size": max(
                (len(g.forms) for g in lemma_map.values()), default=0
            )
        }

        return lemma_map

    def _get_lemma(self, word: str) -> str:
        """
        Get the lemma for a single word via spaCy.

        Args:
            word: The surface word form.

        Returns:
            The lemma. Falls back to the original word if spaCy returns empty.
        """
        doc = self._nlp(word)
        if doc and doc[0].lemma_:
            return doc[0].lemma_.lower()
        return word.lower()

    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the last grouping operation.

        Returns:
            Dict with keys: total_surface_forms, unique_lemmas, largest_group_size.
        """
        return getattr(self, "_stats", {
            "total_surface_forms": 0,
            "unique_lemmas": 0,
            "largest_group_size": 0
        })