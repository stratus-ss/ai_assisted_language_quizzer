"""
Translator Module

Handles word translation using DeepL API.
Shared by subtitle_word_frequency.py and translate_wordlist.py
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple


def get_deepl_translator():
    """
    Get DeepL translator instance.
    
    Returns:
        deepl.Translator instance or None if not available
    """
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        return None
    
    try:
        import deepl
        return deepl.Translator(api_key)
    except ImportError:
        return None


def translate_word(
    word: str,
    translator,
    target_lang: str,
    source_lang: Optional[str] = None
) -> str:
    """
    Translate a single word.
    
    Args:
        word: Word to translate
        translator: DeepL translator instance
        target_lang: Target language code
        source_lang: Source language code (optional)
        
    Returns:
        Translated word
    """
    if source_lang:
        result = translator.translate_text(
            word,
            target_lang=target_lang,
            source_lang=source_lang
        )
    else:
        result = translator.translate_text(
            word,
            target_lang=target_lang
        )
    return result.text


def translate_word_list(
    words: List[str],
    translator,
    target_lang: str,
    source_lang: Optional[str] = None,
    show_progress: bool = True
) -> List[Tuple[str, str]]:
    """
    Translate a list of words.
    
    Args:
        words: List of words to translate
        translator: DeepL translator instance
        target_lang: Target language code
        source_lang: Source language code (optional)
        show_progress: Whether to show progress output
        
    Returns:
        List of (original_word, translation) tuples
    """
    translations = []
    
    for i, word in enumerate(words, 1):
        if show_progress:
            print(f"[{i}/{len(words)}] {word}", end=" → ")
        
        try:
            translation = translate_word(
                word,
                translator,
                target_lang,
                source_lang
            )
            translations.append((word, translation))
            
            if show_progress:
                print(f"{translation} ✓")
                
        except Exception as e:
            if show_progress:
                print(f"❌ Error: {e}")
            translations.append((word, "[ERROR]"))
    
    return translations


def get_api_usage(translator) -> dict:
    """
    Get DeepL API usage statistics.
    
    Args:
        translator: DeepL translator instance
        
    Returns:
        Dictionary with usage information
    """
    try:
        usage = translator.get_usage()
        return {
            'character_count': usage.character.count,
            'character_limit': usage.character.limit if usage.character.limit else 0,
            'percentage_used': (usage.character.count / usage.character.limit * 100)
                               if usage.character.limit else 0
        }
    except Exception:
        return {
            'character_count': 0,
            'character_limit': 0,
            'percentage_used': 0
        }
