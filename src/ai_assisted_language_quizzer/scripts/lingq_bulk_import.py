#!/usr/bin/env python3
"""
LingQ bulk import: upload SRT (+ optional audio) pairs as private lessons.

Scans a directory for .srt files, resolves a LingQ course by name, and
creates one lesson per subtitle file.
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import yaml
from dotenv import load_dotenv

from ai_assisted_language_quizzer.core.lingq_import import Lesson, LingQClient
from ai_assisted_language_quizzer.core.lingq_import.test_harness import LingQTestHarness
from ai_assisted_language_quizzer.core.subtitle_analyzer import SRTParser
from ai_assisted_language_quizzer.paths import PROJECT_ROOT

load_dotenv()


class LingQBulkImporter:
    """Scan directories for SRT/audio pairs and bulk-create LingQ lessons."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize importer with YAML configuration.

        Args:
            config_path: Path to config YAML, or None for default location.

        Returns:
            None
        """
        self.config = self._load_config(config_path)
        defaults = self._get_default_config()["lingq_import"]
        lingq = self.config.setdefault("lingq_import", {})
        for key, val in defaults.items():
            lingq.setdefault(key, val)
        self.srt_parser = SRTParser()

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent
                / "core"
                / "subtitle_analyzer"
                / "config.yaml"
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

    def _get_default_config(self) -> Dict:
        """Return default configuration with lingq_import section only."""
        return {
            "lingq_import": {
                "api_key_env": "LINGQ_API_KEY",
                "default_language": "es",
                "default_status": "private",
                "audio_extensions": [".mp3", ".m4a", ".wav", ".ogg"],
                "api_base_url": "https://www.lingq.com/api/v3",
                "test_course_name": "Your Test Course",
                "test_data_dir": str(
                    PROJECT_ROOT / "data" / "test_lingq" / "normalized"
                ),
            }
        }

    def _normalize_key(self, s: str) -> str:
        """
        Normalize a string for fuzzy matching.

        Lowercases, replaces underscores/hyphens with spaces, strips trailing
        language suffix (.xx), splits CamelCase words, and collapses multiple
        spaces into one.

        Args:
            s: The raw string (typically a filename stem or lesson title).

        Returns:
            Normalized string suitable for fuzzy lookup.
        """
        result = s.lower()
        result = result.replace("_", " ").replace("-", " ")
        # Remove trailing .xx language suffix (e.g., .es, .en)
        result = re.sub(r"\.[a-z]{2}$", "", result, flags=re.IGNORECASE)
        # Collapse runs of underscores/hyphens into single spaces before CamelCase
        # split, so "Inside_Job" and "InsideJob" converge to the same key
        result = re.sub(r"[\s_\-]+", " ", result)
        # Split CamelCase transitions: "InsideJobS01E07" → "Inside Job S01E07"
        result = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z](?=[A-Z][a-z]))", " ", result)
        # Split transitions between letters and digits: "s01e07" → "s 01 e 07"
        result = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", result)
        # Collapse multiple spaces
        result = re.sub(r"\s+", " ", result)
        return result.strip()

    def _make_title(self, s: str) -> str:
        """
        Convert a filename stem to a title that matches LingQ naming conventions.

        Replaces underscores/hyphens with spaces, strips the trailing language
        suffix (.xx), capitalizes each word, and collapses multiple spaces.

        Args:
            s: The raw filename stem (e.g. ``Inside_Job_S01E07.es``).

        Returns:
            Title-cased string suitable as a LingQ lesson title
            (e.g. ``Inside Job S01E07``).
        """
        result = s.replace("_", " ").replace("-", " ")
        result = re.sub(r"\.[a-z]{2}$", "", result, flags=re.IGNORECASE)
        result = re.sub(r"\s+", " ", result)
        result = " ".join(
            word[0].upper() + word[1:] if word else "" for word in result.split(" ")
        )
        return result.strip()

    def _find_audio_file(self, srt_path: Path, extensions: List[str]) -> Optional[Path]:
        """Return first audio file with same stem as srt_path, or None."""
        parent = srt_path.parent
        stem = srt_path.stem
        for ext in extensions:
            candidate = parent / f"{stem}{ext}"
            if candidate.is_file():
                return candidate
        return None

    def _scan_directory(self, directory: Path) -> List[Tuple[Path, Optional[Path]]]:
        """Find SRT files and optional matching audio; print counts."""
        lingq = self.config["lingq_import"]
        exts = list(lingq["audio_extensions"])
        srts = sorted(directory.glob("*.srt"))
        pairs: List[Tuple[Path, Optional[Path]]] = []
        with_audio = 0
        for srt_path in srts:
            audio = self._find_audio_file(srt_path, exts)
            if audio is not None:
                with_audio += 1
            pairs.append((srt_path, audio))
        print(
            f"Found {len(pairs)} SRT file(s), "
            f"{with_audio} with matching audio in {directory}."
        )
        return pairs

    def _upload_single(
        self,
        client: LingQClient,
        srt_path: Path,
        audio_path: Optional[Path],
        language: str,
        collection_id: int,
        status: str,
        title: str,
        dry_run: bool,
    ) -> str:
        """Parse one SRT and create lesson or dry-run; returns outcome key."""
        try:
            lines = self.srt_parser.parse_file(srt_path)
        except Exception as e:
            print(f"  ✗ {srt_path.stem}: {e}")
            return "failed"
        text = "\n".join(lines)
        if dry_run:
            if audio_path:
                print(f"  [dry-run] Would upload: {title} + {audio_path.name}")
            else:
                print(f"  [dry-run] Would upload: {title} (text only)")
            return "skipped"
        try:
            client.create_lesson(
                language=language,
                title=title,
                text=text,
                collection_id=collection_id,
                audio_path=audio_path,
                status=status,
            )
            print(f"  ✓ {title}")
            return "success"
        except Exception as e:
            print(f"  ✗ {title}: {e}")
            return "failed"

    def _resolve_client_and_collection(
        self,
        course_name: str,
        language: Optional[str],
    ) -> Union[Dict, Tuple[LingQClient, int, str]]:
        """Build client and resolve course pk, or return an error summary dict."""
        lingq = self.config["lingq_import"]
        resolved_lang = language or lingq["default_language"]
        api_key = os.getenv(lingq["api_key_env"])
        if not api_key:
            print(
                f"Error: Missing API key. Set {lingq['api_key_env']} in the environment."
            )
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "no_api_key",
            }
        client = LingQClient(api_key, lingq["api_base_url"])
        course = client.find_course_by_name(resolved_lang, course_name)
        if course is None:
            print(f"No course matching '{course_name}'. Available courses:")
            for c in client.list_courses(resolved_lang):
                print(f"  - {c.title}")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "no_course",
            }
        return (client, course.pk, resolved_lang)

    def list_and_confirm_course(
        self,
        course_name: str,
        language: Optional[str],
    ) -> Optional[Tuple[LingQClient, int, str]]:
        """
        List available LingQ courses and let the user confirm or select one.

        For interactive use (TTY stdin): displays numbered list and prompts.
        If only one course matches ``course_name`` as a substring, auto-confirms
        that course unless the user declines.

        For non-interactive use (pipe/non-TTY): returns None immediately,
        allowing callers to fall back to the original non-interactive flow.

        Args:
            course_name: Substring to match against course titles.
            language: LingQ language code; defaults to config.

        Returns:
            Tuple of (client, course_pk, resolved_lang) if confirmed, or None
            if the user declined / non-interactive mode.
        """
        lingq = self.config["lingq_import"]
        resolved_lang = language or lingq["default_language"]
        api_key = os.getenv(lingq["api_key_env"])
        if not api_key:
            print(
                f"Error: Missing API key. Set {lingq['api_key_env']} in the environment."
            )
            return None
        client = LingQClient(api_key, lingq["api_base_url"])

        courses = client.list_courses(resolved_lang)

        # Filter to courses matching the name (case-insensitive substring)
        needle = course_name.casefold()
        matching = [c for c in courses if needle in c.title.casefold()]

        if not matching:
            print(f"No courses matching '{course_name}'. Available courses:")
            for c in courses:
                print(f"  - {c.title}")
            return None

        # Auto-confirm if only one match and stdin is a TTY
        if len(matching) == 1:
            course = matching[0]
            if sys.stdin.isatty():
                print(f"Found exactly one matching course: '{course.title}'")
                print("Proceeding with this course.")
            return (client, course.pk, resolved_lang)

        # Show numbered list
        print("Available courses:")
        for i, c in enumerate(matching, 1):
            print(f"  {i}. {c.title}")

        if not sys.stdin.isatty():
            # Non-interactive: cannot prompt, so abort
            print("Multiple matches found and stdin is not a TTY. Cannot prompt.")
            print(
                "Use --yes to skip confirmation or use a more specific --course name."
            )
            return None

        while True:
            try:
                line = input(
                    f"Select course number [1-{len(matching)}] or 'q' to quit: "
                ).strip()
                if line.lower() == "q":
                    return None
                idx = int(line) - 1
                if 0 <= idx < len(matching):
                    course = matching[idx]
                    print(f"Selected: {course.title}")
                    return (client, course.pk, resolved_lang)
                else:
                    print(f"Please enter a number between 1 and {len(matching)}.")
            except ValueError:
                print("Invalid input. Enter a number or 'q' to quit.")

    def _scan_audio_files(self, directory: Path, extensions: List[str]) -> List[Path]:
        """Return sorted list of audio files matching configured extensions."""
        lingq = self.config["lingq_import"]
        exts = list(lingq["audio_extensions"])
        files: List[Path] = []
        for ext in exts:
            files.extend(sorted(directory.glob(f"*{ext}")))
        return sorted(files, key=lambda p: p.name)

    def _patch_single_audio(
        self,
        client: LingQClient,
        audio_path: Path,
        lesson_pk: int,
        language: str,
        dry_run: bool,
    ) -> str:
        """Patch one lesson's audio or dry-run; returns outcome key."""
        title = audio_path.stem
        if dry_run:
            print(f"  [dry-run] Would patch audio for: {title}")
            return "skipped"
        try:
            client.patch_lesson_audio(language, lesson_pk, audio_path)
            print(f"  ✓ {title}")
            return "patched"
        except Exception as e:
            print(f"  ✗ {title}: {e}")
            return "failed"

    def replace_audio(
        self,
        directory: Path,
        course_name: str,
        language: Optional[str] = None,
        dry_run: bool = False,
        yes: bool = False,
    ) -> Dict:
        """
        Replace audio on existing lessons matched by title from audio files.

        Args:
            directory: Folder containing audio files.
            course_name: Case-insensitive substring to match LingQ course title.
            language: LingQ language code; defaults to config.
            dry_run: If True, only print planned patches.
            yes: If True, skip all confirmation prompts and proceed.

        Returns:
            Summary dict with keys total, matched, patched, failed, skipped,
            unmatched, and optionally error for early exit.
        """
        # Use interactive course selection if stdin is a TTY and --yes is not set
        if sys.stdin.isatty() and not yes:
            prep = self.list_and_confirm_course(course_name, language)
            if prep is None:
                return {
                    "total": 0,
                    "matched": 0,
                    "patched": 0,
                    "failed": 0,
                    "skipped": 0,
                    "unmatched": 0,
                    "error": "course_not_confirmed",
                }
        else:
            prep = self._resolve_client_and_collection(course_name, language)
            if isinstance(prep, dict):
                return prep

        client, course_pk, resolved_lang = prep

        lessons = client.list_lessons(resolved_lang, course_pk)
        # Build lookup dict using normalized keys
        title_to_lesson: Dict[str, Lesson] = {
            self._normalize_key(l.title): l for l in lessons
        }

        audio_files = self._scan_audio_files(
            directory, list(self.config["lingq_import"]["audio_extensions"])
        )
        if not audio_files:
            print("No audio files found.")
            return {
                "total": 0,
                "matched": 0,
                "patched": 0,
                "failed": 0,
                "skipped": 0,
                "unmatched": 0,
            }

        # Collect proposed patches
        proposed: List[Tuple[Path, Lesson]] = []
        unmatched: List[Path] = []
        for audio_path in audio_files:
            key = self._normalize_key(audio_path.stem)
            lesson = title_to_lesson.get(key)
            if lesson is None:
                unmatched.append(audio_path)
            else:
                proposed.append((audio_path, lesson))

        # Print preview table
        print("\n=== Proposed Matches ===")
        print(f"{'Audio File':<40} | {'Lesson Title':<40}")
        print("-" * 83)
        for audio_path, lesson in proposed:
            print(f"{audio_path.name:<40} → {lesson.title:<40}")
        if unmatched:
            print(
                f"\n{len(unmatched)} unmatched audio file(s) (no matching lesson found):"
            )
            for af in unmatched:
                print(f"  ⚠ {af.name}")

        matched_count = len(proposed)
        unmatched_count = len(unmatched)
        total_count = len(audio_files)
        print(
            f"\nProposed matches: {total_count} audio files → {matched_count} lessons."
        )
        if unmatched_count > 0:
            print(f"{unmatched_count} unmatched audio file(s).")

        # Ask for confirmation unless --yes is set or stdin is not a TTY
        if not yes and sys.stdin.isatty():
            response = input("Proceed? [y/N] ").strip().lower()
            if response not in ("y", "yes"):
                print("Aborted.")
                return {
                    "total": total_count,
                    "matched": matched_count,
                    "patched": 0,
                    "failed": 0,
                    "skipped": 0,
                    "unmatched": unmatched_count,
                    "error": "aborted",
                }
        elif not yes and not sys.stdin.isatty():
            print(
                "stdin is not a TTY; skipping confirmation. Use --yes to force proceed."
            )
            return {
                "total": total_count,
                "matched": matched_count,
                "patched": 0,
                "failed": 0,
                "skipped": 0,
                "unmatched": unmatched_count,
                "error": "non_interactive_requires_yes",
            }

        # Execute patches
        summary: Dict = {
            "total": total_count,
            "matched": matched_count,
            "patched": 0,
            "failed": 0,
            "skipped": 0,
            "unmatched": unmatched_count,
        }
        for audio_path, lesson in proposed:
            outcome = self._patch_single_audio(
                client, audio_path, lesson.pk, resolved_lang, dry_run
            )
            summary[outcome] += 1
            if not dry_run:
                time.sleep(5)

        if unmatched:
            print(f"\nWarning: {len(unmatched)} audio file(s) had no matching lesson.")
        return summary

    def import_lessons(
        self,
        directory: Path,
        course_name: str,
        language: Optional[str] = None,
        dry_run: bool = False,
        lesson_path: Optional[Path] = None,
        audio_path: Optional[Path] = None,
    ) -> Dict:
        """
        Resolve course and upload each SRT in directory as a lesson.

        When lesson_path is set, imports a single SRT file directly without
        scanning a directory. When lesson_path is None, falls back to
        directory-scanning bulk behavior.

        Args:
            directory: Folder containing .srt (and optional audio) files.
            course_name: Case-insensitive substring to match LingQ course title.
            language: LingQ language code; defaults to config.
            dry_run: If True, only print planned uploads.
            lesson_path: Path to a single .srt file (single-lesson mode).
            audio_path: Path to a single audio file for that lesson (optional).

        Returns:
            Summary dict with keys total, success, failed, skipped, and
            optionally error for early exit.
        """
        # Single-lesson mode: import one SRT directly
        if lesson_path is not None:
            return self._import_single_lesson(
                course_name=course_name,
                language=language,
                dry_run=dry_run,
                lesson_path=lesson_path,
                audio_path=audio_path,
            )

        # Bulk directory-scan mode (existing behavior)
        prep = self._resolve_client_and_collection(course_name, language)
        if isinstance(prep, dict):
            return prep
        client, collection_id, resolved_lang = prep

        # Fetch existing lessons to derive authoritative titles
        existing = client.list_lessons(resolved_lang, collection_id)
        stem_to_title: Dict[str, str] = {
            self._normalize_key(l.title): l.title for l in existing
        }

        pairs = self._scan_directory(directory)
        if not pairs:
            print("No SRT files found.")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "no_srt",
            }
        lingq = self.config["lingq_import"]
        status = lingq["default_status"]
        summary: Dict = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }
        for srt_path, audio_path in pairs:
            summary["total"] += 1
            key = self._normalize_key(srt_path.stem)
            title = stem_to_title.get(key, self._make_title(srt_path.stem))
            outcome = self._upload_single(
                client,
                srt_path,
                audio_path,
                resolved_lang,
                collection_id,
                status,
                title,
                dry_run,
            )
            summary[outcome] += 1
            if not dry_run:
                time.sleep(5)
        return summary

    def _import_single_lesson(
        self,
        course_name: str,
        language: Optional[str],
        dry_run: bool,
        lesson_path: Path,
        audio_path: Optional[Path],
    ) -> Dict:
        """Import a single SRT file as one lesson, optionally with audio."""
        # Validate lesson file
        if not lesson_path.exists():
            print(f"❌ Lesson file not found: {lesson_path}")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "lesson_not_found",
            }
        if lesson_path.suffix.lower() != ".srt":
            print(f"❌ Lesson file must have .srt extension: {lesson_path}")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "error": "not_srt",
            }

        # Resolve course
        prep = self._resolve_client_and_collection(course_name, language)
        if isinstance(prep, dict):
            return prep
        client, collection_id, resolved_lang = prep

        # Fetch existing lessons to derive authoritative titles
        existing_lessons = client.list_lessons(resolved_lang, collection_id)
        stem_to_title: Dict[str, str] = {
            self._normalize_key(l.title): l.title for l in existing_lessons
        }

        # Find audio if not provided
        if audio_path is None:
            exts = list(self.config["lingq_import"]["audio_extensions"])
            audio_path = self._find_audio_file(lesson_path.with_suffix(""), exts)

        key = self._normalize_key(lesson_path.stem)
        title = stem_to_title.get(key, self._make_title(lesson_path.stem))
        summary: Dict = {
            "total": 1,
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }
        lingq = self.config["lingq_import"]
        status = lingq["default_status"]

        outcome = self._upload_single(
            client,
            lesson_path,
            audio_path,
            resolved_lang,
            collection_id,
            status,
            title,
            dry_run,
        )
        summary[outcome] += 1
        return summary


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for LingQ bulk import."""
    parser = argparse.ArgumentParser(
        description="Bulk-import SRT (+ audio) files as LingQ lessons.",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=Path,
        default=None,
        required=False,
        help="Directory containing .srt (and optional audio) files",
    )
    parser.add_argument(
        "--course",
        "-C",
        required=True,
        help="LingQ course name (case-insensitive partial match)",
    )
    parser.add_argument(
        "--language",
        "-l",
        default=None,
        help="Two-letter LingQ language code (default from config)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=None,
        help="Path to YAML config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without calling the API",
    )
    parser.add_argument(
        "--replace-audio",
        action="store_true",
        help="Replace audio on existing lessons matching by title",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip all confirmation prompts (for scripting)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the LingQ importer test harness on test data",
    )
    parser.add_argument(
        "--lesson",
        "-L",
        type=Path,
        default=None,
        dest="lesson_path",
        help="Path to a single .srt file to import as a lesson (instead of scanning --dir)",
    )
    parser.add_argument(
        "--audio",
        "-a",
        type=Path,
        default=None,
        dest="audio_path",
        help="Path to a single audio file to attach to the lesson (optional)",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point: run bulk import or exit with status code."""
    try:
        args = parse_arguments()

        # Validate that either --dir or --lesson is provided
        if args.dir is None and args.lesson_path is None:
            print("Error: either --dir/-d or --lesson/-L must be provided")
            return 1
        if args.lesson_path is not None and args.replace_audio:
            print("Error: --lesson and --replace-audio cannot be used together")
            return 1

        if args.test:
            harness = LingQTestHarness(args.config)
            result = harness.run_replace_audio_test(
                course_name=args.course,
                dry_run=args.dry_run,
            )
            return 0 if not result.get("errors") else 1

        importer = LingQBulkImporter(args.config)
        if args.replace_audio:
            result = importer.replace_audio(
                directory=args.dir.resolve(),
                course_name=args.course,
                language=args.language,
                dry_run=args.dry_run,
                yes=args.yes,
            )
        elif args.lesson_path:
            # In single-lesson mode, use the SRT's parent directory for audio lookup
            lesson_dir = args.lesson_path.parent.resolve()
            result = importer.import_lessons(
                directory=lesson_dir,
                course_name=args.course,
                language=args.language,
                dry_run=args.dry_run,
                lesson_path=args.lesson_path,
                audio_path=args.audio_path,
            )
        else:
            result = importer.import_lessons(
                directory=args.dir.resolve(),
                course_name=args.course,
                language=args.language,
                dry_run=args.dry_run,
            )
        if result.get("error"):
            return 1
        if result.get("failed", 0) > 0:
            return 1
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
