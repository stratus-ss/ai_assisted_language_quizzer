"""
Report Generator Module

Generates various output formats for word frequency analysis results.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import csv

from .lemma_grouper import LemmaGroup


class ReportGenerator:
    """Generate reports in multiple formats from frequency analysis."""
    
    def __init__(self, output_directory: Path):
        """
        Initialize report generator.
        
        Args:
            output_directory: Directory to save reports
        """
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_csv_report(
        self,
        frequencies: Dict[str, int],
        total_words: int,
        output_file: str = "word_frequency_report.csv",
        top_n: Optional[int] = None
    ) -> Path:
        """
        Generate CSV report with word frequencies.
        
        Args:
            frequencies: Dictionary of word frequencies
            total_words: Total number of words analyzed
            output_file: Output filename
            top_n: If specified, only include top N words
            
        Returns:
            Path to generated CSV file
        """
        filepath = self.output_dir / output_file
        
        # Sort by frequency (descending)
        sorted_words = sorted(
            frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if top_n:
            sorted_words = sorted_words[:top_n]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'frequency', 'percentage'])
            
            for word, freq in sorted_words:
                percentage = (freq / total_words * 100) if total_words > 0 else 0
                writer.writerow([word, freq, f"{percentage:.2f}%"])
        
        return filepath
    
    def generate_anki_wordlist(
        self,
        frequencies: Dict[str, int],
        output_file: str = "anki_import_words.txt",
        top_n: Optional[int] = None,
        include_frequency: bool = False
    ) -> Path:
        """
        Generate simple word list for Anki import.
        
        Args:
            frequencies: Dictionary of word frequencies
            output_file: Output filename
            top_n: If specified, only include top N words
            include_frequency: If True, add frequency as comment
            
        Returns:
            Path to generated word list file
        """
        filepath = self.output_dir / output_file
        
        # Sort by frequency (descending)
        sorted_words = sorted(
            frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if top_n:
            sorted_words = sorted_words[:top_n]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for word, freq in sorted_words:
                if include_frequency:
                    f.write(f"{word}\t# frequency: {freq}\n")
                else:
                    f.write(f"{word}\n")
        
        return filepath
    
    def generate_markdown_summary(
        self,
        frequencies: Dict[str, int],
        statistics: Dict[str, any],
        sources: List[str],
        output_file: str = "word_frequency_summary.md",
        top_n: int = None
    ) -> Path:
        """
        Generate human-readable markdown summary report.
        
        Args:
            frequencies: Dictionary of word frequencies
            statistics: Analysis statistics
            sources: List of source files analyzed
            output_file: Output filename
            top_n: Number of top words to include (None = all words)
            
        Returns:
            Path to generated markdown file
        """
        filepath = self.output_dir / output_file
        
        # Sort by frequency (descending)
        sorted_words = sorted(
            frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # If top_n is None, show all words; otherwise limit to top_n
        if top_n is None:
            top_words = sorted_words
        else:
            top_words = sorted_words[:top_n]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Word Frequency Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Statistics section
            f.write("## 📊 Statistics\n\n")
            f.write(f"- **Total words analyzed:** {statistics.get('total_words', 0):,}\n")
            f.write(f"- **Unique words:** {statistics.get('unique_words', 0):,}\n")
            f.write(f"- **Average frequency:** {statistics.get('avg_frequency', 0):.2f}\n")
            f.write(f"- **Most common word:** {statistics.get('most_common_word', ('N/A', 0))[0]} "
                   f"({statistics.get('most_common_word', ('N/A', 0))[1]} occurrences)\n")
            f.write(f"- **Max frequency:** {statistics.get('max_frequency', 0)}\n")
            f.write(f"- **Median frequency:** {statistics.get('median_frequency', 0):.1f}\n\n")
            
            # Top words section
            if top_n is None:
                f.write(f"## 📝 All Words Meeting Frequency Threshold ({len(top_words)} words)\n\n")
            else:
                f.write(f"## 🔝 Top {min(top_n, len(top_words))} Most Frequent Words\n\n")
            f.write("| Rank | Word | Frequency | Percentage |\n")
            f.write("|------|------|-----------|------------|\n")
            
            total_words = statistics.get('total_words', 1)
            for i, (word, freq) in enumerate(top_words, 1):
                percentage = (freq / total_words * 100) if total_words > 0 else 0
                f.write(f"| {i} | {word} | {freq:,} | {percentage:.2f}% |\n")
            
            # Sources section
            f.write(f"\n## 📁 Source Files ({len(sources)})\n\n")
            for source in sorted(sources):
                f.write(f"- {source}\n")
            
            # Summary stats
            f.write("\n## 📈 Frequency Distribution\n\n")
            
            # Calculate distribution buckets
            distribution = self._calculate_distribution(frequencies)
            for bucket, count in distribution.items():
                f.write(f"- Words appearing {bucket}: {count}\n")
        
        return filepath

    def generate_lemma_markdown_summary(
        self,
        lemma_groups: Dict[str, LemmaGroup],
        statistics: Dict[str, Any],
        sources: List[str],
        output_file: str = "word_frequency_summary.md",
        top_n: Optional[int] = None
    ) -> Path:
        """
        Generate markdown summary with lemma grouping details.

        Args:
            lemma_groups: Dict mapping lemma string -> LemmaGroup.
            statistics: Analysis statistics.
            sources: List of source files analyzed.
            output_file: Output filename.
            top_n: Number of top lemmas to include (None = all).

        Returns:
            Path to generated markdown file.
        """
        filepath = self.output_dir / output_file

        # Sort lemmas by total frequency (descending)
        sorted_groups = sorted(
            lemma_groups.values(),
            key=lambda g: g.total_freq,
            reverse=True
        )

        if top_n:
            sorted_groups = sorted_groups[:top_n]

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Word Frequency Analysis Report (Lemma-Grouped)\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## 📊 Statistics\n\n")
            f.write(f"- **Total surface forms analyzed:** {statistics.get('total_words', 0):,}\n")
            f.write(f"- **Unique lemmas:** {len(lemma_groups):,}\n")
            f.write(f"- **Average frequency per lemma:** "
                   f"{statistics.get('avg_frequency', 0):.2f}\n\n")

            f.write(f"## 📝 Lemma Groups ({len(sorted_groups)} groups)\n\n")
            f.write("| Rank | Lemma | Representative | Total Freq | Forms |\n")
            f.write("|------|-------|---------------|------------|-------|\n")

            for i, group in enumerate(sorted_groups, 1):
                forms_str = ", ".join(
                    f"{form}({freq})" for form, freq in sorted(group.forms.items(), key=lambda x: x[1], reverse=True)
                )
                f.write(f"| {i} | {group.lemma} | {group.representative} | "
                        f"{group.total_freq:,} | {forms_str} |\n")

            f.write(f"\n## 📁 Source Files ({len(sources)})\n\n")
            for source in sorted(sources):
                f.write(f"- {source}\n")

        return filepath

    def _calculate_distribution(
        self, 
        frequencies: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Calculate frequency distribution in buckets.
        
        Args:
            frequencies: Word frequency dictionary
            
        Returns:
            Dictionary mapping bucket labels to counts
        """
        distribution = {
            "1 time": 0,
            "2-5 times": 0,
            "6-10 times": 0,
            "11-20 times": 0,
            "21-50 times": 0,
            "51-100 times": 0,
            "100+ times": 0
        }
        
        for freq in frequencies.values():
            if freq == 1:
                distribution["1 time"] += 1
            elif freq <= 5:
                distribution["2-5 times"] += 1
            elif freq <= 10:
                distribution["6-10 times"] += 1
            elif freq <= 20:
                distribution["11-20 times"] += 1
            elif freq <= 50:
                distribution["21-50 times"] += 1
            elif freq <= 100:
                distribution["51-100 times"] += 1
            else:
                distribution["100+ times"] += 1
        
        return distribution
    
    def generate_all_reports(
        self,
        frequencies: Dict[str, int],
        statistics: Dict[str, any],
        sources: List[str],
        top_n: int = 500
    ) -> Dict[str, Path]:
        """
        Generate all report formats at once.
        
        Args:
            frequencies: Dictionary of word frequencies
            statistics: Analysis statistics
            sources: List of source files
            top_n: Number of words for final lists
            
        Returns:
            Dictionary mapping report type to file path
        """
        reports = {}
        
        # CSV report
        reports['csv'] = self.generate_csv_report(
            frequencies,
            statistics.get('total_words', 0),
            top_n=top_n
        )
        
        # Anki word list
        reports['anki'] = self.generate_anki_wordlist(
            frequencies,
            top_n=top_n
        )
        
        # Markdown summary - show all words by default
        reports['markdown'] = self.generate_markdown_summary(
            frequencies,
            statistics,
            sources,
            top_n=None  # Show all words that meet threshold
        )
        
        return reports
