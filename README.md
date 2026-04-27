# AI Assisted Language Quizzer

An AI-powered language learning tool for extracting vocabulary from subtitles, translating words, and creating Anki flashcards with audio support.

## Features

- 📊 **Subtitle Word Frequency Analyzer** - Extract vocabulary from TV shows and movies
- 🌍 **DeepL Translation** - Translate word lists automatically
- 📚 **Anki Integration** - Import cards and add audio files
- 🎯 **Smart Filtering** - Filter common words and focus on high-frequency vocabulary
- 🧠 **LLM Curation** - Optional Minimax-powered word quality scoring
- 🔤 **Lemmatization** - Optional spaCy-based conjugation grouping
- 🎤 **Audio Generation** - Generate pronunciation audio from All-Talk AI

## Project Structure

```
language/
├── scripts/                        # CLI tools
│   ├── subtitle_word_frequency.py  # Main frequency analyzer
│   ├── translate_wordlist.py       # Translation script
│   └── clean_subtitles.py          # Subtitle cleaner
├── anki_tools/                     # Anki integration
│   ├── add_audio_to_anki.py        # Add audio to cards
│   └── add_words_to_anki_notes.py  # Add translations to notes
├── audio/                          # Audio generation
│   └── download_from_alltalk.py    # Download audio files
├── core/                           # Core modules
│   ├── subtitle_analyzer/          # Frequency analysis library
│   │   ├── __init__.py            # Public API exports
│   │   ├── config.yaml             # Configuration
│   │   ├── stopwords_spanish.txt   # Words to filter
│   │   ├── srt_parser.py
│   │   ├── word_processor.py
│   │   ├── stopword_manager.py
│   │   ├── frequency_analyzer.py
│   │   ├── report_generator.py
│   │   ├── translator.py
│   │   ├── lemma_grouper.py       # Optional spaCy lemmatization
│   │   └── llm_curator.py        # Optional Minimax curation
│   └── modules/                    # Quiz app utilities
│       ├── __init__.py
│       ├── file_handling.py
│       └── review_words.py
├── data/                           # Data files
│   ├── input/                      # Word lists
│   ├── output/                     # Generated reports
│   ├── word_lists/                 # Organized vocabularies
│   └── images/                     # Image assets
├── venv/                           # Virtual environment
├── app.py                          # Gradio quiz UI
└── .env                            # API keys (gitignored)
```

**Subtitles Directory:**
- `subtitles/` - Place your .srt subtitle files here

## Quick Start

### 1. Setup

```bash
# Clone repository
git clone https://github.com/your-username/ai-assisted-language-quizzer.git
cd ai-assisted-language-quizzer

# Create virtual environment
cd language
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt
```

### 2. Configure API Keys

Create `.env` file in `language/` directory:
```bash
DEEPL_API_KEY="your-api-key-here"
```

Get a free DeepL API key: https://www.deepl.com/pro-api (500,000 characters/month)

### 3. Complete Workflow

```bash
# Basic: Extract vocabulary from subtitles
python scripts/subtitle_word_frequency.py

# With LLM curation (scores words by learning value):
python scripts/subtitle_word_frequency.py --curate

# With translation:
python scripts/subtitle_word_frequency.py --translate

# All together:
python scripts/subtitle_word_frequency.py --curate --translate

# Import to Anki:
# File → Import → data/output/translated_words.txt
# Field separator: Tab, Field 1 → Front, Field 2 → Back
```

## Detailed Usage

### Subtitle Frequency Analyzer

**Extract vocabulary from TV shows/movies:**

```bash
cd language
python scripts/subtitle_word_frequency.py
```

**Output:**
- `data/output/anki_import_words.txt` - Words sorted by frequency
- `data/output/word_frequency_report.csv` - Detailed frequency data
- `data/output/word_frequency_summary.md` - Human-readable report

**All-in-one command (analyze + translate):**
```bash
# Extract and translate in one step
python scripts/subtitle_word_frequency.py --translate

# Translate to different language (e.g., German)
python scripts/subtitle_word_frequency.py --translate --target-lang DE

# Specify source language explicitly
python scripts/subtitle_word_frequency.py --translate --source-lang ES --target-lang EN-US
```

**Customize stopwords:**
```bash
# Add words to ignore (character names, etc.)
python scripts/subtitle_word_frequency.py --add-stopwords "vin,elfo,lucy"

# Remove words from stopwords
python scripts/subtitle_word_frequency.py --remove-stopwords "importante"

# List current stopwords
python scripts/subtitle_word_frequency.py --list-stopwords
```

**LLM Curation (optional):**
```bash
# Requires MINIMAX_API_KEY in language/.env
python scripts/subtitle_word_frequency.py --curate
```

**Lemmatization (optional, disabled by default):**

