"""
Frequency Analyzer Module

Analyzes word frequencies and provides smart threshold calculations.
"""

from collections import Counter
from typing import List, Dict, Tuple
import math


class FrequencyAnalyzer:
    """Analyze word frequencies with smart threshold calculations."""
    
    def __init__(self):
        """Initialize frequency analyzer."""
        self.word_frequencies: Counter = Counter()
        self.total_words = 0
        self.unique_words = 0
    
    def analyze(self, words: List[str]) -> Dict[str, int]:
        """
        Analyze word frequencies from a list of words.
        
        Args:
            words: List of words to analyze
            
        Returns:
            Dictionary mapping words to their frequencies
        """
        self.word_frequencies = Counter(words)
        self.total_words = len(words)
        self.unique_words = len(self.word_frequencies)
        
        return dict(self.word_frequencies)
    
    def get_top_n(self, n: int) -> List[Tuple[str, int]]:
        """
        Get top N most frequent words.
        
        Args:
            n: Number of top words to return
            
        Returns:
            List of (word, frequency) tuples
        """
        return self.word_frequencies.most_common(n)
    
    def filter_by_frequency(
        self, 
        min_frequency: int = 1, 
        max_frequency: int = None
    ) -> Dict[str, int]:
        """
        Filter words by frequency range.
        
        Args:
            min_frequency: Minimum frequency (inclusive)
            max_frequency: Maximum frequency (inclusive), None for no limit
            
        Returns:
            Filtered dictionary of word frequencies
        """
        filtered = {}
        
        for word, freq in self.word_frequencies.items():
            if freq >= min_frequency:
                if max_frequency is None or freq <= max_frequency:
                    filtered[word] = freq
        
        return filtered
    
    def calculate_smart_threshold(
        self, 
        target_words: int = 500,
        min_threshold: int = 2
    ) -> int:
        """
        Calculate smart frequency threshold based on dataset size.
        
        This uses a logarithmic scale to adjust the threshold:
        - Small datasets (few words/files): Lower threshold
        - Large datasets: Higher threshold
        
        Args:
            target_words: Target number of words in final list
            min_threshold: Minimum threshold to use
            
        Returns:
            Recommended frequency threshold
        """
        if self.unique_words == 0:
            return min_threshold
        
        # If we already have fewer unique words than target, use min threshold
        if self.unique_words <= target_words:
            return min_threshold
        
        # Calculate threshold that would give approximately target_words
        # Try different thresholds to find the sweet spot
        for threshold in range(min_threshold, 100):
            filtered_count = sum(
                1 for freq in self.word_frequencies.values() 
                if freq >= threshold
            )
            
            if filtered_count <= target_words:
                return threshold
        
        # If we still have too many words even at threshold 100,
        # use a higher threshold based on percentile
        return self._calculate_percentile_threshold(target_words)
    
    def _calculate_percentile_threshold(self, target_words: int) -> int:
        """
        Calculate threshold based on frequency percentile.
        
        Args:
            target_words: Target number of words
            
        Returns:
            Frequency threshold
        """
        if self.unique_words == 0:
            return 1
        
        # Sort frequencies in descending order
        sorted_freqs = sorted(
            self.word_frequencies.values(), 
            reverse=True
        )
        
        # Get the frequency at the target_words position
        if target_words < len(sorted_freqs):
            return sorted_freqs[target_words]
        else:
            return 1
    
    def get_frequency_distribution(self) -> Dict[int, int]:
        """
        Get distribution of frequencies.
        
        Returns:
            Dictionary mapping frequency to count of words with that frequency
        """
        distribution = Counter(self.word_frequencies.values())
        return dict(distribution)
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive statistics about the word frequencies.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.word_frequencies:
            return {
                "total_words": 0,
                "unique_words": 0,
                "avg_frequency": 0,
                "max_frequency": 0,
                "min_frequency": 0
            }
        
        frequencies = list(self.word_frequencies.values())
        
        return {
            "total_words": self.total_words,
            "unique_words": self.unique_words,
            "avg_frequency": sum(frequencies) / len(frequencies),
            "max_frequency": max(frequencies),
            "min_frequency": min(frequencies),
            "median_frequency": self._get_median(frequencies),
            "most_common_word": self.word_frequencies.most_common(1)[0]
        }
    
    def _get_median(self, values: List[int]) -> float:
        """Calculate median of a list of values."""
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n == 0:
            return 0
        
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def get_word_percentage(self, word: str) -> float:
        """
        Get percentage of total words for a specific word.
        
        Args:
            word: Word to check
            
        Returns:
            Percentage (0-100)
        """
        if self.total_words == 0:
            return 0.0
        
        frequency = self.word_frequencies.get(word, 0)
        return (frequency / self.total_words) * 100
    
    def get_sorted_frequencies(
        self, 
        descending: bool = True
    ) -> List[Tuple[str, int]]:
        """
        Get all word frequencies sorted by frequency.
        
        Args:
            descending: If True, sort from highest to lowest frequency
            
        Returns:
            List of (word, frequency) tuples
        """
        return sorted(
            self.word_frequencies.items(),
            key=lambda x: x[1],
            reverse=descending
        )
