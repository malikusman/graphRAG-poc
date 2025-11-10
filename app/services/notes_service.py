"""Service for fetching and preparing note text chunks for the GraphRAG pipeline."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings


logger = logging.getLogger(__name__)


class NoteChunk(BaseModel):
    """Normalized representation of a note text chunk."""

    document_id: str
    text_chunk: str = Field(..., alias="text")
    note_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_api_payload(cls, payload: Dict[str, Any]) -> "NoteChunk":
        """Create a note chunk instance from the raw API payload."""

        text_value = payload.get("text_chunk") or payload.get("text") or ""
        metadata = {
            "source": payload.get("source"),
            "note_id": payload.get("note_id"),
            "user_id": payload.get("user_id"),
            "raw": payload,
        }

        return cls(
            document_id=str(payload.get("document_id", "")),
            text=text_value or "",
            note_id=payload.get("note_id"),
            user_id=payload.get("user_id"),
            metadata=metadata,
        )

    def to_pipeline_chunk(self) -> Dict[str, Any]:
        """Transform the note chunk into the structure expected by the pipeline."""

        return {
            "_id": self.note_id or self.metadata.get("raw", {}).get("_id") or "",
            "document_id": self.document_id,
            "text": self.text_chunk,
            "note_id": self.note_id,
            "metadata": self.metadata,
        }


class NotesService:
    """Service responsible for retrieving and organizing notes for processing."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        page_size: Optional[int] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url or settings.NOTES_API_BASE_URL.rstrip("/")
        self.endpoint = endpoint or settings.NOTES_API_ENDPOINT
        self.token = token or settings.NOTES_API_TOKEN
        self.page_size = page_size or settings.NOTES_API_PAGE_SIZE
        self.timeout_seconds = timeout_seconds

        if not self.token:
            logger.warning("Notes API token is not configured; requests will likely fail.")

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    async def fetch_notes(
        self,
        max_records: Optional[int] = None,
    ) -> List[NoteChunk]:
        """Fetch note chunks from the external API with pagination support."""

        notes: List[NoteChunk] = []
        next_token: Optional[str] = None

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while True:
                payload, next_token = await self._fetch_page(client, next_token=next_token)

                for item in payload:
                    note = NoteChunk.from_api_payload(item)
                    # Skip completely empty chunks
                    if note.text_chunk.strip():
                        notes.append(note)

                    if max_records and len(notes) >= max_records:
                        logger.debug(
                            "Reached max_records=%s while fetching notes", max_records
                        )
                        return notes[:max_records]

                if not next_token:
                    break

        logger.info("Fetched %s note chunks from the external API", len(notes))
        return notes

    def group_by_document(
        self, notes: Iterable[NoteChunk]
    ) -> Dict[str, List[NoteChunk]]:
        """Group note chunks by their document identifier."""

        grouped: Dict[str, List[NoteChunk]] = defaultdict[str, List[NoteChunk]](list)
        for note in notes:
            grouped[note.document_id].append(note)

        for document_id, chunks in grouped.items():
            grouped[document_id] = sorted(
                chunks,
                key=lambda chunk: (chunk.note_id or "", chunk.metadata.get("raw", {}).get("created_at", "")),
            )

        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        next_token: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        params: Dict[str, Any] = {}
        if self.page_size:
            params["limit"] = self.page_size
        if next_token:
            params["next_token"] = next_token

        headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{self.base_url}{self.endpoint}"
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()

        payload = response.json()
        data = payload.get("data", [])
        new_next_token = payload.get("next_token")

        logger.debug(
            "Fetched %s note chunks from API page (next_token=%s)",
            len(data),
            new_next_token,
        )

        return data, new_next_token


