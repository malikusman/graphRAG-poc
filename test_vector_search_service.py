"""
Tests for Vector Search Service

These tests cover:
- Query embedding generation
- Candidate fetching from database
- Similarity calculation
- Ranking and filtering
- End-to-end search functionality

Note: These tests use mocking to avoid requiring a running MongoDB instance.
For integration tests with real database, see test_vector_retrieval_e2e.py
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from app.services.vector_search_service import VectorSearchService, VectorSearchResult


class TestVectorSearchService:
    """Test VectorSearchService functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def search_service(self, mock_db):
        """Create a VectorSearchService with mocked dependencies"""
        with patch('app.services.vector_search_service.EmbeddingsService'):
            service = VectorSearchService(mock_db)
            return service
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_success(self, search_service):
        """Test successful query embedding generation"""
        # Mock the embeddings service
        test_embedding = [0.1] * 1536
        search_service.embeddings_service.generate_embedding = Mock(return_value=test_embedding)
        
        # Generate embedding
        result = await search_service._generate_query_embedding("test query")
        
        # Verify
        assert result is not None
        assert isinstance(result, np.ndarray)
        assert len(result) == 1536
        print("✓ Query embedding generation test passed")
    
    @pytest.mark.asyncio
    async def test_generate_query_embedding_failure(self, search_service):
        """Test handling of embedding generation failure"""
        # Mock failure
        search_service.embeddings_service.generate_embedding = Mock(return_value=None)
        
        # Generate embedding
        result = await search_service._generate_query_embedding("test query")
        
        # Verify
        assert result is None
        print("✓ Query embedding failure handling test passed")
    
    @pytest.mark.asyncio
    async def test_fetch_candidate_embeddings(self, search_service, mock_db):
        """Test fetching candidate embeddings from database"""
        # Mock database response
        mock_sections = [
            {
                "_id": "sec1",
                "document_id": "doc1",
                "text": "CRISPR is a gene editing tool",
                "title": "abstract",
                "embedding": [0.1] * 1536,
                "year": 2023
            },
            {
                "_id": "sec2",
                "document_id": "doc1",
                "text": "p53 is a tumor suppressor",
                "title": "methods",
                "embedding": [0.2] * 1536,
                "year": 2023
            }
        ]
        
        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_sections)
        mock_db.sections.find = Mock(return_value=mock_cursor)
        
        # Fetch candidates
        candidates = await search_service._fetch_candidate_embeddings()
        
        # Verify
        assert len(candidates) == 2
        assert candidates[0]["_id"] == "sec1"
        assert candidates[1]["_id"] == "sec2"
        print("✓ Fetch candidate embeddings test passed")
    
    @pytest.mark.asyncio
    async def test_fetch_candidate_embeddings_with_filters(self, search_service, mock_db):
        """Test fetching candidates with filters"""
        mock_sections = [
            {
                "_id": "sec1",
                "document_id": "doc1",
                "text": "Test content",
                "title": "abstract",
                "embedding": [0.1] * 1536,
                "year": 2023
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_sections)
        mock_db.sections.find = Mock(return_value=mock_cursor)
        
        # Fetch with filters
        filters = {"year": 2023}
        candidates = await search_service._fetch_candidate_embeddings(filters)
        
        # Verify filters were applied
        call_args = mock_db.sections.find.call_args[0][0]
        assert "year" in call_args
        assert call_args["year"] == 2023
        print("✓ Fetch with filters test passed")
    
    def test_calculate_similarities(self, search_service):
        """Test similarity calculation"""
        # Create test data
        query_embedding = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        
        candidates = [
            {
                "_id": "sec1",
                "document_id": "doc1",
                "text": "Similar to query",
                "title": "abstract",
                "embedding": [1.0, 0.0, 0.0],  # Identical to query
                "year": 2023
            },
            {
                "_id": "sec2",
                "document_id": "doc1",
                "text": "Orthogonal to query",
                "title": "methods",
                "embedding": [0.0, 1.0, 0.0],  # Orthogonal
                "year": 2023
            },
            {
                "_id": "sec3",
                "document_id": "doc2",
                "text": "Opposite to query",
                "title": "results",
                "embedding": [-1.0, 0.0, 0.0],  # Opposite
                "year": 2022
            }
        ]
        
        # Calculate similarities
        results = search_service._calculate_similarities(query_embedding, candidates)
        
        # Verify
        assert len(results) == 3
        assert results[0].score == pytest.approx(1.0, abs=0.01)   # Identical
        assert results[1].score == pytest.approx(0.0, abs=0.01)   # Orthogonal
        assert results[2].score == pytest.approx(-1.0, abs=0.01)  # Opposite
        print("✓ Calculate similarities test passed")
    
    def test_rank_and_filter(self, search_service):
        """Test ranking and filtering results"""
        # Create test results with various scores
        results = [
            VectorSearchResult("sec1", "doc1", "High score", "abstract", 0.95),
            VectorSearchResult("sec2", "doc1", "Medium score", "methods", 0.75),
            VectorSearchResult("sec3", "doc2", "Low score", "results", 0.45),
            VectorSearchResult("sec4", "doc2", "Very low score", "discussion", 0.20),
        ]
        
        # Rank and filter
        filtered = search_service._rank_and_filter(
            results,
            limit=3,
            min_score=0.7,
            include_embeddings=False
        )
        
        # Verify
        assert len(filtered) == 2  # Only scores >= 0.7
        assert filtered[0].score == 0.95  # Highest first
        assert filtered[1].score == 0.75  # Second highest
        assert filtered[0].embedding is None  # Embeddings not included
        print("✓ Rank and filter test passed")
    
    def test_rank_and_filter_no_threshold(self, search_service):
        """Test ranking without score threshold"""
        results = [
            VectorSearchResult("sec1", "doc1", "Content 1", "abstract", 0.95),
            VectorSearchResult("sec2", "doc1", "Content 2", "methods", 0.75),
            VectorSearchResult("sec3", "doc2", "Content 3", "results", 0.45),
        ]
        
        # Rank without threshold
        filtered = search_service._rank_and_filter(
            results,
            limit=2,
            min_score=0.0,  # No threshold
            include_embeddings=False
        )
        
        # Verify
        assert len(filtered) == 2  # Limited to 2
        assert filtered[0].score == 0.95
        assert filtered[1].score == 0.75
        print("✓ Rank without threshold test passed")
    
    @pytest.mark.asyncio
    async def test_search_end_to_end_mock(self, search_service, mock_db):
        """Test complete search flow with mocked components"""
        # Mock query embedding generation (must be 1536 dimensions)
        query_embedding = np.array([1.0] + [0.0] * 1535, dtype=np.float32)  # First dim is 1.0, rest are 0
        search_service.embeddings_service.generate_embedding = Mock(
            return_value=query_embedding.tolist()
        )
        
        # Mock database response (embeddings must be 1536 dimensions)
        embedding_similar = [0.9] + [0.0] * 1535  # Similar to query (first dim close to 1.0)
        embedding_different = [0.2] + [0.1] * 1535  # Less similar to query
        
        mock_sections = [
            {
                "_id": "sec1",
                "document_id": "doc1",
                "text": "CRISPR is used for gene editing",
                "title": "abstract",
                "embedding": embedding_similar,
                "year": 2023
            },
            {
                "_id": "sec2",
                "document_id": "doc1",
                "text": "Cancer treatment methods",
                "title": "methods",
                "embedding": embedding_different,
                "year": 2022
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_sections)
        mock_db.sections.find = Mock(return_value=mock_cursor)
        
        # Perform search
        results = await search_service.search(
            query="CRISPR gene editing",
            limit=5,
            min_score=0.5
        )
        
        # Verify
        assert len(results) > 0
        assert isinstance(results[0], VectorSearchResult)
        if len(results) > 1:
            assert results[0].score >= results[1].score  # Sorted by score (descending)
        print(f"✓ End-to-end mock search test passed: {len(results)} results")
    
    @pytest.mark.asyncio
    async def test_search_no_candidates(self, search_service, mock_db):
        """Test search with no candidates in database"""
        # Mock empty database
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.sections.find = Mock(return_value=mock_cursor)
        
        # Mock query embedding
        search_service.embeddings_service.generate_embedding = Mock(
            return_value=[0.1] * 1536
        )
        
        # Perform search
        results = await search_service.search("test query")
        
        # Verify
        assert len(results) == 0
        print("✓ No candidates test passed")
    
    @pytest.mark.asyncio
    async def test_search_embedding_generation_fails(self, search_service):
        """Test search when embedding generation fails"""
        # Mock embedding generation failure
        search_service.embeddings_service.generate_embedding = Mock(return_value=None)
        
        # Perform search
        results = await search_service.search("test query")
        
        # Verify
        assert len(results) == 0
        print("✓ Embedding generation failure test passed")
    
    def test_vector_search_result_creation(self):
        """Test VectorSearchResult dataclass"""
        result = VectorSearchResult(
            section_id="sec1",
            document_id="doc1",
            content="Test content",
            title="abstract",
            score=0.95,
            metadata={"year": 2023}
        )
        
        assert result.section_id == "sec1"
        assert result.score == 0.95
        assert result.metadata["year"] == 2023
        assert result.embedding is None  # Default
        print("✓ VectorSearchResult creation test passed")
    
    def test_get_stats(self, search_service):
        """Test service statistics"""
        # Mock embeddings service methods
        search_service.embeddings_service.get_model_name = Mock(return_value="text-embedding-3-small")
        search_service.embeddings_service.get_embedding_dimensions = Mock(return_value=1536)
        
        stats = search_service.get_stats()
        
        assert "service" in stats
        assert "embedding_model" in stats
        assert "embedding_dimensions" in stats
        assert stats["embedding_dimensions"] == 1536
        print("✓ Get stats test passed")


class TestVectorSearchResultDataclass:
    """Test VectorSearchResult dataclass"""
    
    def test_minimal_creation(self):
        """Test creating result with minimal fields"""
        result = VectorSearchResult(
            section_id="sec1",
            document_id="doc1",
            content="Test",
            title="abstract",
            score=0.9
        )
        
        assert result.metadata == {}  # Auto-initialized
        assert result.embedding is None
        print("✓ Minimal creation test passed")
    
    def test_full_creation(self):
        """Test creating result with all fields"""
        embedding = [0.1] * 1536
        metadata = {"year": 2023, "doi": "10.1000/test"}
        
        result = VectorSearchResult(
            section_id="sec1",
            document_id="doc1",
            content="Full test content",
            title="methods",
            score=0.85,
            embedding=embedding,
            metadata=metadata
        )
        
        assert len(result.embedding) == 1536
        assert result.metadata["year"] == 2023
        assert result.metadata["doi"] == "10.1000/test"
        print("✓ Full creation test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("VECTOR SEARCH SERVICE TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()

