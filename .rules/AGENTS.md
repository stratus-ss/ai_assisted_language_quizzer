# AI Assisted Language Quizzer — Agent Guidelines

## Project Overview

- **Language**: Python ^3.11
- **Package manager**: pip (`requirements.txt`)
- **Virtual environment**: `venv/` (not Poetry)
- **Key libraries**: deepl, soundfile, python-dotenv, pyyaml, spacy

## Dependency Management

- **Never install packages on the host system. Always use the project `venv/`.**
- Install dependencies with: `pip install -r requirements.txt` (inside the venv)
- Activate the venv with: `source venv/bin/activate` before running pip or python scripts
- Do not use Poetry, conda, or other alternative package managers

## Project Structure

```
src/ai_assisted_language_quizzer/
├── core/
│   ├── subtitle_analyzer/   # Library classes (single-responsibility)
│   │   ├── srt_parser.py
│   │   ├── word_processor.py
│   │   ├── stopword_manager.py
│   │   ├── frequency_analyzer.py
│   │   ├── report_generator.py
│   │   └── __init__.py
│   └── lingq_import/        # LingQ API client
├── scripts/                 # CLI entry points (argparse-based)
├── anki_tools/             # Anki deck manipulation
├── audio/                  # TTS generation (AllTalk)
data/
├── input/              # Source word lists
├── output/             # Generated reports, CSVs
└── word_lists/         # Per-language YAML word lists
```

**Pipeline flow**: SRT parsing → word processing → stopword filtering → frequency analysis → (lemmatization) → (LLM curation) → report generation → Anki export → TTS

---

## Code Style

### Imports
- ALL import statements go at the top of the file. Never import inside a function body.
- After editing any Python file, verify no imports exist inside function bodies.
- When adding type hints from `typing` (e.g., `Dict`, `List`, `Optional`, `Any`), verify those names appear in the file's `from typing import` statement.
- Never use lowercase `any` in type annotations. Always use `Any` from `typing`.

### Functions and Classes
- Prefer classes over bare functions for any module with state or multi-step logic.
- Maximum function length: **50 lines** (excluding docstrings).
- Maximum cyclomatic complexity per function: **15**.
- Maximum 4 edit points per task in a single file.
- Use `Path` from `pathlib` instead of raw string paths.
- Use type hints on all public method signatures.

### Naming
- File naming: `snake_case.py` matching the class in `PascalCase`
- Class: `WordProcessor` in `word_processor.py`
- Public methods have docstrings with Args/Returns sections.

### Refactor Before Extend
- If adding functionality would cause a method to exceed 50 lines, first refactor into smaller helpers, then add the new functionality.
- Do not combine structural refactoring with feature addition in the same task.

---

## Configuration Pattern

- All tunable parameters belong in `src/ai_assisted_language_quizzer/core/subtitle_analyzer/config.yaml`.
- Scripts load config via YAML with a `_get_default_config()` fallback.
- CLI flags override config values; config values override defaults.
- New features MUST add their config section to `config.yaml` with comments.

---

## Secrets and Environment

- API keys and service URLs are stored in `.env` (gitignored).
- Reference via `os.getenv()` after `load_dotenv()`.
- Config YAML stores the env var NAME (e.g., `api_key_env: "MINIMAX_API_KEY"`), never the value.
- Never commit `.env` contents.

---

## Output Patterns

- Generated files go in `data/output/`.
- CSV reports include headers: `word,frequency,percentage`
- Anki word lists are tab-separated for direct import.
- Markdown summaries use tables: `| Rank | Word | Frequency | Percentage |`

---

## Pipeline Layer Mapping

When planning tasks, scope to ONE layer per task:

1. **Types/Models** — dataclasses, TypedDicts, config schema
2. **Parsing** — SRT file reading (`srt_parser.py`)
3. **Processing** — tokenization, normalization, lemmatization (`word_processor.py`)
4. **Analysis** — frequency counting (`frequency_analyzer.py`)
5. **Curation** — LLM integration (`llm_curator.py`)
6. **Output** — reports, Anki export, TTS
7. **Integration** — wiring into `SubtitleFrequencyAnalyzer.analyze()`

---

## Script Entry Point Pattern

Follow `src/ai_assisted_language_quizzer/scripts/subtitle_word_frequency.py`:

```python
class SubtitleFrequencyAnalyzer:
    def __init__(self, config_path):
        # load YAML config, initialize components

    def analyze(self):
        # numbered steps with progress output

def parse_arguments():
    # argparse namespace

def main():
    # wires args → class → execution

if __name__ == "__main__":
    sys.exit(main())
```

---

## Plan Authoring Rules (for task specs)

Each task in a plan MUST include:

- **INTENT**: Why the task exists, what problem it solves
- **STRUCTURE**: What to create — method signatures, file paths, class names
- **SCHEMA**: Exact field names, types, and order (when applicable)
- **CONTEXT**: Data sources with class names, method names, file paths
- **CONSTRAINTS**: Which files to modify, patterns to follow, limits
- **NAMING**: File names, class names, method names, variable conventions
- **DON'T**: What NOT to do — no new files, no new abstractions, no features not specified

Each task:
- Has a single, focused goal
- Is ordered to minimize conflicts
- Includes a verification step (run the script, smoke test)
- For .py file modifications, includes `grep` check for indented imports

Final task MUST include a full end-to-end smoke test. `py_compile` alone is insufficient.

---

## Verification Checklist

After implementing any task:

1. Run: `grep -n '^\s\+import \|^\s\+from .* import' FILE` — must return zero matches (no indented imports)
2. Run: `python -c "from module import Class"` — must succeed
3. Run the script with `--help` — must work
4. For new classes, smoke test with real data inside the project venv

---

## Readability Over Brevity

- Prefer straightforward solutions over clever one-liners.
- Avoid premature abstraction. Do not create base classes or factory patterns unless there are 3+ concrete implementations.