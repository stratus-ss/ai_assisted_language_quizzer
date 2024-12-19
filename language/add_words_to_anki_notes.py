import re
import os
import deepl

# This file takes in a text export of anki notes with ALL fields exported
# it then grabs the 4th column and gets a translation from deepl.
# Finally it adds the tranlated word to the note and writes the deck back




deepl_api = os.getenv("DEEPL_API_KEY")
translator = deepl.Translator(deepl_api)

def lookup_word(translate_this: str, language_code: str = None, native_language: str = None) -> str:
    if native_language:
        result = translator.translate_text(
            translate_this, target_lang=language_code, source_lang=native_language
        )
    else:
        result = translator.translate_text(
            translate_this, target_lang=language_code
        )
    return result.text

def process_file(file_path, target_lang, source_lang=None):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    modified_lines = []
    for line in lines:
        fields = line.split('\t')
        if len(fields) >= 4:
            word_field = fields[3]
            match = re.match(r'^(\S+)\s+(\([^)]+\))', word_field)
            if match:
                original_word = match.group(1)
                word_type = match.group(2)                
                # Translate the word
                translated_word = lookup_word(original_word, target_lang, source_lang)
                # Replace the word field with the new format
                new_word_field = f'{original_word}, {translated_word} {word_type}'
                fields[3] = new_word_field                
                # Reconstruct the line
                modified_line = '\t'.join(fields)
                modified_lines.append(modified_line)
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)  # Keep the line unchanged if it doesn't have enough fields
    # Write the modified lines back to the file
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)

# Example usage
file_path = 'spanish_short.txt'
target_language = 'DE'  # German
source_language = 'ES'  # Spanish

process_file(file_path, target_language, source_language)
