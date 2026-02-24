"""
Stop Word Manager Module

Handles loading, managing, and filtering stopwords (common words to ignore).
"""

from pathlib import Path
from typing import Set, List


class StopWordManager:
    """Manage stopwords for frequency analysis filtering."""
    
    def __init__(self, stopwords_file: Path):
        """
        Initialize stopword manager.
        
        Args:
            stopwords_file: Path to stopwords text file
        """
        self.stopwords_file = Path(stopwords_file)
        self.stopwords: Set[str] = set()
        
        if self.stopwords_file.exists():
            self.load_stopwords()
    
    def load_stopwords(self) -> Set[str]:
        """
        Load stopwords from file.
        
        Returns:
            Set of stopwords
        """
        stopwords = set()
        
        try:
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Remove comments and whitespace
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Add word (lowercase for case-insensitive matching)
                    stopwords.add(line.lower())
            
            self.stopwords = stopwords
            
        except Exception as e:
            raise Exception(
                f"Error loading stopwords from {self.stopwords_file}: {e}"
            )
        
        return self.stopwords
    
    def save_stopwords(self) -> None:
        """Save current stopwords to file."""
        try:
            # Read existing comments/header
            header_lines = []
            if self.stopwords_file.exists():
                with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped.startswith('#') or not stripped:
                            header_lines.append(line)
                        else:
                            break  # Stop at first non-comment, non-empty line
            
            # Write header + sorted stopwords
            with open(self.stopwords_file, 'w', encoding='utf-8') as f:
                # Write header
                for line in header_lines:
                    f.write(line)
                
                # Ensure blank line after header
                if header_lines and not header_lines[-1].strip() == '':
                    f.write('\n')
                
                # Write sorted stopwords
                for word in sorted(self.stopwords):
                    f.write(f"{word}\n")
        
        except Exception as e:
            raise Exception(
                f"Error saving stopwords to {self.stopwords_file}: {e}"
            )
    
    def add_stopwords(self, words: List[str]) -> int:
        """
        Add words to stopword list.
        
        Args:
            words: List of words to add
            
        Returns:
            Number of new words added
        """
        original_count = len(self.stopwords)
        
        for word in words:
            word = word.strip().lower()
            if word:
                self.stopwords.add(word)
        
        new_count = len(self.stopwords)
        return new_count - original_count
    
    def remove_stopwords(self, words: List[str]) -> int:
        """
        Remove words from stopword list.
        
        Args:
            words: List of words to remove
            
        Returns:
            Number of words removed
        """
        original_count = len(self.stopwords)
        
        for word in words:
            word = word.strip().lower()
            self.stopwords.discard(word)
        
        removed = original_count - len(self.stopwords)
        return removed
    
    def is_stopword(self, word: str) -> bool:
        """
        Check if a word is a stopword.
        
        Args:
            word: Word to check
            
        Returns:
            True if word is a stopword
        """
        return word.lower() in self.stopwords
    
    def filter_words(self, words: List[str]) -> List[str]:
        """
        Filter out stopwords from a list of words.
        
        Args:
            words: List of words to filter
            
        Returns:
            List of words with stopwords removed
        """
        return [word for word in words if not self.is_stopword(word)]
    
    def get_stopwords(self) -> Set[str]:
        """
        Get current set of stopwords.
        
        Returns:
            Set of stopwords
        """
        return self.stopwords.copy()
    
    def get_count(self) -> int:
        """
        Get number of stopwords.
        
        Returns:
            Count of stopwords
        """
        return len(self.stopwords)
    
    def clear(self) -> None:
        """Clear all stopwords."""
        self.stopwords.clear()
    
    def reset_to_default(self) -> None:
        """Reset stopwords to those in the file."""
        self.clear()
        if self.stopwords_file.exists():
            self.load_stopwords()
