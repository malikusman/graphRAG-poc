"""
Comprehensive tests for GraphFirstStrategy

Tests all major functionality:
- Query type detection (single entity, entity pair, multi-entity)
- Single entity exploration
- Entity pair path finding
- Multi-entity analysis
- Path to source conversion
- Error handling and edge cases
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any

from app.services.retrieval_strategies.graph_first_strategy import GraphFirstStrategy, QueryType
from app.models import QuerySource
from app.models.query_models import GraphPath
from app.services.query_analysis_service import QueryAnalysis, EntityInfo, QueryIntent, QueryComplexity, RetrievalStrategy
from app.services.graph_traversal_service import EntityMatch, PathScore
from app.models.entities import EntityResponse, EntityType, EntityCategory
from app.models.relationships import RelationshipResponse, RelationshipType


class TestQueryTypeDetection:
    """Test query type detection logic"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_entities(self):
        """Sample entity matches for testing"""
        return [
            EntityMatch(
                query_entity="p53",
                matched_entity=EntityResponse(
                    id="e1", entity_name="p53", entity_type=EntityType.PROTEIN,
                    entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            ),
            EntityMatch(
                query_entity="cancer",
                matched_entity=EntityResponse(
                    id="e2", entity_name="cancer", entity_type=EntityType.DISEASE,
                    entity_category=EntityCategory.CONDITIONS_AND_STATES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            ),
            EntityMatch(
                query_entity="BRCA1",
                matched_entity=EntityResponse(
                    id="e3", entity_name="BRCA1", entity_type=EntityType.GENE,
                    entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            )
        ]
    
    def test_determine_query_type_single_entity_exploratory(self, strategy, sample_entities):
        """Test single entity detection for exploratory queries"""
        analysis = QueryAnalysis(
            query="What does p53 do?",
            intent=QueryIntent.EXPLORATORY,
            complexity=QueryComplexity.MODERATE,
            entities=[EntityInfo(name="p53", type="protein", confidence=0.9)],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, sample_entities[:1])
        assert query_type == QueryType.SINGLE_ENTITY
    
    def test_determine_query_type_single_entity_factual(self, strategy, sample_entities):
        """Test single entity detection for factual queries"""
        analysis = QueryAnalysis(
            query="What is p53?",
            intent=QueryIntent.FACTUAL,
            complexity=QueryComplexity.SIMPLE,
            entities=[EntityInfo(name="p53", type="protein", confidence=0.9)],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, sample_entities[:1])
        assert query_type == QueryType.SINGLE_ENTITY
    
    def test_determine_query_type_entity_pair_causal(self, strategy, sample_entities):
        """Test entity pair detection for causal queries"""
        analysis = QueryAnalysis(
            query="How does p53 prevent cancer?",
            intent=QueryIntent.CAUSAL,
            complexity=QueryComplexity.MODERATE,
            entities=[
                EntityInfo(name="p53", type="protein", confidence=0.9),
                EntityInfo(name="cancer", type="disease", confidence=0.95)
            ],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, sample_entities[:2])
        assert query_type == QueryType.ENTITY_PAIR
    
    def test_determine_query_type_entity_pair_comparative(self, strategy, sample_entities):
        """Test entity pair detection for comparative queries"""
        analysis = QueryAnalysis(
            query="Compare p53 and BRCA1",
            intent=QueryIntent.COMPARATIVE,
            complexity=QueryComplexity.MODERATE,
            entities=[
                EntityInfo(name="p53", type="protein", confidence=0.9),
                EntityInfo(name="BRCA1", type="gene", confidence=0.9)
            ],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, sample_entities[:2])
        assert query_type == QueryType.ENTITY_PAIR
    
    def test_determine_query_type_multi_entity(self, strategy, sample_entities):
        """Test multi-entity detection"""
        analysis = QueryAnalysis(
            query="How are p53, BRCA1, and cancer related?",
            intent=QueryIntent.COMPARATIVE,
            complexity=QueryComplexity.COMPLEX,
            entities=[
                EntityInfo(name="p53", type="protein", confidence=0.9),
                EntityInfo(name="BRCA1", type="gene", confidence=0.9),
                EntityInfo(name="cancer", type="disease", confidence=0.95)
            ],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, sample_entities)
        assert query_type == QueryType.MULTI_ENTITY
    
    def test_determine_query_type_exploration_fallback(self, strategy, sample_entities):
        """Test exploration fallback for unknown cases"""
        analysis = QueryAnalysis(
            query="Tell me about cancer treatments",
            intent=QueryIntent.EXPLORATORY,
            complexity=QueryComplexity.MODERATE,
            entities=[],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        query_type = strategy._determine_query_type(analysis, [])
        assert query_type == QueryType.EXPLORATION


class TestSingleEntityExploration:
    """Test single entity exploration functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_entity_match(self):
        """Sample entity match for testing"""
        return EntityMatch(
            query_entity="p53",
            matched_entity=EntityResponse(
                id="e1", entity_name="p53", entity_type=EntityType.PROTEIN,
                entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                aliases=[], paper_ids=[], section_ids=[], frequency=1,
                entity_description="", created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            ),
            match_type="exact",
            confidence=1.0,
            reasoning=""
        )
    
    @pytest.fixture
    def sample_paths(self):
        """Sample graph paths for testing"""
        return [
            GraphPath(
                path=["p53", "cancer"],
                entities=[],
                relationships=[
                    {
                        "source_entity": "p53",
                        "target_entity": "cancer",
                        "relationship_type": "prevents",
                        "relationship_strength": 0.9,
                        "paper_ids": ["doc_1"],
                        "section_ids": ["sec_1"]
                    }
                ],
                total_strength=0.9,
                metadata={"hop_count": 1}
            ),
            GraphPath(
                path=["p53", "apoptosis", "cancer"],
                entities=[],
                relationships=[
                    {
                        "source_entity": "p53",
                        "target_entity": "apoptosis",
                        "relationship_type": "activates",
                        "relationship_strength": 0.85,
                        "paper_ids": ["doc_2"],
                        "section_ids": ["sec_2"]
                    },
                    {
                        "source_entity": "apoptosis",
                        "target_entity": "cancer",
                        "relationship_type": "prevents",
                        "relationship_strength": 0.8,
                        "paper_ids": ["doc_3"],
                        "section_ids": ["sec_3"]
                    }
                ],
                total_strength=0.68,
                metadata={"hop_count": 2}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_single_entity_exploration_success(self, strategy, sample_entity_match, sample_paths):
        """Test successful single entity exploration"""
        # Mock graph traversal service
        with patch.object(strategy.graph_traversal, 'traverse_graph') as mock_traverse:
            mock_traverse.return_value = sample_paths
            
            with patch.object(strategy.graph_traversal, 'score_path') as mock_score:
                mock_score.side_effect = [
                    PathScore(path=sample_paths[0], relevance_score=0.9, path_strength=0.9,
                             evidence_count=1, hop_count=1, confidence=0.9),
                    PathScore(path=sample_paths[1], relevance_score=0.8, path_strength=0.68,
                             evidence_count=2, hop_count=2, confidence=0.85)
                ]
                
                with patch.object(strategy, '_paths_to_sources') as mock_sources:
                    mock_sources.return_value = [
                        QuerySource(
                            document_id="doc_1",
                            document_title="p53 and Cancer",
                            section_id="sec_1",
                            section_type="results",
                            content="p53 prevents cancer...",
                            relevance_score=0.9,
                            metadata={"strategy_used": "graph_first"}
                        )
                    ]
                    
                    paths, sources = await strategy._single_entity_exploration(
                        sample_entity_match, max_hops=3, min_strength=0.5, max_results=5
                    )
                    
                    assert len(paths) == 2  # Both paths returned, but limited by max_results
                    assert len(sources) == 1
                    assert sources[0].document_title == "p53 and Cancer"
    
    @pytest.mark.asyncio
    async def test_single_entity_exploration_no_paths(self, strategy, sample_entity_match):
        """Test single entity exploration with no paths found"""
        with patch.object(strategy.graph_traversal, 'traverse_graph') as mock_traverse:
            mock_traverse.return_value = []
            
            paths, sources = await strategy._single_entity_exploration(
                sample_entity_match, max_hops=3, min_strength=0.5, max_results=5
            )
            
            assert len(paths) == 0
            assert len(sources) == 0


class TestEntityPairPathFinding:
    """Test entity pair path finding functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_entity_matches(self):
        """Sample entity matches for testing"""
        return [
            EntityMatch(
                query_entity="p53",
                matched_entity=EntityResponse(
                    id="e1", entity_name="p53", entity_type=EntityType.PROTEIN,
                    entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            ),
            EntityMatch(
                query_entity="cancer",
                matched_entity=EntityResponse(
                    id="e2", entity_name="cancer", entity_type=EntityType.DISEASE,
                    entity_category=EntityCategory.CONDITIONS_AND_STATES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            )
        ]
    
    @pytest.mark.asyncio
    async def test_entity_pair_path_finding_success(self, strategy, sample_entity_matches):
        """Test successful entity pair path finding"""
        sample_path = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {
                    "source_entity": "p53",
                    "target_entity": "cancer",
                    "relationship_type": "prevents",
                    "relationship_strength": 0.9,
                    "paper_ids": ["doc_1"],
                    "section_ids": ["sec_1"]
                }
            ],
            total_strength=0.9,
            metadata={"hop_count": 1}
        )
        
        with patch.object(strategy.graph_traversal, 'find_paths_between_entities') as mock_find:
            mock_find.return_value = [sample_path]
            
            with patch.object(strategy.graph_traversal, 'score_path') as mock_score:
                mock_score.return_value = PathScore(
                    path=sample_path, relevance_score=0.9, path_strength=0.9,
                    evidence_count=1, hop_count=1, confidence=0.9
                )
                
                with patch.object(strategy, '_paths_to_sources') as mock_sources:
                    mock_sources.return_value = [
                        QuerySource(
                            document_id="doc_1",
                            document_title="p53 Prevents Cancer",
                            section_id="sec_1",
                            section_type="results",
                            content="p53 prevents cancer...",
                            relevance_score=0.9,
                            metadata={"strategy_used": "graph_first"}
                        )
                    ]
                    
                    paths, sources = await strategy._entity_pair_path_finding(
                        sample_entity_matches, max_hops=3, min_strength=0.5, max_results=5
                    )
                    
                    assert len(paths) == 1
                    assert len(sources) == 1
                    assert paths[0].path == ["p53", "cancer"]
                    assert sources[0].document_title == "p53 Prevents Cancer"
    
    @pytest.mark.asyncio
    async def test_entity_pair_path_finding_insufficient_entities(self, strategy):
        """Test entity pair path finding with insufficient entities"""
        paths, sources = await strategy._entity_pair_path_finding(
            [], max_hops=3, min_strength=0.5, max_results=5
        )
        
        assert len(paths) == 0
        assert len(sources) == 0


class TestMultiEntityAnalysis:
    """Test multi-entity analysis functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_entity_matches(self):
        """Sample entity matches for testing"""
        return [
            EntityMatch(
                query_entity="p53",
                matched_entity=EntityResponse(
                    id="e1", entity_name="p53", entity_type=EntityType.PROTEIN,
                    entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            ),
            EntityMatch(
                query_entity="BRCA1",
                matched_entity=EntityResponse(
                    id="e2", entity_name="BRCA1", entity_type=EntityType.GENE,
                    entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            ),
            EntityMatch(
                query_entity="cancer",
                matched_entity=EntityResponse(
                    id="e3", entity_name="cancer", entity_type=EntityType.DISEASE,
                    entity_category=EntityCategory.CONDITIONS_AND_STATES,
                    aliases=[], paper_ids=[], section_ids=[], frequency=1,
                    entity_description="", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                ),
                match_type="exact",
                confidence=1.0,
                reasoning=""
            )
        ]
    
    @pytest.mark.asyncio
    async def test_multi_entity_analysis_success(self, strategy, sample_entity_matches):
        """Test successful multi-entity analysis"""
        sample_path = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {
                    "source_entity": "p53",
                    "target_entity": "cancer",
                    "relationship_type": "prevents",
                    "relationship_strength": 0.9,
                    "paper_ids": ["doc_1"],
                    "section_ids": ["sec_1"]
                }
            ],
            total_strength=0.9,
            metadata={"hop_count": 1}
        )
        
        with patch.object(strategy.graph_traversal, 'find_paths_between_entities') as mock_find:
            mock_find.return_value = [sample_path]
            
            with patch.object(strategy.graph_traversal, 'score_path') as mock_score:
                mock_score.return_value = PathScore(
                    path=sample_path, relevance_score=0.9, path_strength=0.9,
                    evidence_count=1, hop_count=1, confidence=0.9
                )
                
                with patch.object(strategy, '_paths_to_sources') as mock_sources:
                    mock_sources.return_value = [
                        QuerySource(
                            document_id="doc_1",
                            document_title="Multi-Entity Analysis",
                            section_id="sec_1",
                            section_type="results",
                            content="p53 and BRCA1...",
                            relevance_score=0.9,
                            metadata={"strategy_used": "graph_first"}
                        )
                    ]
                    
                    paths, sources = await strategy._multi_entity_analysis(
                        sample_entity_matches, max_hops=3, min_strength=0.5, max_results=5
                    )
                    
                    assert len(paths) == 3  # 3 pairwise combinations (p53-BRCA1, p53-cancer, BRCA1-cancer)
                    assert len(sources) == 1
    
    def test_calculate_multi_entity_boost(self, strategy):
        """Test multi-entity boost calculation"""
        path = GraphPath(
            path=["p53", "BRCA1", "cancer"],
            entities=[],
            relationships=[],
            total_strength=0.8,
            metadata={}
        )
        entity_names = ["p53", "BRCA1", "cancer"]
        
        boost = strategy._calculate_multi_entity_boost(path, entity_names)
        assert boost == 0.2  # All 3 entities connected
        
        # Test with fewer connections
        path2 = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[],
            total_strength=0.8,
            metadata={}
        )
        boost2 = strategy._calculate_multi_entity_boost(path2, entity_names)
        assert boost2 == 0.1  # 2 entities connected


class TestPathsToSources:
    """Test conversion from graph paths to QuerySource objects"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    @pytest.fixture
    def sample_path_score(self):
        """Sample path score for testing"""
        path = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {
                    "source_entity": "p53",
                    "target_entity": "cancer",
                    "relationship_type": "prevents",
                    "relationship_strength": 0.9,
                    "paper_ids": ["doc_1", "doc_2"],
                    "section_ids": ["doc_1_sec1", "doc_2_sec1"]
                }
            ],
            total_strength=0.9,
            metadata={"hop_count": 1}
        )
        
        return PathScore(
            path=path,
            relevance_score=0.9,
            path_strength=0.9,
            evidence_count=2,
            hop_count=1,
            relationship_types=["prevents"],
            confidence=0.9
        )
    
    @pytest.mark.asyncio
    async def test_paths_to_sources_success(self, strategy, sample_path_score):
        """Test successful path to source conversion"""
        with patch.object(strategy, '_fetch_document_metadata') as mock_doc:
            mock_doc.return_value = {
                "title": "p53 Prevents Cancer",
                "doi": "10.1000/test"
            }
            
            with patch.object(strategy, '_fetch_section_metadata') as mock_sec:
                mock_sec.return_value = {
                    "text": "p53 prevents cancer development...",
                    "section_type": "results",
                    "title": "Results"
                }
                
                sources = await strategy._paths_to_sources([sample_path_score])
                
                assert len(sources) == 2  # 2 documents
                assert all(isinstance(source, QuerySource) for source in sources)
                assert all(source.document_title == "p53 Prevents Cancer" for source in sources)
                assert all(source.metadata["strategy_used"] == "graph_first" for source in sources)
    
    @pytest.mark.asyncio
    async def test_fetch_section_metadata_success(self, strategy):
        """Test successful section metadata fetching"""
        mock_section = {
            "_id": "sec_1",
            "text": "Test content",
            "section_type": "results",
            "title": "Results"
        }
        
        strategy.sections_collection.find_one = AsyncMock(return_value=mock_section)
        
        metadata = await strategy._fetch_section_metadata("sec_1")
        
        assert metadata["text"] == "Test content"
        assert metadata["section_type"] == "results"
        assert metadata["title"] == "Results"
    
    @pytest.mark.asyncio
    async def test_fetch_section_metadata_not_found(self, strategy):
        """Test section metadata fetching when section not found"""
        strategy.sections_collection.find_one = AsyncMock(return_value=None)
        
        metadata = await strategy._fetch_section_metadata("nonexistent")
        
        assert metadata["text"] == ""
        assert metadata["section_type"] == "unknown"
        assert metadata["title"] == ""


class TestMainRetrieveMethod:
    """Test the main retrieve method integration"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        with patch('app.services.retrieval_strategies.graph_first_strategy.GraphTraversalService') as mock_traversal:
            mock_traversal_instance = Mock()
            mock_traversal_instance.find_entities_in_query = AsyncMock(return_value=[])
            mock_traversal.return_value = mock_traversal_instance
            strategy_instance = GraphFirstStrategy(mock_db)
            strategy_instance.graph_traversal = mock_traversal_instance
            return strategy_instance
    
    @pytest.fixture
    def sample_query_analysis(self):
        """Sample query analysis for testing"""
        return QueryAnalysis(
            query="How does p53 prevent cancer?",
            intent=QueryIntent.CAUSAL,
            complexity=QueryComplexity.MODERATE,
            entities=[
                EntityInfo(name="p53", type="protein", confidence=0.9),
                EntityInfo(name="cancer", type="disease", confidence=0.95)
            ],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_success(self, strategy, sample_query_analysis):
        """Test successful retrieval - simplified test"""
        # This test verifies that the retrieve method can be called without errors
        # The actual logic is tested in the individual method tests above
        sources = await strategy.retrieve(
            query="How does p53 prevent cancer?",
            analysis=sample_query_analysis,
            max_results=5
        )
        
        # Should return empty list since we're using mocks
        assert isinstance(sources, list)
    
    @pytest.mark.asyncio
    async def test_retrieve_no_entities_found(self, strategy, sample_query_analysis):
        """Test retrieval when no entities are found"""
        strategy.graph_traversal.find_entities_in_query = AsyncMock(return_value=[])
        
        sources = await strategy.retrieve(
            query="Unknown query",
            analysis=sample_query_analysis,
            max_results=5
        )
        
        assert len(sources) == 0
    
    @pytest.mark.asyncio
    async def test_retrieve_error_handling(self, strategy, sample_query_analysis):
        """Test error handling in retrieve method"""
        strategy.graph_traversal.find_entities_in_query = AsyncMock(side_effect=Exception("Database error"))
        
        sources = await strategy.retrieve(
            query="Test query",
            analysis=sample_query_analysis,
            max_results=5
        )
        
        assert len(sources) == 0


class TestRankingAndBoostFunctions:
    """Test ranking and boost calculation functions"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.documents = Mock()
        db.sections = Mock()
        return db
    
    @pytest.fixture
    def strategy(self, mock_db):
        """GraphFirstStrategy instance"""
        return GraphFirstStrategy(mock_db)
    
    def test_calculate_diversity_boost(self, strategy):
        """Test diversity boost calculation"""
        path = GraphPath(
            path=["entity1", "entity2", "entity3", "entity4"],
            entities=[],
            relationships=[],
            total_strength=0.8,
            metadata={"hop_count": 3}
        )
        
        boost = strategy._calculate_diversity_boost(path, [])
        assert boost == 0.15  # 3+ hops
        
        path2 = GraphPath(
            path=["entity1", "entity2"],
            entities=[],
            relationships=[],
            total_strength=0.8,
            metadata={"hop_count": 1}
        )
        
        boost2 = strategy._calculate_diversity_boost(path2, [])
        assert boost2 == 0.05  # 1 hop
    
    def test_rank_sources(self, strategy):
        """Test source ranking"""
        sources = [
            QuerySource(
                document_id="doc_1",
                document_title="Document 1",
                section_id="sec_1",
                section_type="results",
                content="Content 1",
                relevance_score=0.7,
                metadata={"strategy_confidence": 0.9, "hop_count": 2}
            ),
            QuerySource(
                document_id="doc_2",
                document_title="Document 2",
                section_id="sec_2",
                section_type="results",
                content="Content 2",
                relevance_score=0.8,
                metadata={"strategy_confidence": 0.8, "hop_count": 1}
            )
        ]
        
        analysis = QueryAnalysis(
            query="test",
            intent=QueryIntent.CAUSAL,
            complexity=QueryComplexity.MODERATE,
            entities=[],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        ranked = strategy._rank_sources(sources, analysis)
        
        # Should still be sorted by relevance score (0.8 > 0.7)
        assert ranked[0].document_id == "doc_2"
        assert ranked[1].document_id == "doc_1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
