"""Run the notes pipeline on a small sample with detailed logging."""

import argparse
import asyncio
import json
import logging
import os
from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Dict, List

import httpx

from app.pipelines.graphrag_pipeline_notes import GraphRAGPipeline
from app.services.text_chunk_cleaning_service import TextChunkCleaningService


logger = logging.getLogger("notes_pipeline_sample")


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    # Quiet overly noisy loggers unless verbose
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)


async def fetch_sample_notes(token: str, base_url: str, endpoint: str) -> Dict[str, Any]:
    base = base_url.rstrip("/") if base_url else "https://writing-api.sagewrite.com"
    path = endpoint or "/document-vectors/"
    url = f"{base}{path}"

    headers = {"Authorization": f"Bearer {token}"}
    logger.info("Fetching notes endpoint once: %s", url)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    raw_path = "notes_api_raw.json"
    with open(raw_path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info("Saved raw API response to %s", raw_path)

    data = payload.get("data")
    if data is None:
        if isinstance(payload, list):
            data = payload
        else:
            raise RuntimeError("Unexpected notes API response shape; missing 'data' field")

    logger.info("API returned %d chunks", len(data))
    if data:
        logger.debug("First chunk preview: %s", json.dumps(data[0], ensure_ascii=False)[:400])

    data_sorted = sorted(
        data,
        key=lambda item: (str(item.get("document_id", "")), str(item.get("note_id", ""))),
    )

    return {
        "raw": payload,
        "entries": data_sorted,
    }


def summarize_cleaning(discarded: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not discarded:
        return {"discarded_count": 0}
    reasons = Counter(d["cleaning_metadata"].get("reason", "unknown") for d in discarded)
    noise_values = [d["cleaning_metadata"].get("noise_ratio") or 0.0 for d in discarded]
    return {
        "discarded_count": len(discarded),
        "common_reasons": reasons.most_common(3),
        "avg_noise_ratio": round(mean(noise_values), 3) if noise_values else None,
    }


def summarize_entities(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entities:
        return {"count": 0}
    types = Counter(e.get("entity_type", "unknown") for e in entities)
    sample = [e.get("entity_name") for e in entities[:5]]
    return {
        "count": len(entities),
        "top_types": types.most_common(5),
        "sample_entities": sample,
    }


def summarize_relationships(relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not relationships:
        return {"count": 0}
    types = Counter(r.get("relationship_type", "unknown") for r in relationships)
    sample = [
        {
            "source": r.get("source_entity"),
            "type": r.get("relationship_type"),
            "target": r.get("target_entity"),
            "strength": r.get("relationship_strength"),
        }
        for r in relationships[:5]
    ]
    return {
        "count": len(relationships),
        "top_types": types.most_common(5),
        "sample_relationships": sample,
    }


def build_pipeline_chunk(raw_chunk: Dict[str, Any]) -> Dict[str, Any]:
    text = raw_chunk.get("text_chunk") or raw_chunk.get("text") or ""
    note_id = raw_chunk.get("note_id") or raw_chunk.get("_id")
    return {
        "_id": note_id or "",
        "note_id": note_id,
        "document_id": str(raw_chunk.get("document_id", "")),
        "text": text,
        "metadata": {"raw": raw_chunk},
    }


async def run_pipeline(
    grouped_chunks: Dict[str, List[Dict[str, Any]]], noise_threshold: float, verbose: bool
) -> List[Dict[str, Any]]:
    cleaner = TextChunkCleaningService(noise_threshold=noise_threshold)
    pipeline = GraphRAGPipeline()

    per_doc_results: List[Dict[str, Any]] = []

    sample_items = sorted(grouped_chunks.items(), key=lambda kv: kv[0])

    for document_id, notes in sample_items:
        logger.info("Processing document %s", document_id)

        pipeline_chunks = [build_pipeline_chunk(chunk) for chunk in notes]
        filtered, discarded, cleaning_errors = await cleaner.clean_chunks(pipeline_chunks)

        cleaning_summary = summarize_cleaning(discarded)
        cleaning_summary["errors"] = cleaning_errors
        logger.info(
            "Cleaning summary for %s: %s",
            document_id,
            json.dumps(cleaning_summary, ensure_ascii=False),
        )

        result = await pipeline.process_document(
            document_id=document_id,
            text_chunks=pipeline_chunks,
            filtered_chunks=filtered,
            discarded_chunks=discarded,
        )

        entity_summary = summarize_entities(result.get("final_entities", []))
        relationship_summary = summarize_relationships(result.get("final_relationships", []))

        logger.info(
            "Final entities for %s: %s",
            document_id,
            json.dumps(entity_summary, ensure_ascii=False),
        )
        logger.info(
            "Final relationships for %s: %s",
            document_id,
            json.dumps(relationship_summary, ensure_ascii=False),
        )

        retained_chunks = [
            {
                "note_id": chunk.get("note_id"),
                "document_id": chunk.get("document_id"),
                "text": chunk.get("text"),
                "cleaning_metadata": chunk.get("cleaning_metadata"),
            }
            for chunk in filtered
        ]
        discarded_chunks = [
            {
                "note_id": chunk.get("note_id"),
                "document_id": chunk.get("document_id"),
                "text": chunk.get("text"),
                "cleaning_metadata": chunk.get("cleaning_metadata"),
            }
            for chunk in discarded
        ]

        per_doc_results.append(
            {
                "document_id": document_id,
                "chunks_total": len(pipeline_chunks),
                "chunks_retained": len(filtered),
                "cleaning_summary": cleaning_summary,
                "retained_chunks": retained_chunks,
                "discarded_chunks": discarded_chunks,
                "entity_summary": entity_summary,
                "relationship_summary": relationship_summary,
                "final_entities": result.get("final_entities", []),
                "final_relationships": result.get("final_relationships", []),
                "pipeline_result": result,
            }
        )

    return per_doc_results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run notes pipeline sample with detailed logging.")
    parser.add_argument("--limit", type=int, default=10, help="How many chunks (from the single API call) to process in order")
    parser.add_argument("--noise-threshold", type=float, default=None, help="Noise threshold override")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--notes-base-url", default=os.getenv("NOTES_API_BASE_URL", ""))
    parser.add_argument("--notes-endpoint", default=os.getenv("NOTES_API_ENDPOINT", ""))
    args = parser.parse_args()

    configure_logging(args.verbose)

    token = os.getenv("NOTES_API_TOKEN")
    if not token:
        raise SystemExit("NOTES_API_TOKEN environment variable is required to fetch notes.")

    fetch_result = await fetch_sample_notes(
        token=token,
        base_url=args.notes_base_url,
        endpoint=args.notes_endpoint,
    )

    entries = fetch_result["entries"]
    selected_entries = entries[: args.limit]

    grouped = defaultdict(list)
    for item in selected_entries:
        grouped[str(item.get("document_id", ""))].append(item)

    logger.info(
        "Selected %d entries spanning %d documents",
        len(selected_entries),
        len(grouped),
    )
    for doc_id, doc_chunks in grouped.items():
        logger.info("Document %s has %d selected chunks", doc_id, len(doc_chunks))

    noise_threshold = args.noise_threshold if args.noise_threshold is not None else None
    results = await run_pipeline(grouped, noise_threshold=noise_threshold, verbose=args.verbose)

    output_path = "notes_pipeline_results_first_selection.json"
    with open(output_path, "w") as f:
        json.dump({
            "selection_size": len(selected_entries),
            "documents": results,
        }, f, indent=2)

    logger.info("Wrote pipeline results to %s", output_path)


if __name__ == "__main__":
    asyncio.run(main())

