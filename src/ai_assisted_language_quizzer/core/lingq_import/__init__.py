"""
LingQ Bulk Import Client

HTTP client for the LingQ REST API v3, supporting course listing,
lesson creation with audio upload, and audio replacement on existing lessons.
"""

from .client import Course, Lesson, LingQClient
from .test_harness import LingQTestHarness

__all__ = [
    "LingQClient",
    "Course",
    "Lesson",
    "LingQTestHarness",
]
