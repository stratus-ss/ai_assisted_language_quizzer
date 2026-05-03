"""
LLM Curator Module

Provides optional LLM-based curation of lemma-grouped vocabulary lists.
Uses Minimax API to judge learning value, select best forms, and assign CEFR levels.
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
import httpx

from .lemma_grouper import LemmaGroup


@dataclass
class CuratedWord:
    """A word that has been reviewed and curated by an LLM."""
    lemma: str
    best_form: str
    difficulty: str       # A1, A2, B1, B2
    note: str             # max 5 words, English hint
    keep: bool
    original_freq: int
    translation: str      # pronoun-aware English translation


class LLMCurator:
    """Curate vocabulary using Minimax LLM API."""

    SYSTEM_PROMPT = (
        "You curate Spanish vocabulary for a {learner_level} learner building Anki flashcards. "
        "For each lemma group, return a JSON object with a 'words' key containing a JSON array "
        "(same order as input) with objects containing: "
        "- keep: true/false (false for jargon, character names, ultra-rare words) "
        "- best_form: the single best conjugation/form to study first "
        "- difficulty: A1, A2, B1, or B2 "
        "- note: max 5-word English hint for the flashcard "
        "- translation: English meaning with subject pronoun for verbs "
        "(e.g. 'I know' for sé, 'they go' for van, 'he said' for dijo); "
        "for nouns/adjectives just the English word "
        "Input is a JSON object with 'words' key. Output ONLY a JSON object: {{\"words\": [...]}}, no other text."
    )

    def __init__(
        self,
        api_key: str,
        model: str = "minimax-m2.5",
        api_url: str = "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
        batch_size: int = 40,
        learner_level: str = "A2-B1"
    ):
        """
        Initialize the LLM curator.

        Args:
            api_key: Minimax API key.
            model: Model name to use.
            api_url: Full URL of the Minimax chat completion endpoint.
            batch_size: Number of lemma groups per API call.
            learner_level: CEFR level target for curation decisions.
        """
        self._api_key = api_key
        self._model = model
        self._api_url = api_url
        self._batch_size = batch_size
        self._system_prompt = self.SYSTEM_PROMPT.format(learner_level=learner_level)

    def curate(self, lemma_groups: Dict[str, LemmaGroup]) -> List[CuratedWord]:
        """
        Send lemma groups to LLM in batches and return curated words.

        Args:
            lemma_groups: Dict mapping lemma string -> LemmaGroup.

        Returns:
            List of CuratedWord objects, one per input lemma group.
        """
        results: List[CuratedWord] = []
        items = list(lemma_groups.items())

        total_batches = (len(items) + self._batch_size - 1) // self._batch_size
        for i in range(0, len(items), self._batch_size):
            batch_num = i // self._batch_size + 1
            batch = items[i:i + self._batch_size]
            print(f"    Batch {batch_num}/{total_batches} ({len(batch)} words)...", flush=True)
            payload = self._build_batch_payload(batch)

            try:
                raw = self._send_batch(payload)
                batch_results = self._parse_response(raw, batch)
            except Exception as exc:
                print(f"[LLMCurator] Batch {batch_num} failed: {exc}", flush=True)
                batch_results = [
                    CuratedWord(
                        lemma=lemma,
                        best_form=lg.representative,
                        difficulty="A2",
                        note="",
                        keep=True,
                        original_freq=lg.total_freq,
                        translation=""
                    )
                    for lemma, lg in batch
                ]

            results.extend(batch_results)

        return results

    def _build_batch_payload(
        self, batch: List[Tuple[str, LemmaGroup]]
    ) -> Dict:
        """Build compact JSON object wrapping array for one batch. Fields: lemma, freq, forms."""
        return {
            "words": [
                {
                    "lemma": lemma,
                    "freq": lg.total_freq,
                    "forms": list(lg.forms.keys())
                }
                for lemma, lg in batch
            ]
        }

    def _send_batch(self, payload: Dict) -> Dict:
        """POST to Minimax API, parse JSON response. Retries once on failure."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": 'Input: ' + json.dumps(payload, ensure_ascii=False)}
            ]
        }

        for attempt in range(2):
            try:
                with httpx.Client(timeout=180.0) as client:
                    resp = client.post(self._api_url, json=body, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)
                    return json.loads(content)
            except Exception as e:
                if attempt == 0:
                    continue
                raise RuntimeError(f"LLM API call failed: {e}") from e

    def _parse_response(
        self,
        raw: Dict,
        batch: List[Tuple[str, LemmaGroup]]
    ) -> List[CuratedWord]:
        """Map LLM response dicts to CuratedWord dataclasses."""
        words = raw.get("words", [])
        results = []
        for i in range(len(batch)):
            lemma, lg = batch[i]
            item = words[i] if i < len(words) else {}
            results.append(CuratedWord(
                lemma=lemma,
                best_form=item.get("best_form", lg.representative),
                difficulty=item.get("difficulty", "A2"),
                note=item.get("note", "")[:50],
                keep=item.get("keep", True),
                original_freq=lg.total_freq,
                translation=item.get("translation", item.get("note", ""))
            ))
        return results