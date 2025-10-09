"""
Integration test for RetrievalService with Vector-First Strategy

This test validates that:
1. RetrievalService initializes correctly with strategies
2. Query analysis works
3. Strategy selection works
4. Vector-First strategy is executed
5. Response is properly formatted
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from app.services.retrieval_service import RetrievalService
from app.services.query_analysis_service import QueryAnalysis, QueryIntent, QueryComplexity, RetrievalStrategy, EntityInfo
from app.services.vector_search_service import VectorSearchResult
from app.models import QueryResponse, QuerySource


class TestRetrievalServiceIntegration:
    """Test RetrievalService integration with Vector-First Strategy"""
    
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
    def retrieval_service(self, mock_db):
        """Create RetrievalService with mocked dependencies"""
        with patch('app.services.retrieval_service.VectorFirstStrategy'):
            with patch('app.services.retrieval_service.QueryAnalysisService'):
                return RetrievalService(mock_db)
    
    def test_initialization(self, retrieval_service):
        """Test that RetrievalService initializes with strategies"""
        assert retrieval_service is not None
        assert hasattr(retrieval_service, 'strategies')
        assert RetrievalStrategy.VECTOR_FIRST in retrieval_service.strategies
        print("✓ Initialization test passed")
    
    @pytest.mark.asyncio
    async def test_process_query_end_to_end(self, retrieval_service, mock_db):
        """Test complete query processing flow"""
        # Mock query analysis
        mock_analysis = QueryAnalysis(
            query="What is CRISPR?",
            intent=QueryIntent.FACTUAL,
            complexity=QueryComplexity.SIMPLE,
            entities=[EntityInfo(name="CRISPR", type="method", confidence=0.9)],
            recommended_strategy=RetrievalStrategy.VECTOR_FIRST,
            confidence=0.85
        )
        
        retrieval_service.query_analyzer.analyze_query = AsyncMock(return_value=mock_analysis)
        
        # Mock strategy execution
        mock_sources = [
            QuerySource(
                document_id="507f1f77bcf86cd799439011",
                document_title="CRISPR Research",
                section_id="sec1",
                section_type="abstract",
                content="CRISPR is a revolutionary gene editing technology...",
                relevance_score=0.92,
                doi="10.1000/test",
                metadata={
                    "year": 2023,
                    "strategy_used": "vector_first",
                    "strategy_confidence": 0.88
                }
            ),
            QuerySource(
                document_id="507f1f77bcf86cd799439012",
                document_title="Gene Editing Methods",
                section_id="sec2",
                section_type="methods",
                content="Various gene editing techniques including CRISPR-Cas9...",
                relevance_score=0.85,
                doi="10.1000/test2",
                metadata={
                    "year": 2024,
                    "strategy_used": "vector_first",
                    "strategy_confidence": 0.88
                }
            )
        ]
        
        # Mock the strategy's retrieve method
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].retrieve = AsyncMock(
            return_value=mock_sources
        )
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].get_strategy_name = Mock(
            return_value="VectorFirstStrategy"
        )
        
        # Execute process_query
        response = await retrieval_service.process_query(
            query="What is CRISPR?",
            max_results=5
        )
        
        # Verify response
        assert isinstance(response, QueryResponse)
        assert response.query == "What is CRISPR?"
        assert len(response.sources) == 2
        assert response.sources[0].document_title == "CRISPR Research"
        assert response.sources[0].relevance_score == 0.92
        assert response.confidence == 0.88  # From strategy
        assert response.metadata["strategy_used"] == "vector_first"
        assert response.metadata["sources_count"] == 2
        assert "CRISPR" in response.answer
        assert response.processing_time > 0
        
        print(f"✓ End-to-end test passed: {len(response.sources)} sources retrieved")
        print(f"  Answer: {response.answer[:100]}...")
        print(f"  Confidence: {response.confidence:.2f}")
        print(f"  Processing time: {response.processing_time*1000:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_process_query_no_sources(self, retrieval_service):
        """Test query processing when no sources are found"""
        # Mock query analysis
        mock_analysis = QueryAnalysis(
            query="Unknown topic",
            intent=QueryIntent.FACTUAL,
            complexity=QueryComplexity.SIMPLE,
            entities=[],
            recommended_strategy=RetrievalStrategy.VECTOR_FIRST,
            confidence=0.5
        )
        
        retrieval_service.query_analyzer.analyze_query = AsyncMock(return_value=mock_analysis)
        
        # Mock strategy returning empty results
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].retrieve = AsyncMock(
            return_value=[]
        )
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].get_strategy_name = Mock(
            return_value="VectorFirstStrategy"
        )
        
        # Execute
        response = await retrieval_service.process_query(query="Unknown topic")
        
        # Verify
        assert isinstance(response, QueryResponse)
        assert len(response.sources) == 0
        assert response.confidence == 0.0
        assert "couldn't find" in response.answer.lower()
        
        print("✓ No sources test passed")
    
    @pytest.mark.asyncio
    async def test_strategy_fallback(self, retrieval_service):
        """Test fallback to VECTOR_FIRST when recommended strategy not available"""
        # Mock query analysis recommending unavailable strategy
        mock_analysis = QueryAnalysis(
            query="Test query",
            intent=QueryIntent.FACTUAL,
            complexity=QueryComplexity.SIMPLE,
            entities=[],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,  # Not available yet
            confidence=0.7
        )
        
        retrieval_service.query_analyzer.analyze_query = AsyncMock(return_value=mock_analysis)
        
        # Mock vector strategy
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].retrieve = AsyncMock(
            return_value=[]
        )
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].get_strategy_name = Mock(
            return_value="VectorFirstStrategy"
        )
        
        # Execute
        response = await retrieval_service.process_query(query="Test query")
        
        # Verify it fell back to VECTOR_FIRST
        assert isinstance(response, QueryResponse)
        # Strategy was called even though GRAPH_FIRST was recommended
        retrieval_service.strategies[RetrievalStrategy.VECTOR_FIRST].retrieve.assert_called_once()
        
        print("✓ Strategy fallback test passed")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, retrieval_service):
        """Test error handling in query processing"""
        # Mock query analyzer to raise an error
        retrieval_service.query_analyzer.analyze_query = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        # Execute
        response = await retrieval_service.process_query(query="Test query")
        
        # Verify error response
        assert isinstance(response, QueryResponse)
        assert response.confidence == 0.0
        assert "error" in response.answer.lower()
        assert "error" in response.metadata
        
        print("✓ Error handling test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("RETRIEVAL SERVICE INTEGRATION TEST SUITE")
    print("="*70 + "\n")
    
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()

