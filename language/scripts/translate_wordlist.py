#!/usr/bin/env python3
"""
Translate Word List

Translates words from the frequency analyzer output using DeepL API.
Uses shared translator module from subtitle_analyzer.
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add core modules to path for shared modules
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from subtitle_analyzer.translator import (
    get_deepl_translator,
    translate_word_list,
    get_api_usage
)


# Load environment variables
load_dotenv()


def translate_wordlist(
    input_file: Path,
    output_file: Path,
    target_lang: str,
    source_lang: str = None,
    format_type: str = "anki"
) -> None:
    """
    Translate a list of words from a file.
    
    Args:
        input_file: Path to input word list (one word per line)
        output_file: Path to output file with translations
        target_lang: Target language code
        source_lang: Source language code (optional)
        format_type: Output format ("anki" or "csv")
    """
    # Get translator
    translator = get_deepl_translator()
    if not translator:
        print("❌ Error: DEEPL_API_KEY not found in environment")
        print("Please add it to your .env file")
        sys.exit(1)
    
    # Read input words
    print(f"📖 Reading words from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"✓ Found {len(words)} words to translate")
    print(f"🌍 Translating {source_lang or 'auto-detect'} → {target_lang}\n")
    
    # Translate using shared module
    translations = translate_word_list(
        words,
        translator,
        target_lang,
        source_lang,
        show_progress=True
    )
    
    # Count errors
    errors = sum(1 for _, t in translations if t == "[ERROR]")
    
    # Write output
    print(f"\n💾 Writing translations to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        if format_type == "anki":
            # Format: spanish_word<tab>english_translation
            for word, translation in translations:
                f.write(f"{word}\t{translation}\n")
        
        elif format_type == "csv":
            # Format: spanish_word,english_translation
            f.write("original,translation\n")
            for word, translation in translations:
                f.write(f"{word},{translation}\n")
        
        else:  # plain text
            for word, translation in translations:
                f.write(f"{word} → {translation}\n")
    
    # Summary
    print("\n" + "=" * 60)
    print("TRANSLATION COMPLETE")
    print("=" * 60)
    print(f"✓ Translated: {len(words) - errors} words")
    if errors:
        print(f"❌ Errors: {errors}")
    print(f"📄 Output: {output_file}")
    print("=" * 60)


def check_api_usage():
    """Check DeepL API usage."""
    translator = get_deepl_translator()
    if not translator:
        print("❌ Error: DEEPL_API_KEY not found in environment")
        return
    
    usage = get_api_usage(translator)
    if usage['character_count'] > 0 or usage['character_limit'] > 0:
        print(f"\n📊 DeepL API Usage:")
        print(f"  Characters used: {usage['character_count']:,}")
        if usage['character_limit'] > 0:
            print(f"  Character limit: {usage['character_limit']:,}")
            print(f"  Usage: {usage['percentage_used']:.1f}%")
    else:
        print("⚠️  Could not fetch usage stats")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Translate word list using DeepL API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate Spanish words to English
  python translate_wordlist.py -i data/output/anki_import_words.txt -o data/output/translated_words.txt
  
  # Specify languages explicitly
  python translate_wordlist.py -i words.txt -o output.txt --source ES --target EN-US
  
  # Generate CSV format
  python translate_wordlist.py -i words.txt -o output.csv --format csv
  
  # Check API usage
  python translate_wordlist.py --check-usage

Supported language codes:
  Source: ES (Spanish), FR (French), DE (German), IT (Italian), PT (Portuguese)
  Target: EN-US, EN-GB, DE, FR, ES, IT, PT-BR, and more
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=Path,
        help='Input word list file (one word per line)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file with translations'
    )
    
    parser.add_argument(
        '--source',
        default='ES',
        help='Source language code (default: ES for Spanish)'
    )
    
    parser.add_argument(
        '--target',
        default='EN-US',
        help='Target language code (default: EN-US for English)'
    )
    
    parser.add_argument(
        '--format',
        choices=['anki', 'csv', 'plain'],
        default='anki',
        help='Output format (default: anki)'
    )
    
    parser.add_argument(
        '--check-usage',
        action='store_true',
        help='Check DeepL API usage and exit'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check usage only
    if args.check_usage:
        check_api_usage()
        return 0
    
    # Validate required arguments
    if not args.input or not args.output:
        print("❌ Error: Both --input and --output are required")
        print("Use --help for usage information")
        return 1
    
    # Validate input file exists
    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return 1
    
    # Translate
    try:
        translate_wordlist(
            args.input,
            args.output,
            args.target,
            args.source,
            args.format
        )
        
        # Show API usage (translator already used in translate_wordlist)
        # check_api_usage()  # Already shown in translate_wordlist
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Translation interrupted by user")
        return 130
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
