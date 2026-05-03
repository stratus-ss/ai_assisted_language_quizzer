# AI Assisted Language Quizzer

A language learning tool that analyzes subtitle files (SRT) to build vocabulary lists and generate Anki flashcards with audio support.

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Scripts](#scripts)
- [Configuration](#configuration)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

This tool extracts vocabulary from SRT subtitle files using frequency analysis, lemmatization, and LLM curation to build focused word lists for language learning. Output goes to Anki for spaced-repetition study or LingQ for bulk import.

**Pipeline:** SRT parsing → word processing → stopword filtering → frequency analysis → lemmatization → LLM curation → report generation → Anki/LingQ export → TTS audio

---

## Quick Start

```bash
# 1. Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -e .
python -m spacy download es_core_news_sm

# 2. Configure API keys
cp .env.example .env  # then edit with your API keys

# 3. Run word frequency analysis
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --stopwords-file stopwords_spanish.txt
```

---

## Scripts

### subtitle_word_frequency.py

Main analysis pipeline. Reads SRT files, extracts words, filters stopwords, generates frequency-sorted vocabulary lists.

```bash
# Basic run (uses bundled stopwords from config.yaml)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles

# With repo-root stopwords file
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --stopwords-file stopwords_spanish.txt

# Add stopwords inline (comma-separated)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --add-stopwords "name1,name2"

# Remove a stopword from the list
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --remove-stopwords "word"

# Show current stopwords loaded
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --list-stopwords

# LLM curation (requires MINIMAX_API_KEY)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --stopwords-file stopwords_spanish.txt --curate

# DeepL translation (requires DEEPL_API_KEY)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --translate --target-lang EN-US

# Custom minimum frequency threshold
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --min-freq 10

# Multi-step: curation + translation
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --stopwords-file stopwords_spanish.txt --curate --translate --target-lang DE
```

**Output files** (written to `data/output/`):
- `anki_import_words.txt` — tab-separated word list for Anki import
- `word_frequency_report.csv` — frequency, cumulative %, statistics
- `word_frequency_summary.md` — ranked vocabulary table

**Key flags:**
| Flag | Description |
|------|-------------|
| `--curate` | Enable LLM curation (needs MINIMAX_API_KEY) |
| `--translate` | Run DeepL translation on output word list |
| `--target-lang` | DeepL target language (EN-US, DE, FR, ES, etc.) |
| `--source-lang` | Source language for analysis (default: ES) |
| `--subtitles-dir` | Directory containing .srt subtitle files |
| `--output-dir` | Output directory (default: data/output/) |
| `--stopwords-file` | Custom stopwords file path |
| `--add-stopwords` | Comma-separated words to add to stopwords |
| `--remove-stopwords` | Comma-separated words to remove from stopwords |
| `--list-stopwords` | Print current stopwords and exit |
| `--min-freq` | Minimum word frequency threshold |

---

### translate_wordlist.py

Standalone translation script for translating existing word lists via DeepL. Supports deduplication.

```bash
# Translate an existing word list
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist -i data/output/anki_import_words.txt -o data/output/translated_words.txt

# Translate a CSV word list
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist -i words.txt -o out.txt --format csv

# Check DeepL API usage
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist --check-usage

# Specify source and target languages
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist -i words.txt -o out.txt --source-lang ES --target-lang DE
```

**Supported languages:**
- Source: ES, FR, DE, IT, PT, RU, JA, ZH
- Target: EN-US, EN-GB, DE, FR, ES, IT, PT-BR, RU, JA, ZH

**Note:** DeepL free tier: 500,000 characters/month (~50,000 words).

---

### lingq_bulk_import.py

Import vocabulary lists into LingQ for spaced-repetition learning.

```bash
# Import from word list file (uses LINGQ_API_KEY env var)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --input data/output/anki_import_words.txt --course-id YOUR_COURSE_ID --title "Spanish Vocabulary"

# With explicit API key
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --input data/output/anki_import_words.txt --api-key YOUR_API_KEY --course-id YOUR_COURSE_ID --title "Spanish Vocabulary"
```

**Note:** Requires LingQ API key (`LINGQ_API_KEY` in .env or `--api-key` flag).

---

### clean_subtitles.py

Clean and normalize .srt subtitle files before analysis. Removes timestamps, indices, and standardizes formatting.

```bash
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.clean_subtitles --input-dir subtitles --output-dir subtitles_cleaned
```

---

## Configuration

Configuration lives in `src/ai_assisted_language_quizzer/core/subtitle_analyzer/config.yaml`.

**Key sections:**

| Section | Description |
|---------|-------------|
| `stopwords:` | Language-specific stopword lists and files |
| `frequency:` | Min frequency thresholds and threshold mode |
| `lemmatization:` | spaCy lemmatization settings (requires `python -m spacy download es_core_news_sm`) |
| `llm_curation:` | LLM curation settings (enable with `--curate` flag, needs MINIMAX_API_KEY) |
| `translation:` | DeepL translation defaults (needs DEEPL_API_KEY) |

**Stopwords file:** The repo root contains `stopwords_spanish.txt` (907 Spanish stopwords). Use `--stopwords-file stopwords_spanish.txt` to reference it, or point to a custom file.

**Secrets** go in `.env` at repo root:

```env
DEEPL_API_KEY=your_key_here
MINIMAX_API_KEY=your_key_here
LINGQ_API_KEY=your_key_here
ALLTALK_URL=http://localhost:8000
```

---

## Directory Structure

```
ai_assisted_language_quizzer/
├── src/ai_assisted_language_quizzer/
│   ├── core/
│   │   ├── subtitle_analyzer/   # SRT parsing, word processing, frequency, reports
│   │   │   ├── config.yaml      # Tunable parameters
│   │   │   ├── srt_parser.py
│   │   │   ├── word_processor.py
│   │   │   ├── stopword_manager.py
│   │   │   ├── frequency_analyzer.py
│   │   │   ├── lemma_grouper.py  # Optional spaCy lemmatization
│   │   │   ├── llm_curator.py   # Optional Minimax curation
│   │   │   ├── translator.py    # DeepL translation
│   │   │   └── report_generator.py
│   │   └── lingq_import/        # LingQ API client
│   ├── scripts/                 # CLI entry points
│   │   ├── subtitle_word_frequency.py
│   │   ├── translate_wordlist.py
│   │   ├── lingq_bulk_import.py
│   │   └── clean_subtitles.py
│   ├── anki_tools/              # AnkiConnect integration
│   │   ├── add_words_to_anki_notes.py
│   │   └── add_audio_to_anki.py
│   └── audio/                   # AllTalk TTS generation
│       └── download_from_alltalk.py
├── data/
│   ├── input/                   # Source word lists
│   ├── output/                  # Generated reports, CSVs
│   ├── audio/                   # TTS audio files from AllTalk
│   ├── images/                  # Image files for Anki cards
│   └── word_lists/             # Per-language YAML word lists
├── subtitles/                  # SRT subtitle files for analysis
├── stopwords_spanish.txt       # Spanish stopwords (907 words)
├── .env.example                # API key template
└── venv/                       # Python virtual environment
```

---

## Troubleshooting

**"No module named spacy"** — Run:
```bash
pip install spacy && python -m spacy download es_core_news_sm
```

**"Failed to parse SRT"** — Check that subtitle files are valid SRT format (UTF-8 encoded .srt files).

**"Permission denied: .env"** — Run:
```bash
chmod 600 .env
```

**AnkiConnect error** — Ensure Anki is running with AnkiConnect add-on installed (Tools → Add-ons → code: 2055492159).

**spaCy model missing** — Run:
```bash
python -m spacy download es_core_news_sm
```
(only needed if `lemmatization.enabled: true` in config.yaml)

---

## Documentation

- `CODEFLOW.md` — Comprehensive code flow diagrams (Mermaid)
- `docs/curation.md` — LLM curation design and configuration
- `src/ai_assisted_language_quizzer/core/subtitle_analyzer/README.md` — Core library documentation

Use `--help` on any script for usage information.