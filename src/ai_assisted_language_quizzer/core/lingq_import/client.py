"""
LingQ API v3 HTTP client.

Encapsulates authentication, course and lesson listing, lesson creation
with optional multipart audio, and PATCH updates for lesson audio.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


@dataclass
class Course:
    pk: int
    title: str
    description: str
    level: str


@dataclass
class Lesson:
    pk: int
    title: str
    collection_id: int
    audio_url: Optional[str]


class LingQClient:
    """Perform LingQ API v3 operations using a shared authenticated session."""

    def __init__(
        self, api_key: str, base_url: str = "https://www.lingq.com/api/v3"
    ) -> None:
        """
        Initialize the client with API credentials.

        Args:
            api_key: LingQ API token value.
            base_url: Root URL for API v3 (no trailing slash required).

        Returns:
            None
        """
        self.api_key: str = api_key
        self.base_url: str = base_url
        self._session: requests.Session = requests.Session()
        self._session.headers.update({"Authorization": f"Token {api_key}"})

    def list_courses(self, language: str) -> List[Course]:
        """
        List all courses for the authenticated user in the given language.

        Args:
            language: LingQ language code (e.g. ``es``).

        Returns:
            All courses from paginated ``collections/my/`` results.

        Raises:
            requests.HTTPError: If any response status is not 2xx.
        """
        courses: List[Course] = []
        url: Optional[str] = f"{self.base_url.rstrip('/')}/{language}/collections/my/"
        while url:
            response = self._session.get(url)
            response.raise_for_status()
            payload = response.json()
            for row in payload.get("results", []):
                raw_pk = row.get("pk") or row.get("id")
                courses.append(
                    Course(
                        pk=int(raw_pk) if raw_pk is not None else 0,
                        title=str(row.get("title", "")),
                        description=str(row.get("description", "")),
                        level=str(row.get("level", "")),
                    )
                )
            next_url = payload.get("next")
            url = str(next_url) if next_url else None
        return courses

    def find_course_by_name(self, language: str, name: str) -> Optional[Course]:
        """
        Return the first course whose title contains ``name`` (case-insensitive).

        Args:
            language: LingQ language code.
            name: Substring to match against course titles.

        Returns:
            Matching ``Course``, or ``None`` if no title matches.
        """
        needle = name.casefold()
        for course in self.list_courses(language):
            if needle in course.title.casefold():
                return course
        return None

    def list_lessons(self, language: str, course_id: int) -> List[Lesson]:
        """
        List lessons for a course from the dedicated lessons endpoint.

        Args:
            language: LingQ language code.
            course_id: Course (collection) primary key.

        Returns:
            Lessons parsed from paginated ``collections/{id}/lessons/`` results.

        Raises:
            requests.HTTPError: If the response status is not 2xx.
        """
        lessons: List[Lesson] = []
        url: Optional[str] = (
            f"{self.base_url.rstrip('/')}/{language}/collections/{course_id}/lessons/"
        )
        while url:
            response = self._session.get(url)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("results", []):
                raw_id = item.get("id", item.get("pk"))
                pk = int(raw_id) if raw_id is not None else 0
                title = str(item.get("title", ""))
                raw_coll = item.get("collectionId", item.get("collection_id"))
                coll = int(raw_coll) if raw_coll is not None else course_id
                lessons.append(
                    Lesson(
                        pk=pk,
                        title=title,
                        collection_id=coll,
                        audio_url=self._lesson_audio_url(item),
                    )
                )
            next_url = payload.get("next")
            url = str(next_url) if next_url else None
        return lessons

    def create_lesson(
        self,
        language: str,
        title: str,
        text: str,
        collection_id: int,
        audio_path: Optional[Path] = None,
        status: str = "private",
    ) -> Dict[str, Any]:
        """
        Create a lesson, optionally uploading audio as multipart form data.

        Args:
            language: LingQ language code.
            title: Lesson title.
            text: Lesson text content.
            collection_id: Target course ``pk`` (sent as ``collection`` field).
            audio_path: Optional path to an MPEG audio file to attach.
            status: Lesson visibility (default ``private``).

        Returns:
            Parsed JSON body from the API response.

        Raises:
            requests.HTTPError: If the response status is not 2xx.
        """
        fields: List[Any] = [
            ("title", title),
            ("text", text),
            ("status", status),
            ("collection", str(collection_id)),
            ("save", "true"),
        ]
        audio_file = None
        if audio_path is not None and audio_path.exists():
            audio_file = open(audio_path, "rb")
            fields.append(("audio", (audio_path.name, audio_file, "audio/mpeg")))
        try:
            encoder = MultipartEncoder(fields=fields)  # type: ignore
            post_url = f"{self.base_url.rstrip('/')}/{language}/lessons/import/"
            resp = self._session.post(
                post_url,
                data=encoder,
                headers={"Content-Type": encoder.content_type},
            )
            resp.raise_for_status()
            return resp.json()
        finally:
            if audio_file is not None:
                audio_file.close()

    def patch_lesson_audio(
        self, language: str, lesson_id: int, audio_path: Path
    ) -> Dict[str, Any]:
        """
        Replace lesson audio via multipart PATCH.

        Args:
            language: LingQ language code.
            lesson_id: Lesson primary key.
            audio_path: Path to the new MPEG audio file.

        Returns:
            Parsed JSON body from the API response.

        Raises:
            requests.HTTPError: If the response status is not 2xx.
        """
        audio_file = open(audio_path, "rb")
        try:
            encoder = MultipartEncoder(  # type: ignore
                fields=[
                    ("audio", (audio_path.name, audio_file, "audio/mpeg")),
                ]
            )
            patch_url = f"{self.base_url.rstrip('/')}/{language}/lessons/{lesson_id}/"
            resp = self._session.patch(
                patch_url,
                data=encoder,
                headers={"Content-Type": encoder.content_type},
            )
            resp.raise_for_status()
            return resp.json()
        finally:
            audio_file.close()

    def _lesson_audio_url(self, item: Dict[str, Any]) -> Optional[str]:
        """Resolve a best-effort audio URL from a lesson JSON object."""
        for key in ("audio_url", "audio", "sound", "sound_url", "url"):
            val = item.get(key)
            if isinstance(val, str) and val:
                return val
        nested = item.get("audio_file") or item.get("media")
        if isinstance(nested, dict):
            for key in ("url", "audio", "file"):
                val = nested.get(key)
                if isinstance(val, str) and val:
                    return val
        return None
