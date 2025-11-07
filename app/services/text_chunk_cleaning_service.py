"""LLM-powered cleaning service for note text chunks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.configs.schemas import load_prompt
from app.core.config import settings
from app.core.llm_provider import get_llm


logger = logging.getLogger(__name__)


class TextChunkCleaningService:
    """Service that assesses note chunks and filters out noisy content."""

    def __init__(
        self,
        noise_threshold: Optional[float] = None,
    ) -> None:
        self.noise_threshold = noise_threshold or settings.TEXT_CHUNK_NOISE_THRESHOLD

        prompt_config = load_prompt("text_chunk_cleaning", "preprocess")

        self.prompt = ChatPromptTemplate.from_messages(
            (
                ("system", prompt_config.get("system_prompt", "")),
                ("human", prompt_config.get("user_prompt", "")),
            )
        )

        temperature = prompt_config.get("temperature", 0.0)
        max_tokens = prompt_config.get("max_tokens")

        self.llm = get_llm(temperature=temperature, max_tokens=max_tokens)
        self.parser = JsonOutputParser()
        self.chain = self.prompt | self.llm | self.parser

    async def clean_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """Return filtered and discarded chunk lists plus any errors."""

        filtered: List[Dict[str, Any]] = []
        discarded: List[Dict[str, Any]] = []
        errors: List[str] = []

        for index, chunk in enumerate(chunks):
            chunk_id = self._get_chunk_id(chunk, index)
            chunk_text = self._get_chunk_text(chunk)

            if not chunk_text.strip():
                logger.debug("Skipping empty chunk %s", chunk_id)
                discarded.append(
                    self._with_metadata(
                        chunk,
                        {
                            "keep": False,
                            "noise_ratio": 1.0,
                            "reason": "Chunk is empty after stripping whitespace",
                            "cleaned_preview": "",
                        },
                        chunk_id,
                    )
                )
                continue

            try:
                result = await self.chain.ainvoke(
                    {
                        "chunk_text": chunk_text,
                        "noise_threshold": self.noise_threshold,
                    }
                )

                keep = bool(result.get("keep", True))
                noise_ratio = self._safe_float(result.get("noise_ratio", 0.0))
                metadata = {
                    "keep": keep,
                    "noise_ratio": noise_ratio,
                    "reason": result.get("reason", ""),
                    "cleaned_preview": result.get("cleaned_preview", ""),
                }

                chunk_with_metadata = self._with_metadata(chunk, metadata, chunk_id)

                if keep:
                    filtered.append(chunk_with_metadata)
                else:
                    discarded.append(chunk_with_metadata)

            except Exception as exc:  # pragma: no cover - defensive path
                error_message = f"Chunk cleaning failed for {chunk_id}: {exc}"
                logger.error(error_message)
                errors.append(error_message)
                chunk_with_metadata = self._with_metadata(
                    chunk,
                    {
                        "keep": True,
                        "noise_ratio": None,
                        "reason": "Cleaning failure: defaulting to keep",
                        "cleaned_preview": chunk_text[:200],
                    },
                    chunk_id,
                )
                filtered.append(chunk_with_metadata)

        return filtered, discarded, errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _get_chunk_text(chunk: Dict[str, Any]) -> str:
        return (
            str(
                chunk.get("text")
                or chunk.get("text_chunk")
                or chunk.get("content")
                or chunk.get("body")
                or chunk.get("raw")
                or ""
            )
        )

    @staticmethod
    def _get_chunk_id(chunk: Dict[str, Any], index: int) -> str:
        return str(
            chunk.get("note_id")
            or chunk.get("chunk_id")
            or chunk.get("_id")
            or chunk.get("id")
            or chunk.get("uuid")
            or f"chunk_{index}"
        )

    @staticmethod
    def _with_metadata(
        chunk: Dict[str, Any], metadata: Dict[str, Any], chunk_id: str
    ) -> Dict[str, Any]:
        chunk_copy = dict(chunk)
        existing = chunk_copy.get("cleaning_metadata", {})
        merged = dict(existing)
        merged.update(metadata)
        chunk_copy["cleaning_metadata"] = merged
        chunk_copy.setdefault("_chunk_internal_id", chunk_id)
        return chunk_copy


