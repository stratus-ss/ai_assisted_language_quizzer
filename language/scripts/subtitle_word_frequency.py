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
from pathlib import Path
import yaml
from typing import Dict, List, Optional
from dotenv import load_dotenv


# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from subtitle_analyzer import (
    SRTParser,
    WordProcessor,
    StopWordManager,
    FrequencyAnalyzer,
    ReportGenerator
)
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
                'subtitles_directory': '../../subtitles',
                'output_directory': '../output',
                'stopwords_file': './stopwords_spanish.txt'
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
            stopwords_file = language_root / "core" / "subtitle_analyzer" / stopwords_file.name
        self.stopword_manager = StopWordManager(stopwords_file)
        
        # Report generator
        output_dir = Path(self.config['paths']['output_directory'])
        if not output_dir.is_absolute():
            output_dir = language_root / output_dir
        self.report_generator = ReportGenerator(output_dir)
    
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
        
        # Determine subtitles directory
        if subtitles_dir is None:
            subtitles_dir = Path(self.config['paths']['subtitles_directory'])
            if not subtitles_dir.is_absolute():
                script_dir = Path(__file__).parent
                subtitles_dir = script_dir / subtitles_dir
        
        subtitles_dir = Path(subtitles_dir)
        
        print(f"\n📁 Subtitles directory: {subtitles_dir}")
        print(f"📝 Stopwords file: {self.stopword_manager.stopwords_file}")
        print(f"💾 Output directory: {self.report_generator.output_dir}\n")
        
        # Step 1: Parse subtitle files
        print("Step 1: Parsing subtitle files...")
        try:
            file_pattern = self.config.get('advanced', {}).get('file_pattern', '*.srt')
            parsed_data = self.parser.parse_directory(subtitles_dir, file_pattern)
            print(f"✓ Parsed {len(parsed_data)} files")
        except Exception as e:
            print(f"❌ Error parsing files: {e}")
            return None
        
        # Step 2: Process words
        print("\nStep 2: Processing words...")
        all_words = []
        for filename, lines in parsed_data.items():
            words = self.word_processor.process_lines(lines)
            all_words.extend(words)
        
        print(f"✓ Extracted {len(all_words)} total words")
        
        # Step 3: Filter stopwords
        print("\nStep 3: Filtering stopwords...")
        print(f"  Stopwords loaded: {self.stopword_manager.get_count()}")
        filtered_words = self.stopword_manager.filter_words(all_words)
        removed_count = len(all_words) - len(filtered_words)
        print(f"✓ Filtered out {removed_count} stopwords")
        print(f"  Remaining words: {len(filtered_words)}")
        
        # Step 4: Analyze frequencies
        print("\nStep 4: Analyzing word frequencies...")
        self.frequency_analyzer.analyze(filtered_words)
        stats = self.frequency_analyzer.get_statistics()
        
        print(f"✓ Found {stats['unique_words']} unique words")
        print(f"  Most common: {stats['most_common_word'][0]} ({stats['most_common_word'][1]}x)")
        
        # Step 5: Apply frequency threshold
        print("\nStep 5: Applying frequency threshold...")
        freq_config = self.config.get('frequency', {})
        
        if freq_config.get('threshold_mode') == 'auto':
            target_words = freq_config.get('target_words', 500)
            threshold = self.frequency_analyzer.calculate_smart_threshold(
                target_words=target_words
            )
            print(f"  Auto-calculated threshold: {threshold}")
        else:
            threshold = freq_config.get('min_frequency', 3)
            print(f"  Manual threshold: {threshold}")
        
        filtered_frequencies = self.frequency_analyzer.filter_by_frequency(
            min_frequency=threshold
        )
        
        # Apply max results limit
        max_results = freq_config.get('max_results', 1000)
        if len(filtered_frequencies) > max_results:
            sorted_freqs = sorted(
                filtered_frequencies.items(),
                key=lambda x: x[1],
                reverse=True
            )
            filtered_frequencies = dict(sorted_freqs[:max_results])
        
        print(f"✓ {len(filtered_frequencies)} words meet threshold criteria")
        
        # Step 6: Generate reports
        print("\nStep 6: Generating reports...")
        output_config = self.config.get('output', {})
        
        source_files = list(parsed_data.keys())
        reports = self.report_generator.generate_all_reports(
            filtered_frequencies,
            stats,
            source_files,
            top_n=len(filtered_frequencies)
        )
        
        print(f"✓ Generated {len(reports)} reports:")
        for report_type, filepath in reports.items():
            print(f"  - {report_type}: {filepath}")
        
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
    
    def translate_wordlist(
        self,
        word_list_file: Path,
        output_file: Path,
        source_lang: str = "ES",
        target_lang: str = "EN-US"
    ) -> Optional[Path]:
        """
        Translate word list using DeepL API.
        
        Args:
            word_list_file: Path to word list file
            output_file: Path to output translated file
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Path to translated file or None if failed
        """
        # Get translator
        translator = get_deepl_translator()
        if not translator:
            print("\n⚠️  DeepL API key not found in environment")
            print("   Translation skipped. Set DEEPL_API_KEY in .env to enable.")
            return None
        
        print("\n" + "=" * 70)
        print("TRANSLATING WORD LIST")
        print("=" * 70)
        
        try:
            # Read words
            print(f"📖 Reading words from: {word_list_file}")
            with open(word_list_file, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            print(f"✓ Found {len(words)} words to translate")
            print(f"🌍 Translating {source_lang} → {target_lang}\n")
            
            # Translate using shared module
            translations = translate_word_list(
                words,
                translator,
                target_lang,
                source_lang,
                show_progress=True
            )
            
            # Write output
            print(f"\n💾 Writing translations to: {output_file}")
            with open(output_file, 'w', encoding='utf-8') as f:
                for word, translation in translations:
                    f.write(f"{word}\t{translation}\n")
            
            # Check API usage
            usage = get_api_usage(translator)
            if usage['character_count'] > 0:
                print(f"\n📊 DeepL API Usage:")
                print(f"  Characters used: {usage['character_count']:,}")
                if usage['character_limit'] > 0:
                    print(f"  Character limit: {usage['character_limit']:,}")
                    print(f"  Usage: {usage['percentage_used']:.1f}%")
            
            # Count errors
            errors = sum(1 for _, t in translations if t == "[ERROR]")
            
            print("\n" + "=" * 70)
            print("TRANSLATION COMPLETE!")
            print("=" * 70)
            print(f"✓ Translated: {len(words) - errors} words")
            if errors:
                print(f"❌ Errors: {errors}")
            print(f"📄 Output: {output_file}")
            print("=" * 70)
            
            return output_file
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
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
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
