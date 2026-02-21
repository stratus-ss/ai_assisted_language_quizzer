#!/usr/bin/env python3
"""
Translate Word List

Translates words from the frequency analyzer output using DeepL API.
Reuses the translation pattern from add_words_to_anki_notes.py
"""

import os
import sys
import argparse
from pathlib import Path
import deepl
from dotenv import load_dotenv


# Load environment variables from parent directory's .env
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
if not env_path.exists():
    env_path = script_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize DeepL translator
deepl_api = os.getenv("DEEPL_API_KEY")
if not deepl_api:
    print("❌ Error: DEEPL_API_KEY not found in environment")
    print("Please add it to your .env file")
    sys.exit(1)

translator = deepl.Translator(deepl_api)


def lookup_word(
    translate_this: str, 
    language_code: str = None, 
    native_language: str = None
) -> str:
    """
    Translate a word using DeepL API.
    
    Args:
        translate_this: Word to translate
        language_code: Target language code (e.g., "EN-US", "DE")
        native_language: Source language code (e.g., "ES", "FR")
        
    Returns:
        Translated word
    """
    if native_language:
        result = translator.translate_text(
            translate_this, 
            target_lang=language_code, 
            source_lang=native_language
        )
    else:
        result = translator.translate_text(
            translate_this, 
            target_lang=language_code
        )
    return result.text


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
    # Read input words
    print(f"📖 Reading words from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"✓ Found {len(words)} words to translate")
    print(f"🌍 Translating {source_lang or 'auto-detect'} → {target_lang}\n")
    
    # Translate each word
    translations = []
    errors = 0
    
    for i, word in enumerate(words, 1):
        print(f"[{i}/{len(words)}] {word}", end=" → ")
        
        try:
            translation = lookup_word(word, target_lang, source_lang)
            translations.append((word, translation))
            print(f"{translation} ✓")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            translations.append((word, f"[ERROR]"))
            errors += 1
    
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
    try:
        usage = translator.get_usage()
        print(f"\n📊 DeepL API Usage:")
        print(f"  Characters used: {usage.character.count:,}")
        if usage.character.limit:
            print(f"  Character limit: {usage.character.limit:,}")
            percentage = (usage.character.count / usage.character.limit) * 100
            print(f"  Usage: {percentage:.1f}%")
    except Exception as e:
        print(f"⚠️  Could not fetch usage stats: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Translate word list using DeepL API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate Spanish words to English
  python translate_wordlist.py -i output/anki_import_words.txt -o translated_words.txt
  
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
        
        # Show API usage
        check_api_usage()
        
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
