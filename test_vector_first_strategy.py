"""
Tests for Vector-First Retrieval Strategy

Tests cover:
- Strategy initialization
- Query preparation
- Vector search integration
- Result enrichment
- Confidence calculation
- End-to-end retrieval
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from app.services.retrieval_strategies.vector_first_strategy import VectorFirstStrategy
from app.services.vector_search_service import VectorSearchResult
from app.services.query_analysis_service import QueryAnalysis, QueryIntent, QueryComplexity, RetrievalStrategy, EntityInfo
from app.models import QuerySource


class TestVectorFirstStrategy:
    """Test VectorFirstStrategy functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """Create a VectorFirstStrategy with mocked dependencies"""
        with patch('app.services.retrieval_strategies.vector_first_strategy.VectorSearchService'):
            return VectorFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_analysis(self):
        """Create a sample QueryAnalysis"""
        return QueryAnalysis(
            query="What is CRISPR?",
            intent=QueryIntent.FACTUAL,
            complexity=QueryComplexity.SIMPLE,
            entities=[
                EntityInfo(name="CRISPR", type="method", confidence=0.9)
            ],
            recommended_strategy=RetrievalStrategy.VECTOR_FIRST,
            confidence=0.85
        )
    
    def test_strategy_initialization(self, strategy):
        """Test strategy initializes correctly"""
        assert strategy is not None
        assert strategy.vector_search is not None
        assert strategy.get_strategy_name() == "VectorFirstStrategy"
        print("✓ Strategy initialization test passed")
    
    def test_prepare_query(self, strategy, sample_analysis):
        """Test query preparation"""
        query = "What is CRISPR?"
        prepared = strategy._prepare_query(query, sample_analysis)
        
        # Currently just returns original query
        assert prepared == query
        print("✓ Query preparation test passed")
    
    def test_calculate_confidence_high_scores(self, strategy, sample_analysis):
        """Test confidence calculation with high, consistent scores"""
        sources = [
            QuerySource(
                document_id="doc1",
                document_title="Test1",
                section_id="sec1",
                section_type="abstract",
                content="Content 1",
                relevance_score=0.95
            ),
            QuerySource(
                document_id="doc2",
                document_title="Test2",
                section_id="sec2",
                section_type="methods",
                content="Content 2",
                relevance_score=0.93
            ),
            QuerySource(
                document_id="doc3",
                document_title="Test3",
                section_id="sec3",
                section_type="results",
                content="Content 3",
                relevance_score=0.91
            )
        ]
        
        confidence = strategy._calculate_confidence(sources, sample_analysis)
        
        # High, consistent scores should give high confidence
        assert confidence > 0.8
        print(f"✓ High confidence test passed: {confidence:.2f}")
    
    def test_calculate_confidence_mixed_scores(self, strategy, sample_analysis):
        """Test confidence calculation with mixed scores"""
        sources = [
            QuerySource(
                document_id="doc1",
                document_title="Test1",
                section_id="sec1",
                section_type="abstract",
                content="Content 1",
                relevance_score=0.75
            ),
            QuerySource(
                document_id="doc2",
                document_title="Test2",
                section_id="sec2",
                section_type="methods",
                content="Content 2",
                relevance_score=0.55
            ),
            QuerySource(
                document_id="doc3",
                document_title="Test3",
                section_id="sec3",
                section_type="results",
                content="Content 3",
                relevance_score=0.42
            )
        ]
        
        confidence = strategy._calculate_confidence(sources, sample_analysis)
        
        # Mixed scores should give moderate confidence
        assert 0.4 < confidence < 0.7
        print(f"✓ Moderate confidence test passed: {confidence:.2f}")
    
    def test_calculate_confidence_no_sources(self, strategy, sample_analysis):
        """Test confidence calculation with no sources"""
        confidence = strategy._calculate_confidence([], sample_analysis)
        
        assert confidence == 0.0
        print("✓ No sources confidence test passed")
    
    def test_calculate_confidence_single_source(self, strategy, sample_analysis):
        """Test confidence calculation with single source"""
        sources = [
            QuerySource(
                document_id="doc1",
                document_title="Test1",
                section_id="sec1",
                section_type="abstract",
                content="Content 1",
                relevance_score=0.85
            )
        ]
        
        confidence = strategy._calculate_confidence(sources, sample_analysis)
        
        # Single high score should give reasonable confidence
        assert 0.5 < confidence < 0.8
        print(f"✓ Single source confidence test passed: {confidence:.2f}")
    
    @pytest.mark.asyncio
    async def test_perform_vector_search(self, strategy):
        """Test vector search execution"""
        # Mock vector search results
        mock_results = [
            VectorSearchResult(
                section_id="sec1",
                document_id="doc1",
                content="CRISPR is a gene editing tool",
                title="abstract",
                score=0.92
            ),
            VectorSearchResult(
                section_id="sec2",
                document_id="doc1",
                content="Gene editing applications",
                title="methods",
                score=0.85
            )
        ]
        
        strategy.vector_search.search = AsyncMock(return_value=mock_results)
        
        results = await strategy._perform_vector_search("CRISPR", max_results=10)
        
        assert len(results) == 2
        assert results[0].score == 0.92
        print("✓ Vector search execution test passed")
    
    @pytest.mark.asyncio
    async def test_enrich_results(self, strategy, mock_db):
        """Test result enrichment with document metadata"""
        # Mock vector search results
        vector_results = [
            VectorSearchResult(
                section_id="sec1",
                document_id="507f1f77bcf86cd799439011",  # Valid 24-char hex string
                content="Test content",
                title="abstract",
                score=0.90
            )
        ]
        
        # Mock document metadata
        mock_doc = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "CRISPR Research Paper",
            "doi": "10.1000/test",
            "year": 2023,
            "status": "processed"
        }
        
        mock_db.documents.find_one = AsyncMock(return_value=mock_doc)
        
        sources = await strategy._enrich_results(vector_results)
        
        assert len(sources) == 1
        assert isinstance(sources[0], QuerySource)
        assert sources[0].document_title == "CRISPR Research Paper"
        assert sources[0].doi == "10.1000/test"
        assert sources[0].relevance_score == 0.90
        assert sources[0].metadata["year"] == 2023
        print("✓ Result enrichment test passed")
    
    @pytest.mark.asyncio
    async def test_retrieve_end_to_end(self, strategy, sample_analysis, mock_db):
        """Test complete retrieve flow"""
        # Mock vector search results (use valid ObjectIds)
        doc_id_1 = "507f1f77bcf86cd799439011"
        doc_id_2 = "507f1f77bcf86cd799439012"
        
        mock_vector_results = [
            VectorSearchResult(
                section_id="sec1",
                document_id=doc_id_1,
                content="CRISPR is a gene editing tool",
                title="abstract",
                score=0.92
            ),
            VectorSearchResult(
                section_id="sec2",
                document_id=doc_id_2,
                content="Applications of CRISPR in medicine",
                title="introduction",
                score=0.87
            )
        ]
        
        strategy.vector_search.search = AsyncMock(return_value=mock_vector_results)
        
        # Mock document metadata
        mock_doc1 = {
            "_id": doc_id_1,
            "title": "CRISPR Fundamentals",
            "doi": "10.1000/crispr1",
            "year": 2023,
            "status": "processed"
        }
        mock_doc2 = {
            "_id": doc_id_2,
            "title": "Medical Applications of Gene Editing",
            "doi": "10.1000/crispr2",
            "year": 2024,
            "status": "processed"
        }
        
        # Mock document fetching
        async def mock_find_one(query):
            doc_id = str(query["_id"])
            if doc_id_1 in doc_id:
                return mock_doc1
            elif doc_id_2 in doc_id:
                return mock_doc2
            return None
        
        mock_db.documents.find_one = AsyncMock(side_effect=mock_find_one)
        
        # Execute retrieve
        sources = await strategy.retrieve(
            query="What is CRISPR?",
            analysis=sample_analysis,
            max_results=5
        )
        
        # Verify results
        assert len(sources) == 2
        assert isinstance(sources[0], QuerySource)
        assert sources[0].document_title == "CRISPR Fundamentals"
        assert sources[1].document_title == "Medical Applications of Gene Editing"
        assert sources[0].relevance_score == 0.92
        assert sources[1].relevance_score == 0.87
        assert "strategy_confidence" in sources[0].metadata
        assert "strategy_used" in sources[0].metadata
        assert sources[0].metadata["strategy_used"] == "vector_first"
        
        print(f"✓ End-to-end retrieve test passed: {len(sources)} sources retrieved")
    
    @pytest.mark.asyncio
    async def test_retrieve_no_results(self, strategy, sample_analysis):
        """Test retrieve with no vector search results"""
        # Mock empty results
        strategy.vector_search.search = AsyncMock(return_value=[])
        
        sources = await strategy.retrieve(
            query="Unknown query",
            analysis=sample_analysis,
            max_results=5
        )
        
        assert len(sources) == 0
        print("✓ No results test passed")
    
    def test_get_strategy_description(self, strategy):
        """Test strategy description"""
        description = strategy.get_strategy_description()
        
        assert "VectorFirstStrategy" in description
        assert "semantic similarity" in description.lower()
        print("✓ Strategy description test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("VECTOR-FIRST STRATEGY TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()

