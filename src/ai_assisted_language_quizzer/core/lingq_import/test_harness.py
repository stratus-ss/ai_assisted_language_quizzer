"""
LingQ Test Harness.

Single-responsibility orchestrator for testing LingQ importer with normalized
audio files (dry-run + replace-audio). Follows SubtitleFrequencyAnalyzer
pattern from subtitle_word_frequency.py exactly.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv


load_dotenv()


from ai_assisted_language_quizzer.paths import PROJECT_ROOT

from .client import Course, Lesson, LingQClient


class LingQTestHarness:
    """Single-responsibility test class for LingQ importer (one layer only)."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize following SubtitleFrequencyAnalyzer.__init__ exactly."""
        self.config = self._load_config(config_path)
        from scripts.lingq_bulk_import import LingQBulkImporter

        self.importer = LingQBulkImporter(config_path)
        self.client: Optional[LingQClient] = None
        lingq = self.config.get("lingq_import", {})
        self.test_dir: Path = Path(
            lingq.get("test_data_dir", str(PROJECT_ROOT / "data" / "test_lingq" / "normalized"))
        )

    def _load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Exact _load_config pattern from subtitle_word_frequency.py and lingq_bulk_import.py."""
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent / "subtitle_analyzer" / "config.yaml"
            )
        if not config_path.exists():
            print(f"⚠️  Config file not found: {config_path}")
            print("Using default configuration.")
            return self._get_default_config()
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if config is None:
                return self._get_default_config()
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            print("Using default configuration.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Default config referencing Task 2 test values (for Task 4)."""
        return {
            "lingq_import": {
                "api_key_env": "LINGQ_API_KEY",
                "default_language": "es",
                "default_status": "private",
                "api_base_url": "https://www.lingq.com/api/v3",
                "test_course_name": "Your Test Course",
                "test_data_dir": str(PROJECT_ROOT / "data" / "test_lingq" / "normalized"),
            }
        }

    def setup_test_data(self) -> None:
        """Setup test data via shutil copy from scratch_pad (per plan; <50 lines)."""
        source = Path(
            "/home/stratus/git_projects/scratch_pad/audio_normilization/audionorm/recordings/normalized"
        )
        target = self.test_dir.absolute()
        target.mkdir(parents=True, exist_ok=True)
        if source.exists() and len(list(target.glob("*.mp3"))) == 0:
            print("Copying normalized audios for test...")
            for audio in source.glob("*.mp3"):
                shutil.copy(audio, target / audio.name)
                print(f"✓ Copied {audio.name}")
        print(
            f"✓ Test data ready in {target} ({len(list(target.glob('*.mp3')))} files)"
        )

    def run_replace_audio_test(
        self, course_name: Optional[str] = None, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Run replace-audio test (dry_run default); uses Task 2 config, client patterns, exact prints (<50 lines)."""
        load_dotenv()
        lingq = self.config.get("lingq_import", {})
        api_key = os.getenv(lingq.get("api_key_env", "LINGQ_API_KEY"))
        if not api_key:
            raise ValueError("LINGQ_API_KEY missing from .env")
        course_name = course_name or lingq.get("test_course_name", "Your Test Course")
        language = lingq.get("default_language", "es")
        self.client = LingQClient(api_key, lingq.get("api_base_url"))
        self.setup_test_data()
        test_dir = self.test_dir
        summary: Dict[str, Any] = {
            "course": course_name,
            "dry_run": dry_run,
            "processed": 0,
            "updated": 0,
            "errors": [],
        }
        print(
            f"Starting LingQ replace-audio test for '{course_name}' (dry_run={dry_run})"
        )
        course = self.client.find_course_by_name(language, course_name)
        if not course:
            print(f"[dry-run] Would create course '{course_name}'")
            summary["course_created"] = True
        else:
            print(f"✓ Found course '{course.title}' (pk={course.pk})")
            summary["course_pk"] = course.pk
            lessons = self.client.list_lessons(language, course.pk)
            audios = list(test_dir.glob("*.mp3"))[:3]  # limit for test
            for audio_path in audios:
                stem = audio_path.stem
                print(f"✓ Processing audio: {audio_path.name} (stem={stem})")
                matched = any(
                    stem.lower() in lesson.title.lower() for lesson in lessons
                )
                if dry_run:
                    print(f"[dry-run] Would patch lesson audio for stem '{stem}'")
                elif matched and self.client:
                    # Use cleaned client from Task 1 (no full importer replace logic per constraints)
                    try:
                        self.client.patch_lesson_audio(
                            language, lessons[0].pk, audio_path
                        )  # example match
                        summary["updated"] += 1
                        print(f"✓ Patched audio for {stem}")
                    except Exception as e:
                        summary["errors"].append(str(e))
                        print(f"❌ Error patching {stem}: {e}")
                summary["processed"] += 1
        print("Test complete. Summary:", summary)
        return summary
