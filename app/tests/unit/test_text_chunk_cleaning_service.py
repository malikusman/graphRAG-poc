import pytest

from app.services.text_chunk_cleaning_service import TextChunkCleaningService


class _StubChain:
    def __init__(self, responses):
        self._responses = responses
        self._index = 0

    async def ainvoke(self, _):
        response = self._responses[self._index]
        self._index += 1
        return response


@pytest.mark.asyncio
async def test_text_chunk_cleaning_service_filters_noise(monkeypatch):
    service = TextChunkCleaningService(noise_threshold=0.7)

    stub_chain = _StubChain(
        [
            {
                "keep": True,
                "noise_ratio": 0.2,
                "reason": "Contains meaningful prose",
                "cleaned_preview": "Meaningful",
            },
            {
                "keep": False,
                "noise_ratio": 0.9,
                "reason": "Mostly noise",
                "cleaned_preview": "",
            },
        ]
    )

    monkeypatch.setattr(service, "chain", stub_chain)

    chunks = [
        {"text": "This is a meaningful research note.", "note_id": "note-1"},
        {"text": "123 456 789", "note_id": "note-2"},
    ]

    filtered, discarded, errors = await service.clean_chunks(chunks)

    assert errors == []
    assert len(filtered) == 1
    assert len(discarded) == 1

    kept_chunk = filtered[0]
    assert kept_chunk["cleaning_metadata"]["keep"] is True
    assert kept_chunk["cleaning_metadata"]["noise_ratio"] == pytest.approx(0.2)

    discarded_chunk = discarded[0]
    assert discarded_chunk["cleaning_metadata"]["keep"] is False
    assert discarded_chunk["cleaning_metadata"]["noise_ratio"] == pytest.approx(0.9)

