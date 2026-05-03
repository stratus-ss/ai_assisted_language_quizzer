"""
Subtitle Word Frequency Analyzer

A tool for analyzing word frequencies in subtitle files (.srt format)
and generating reports for language learning with Anki integration.
"""

__version__ = "1.0.0"
__author__ = "AI Language Quizzer Project"

from .srt_parser import SRTParser
from .word_processor import WordProcessor
from .stopword_manager import StopWordManager
from .frequency_analyzer import FrequencyAnalyzer
from .report_generator import ReportGenerator
from .lemma_grouper import LemmaGrouper, LemmaGroup
from .llm_curator import LLMCurator, CuratedWord
from . import translator
from .pronoun_context import PronounContextHelper

__all__ = [
    "SRTParser",
    "WordProcessor",
    "StopWordManager",
    "FrequencyAnalyzer",
    "ReportGenerator",
    "LemmaGrouper",
    "LemmaGroup",
    "LLMCurator",
    "CuratedWord",
    "translator",
    "PronounContextHelper",
]
