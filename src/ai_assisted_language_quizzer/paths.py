#!/usr/bin/env python3
"""Centralized path resolution for ai_assisted_language_quizzer.

Provides PROJECT_ROOT and DATA_DIR based on the location of this file,
with optional environment variable override.

Usage:
    from ai_assisted_language_quizzer.paths import PROJECT_ROOT, DATA_DIR

Paths are relative to the repo root (parent of src/).
"""

import os
from pathlib import Path

# Base directory: this file lives at src/ai_assisted_language_quizzer/paths.py
# PROJECT_ROOT is parents[2] from here (src/ai_assisted_language_quizzer/paths.py -> src/ -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data directory at repo root (runtime data: word lists, test fixtures, output)
# Can be overridden via AI_LANG_QUIZ_DATA_DIR env var
DATA_DIR = Path(os.environ.get("AI_LANG_QUIZ_DATA_DIR", str(PROJECT_ROOT / "data")))

# Subdirectories
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
TEST_LINGQ_DIR = DATA_DIR / "test_lingq" / "normalized"
SUBTITLES_DIR = PROJECT_ROOT / "subtitles"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"  # legacy audio path



def resolve_config_paths(config: dict) -> dict:
    """Resolve __REPO_ROOT__ tokens in config paths to actual PROJECT_ROOT."""
    import copy
    resolved = copy.deepcopy(config)
    repo_root = str(PROJECT_ROOT)
    def _resolve(value):
        if isinstance(value, str) and '__REPO_ROOT__' in value:
            return value.replace('__REPO_ROOT__', repo_root)
        return value
    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_walk(x) for x in obj]
        else:
            return _resolve(obj)
    return _walk(resolved)