Enable in `core/subtitle_analyzer/config.yaml` under `lemmatization.enabled: true`.
Requires: `pip install spacy && python -m spacy download es_core_news_sm`

**Configuration:** Edit `core/subtitle_analyzer/config.yaml`
- `target_words`: Number of words in final list (default: 500)
- `min_word_length`: Minimum word length (default: 2)
- `threshold_mode`: "auto" or "manual" frequency filtering
- `lemmatization.enabled`: Group conjugations under root form (default: false)
- `llm_curation.enabled`: LLM word scoring (default: false, or use `--curate`)
- `translation.enabled`: Auto-translate after analysis (default: false)
- `translation.source_lang`: Source language (default: ES)
- `translation.target_lang`: Target language (default: EN-US)

### Word Translation

**Translate word lists using DeepL API:**

```bash
source venv/bin/activate

# Spanish to English (default)
python scripts/translate_wordlist.py \
  -i data/output/anki_import_words.txt \
  -o data/output/translated_words.txt

# Check API usage
python scripts/translate_wordlist.py --check-usage
```

**Output formats:**
- `--format anki` - Tab-separated (default, Anki-ready)
- `--format csv` - Comma-separated with header
- `--format plain` - Human-readable

**Supported languages:**
- Source: ES, FR, DE, IT, PT, RU, JA, ZH
- Target: EN-US, EN-GB, DE, FR, ES, IT, PT-BR, RU, JA, ZH

### Anki Import

**Import translated words to Anki:**

1. Open Anki → File → Import
2. Select `data/output/translated_words.txt`
3. Configure:
   - Type: **Basic**
   - Field separator: **Tab**
   - Field 1 → **Front** (Spanish)
   - Field 2 → **Back** (English)
4. Click **Import**

**Add audio to Anki cards (optional):**

```bash
python anki_tools/add_audio_to_anki.py \
  -a ./audio_directory \
  -w data/output/anki_import_words.txt \
  -d "Your Deck Name" \
  --search-field "Front" \
  --audio-field "Front"
```

**Prerequisites:**
- Anki must be running
- AnkiConnect add-on installed (Code: 2055492159)

### Audio Generation

**Generate pronunciation audio:**

```bash
python audio/download_from_alltalk.py \
  -w data/input/spanish_words.txt \
  -l es \
  -v female_03-female_07
```

**Requirements:**
- All-Talk AI server running
- Update `all_talk_url` in script if needed

## Tips & Best Practices

### Vocabulary Learning Strategy

1. **Start small:** Import top 50-100 words first
2. **High-frequency focus:** Words appearing most often give best comprehension boost
3. **Review stopwords:** Add character names and unwanted words after first run
4. **Genre-specific:** Different shows = different vocabulary

### Frequency Thresholds

The analyzer uses smart thresholds based on dataset size:
- **Small dataset (few files):** Lower threshold, more words
- **Large dataset (many files):** Higher threshold, focus on common words

**Manual control:**
```bash
# Only words appearing 10+ times
python scripts/subtitle_word_frequency.py --min-freq 10
```

### API Usage Management

**DeepL Free Tier:** 500,000 characters/month
- ~410 words ≈ 2,400 characters (0.5% usage)
- ~50,000 words possible per month
- Check usage: `python translate_wordlist.py --check-usage`

### Batch Processing

**Process multiple subtitle files:**
```bash
# Place all .srt files in subtitles/ directory
python scripts/subtitle_word_frequency.py

# Analyzer processes all files automatically
# Results are combined and sorted by frequency
```

**Import in stages:**
```bash
# Top 100 words
head -100 data/output/anki_import_words.txt > batch1.txt
python scripts/translate_wordlist.py -i batch1.txt -o translated_batch1.txt

# Next 100 words
head -200 data/output/anki_import_words.txt | tail -100 > batch2.txt
python scripts/translate_wordlist.py -i batch2.txt -o translated_batch2.txt
```

## Troubleshooting

**"Permission denied: .env"**
```bash
chmod 600 language/.env
```

**"Module not found: deepl"**
```bash
cd language
source venv/bin/activate
pip install deepl python-dotenv pyyaml
```

**"No files matching '*.srt' found"**
- Ensure subtitle files are in `subtitles/` directory
- Check file extensions are `.srt` (lowercase)

**"AnkiConnect error"**
- Ensure Anki is running
- Install AnkiConnect add-on: Tools → Add-ons → Get Add-ons → Code: 2055492159

## Documentation

- `CODEFLOW.md` - **Start here** - Comprehensive code flow diagrams and architecture overview
- `core/subtitle_analyzer/README.md` - Detailed frequency analyzer documentation
- `core/subtitle_analyzer/config.yaml` - Configuration options with comments
- `docs/curation.md` - LLM curation design, configuration, and performance guide
- `--help` flag on any script for usage information

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html)
