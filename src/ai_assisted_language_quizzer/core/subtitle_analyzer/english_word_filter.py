"""
English Word Filter Module

Filters common English words from Spanish vocabulary lists.
Used after stopword filtering to remove English loanwords and
bilingual dialog that leaks into subtitle files.
"""

from pathlib import Path
from typing import List, Set


class EnglishWordFilter:
    """Filter English words from vocabulary lists."""

    def __init__(self, english_words_file: Path) -> None:
        """
        Initialize English word filter.

        Args:
            english_words_file: Path to english_words.txt file
        """
        self.english_words_file: Path = Path(english_words_file)
        self.english_words: Set[str] = set()

        if self.english_words_file.exists():
            self.load_words()
        else:
            print(f"⚠️  English words file not found: {self.english_words_file}")

    def load_words(self) -> Set[str]:
        """
        Load English words from file.

        Returns:
            Set of English words
        """
        words: Set[str] = set()

        try:
            with open(self.english_words_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    words.add(line.lower())

            self.english_words = words

        except Exception as e:
            print(f"❌ Error loading English words from {self.english_words_file}: {e}")

        return self.english_words

    def filter_words(self, words: List[str]) -> List[str]:
        """
        Remove English words from a word list.

        Args:
            words: List of words to filter

        Returns:
            List with English words removed
        """
        return [word for word in words if not self.is_english_word(word)]

    def is_english_word(self, word: str) -> bool:
        """
        Check if a word is in the English words set.

        Args:
            word: Word to check

        Returns:
            True if word is a known English word
        """
        return word.lower() in self.english_words

    def get_count(self) -> int:
        """
        Get number of loaded English words.

        Returns:
            Count of English words
        """
        return len(self.english_words)
