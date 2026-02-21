# AI Assisted Language Quizzer

An AI-powered language learning tool for extracting vocabulary from subtitles, translating words, and creating Anki flashcards with audio support.

## Features

- 📊 **Subtitle Word Frequency Analyzer** - Extract vocabulary from TV shows and movies
- 🌍 **DeepL Translation** - Translate word lists automatically
- 📚 **Anki Integration** - Import cards and add audio files
- 🎯 **Smart Filtering** - Filter common words and focus on high-frequency vocabulary
- 🎤 **Audio Generation** - Generate pronunciation audio from All-Talk AI

## Project Structure

```
language/
├── input/                          # Input files (word lists)
├── output/                         # Generated reports and translations
├── subtitle_analyzer/              # Word frequency analysis module
│   ├── config.yaml                 # Configuration
│   └── stopwords_spanish.txt       # Words to filter
├── venv/                           # Virtual environment
├── subtitle_word_frequency.py      # Main frequency analyzer
├── translate_wordlist.py           # Translation script
├── add_audio_to_anki.py           # Add audio to Anki cards
└── add_words_to_anki_notes.py     # Add translations to notes
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
# Step 1: Extract vocabulary from subtitles
python subtitle_word_frequency.py

# Step 2: Translate words to English
python translate_wordlist.py \
  -i output/anki_import_words.txt \
  -o output/translated_words.txt

# Step 3: Import to Anki (use Anki UI)
# File → Import → translated_words.txt
# Field separator: Tab
# Field 1 → Front, Field 2 → Back
```

## Detailed Usage

### Subtitle Frequency Analyzer

**Extract vocabulary from TV shows/movies:**

```bash
cd language
python subtitle_word_frequency.py
```

**Output:**
- `output/anki_import_words.txt` - Words sorted by frequency
- `output/word_frequency_report.csv` - Detailed frequency data
- `output/word_frequency_summary.md` - Human-readable report

**Customize stopwords:**
```bash
# Add words to ignore (character names, etc.)
python subtitle_word_frequency.py --add-stopwords "vin,elfo,lucy"

# Remove words from stopwords
python subtitle_word_frequency.py --remove-stopwords "importante"

# List current stopwords
python subtitle_word_frequency.py --list-stopwords
```

**Configuration:** Edit `subtitle_analyzer/config.yaml`
- `target_words`: Number of words in final list (default: 500)
- `min_word_length`: Minimum word length (default: 2)
- `threshold_mode`: "auto" or "manual" frequency filtering

### Word Translation

**Translate word lists using DeepL API:**

```bash
source venv/bin/activate

# Spanish to English (default)
python translate_wordlist.py \
  -i output/anki_import_words.txt \
  -o output/translated_words.txt

# Check API usage
python translate_wordlist.py --check-usage
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
2. Select `output/translated_words.txt`
3. Configure:
   - Type: **Basic**
   - Field separator: **Tab**
   - Field 1 → **Front** (Spanish)
   - Field 2 → **Back** (English)
4. Click **Import**

**Add audio to Anki cards (optional):**

```bash
python add_audio_to_anki.py \
  -a ./audio_directory \
  -w output/anki_import_words.txt \
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
python download_from_alltalk.py \
  -w input/spanish_words.txt \
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
python subtitle_word_frequency.py --min-freq 10
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
python subtitle_word_frequency.py

# Analyzer processes all files automatically
# Results are combined and sorted by frequency
```

**Import in stages:**
```bash
# Top 100 words
head -100 output/anki_import_words.txt > batch1.txt
python translate_wordlist.py -i batch1.txt -o translated_batch1.txt

# Next 100 words
head -200 output/anki_import_words.txt | tail -100 > batch2.txt
python translate_wordlist.py -i batch2.txt -o translated_batch2.txt
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

- `subtitle_analyzer/README.md` - Detailed frequency analyzer documentation
- `subtitle_analyzer/config.yaml` - Configuration options with comments
- `--help` flag on any script for usage information

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the [AGPLv3](https://www.gnu.org/licenses/agpl-3.0.en.html)
