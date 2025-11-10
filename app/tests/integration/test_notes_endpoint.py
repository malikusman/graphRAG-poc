from fastapi.testclient import TestClient

from app.api.endpoints import notes as notes_module
from app.core.config import settings
from app.main import app


class _FakeNote:
    document_id = "doc-1"
    note_id = "note-1"
    text_chunk = "CRISPR-Cas9 editing increases efficiency."

    def to_pipeline_chunk(self):
        return {
            "_id": self.note_id,
            "note_id": self.note_id,
            "document_id": self.document_id,
            "text": self.text_chunk,
        }


class _FakeNotesService:
    def __init__(self, *args, **kwargs):
        pass

    async def fetch_notes(self, max_records=None):
        return [_FakeNote()]

    def group_by_document(self, notes):
        return {"doc-1": notes}


class _FakeCleaner:
    def __init__(self, *args, **kwargs):
        pass

    async def clean_chunks(self, chunks):
        enhanced = []
        for chunk in chunks:
            new_chunk = dict(chunk)
            new_chunk["cleaning_metadata"] = {
                "keep": True,
                "noise_ratio": 0.1,
                "reason": "clean",
                "cleaned_preview": new_chunk.get("text", "")[:50],
            }
            new_chunk["_chunk_internal_id"] = new_chunk.get("note_id")
            enhanced.append(new_chunk)
        return enhanced, [], []


class _FakePipeline:
    async def process_document(self, document_id, text_chunks, filtered_chunks, discarded_chunks):
        return {
            "success": True,
            "document_id": document_id,
            "entities_extracted": 0,
            "relationships_extracted": 0,
            "final_entities": [],
            "final_relationships": [],
            "errors": [],
            "discarded_chunks": discarded_chunks,
        }


def test_notes_endpoint_returns_pipeline_output(monkeypatch):
    monkeypatch.setattr(notes_module, "NotesService", _FakeNotesService)
    monkeypatch.setattr(notes_module, "TextChunkCleaningService", _FakeCleaner)
    monkeypatch.setattr(notes_module, "GraphRAGPipeline", _FakePipeline)

    monkeypatch.setattr(settings, "NOTES_API_TOKEN", "fake-token", raising=False)

    client = TestClient(app)
    response = client.post("/api/v1/notes/entity-relationships", json={})

    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    assert payload["total_documents"] == 1
    assert payload["total_chunks"] == 1
    assert payload["total_retained"] == 1
    assert payload["total_discarded"] == 0

    document_result = payload["documents"][0]
    assert document_result["document_id"] == "doc-1"
    assert document_result["chunks_total"] == 1
    assert document_result["chunks_retained"] == 1
    assert document_result["pipeline_result"]["success"] is True

