#!/usr/bin/env python3
"""
Subtitle Word Frequency Analyzer

Analyzes word frequencies in subtitle files and generates reports
for language learning with Anki integration support.

Usage:
    python subtitle_word_frequency.py [options]
    python subtitle_word_frequency.py --config config.yaml
    python subtitle_word_frequency.py --add-stopwords "palabra1,palabra2"
    python subtitle_word_frequency.py --subtitles-dir ../subtitles --min-freq 5
"""

import argparse
import sys
import os
import traceback
from pathlib import Path
import yaml
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv


# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from subtitle_analyzer import (
    SRTParser,
    WordProcessor,
    StopWordManager,
    FrequencyAnalyzer,
    ReportGenerator,
    LemmaGrouper,
    LemmaGroup,
)
from subtitle_analyzer.llm_curator import LLMCurator, CuratedWord
from subtitle_analyzer.translator import (
    get_deepl_translator,
    translate_word_list,
    get_api_usage
)

# Load environment variables for DeepL API
load_dotenv()


class SubtitleFrequencyAnalyzer:
    """Main application class for subtitle frequency analysis."""
    
    def __init__(self, config_path: Path = None):
        """
        Initialize analyzer with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.parser = SRTParser()
        self.word_processor = None
        self.stopword_manager = None
        self.frequency_analyzer = FrequencyAnalyzer()
        self.report_generator = None
        
        self._initialize_components()
    
    def _load_config(self, config_path: Path = None) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            # Default config location (now in core/subtitle_analyzer/)
            config_path = Path(__file__).parent.parent / "core" / "subtitle_analyzer" / "config.yaml"
        
        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("Using default configuration.")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            print("Using default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'paths': {
                'subtitles_directory': '../subtitles',
                'output_directory': './data/output',
                'stopwords_file': './core/subtitle_analyzer/stopwords_spanish.txt'
            },
            'processing': {
                'min_word_length': 2,
                'keep_accents': True,
                'lowercase': True
            },
            'frequency': {
                'threshold_mode': 'auto',
                'min_frequency': 3,
                'target_words': 500,
                'max_results': 1000
            },
            'lemmatization': {
                'enabled': False,
                'language_model': 'es_core_news_sm',
                'representative_strategy': 'highest_frequency'
            },
            'llm_curation': {
                'enabled': False,
                'provider': 'minimax',
                'model': 'minimax-m2.5',
                'api_url': 'https://api.minimaxi.chat/v1/text/chatcompletion_v2',
                'api_key_env': 'MINIMAX_API_KEY',
                'batch_size': 40,
                'learner_level': 'A2-B1'
            },
            'output': {
                'generate_csv': True,
                'generate_markdown': True,
                'generate_anki_list': True,
                'markdown_top_n': 50,
                'anki_include_frequency': True
            },
            'advanced': {
                'file_pattern': '*.srt',
                'verbose': True
            }
        }
    
    def _initialize_components(self):
        """Initialize processing components from config."""
        # Resolve paths relative to language root (parent of scripts/)
        language_root = Path(__file__).parent.parent
        
        # Word processor
        proc_config = self.config.get('processing', {})
        self.word_processor = WordProcessor(
            min_word_length=proc_config.get('min_word_length', 2),
            keep_accents=proc_config.get('keep_accents', True),
            lowercase=proc_config.get('lowercase', True)
        )
        
        # Stopword manager
        stopwords_file = Path(self.config['paths']['stopwords_file'])
        if not stopwords_file.is_absolute():
            stopwords_file = language_root / stopwords_file
        self.stopword_manager = StopWordManager(stopwords_file)
        
        # Report generator
        output_dir = Path(self.config['paths']['output_directory'])
        if not output_dir.is_absolute():
            output_dir = language_root / output_dir
        self.report_generator = ReportGenerator(output_dir)

        # Lemma grouper (optional -- requires spaCy model)
        self.lemma_grouper = None
        lemma_config = self.config.get('lemmatization', {})
        if lemma_config.get('enabled', False):
            try:
                self.lemma_grouper = LemmaGrouper(
                    language_model=lemma_config.get('language_model', 'es_core_news_sm')
                )
            except OSError as e:
                print(f"LemmaGrouper disabled: {e}")
                self.lemma_grouper = None

        self._curated_words: List[CuratedWord] = []
        self._sentence_context: Dict[str, str] = {}

    def _parse_subtitles(self, subtitles_dir: Path) -> Dict[str, List[str]]:
        """Step 1: Parse subtitle files."""
        file_pattern = self.config.get('advanced', {}).get('file_pattern', '*.srt')
        return self.parser.parse_directory(subtitles_dir, file_pattern)

    def _process_and_filter(self, parsed_data: Dict[str, List[str]]) -> List[str]:
        """Steps 2+3: Process words, build sentence context, filter stopwords."""
        all_words = []
        for filename, lines in parsed_data.items():
            for line in lines:
                words = self.word_processor.process_text(line)
                for word in words:
                    if word not in self._sentence_context:
                        self._sentence_context[word] = line
                all_words.extend(words)
        return self.stopword_manager.filter_words(all_words)

    def _apply_lemmatization(self) -> Tuple[Dict[str, LemmaGroup], Dict[str, int]]:
        """Step 4a: Group words by lemma if enabled. Returns (groups, filtered_frequencies)."""
        lemma_groups: Dict[str, LemmaGroup] = {}
        filtered_frequencies: Dict[str, int] = {}
        if self.lemma_grouper:
            all_frequencies = self.frequency_analyzer.filter_by_frequency(min_frequency=1)
            lemma_groups = self.lemma_grouper.group_by_lemma(all_frequencies)
            lemma_stats = self.lemma_grouper.get_statistics()
            print(f"  Grouped {lemma_stats['total_surface_forms']} forms into {lemma_stats['unique_lemmas']} lemmas")
            filtered_frequencies = {
                lg.representative: lg.total_freq for lg in lemma_groups.values()
            }
        return lemma_groups, filtered_frequencies

    def _apply_threshold(
        self,
        lemma_groups: Dict[str, LemmaGroup],
        filtered_frequencies: Dict[str, int]
    ) -> Tuple[Dict[str, int], Optional[int]]:
        """Step 5: Apply frequency threshold. Returns (filtered_frequencies, threshold)."""
        freq_config = self.config.get('frequency', {})
        threshold: Optional[int] = None

        if lemma_groups:
            min_freq_val = freq_config.get('min_frequency', 3)
            if freq_config.get('threshold_mode') == 'manual':
                threshold = min_freq_val
            else:
                target_words = freq_config.get('target_words', 500)
                sorted_items = sorted(filtered_frequencies.items(), key=lambda x: x[1], reverse=True)
                threshold = sorted_items[target_words - 1][1] if target_words < len(sorted_items) else 1
            filtered_frequencies = {k: v for k, v in filtered_frequencies.items() if v >= threshold}
        else:
            if freq_config.get('threshold_mode') == 'auto':
                target_words = freq_config.get('target_words', 500)
                threshold = self.frequency_analyzer.calculate_smart_threshold(target_words=target_words)
            else:
                threshold = freq_config.get('min_frequency', 3)
            filtered_frequencies = self.frequency_analyzer.filter_by_frequency(min_frequency=threshold)
            max_results = freq_config.get('max_results', 1000)
            if len(filtered_frequencies) > max_results:
                sorted_freqs = sorted(filtered_frequencies.items(), key=lambda x: x[1], reverse=True)
                filtered_frequencies = dict(sorted_freqs[:max_results])

        return filtered_frequencies, threshold

    def _apply_curation(
        self,
        filtered_frequencies: Dict[str, int],
        lemma_groups: Dict[str, LemmaGroup]
    ) -> Dict[str, int]:
        """Step 5a: LLM curation (optional)."""
        llm_config = self.config.get('llm_curation', {})
        if not llm_config.get('enabled', False):
            return filtered_frequencies

        # Build lemma groups from raw frequencies if none exist
        effective_groups = lemma_groups
        if not lemma_groups:
            effective_groups = {
                word: LemmaGroup(lemma=word, total_freq=freq, forms={word: freq}, representative=word)
                for word, freq in filtered_frequencies.items()
            }

        api_key = os.getenv(llm_config.get('api_key_env', 'MINIMAX_API_KEY'))
        if not api_key:
            print("  Step 5a skipped: MINIMAX_API_KEY not found in .env")
            return filtered_frequencies

        print("  Step 5a: Curating word list via LLM...")
        curator = LLMCurator(
            api_key=api_key,
            model=llm_config.get('model', 'minimax-m2.5'),
            api_url=llm_config.get('api_url', ''),
            batch_size=llm_config.get('batch_size', 40),
            learner_level=llm_config.get('learner_level', 'A2-B1')
        )
        curated = curator.curate(effective_groups)
        self._curated_words = [w for w in curated if w.keep]
        filtered_frequencies = {w.best_form: w.original_freq for w in curated if w.keep}
        print(f"  LLM kept {len(filtered_frequencies)} of {len(curated)} entries")
        return filtered_frequencies

    def _generate_reports(
        self,
        filtered_frequencies: Dict[str, int],
        stats: Dict[str, int],
        source_files: List[str],
        lemma_groups: Dict[str, LemmaGroup]
    ) -> Dict[str, Path]:
        """Step 6: Generate all reports."""
        reports = self.report_generator.generate_all_reports(
            filtered_frequencies, stats, source_files, top_n=len(filtered_frequencies)
        )
        if lemma_groups:
            reports['lemma_markdown'] = self.report_generator.generate_lemma_markdown_summary(
                lemma_groups, stats, source_files, top_n=len(filtered_frequencies)
            )
        return reports

    def analyze(self, subtitles_dir: Path = None) -> Dict:
        """
        Run the complete analysis pipeline.

        Args:
            subtitles_dir: Override subtitles directory from config

        Returns:
            Dictionary with analysis results
        """
        print("=" * 70)
        print("SUBTITLE WORD FREQUENCY ANALYZER")
        print("=" * 70)

        # Resolve subtitles directory relative to language_root
        language_root = Path(__file__).parent.parent
        if subtitles_dir is None:
            subtitles_dir = Path(self.config['paths']['subtitles_directory'])
            if not subtitles_dir.is_absolute():
                subtitles_dir = language_root / subtitles_dir
        subtitles_dir = Path(subtitles_dir)

        print(f"\n📁 Subtitles directory: {subtitles_dir}")
        print(f"📝 Stopwords file: {self.stopword_manager.stopwords_file}")
        print(f"💾 Output directory: {self.report_generator.output_dir}\n")

        # Step 1
        print("Step 1: Parsing subtitle files...")
        try:
            parsed_data = self._parse_subtitles(subtitles_dir)
            print(f"✓ Parsed {len(parsed_data)} files")
        except Exception as e:
            print(f"❌ Error parsing files: {e}")
            return None

        # Steps 2+3
        print("\nStep 2: Processing words...")
        filtered_words = self._process_and_filter(parsed_data)
        print(f"✓ Extracted {len(filtered_words)} total words")
        print(f"  Stopwords loaded: {self.stopword_manager.get_count()}")

        print("\nStep 3: Filtering stopwords...")
        print(f"✓ Filtered stopwords, {len(filtered_words)} words remaining")

        # Step 4
        print("\nStep 4: Analyzing word frequencies...")
        self.frequency_analyzer.analyze(filtered_words)
        stats = self.frequency_analyzer.get_statistics()
        print(f"✓ Found {stats['unique_words']} unique words")

        # Step 4a
        lemma_groups: Dict[str, LemmaGroup] = {}
        filtered_frequencies: Dict[str, int] = {}
        lemma_groups, filtered_frequencies = self._apply_lemmatization()
        if lemma_groups:
            print(f"\nStep 4a: Grouped into {len(lemma_groups)} lemma groups")

        # Step 5
        print("\nStep 5: Applying frequency threshold...")
        filtered_frequencies, threshold = self._apply_threshold(lemma_groups, filtered_frequencies)
        print(f"✓ {len(filtered_frequencies)} words meet threshold, threshold={threshold}")

        # Step 5a
        filtered_frequencies = self._apply_curation(filtered_frequencies, lemma_groups)

        # Step 6
        print("\nStep 6: Generating reports...")
        source_files = list(parsed_data.keys())
        reports = self._generate_reports(filtered_frequencies, stats, source_files, lemma_groups)
        print(f"✓ Generated {len(reports)} reports")

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE!")
        print("=" * 70)

        return {
            'frequencies': filtered_frequencies,
            'statistics': stats,
            'reports': reports,
            'threshold': threshold
        }
    
    def add_stopwords(self, words: List[str]) -> None:
        """Add words to stopword list."""
        count = self.stopword_manager.add_stopwords(words)
        self.stopword_manager.save_stopwords()
        print(f"✓ Added {count} new stopwords")
        print(f"  Total stopwords: {self.stopword_manager.get_count()}")
    
    def remove_stopwords(self, words: List[str]) -> None:
        """Remove words from stopword list."""
        count = self.stopword_manager.remove_stopwords(words)
        self.stopword_manager.save_stopwords()
        print(f"✓ Removed {count} stopwords")
        print(f"  Total stopwords: {self.stopword_manager.get_count()}")
    
    def _read_word_list(self, word_list_file: Path) -> List[str]:
        """Read words from a word list file."""
        print(f"Reading words from: {word_list_file}")
        with open(word_list_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        print(f"Found {len(words)} words to translate")
        return words

    def _write_and_report_translations(
        self,
        output_file: Path,
        translations: List[Tuple[str, str]],
        translator
    ) -> None:
        """Write translation file and print API usage summary."""
        print(f"\nWriting translations to: {output_file}")
        skipped = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for word, translation in translations:
                translation = translation.strip() if translation else ""
                if translation and translation != "[ERROR]":
                    f.write(f"{word}\t{translation}\n")
                else:
                    skipped += 1
        if skipped:
            print(f"Skipped {skipped} words with no translation")

        usage = get_api_usage(translator)
        if usage['character_count'] > 0:
            print(f"\nDeepL API Usage:")
            print(f"  Characters used: {usage['character_count']:,}")
            if usage['character_limit'] > 0:
                print(f"  Character limit: {usage['character_limit']:,}")
                print(f"  Usage: {usage['percentage_used']:.1f}%")

        written = sum(1 for _, t in translations if (t.strip() if t else "") and t != "[ERROR]")
        errors = sum(1 for _, t in translations if t == "[ERROR]")
        print("\n" + "=" * 70)
        print("TRANSLATION COMPLETE!")
        print("=" * 70)
        print(f"Translated: {written} words")
        if errors:
            print(f"Errors: {errors}")
        if skipped:
            print(f"Skipped: {skipped} (empty)")
        print(f"Output: {output_file}")
        print("=" * 70)

    def translate_wordlist(
        self,
        word_list_file: Path,
        output_file: Path,
        source_lang: str = "ES",
        target_lang: str = "EN-US"
    ) -> Optional[Path]:
        """Translate word list using DeepL API."""
        translator = get_deepl_translator()
        if not translator:
            print("\nDeepL API key not found in environment")
            print("Translation skipped. Set DEEPL_API_KEY in .env to enable.")
            return None

        if self._curated_words:
            return self._write_curated_translations(output_file)

        return self._translate_via_deepl(
            word_list_file, output_file, source_lang, target_lang, translator
        )

    def _write_curated_translations(self, output_file: Path) -> Path:
        """Write LLM-curated translations directly, bypassing DeepL."""
        print("\n" + "=" * 70)
        print("WRITING LLM-CURATED TRANSLATIONS")
        print("=" * 70)
        print(f"Using {len(self._curated_words)} translations from LLM curation...")
        skipped = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for cw in self._curated_words:
                translation = (cw.translation or cw.note or "").strip()
                if translation:
                    f.write(f"{cw.best_form}\t{translation}\n")
                else:
                    skipped += 1
        written = len(self._curated_words) - skipped
        print(f"Wrote {written} translations")
        if skipped:
            print(f"Skipped {skipped} words with no translation")
        print(f"Output: {output_file}")
        print("=" * 70)
        return output_file

    def _translate_via_deepl(
        self,
        word_list_file: Path,
        output_file: Path,
        source_lang: str,
        target_lang: str,
        translator
    ) -> Optional[Path]:
        """Translate word list via DeepL API."""
        print("\n" + "=" * 70)
        print("TRANSLATING WORD LIST")
        print("=" * 70)

        try:
            words = self._read_word_list(word_list_file)
            print(f"Translating {source_lang} -> {target_lang}\n")

            translations = translate_word_list(
                words,
                translator,
                target_lang,
                source_lang,
                show_progress=True,
                sentence_context=self._sentence_context
            )

            self._write_and_report_translations(output_file, translations, translator)
            return output_file

        except Exception as e:
            print(f"Translation error: {e}")
            return None


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze word frequencies in subtitle files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python subtitle_word_frequency.py
  
  # Specify custom config file
  python subtitle_word_frequency.py --config my_config.yaml
  
  # Override subtitles directory
  python subtitle_word_frequency.py --subtitles-dir /path/to/subtitles
  
  # Add stopwords
  python subtitle_word_frequency.py --add-stopwords "hola,adiós,gracias"
  
  # Remove stopwords
  python subtitle_word_frequency.py --remove-stopwords "importante,necesario"
  
  # Use manual threshold
  python subtitle_word_frequency.py --min-freq 5
  
  # Analyze and translate in one command
  python subtitle_word_frequency.py --translate
  
  # Translate to German
  python subtitle_word_frequency.py --translate --target-lang DE
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Path to configuration YAML file'
    )
    
    parser.add_argument(
        '--subtitles-dir', '-s',
        type=Path,
        help='Directory containing subtitle files (overrides config)'
    )
    
    parser.add_argument(
        '--min-freq', '-f',
        type=int,
        help='Minimum frequency threshold (sets threshold_mode to manual)'
    )
    
    parser.add_argument(
        '--add-stopwords',
        type=str,
        help='Comma-separated list of stopwords to add'
    )
    
    parser.add_argument(
        '--remove-stopwords',
        type=str,
        help='Comma-separated list of stopwords to remove'
    )
    
    parser.add_argument(
        '--list-stopwords',
        action='store_true',
        help='List all current stopwords and exit'
    )
    
    parser.add_argument(
        '--translate',
        action='store_true',
        help='Translate word list after analysis (requires DEEPL_API_KEY in .env)'
    )

    parser.add_argument(
        '--curate',
        action='store_true',
        help='Enable LLM curation of word list (requires MINIMAX_API_KEY in .env)'
    )

    parser.add_argument(
        '--source-lang',
        default=None,
        help='Source language for translation (default: from config.yaml or ES)'
    )
    
    parser.add_argument(
        '--target-lang',
        default=None,
        help='Target language for translation (default: from config.yaml or EN-US)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    try:
        # Initialize analyzer
        analyzer = SubtitleFrequencyAnalyzer(config_path=args.config)
        
        # Handle stopword management
        if args.list_stopwords:
            stopwords = sorted(analyzer.stopword_manager.get_stopwords())
            print(f"\nCurrent stopwords ({len(stopwords)}):")
            for word in stopwords:
                print(f"  - {word}")
            return 0
        
        if args.add_stopwords:
            words = [w.strip() for w in args.add_stopwords.split(',')]
            analyzer.add_stopwords(words)
            return 0
        
        if args.remove_stopwords:
            words = [w.strip() for w in args.remove_stopwords.split(',')]
            analyzer.remove_stopwords(words)
            return 0
        
        # Override config with command-line arguments
        if args.min_freq:
            analyzer.config['frequency']['threshold_mode'] = 'manual'
            analyzer.config['frequency']['min_frequency'] = args.min_freq

        if args.curate:
            analyzer.config['llm_curation']['enabled'] = True

        # Run analysis
        results = analyzer.analyze(subtitles_dir=args.subtitles_dir)
        
        if results is None:
            return 1
        
        print(f"\n📊 Final Results:")
        print(f"  Words in report: {len(results['frequencies'])}")
        print(f"  Frequency threshold used: {results['threshold']}")
        print(f"\n✨ Reports saved to: {analyzer.report_generator.output_dir}")
        
        # Translate if requested (via --translate flag or config)
        translation_config = analyzer.config.get('translation', {})
        should_translate = args.translate or translation_config.get('enabled', False)
        
        if should_translate:
            anki_words_file = results['reports'].get('anki')
            if anki_words_file:
                # Use command-line args if provided, otherwise use config, otherwise use defaults
                source_lang = args.source_lang or translation_config.get('source_lang', 'ES')
                target_lang = args.target_lang or translation_config.get('target_lang', 'EN-US')
                output_filename = translation_config.get('output_filename', 'translated_words.txt')
                translated_file = analyzer.report_generator.output_dir / output_filename
                
                result = analyzer.translate_wordlist(
                    anki_words_file,
                    translated_file,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                if result:
                    print(f"\n📚 Anki-ready file: {result}")
                    print("   Import to Anki: File → Import → Tab-separated")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
