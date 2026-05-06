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

# 3. Run word frequency analysis (stopwords loaded from config.yaml)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles
```

---

## Scripts

### subtitle_word_frequency.py

Main analysis pipeline. Reads SRT files, extracts words, filters stopwords, generates frequency-sorted vocabulary lists.

```bash
# Basic run (uses bundled stopwords from config.yaml)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles

# Add stopwords inline (comma-separated)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --add-stopwords "name1,name2"

# Remove a stopword from the list
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --remove-stopwords "word"

# Show current stopwords loaded
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --list-stopwords

# LLM curation (requires MINIMAX_API_KEY)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --curate

# DeepL translation (requires DEEPL_API_KEY)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --translate --target-lang EN-US

# Custom minimum frequency threshold
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --min-freq 10

# Multi-step: curation + translation
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --curate --translate --target-lang DE
```

**Output files** (written to `data/output/`):
- `anki_import_words.txt` — tab-separated word list for Anki import
- `word_frequency_report.csv` — frequency, cumulative %, statistics
- `word_frequency_summary.md` — ranked vocabulary table

**Key flags:**
| Flag | Description |
|------|-------------|
| `--config`, `-c` | Path to custom config YAML file |
| `--subtitles-dir`, `-s` | Directory containing .srt subtitle files |
| `--curate` | Enable LLM curation (needs MINIMAX_API_KEY) |
| `--translate` | Run DeepL translation on output word list |
| `--target-lang` | DeepL target language (EN-US, DE, FR, ES, etc.) |
| `--source-lang` | Source language for translation (default: ES) |
| `--min-freq`, `-f` | Minimum word frequency threshold |
| `--add-stopwords` | Comma-separated words to add to stopwords |
| `--remove-stopwords` | Comma-separated words to remove from stopwords |
| `--list-stopwords` | Print current stopwords and exit |

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
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.translate_wordlist -i words.txt -o out.txt --source ES --target DE
```

**Supported languages:**
- Source: ES, FR, DE, IT, PT, RU, JA, ZH
- Target: EN-US, EN-GB, DE, FR, ES, IT, PT-BR, RU, JA, ZH

**Note:** DeepL free tier: 500,000 characters/month (~50,000 words).

---

### lingq_bulk_import.py

Bulk-import SRT subtitle files (with optional audio) as LingQ lessons. Scans a directory for `.srt` files, resolves a LingQ course by name, and creates one lesson per subtitle file.

```bash
# Bulk-import all SRT files from a directory into a LingQ course
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --dir subtitles --course "Spanish Vocabulary"

# Preview without making changes
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --dir subtitles --course "Spanish Vocabulary" --dry-run

# Import a single SRT file as a lesson (with optional audio)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --lesson path/to/episode.srt --audio path/to/episode.mp3 --course "Spanish Vocabulary"

# Replace audio on existing lessons (matches by title)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --dir subtitles --course "Spanish Vocabulary" --replace-audio

# Specify language code and skip confirmation prompts
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import --dir subtitles --course "Spanish Vocabulary" --language es --yes
```

**Key flags:**
| Flag | Description |
|------|-------------|
| `--dir`, `-d` | Directory containing .srt (and optional audio) files |
| `--course`, `-C` | LingQ course name (case-insensitive partial match) |
| `--lesson`, `-L` | Single .srt file to import (instead of scanning `--dir`) |
| `--audio`, `-a` | Audio file to attach to a single lesson |
| `--language`, `-l` | Two-letter LingQ language code (default from config: `es`) |
| `--config`, `-c` | Path to custom YAML config file |
| `--dry-run` | Preview what would be uploaded without API calls |
| `--replace-audio` | Replace audio on existing lessons matched by title |
| `--yes`, `-y` | Skip all confirmation prompts (for scripting) |
| `--test` | Run the test harness on test data |

**Note:** Requires LingQ API key (`LINGQ_API_KEY` in `.env`).

---

### clean_subtitles.py

Clean and normalize .srt subtitle files before analysis. Removes Amara.org credits and renumbers entries in-place. Operates on the subtitles directory relative to the script location.

```bash
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.clean_subtitles
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

**Stopwords file:** The default stopwords file is bundled at `src/ai_assisted_language_quizzer/core/subtitle_analyzer/stopwords_spanish.txt` (907 Spanish stopwords). A copy also exists at the repo root. Configure the path via `paths.stopwords_file` in `config.yaml`, or use `--add-stopwords` / `--remove-stopwords` to adjust at runtime.

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
│   │   │   ├── stopwords_spanish.txt  # Bundled Spanish stopwords
│   │   │   ├── frequency_analyzer.py
│   │   │   ├── lemma_grouper.py  # Optional spaCy lemmatization
│   │   │   ├── llm_curator.py   # Optional Minimax curation
│   │   │   ├── pronoun_context.py  # Pronoun context extraction
│   │   │   ├── translator.py    # DeepL translation
│   │   │   └── report_generator.py
│   │   └── lingq_import/        # LingQ API client
│   │       ├── client.py
│   │       └── test_harness.py
│   ├── scripts/                 # CLI entry points
│   │   ├── subtitle_word_frequency.py
│   │   ├── translate_wordlist.py
│   │   ├── lingq_bulk_import.py
│   │   └── clean_subtitles.py
│   ├── anki_tools/              # AnkiConnect integration
│   │   ├── add_words_to_anki_notes.py
│   │   └── add_audio_to_anki.py
│   ├── audio/                   # AllTalk TTS generation
│   │   └── download_from_alltalk.py
│   └── paths.py                 # Project root path helper
├── data/
│   ├── input/                   # Source word lists
│   ├── output/                  # Generated reports, CSVs
│   ├── audio/                   # TTS audio files from AllTalk
│   ├── images/                  # Image files for Anki cards
│   └── word_lists/             # Per-language YAML word lists
├── subtitles/                  # SRT subtitle files for analysis
├── stopwords_spanish.txt       # Spanish stopwords (907 words, copy)
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