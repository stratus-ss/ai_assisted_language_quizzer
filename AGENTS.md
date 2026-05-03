# ai_assisted_language_quizzer

<!-- Purpose: Briefing document for AI coding agents.
     Keep under 150 lines. Cover what an agent needs to be productive.
     Ref: AGENTS.md standard (agentsmd.online), wimpysworld conventions. -->

## Project Overview

Language learning tool that analyzes subtitle files (SRT) to build vocabulary lists, generate Anki flashcards, and run a quiz app. Pipelines: subtitle -> word frequency analysis -> LLM curation -> reports -> Anki/TTS export.

- **Language:** Python 3.11
- **Package manager:** pip (pyproject.toml, venv/)
- **Key dependencies:** deepl, spacy, soundfile, pyyaml, python-dotenv

## Commands

```bash
# Activate venv
source venv/bin/activate

# Install dependencies
pip install -e .
# Post-install: python -m spacy download es_core_news_sm

# Subtitle word frequency analysis (CLI)
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.subtitle_word_frequency --subtitles-dir subtitles --stopwords-file stopwords_spanish.txt

# LingQ bulk import
PYTHONPATH=src python -m ai_assisted_language_quizzer.scripts.lingq_bulk_import

# LingQ bulk import
lingq-bulk-import --input data/output/wordlist.csv
```

## Code Style

- Formatter: ruff (repo has .ruff_cache)
- Type hints required on all public method signatures
- Imports at top of file only -- never inside function bodies
- Max function length: 50 lines; max complexity: 15
- Prefer classes over bare functions for stateful/multi-step logic
- Use Path from pathlib instead of raw string paths

## File Structure

```
ai_assisted_language_quizzer/
  src/ai_assisted_language_quizzer/
    core/
      subtitle_analyzer/       # Library classes (srt_parser, word_processor, etc.)
        config.yaml           # Tunable parameters
      lingq_import/           # LingQ import client
    scripts/
      subtitle_word_frequency.py  # Main subtitle analysis CLI
      lingq_bulk_import.py    # LingQ bulk import CLI
    anki_tools/               # Anki deck manipulation
    audio/                    # TTS generation (AllTalk)
    data/
      input/                  # Source word lists
      output/                 # Generated reports, CSVs
      audio/                  # TTS audio files from AllTalk
      word_lists/             # Per-language YAML word lists
  venv/                       # Virtual environment (NEVER install to system)
  pyproject.toml              # Package configuration and dependencies
  README.md                   # Full install guide
  CODEFLOW.md                 # Full pipeline documentation
```

## Configuration

- Tunable params: src/ai_assisted_language_quizzer/core/subtitle_analyzer/config.yaml
- Secrets: .env (DEEPL_API_KEY, MINIMAX_API_KEY, etc.) -- gitignored
- Scripts load config via YAML with _get_default_config() fallback; CLI flags override config

## Do Not

- Do not install packages to the host system -- always use venv/
- Do not commit .env or any file with actual API keys
- Do not add deps without good reason -- check pyproject.toml first
- Do not put imports inside function bodies
- Do not increase function length past 50 lines without refactoring first

## Testing

- No pytest suite. Manual validation only.
- Run scripts with --help and small input to smoke test.
- After editing Python: grep for indented imports, verify import at top succeeds.

<!-- Guidelines:
     - Keep the whole file under 150 lines
     - Focus on what an agent needs to be immediately productive
     - Commands must be copy-paste ready
     - File structure should match current reality (update when structure changes)
-->