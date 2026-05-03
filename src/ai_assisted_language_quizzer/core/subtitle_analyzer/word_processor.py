"""
Word Processor Module

Handles text cleaning, normalization, and tokenization.
"""

import re
import unicodedata
from typing import List, Set


class WordProcessor:
    """Clean, normalize, and tokenize text for word frequency analysis."""
    
    def __init__(
        self,
        min_word_length: int = 2,
        keep_accents: bool = True,
        lowercase: bool = True
    ):
        """
        Initialize word processor.
        
        Args:
            min_word_length: Minimum length for a word to be considered
            keep_accents: Whether to keep accented characters (á, é, etc.)
            lowercase: Whether to convert all text to lowercase
        """
        self.min_word_length = min_word_length
        self.keep_accents = keep_accents
        self.lowercase = lowercase
    
    def normalize_word(self, word: str) -> str:
        """
        Normalize a single word.
        
        Args:
            word: Word to normalize
            
        Returns:
            Normalized word
        """
        # Remove leading/trailing whitespace
        word = word.strip()
        
        # Convert to lowercase if configured
        if self.lowercase:
            word = word.lower()
        
        # Remove common punctuation except internal apostrophes/hyphens
        # This preserves words like "l'amour" or "bien-être"
        word = re.sub(r'^[^\w]+|[^\w]+$', '', word, flags=re.UNICODE)
        
        # Remove accents if configured
        if not self.keep_accents:
            word = self._remove_accents(word)
        
        return word
    
    def _remove_accents(self, text: str) -> str:
        """
        Remove accent marks from text.
        
        Args:
            text: Text with potential accents
            
        Returns:
            Text without accents
        """
        # Decompose unicode characters
        nfd = unicodedata.normalize('NFD', text)
        # Filter out combining marks (accents)
        without_accents = ''.join(
            char for char in nfd 
            if unicodedata.category(char) != 'Mn'
        )
        return unicodedata.normalize('NFC', without_accents)
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Split text into individual words.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of words
        """
        # Split on whitespace and basic punctuation
        # This regex keeps letters, numbers, and common word characters
        words = re.findall(r'\b[\w\-\']+\b', text, flags=re.UNICODE)
        return words
    
    def process_text(self, text: str) -> List[str]:
        """
        Tokenize and normalize text in one step.
        
        Args:
            text: Text to process
            
        Returns:
            List of normalized words meeting minimum length requirement
        """
        # Tokenize
        words = self.tokenize_text(text)
        
        # Normalize and filter
        processed_words = []
        for word in words:
            normalized = self.normalize_word(word)
            
            # Apply filters
            if len(normalized) >= self.min_word_length:
                # Additional check: must contain at least one letter
                if re.search(r'[a-záéíóúñüA-ZÁÉÍÓÚÑÜ]', normalized):
                    processed_words.append(normalized)
        
        return processed_words
    
    def process_lines(self, lines: List[str]) -> List[str]:
        """
        Process multiple lines of text.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of all normalized words from all lines
        """
        all_words = []
        for line in lines:
            words = self.process_text(line)
            all_words.extend(words)
        return all_words
    
    def get_unique_words(self, words: List[str]) -> Set[str]:
        """
        Get set of unique words.
        
        Args:
            words: List of words
            
        Returns:
            Set of unique words
        """
        return set(words)
    
    def filter_by_pattern(
        self, 
        words: List[str], 
        pattern: str, 
        exclude: bool = True
    ) -> List[str]:
        """
        Filter words by regex pattern.
        
        Args:
            words: List of words to filter
            pattern: Regex pattern to match
            exclude: If True, exclude matches; if False, include only matches
            
        Returns:
            Filtered list of words
        """
        regex = re.compile(pattern)
        
        if exclude:
            return [w for w in words if not regex.search(w)]
        else:
            return [w for w in words if regex.search(w)]
