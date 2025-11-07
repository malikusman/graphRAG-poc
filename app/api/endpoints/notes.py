"""Endpoints for processing note text chunks into entities and relationships."""

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, constr

from app.core.config import settings
from app.pipelines.graphrag_pipeline_notes import GraphRAGPipeline
from app.services.notes_service import NotesService
from app.services.text_chunk_cleaning_service import TextChunkCleaningService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["Notes"])


class NotesProcessingRequest(BaseModel):
    """Request model for transforming notes into entity relationships."""

    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=2000,
        description="Maximum number of note chunks to fetch across all documents.",
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="Override the notes API endpoint (defaults to NOTES_API_ENDPOINT).",
    )
    token: Optional[str] = Field(
        default=None,
        description="Override the notes API bearer token (defaults to NOTES_API_TOKEN).",
    )
    noise_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Threshold for discarding noisy chunks (defaults to TEXT_CHUNK_NOISE_THRESHOLD).",
    )
    document_ids: Optional[List[constr(min_length=1)]] = Field(
        default=None,
        description="If provided, restrict processing to these document IDs.",
    )
    include_discarded_chunks: bool = Field(
        default=True,
        description="Include details about discarded chunks in the response.",
    )


class DocumentProcessingResult(BaseModel):
    """Per-document processing result."""

    document_id: str
    chunks_total: int
    chunks_retained: int
    chunks_discarded: int
    cleaning_errors: List[str]
    pipeline_result: Dict[str, Any]
    discarded_chunks: Optional[List[Dict[str, Any]]] = None


class NotesProcessingResponse(BaseModel):
    """Response returned after processing notes through the pipeline."""

    success: bool
    total_documents: int
    total_chunks: int
    total_retained: int
    total_discarded: int
    documents: List[DocumentProcessingResult]


@router.post("/entity-relationships", response_model=NotesProcessingResponse)
async def notes_to_entity_relationships(request: NotesProcessingRequest) -> NotesProcessingResponse:
    """Fetch notes, clean them with the LLM, and extract entities/relationships per document."""

    api_token = request.token or settings.NOTES_API_TOKEN
    if not api_token:
        raise HTTPException(
            status_code=400,
            detail="Notes API token is required. Provide `token` in the request or configure NOTES_API_TOKEN.",
        )

    endpoint = request.endpoint or settings.NOTES_API_ENDPOINT
    service = NotesService(
        token=api_token,
        endpoint=endpoint,
    )

    try:
        notes = await service.fetch_notes(max_records=request.limit)
    except httpx.HTTPStatusError as exc:  # pragma: no cover - passthrough
        logger.error(
            "Notes API request failed with status %s: %s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Notes API returned {exc.response.status_code}: {exc.response.text}",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Notes API request failed: %s", exc)
        raise HTTPException(500, detail=f"Failed to fetch notes: {exc}") from exc

    if request.document_ids:
        allowed_ids = {doc_id for doc_id in request.document_ids}
        notes = [note for note in notes if note.document_id in allowed_ids]

    if not notes:
        return NotesProcessingResponse(
            success=True,
            total_documents=0,
            total_chunks=0,
            total_retained=0,
            total_discarded=0,
            documents=[],
        )

    grouped_notes = service.group_by_document(notes)

    cleaner = TextChunkCleaningService(noise_threshold=request.noise_threshold)
    pipeline = GraphRAGPipeline()

    documents: List[DocumentProcessingResult] = []
    total_chunks = 0
    total_retained = 0
    total_discarded = 0

    for document_id, chunks in grouped_notes.items():
        pipeline_chunks = [chunk.to_pipeline_chunk() for chunk in chunks]
        filtered_chunks, discarded_chunks, cleaning_errors = await cleaner.clean_chunks(pipeline_chunks)

        total_chunks += len(pipeline_chunks)
        total_retained += len(filtered_chunks)
        total_discarded += len(discarded_chunks)

        pipeline_result = await pipeline.process_document(
            document_id=document_id,
            text_chunks=pipeline_chunks,
            filtered_chunks=filtered_chunks,
            discarded_chunks=discarded_chunks,
        )

        discarded_payload: Optional[List[Dict[str, Any]]] = None
        if request.include_discarded_chunks and discarded_chunks:
            discarded_payload = [
                {
                    "note_id": chunk.get("note_id") or chunk.get("_id"),
                    "cleaning_metadata": chunk.get("cleaning_metadata"),
                    "text_preview": (chunk.get("text") or "")[:200],
                }
                for chunk in discarded_chunks
            ]

        documents.append(
            DocumentProcessingResult(
                document_id=document_id,
                chunks_total=len(pipeline_chunks),
                chunks_retained=len(filtered_chunks),
                chunks_discarded=len(discarded_chunks),
                cleaning_errors=cleaning_errors,
                pipeline_result=pipeline_result,
                discarded_chunks=discarded_payload,
            )
        )

    return NotesProcessingResponse(
        success=True,
        total_documents=len(documents),
        total_chunks=total_chunks,
        total_retained=total_retained,
        total_discarded=total_discarded,
        documents=documents,
    )


