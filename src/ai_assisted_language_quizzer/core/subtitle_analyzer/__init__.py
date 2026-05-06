"""
Subtitle Word Frequency Analyzer

A tool for analyzing word frequencies in subtitle files (.srt format)
and generating reports for language learning with Anki integration.
"""

__version__ = "1.0.0"
__author__ = "AI Language Quizzer Project"

from . import translator
from .english_word_filter import EnglishWordFilter
from .frequency_analyzer import FrequencyAnalyzer
from .lemma_grouper import LemmaGroup, LemmaGrouper
from .llm_curator import CuratedWord, LLMCurator
from .pronoun_context import PronounContextHelper
from .report_generator import ReportGenerator
from .srt_parser import SRTParser
from .stopword_manager import StopWordManager
from .word_processor import WordProcessor

__all__ = [
    "SRTParser",
    "WordProcessor",
    "StopWordManager",
    "EnglishWordFilter",
    "FrequencyAnalyzer",
    "ReportGenerator",
    "LemmaGrouper",
    "LemmaGroup",
    "LLMCurator",
    "CuratedWord",
    "translator",
    "PronounContextHelper",
]
