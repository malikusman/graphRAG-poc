"""
Comprehensive tests for GraphTraversalService

Tests all major functionality:
- Entity matching (exact, alias, fuzzy)
- BFS graph traversal
- Bidirectional path finding
- Path scoring algorithms
- Edge cases and error handling
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any

from app.services.graph_traversal_service import GraphTraversalService, EntityMatch, PathScore
from app.models.entities import EntityResponse, EntityType, EntityCategory
from app.models.relationships import RelationshipResponse, RelationshipType
from app.models.query_models import GraphPath
from app.services.query_analysis_service import QueryAnalysis, EntityInfo, QueryIntent, QueryComplexity, RetrievalStrategy


class TestEntityMatching:
    """Test entity matching functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def traversal_service(self, mock_db):
        """Graph traversal service instance"""
        return GraphTraversalService(mock_db)
    
    @pytest.fixture
    def sample_query_analysis(self):
        """Sample query analysis for testing"""
        return QueryAnalysis(
            query="How does TP53 prevent cancer?",
            intent=QueryIntent.CAUSAL,
            complexity=QueryComplexity.MODERATE,
            entities=[
                EntityInfo(name="TP53", type="gene", confidence=0.9),
                EntityInfo(name="cancer", type="disease", confidence=0.95)
            ],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
    
    @pytest.fixture
    def sample_entities(self):
        """Sample entities from knowledge graph"""
        return [
            EntityResponse(
                id="entity_1",
                entity_name="p53",
                entity_type=EntityType.PROTEIN,
                entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
                aliases=["TP53", "tumor protein 53"],
                paper_ids=["doc_1", "doc_2"],
                section_ids=["sec_1", "sec_2"],
                frequency=5,
                entity_description="Tumor suppressor protein",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            ),
            EntityResponse(
                id="entity_2",
                entity_name="cancer",
                entity_type=EntityType.DISEASE,
                entity_category=EntityCategory.CONDITIONS_AND_STATES,
                aliases=["tumor", "malignancy"],
                paper_ids=["doc_1", "doc_3"],
                section_ids=["sec_1", "sec_3"],
                frequency=8,
                entity_description="Disease characterized by uncontrolled cell growth",
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_find_entities_in_query_exact_match(self, traversal_service, sample_query_analysis, sample_entities):
        """Test finding entities with exact matches"""
        # Mock EntityCollection.find_similar_entities_by_name
        with patch('app.services.graph_traversal_service.EntityCollection.find_similar_entities_by_name') as mock_find:
            # First call for TP53 (exact match fails, alias succeeds)
            # Second call for cancer (exact match succeeds)
            mock_find.side_effect = [
                [],  # No exact match for TP53
                [sample_entities[0]],  # TP53 alias match (p53 has TP53 in aliases)
                [sample_entities[1]],  # cancer exact match
                []  # No alias match needed for cancer
            ]
            
            matches = await traversal_service.find_entities_in_query(
                "How does TP53 prevent cancer?", 
                sample_query_analysis
            )
            
            assert len(matches) == 2
            
            # Find the cancer match
            cancer_match = next(m for m in matches if m.query_entity == "cancer")
            assert cancer_match.matched_entity.entity_name == "cancer"
            assert cancer_match.match_type == "exact"
            assert cancer_match.confidence == 1.0
    
    @pytest.mark.asyncio
    async def test_find_entities_in_query_alias_match(self, traversal_service, sample_query_analysis, sample_entities):
        """Test finding entities with alias matches"""
        with patch('app.services.graph_traversal_service.EntityCollection.find_similar_entities_by_name') as mock_find:
            # First call returns no exact match for TP53, second call returns p53 with TP53 alias
            mock_find.side_effect = [
                [],  # No exact match for TP53
                [sample_entities[0]],  # p53 entity with TP53 in aliases
                [sample_entities[1]]   # cancer exact match
            ]
            
            matches = await traversal_service.find_entities_in_query(
                "How does TP53 prevent cancer?", 
                sample_query_analysis
            )
            
            assert len(matches) == 2
            tp53_match = next(m for m in matches if m.query_entity == "TP53")
            assert tp53_match.matched_entity.entity_name == "p53"
            assert tp53_match.match_type == "alias"
            assert tp53_match.confidence == 0.95
            assert "TP53" in tp53_match.matched_entity.aliases
    
    @pytest.mark.asyncio
    async def test_find_entities_in_query_fuzzy_match(self, traversal_service, sample_query_analysis, sample_entities):
        """Test finding entities with fuzzy matches"""
        with patch('app.services.graph_traversal_service.EntityCollection.find_similar_entities_by_name') as mock_find:
            # No exact or alias match, but fuzzy match found
            mock_find.side_effect = [
                [],  # No exact match
                [],  # No alias match
                [sample_entities[0]],  # Fuzzy match for TP53 -> p53
                [sample_entities[1]]   # cancer exact match
            ]
            
            matches = await traversal_service.find_entities_in_query(
                "How does TP53 prevent cancer?", 
                sample_query_analysis
            )
            
            assert len(matches) == 2
            tp53_match = next(m for m in matches if m.query_entity == "TP53")
            assert tp53_match.match_type == "fuzzy"
            assert tp53_match.confidence == 0.8
    
    @pytest.mark.asyncio
    async def test_find_entities_in_query_no_match(self, traversal_service, sample_query_analysis):
        """Test handling when no entities are found"""
        with patch('app.services.graph_traversal_service.EntityCollection.find_similar_entities_by_name') as mock_find:
            mock_find.return_value = []  # No matches found
            
            matches = await traversal_service.find_entities_in_query(
                "How does unknown_entity work?", 
                sample_query_analysis
            )
            
            assert len(matches) == 0


class TestGraphTraversal:
    """Test graph traversal algorithms"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def traversal_service(self, mock_db):
        """Graph traversal service instance"""
        return GraphTraversalService(mock_db)
    
    @pytest.fixture
    def sample_relationships(self):
        """Sample relationships for testing"""
        return [
            RelationshipResponse(
                id="rel_1",
                source_entity="p53",
                target_entity="cancer",
                relationship_type=RelationshipType.PREVENTS,
                relationship_strength=0.9,
                description="p53 prevents cancer development",
                paper_ids=["doc_1"],
                section_ids=["sec_1"],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            ),
            RelationshipResponse(
                id="rel_2",
                source_entity="p53",
                target_entity="apoptosis",
                relationship_type=RelationshipType.ACTIVATES,
                relationship_strength=0.85,
                description="p53 activates apoptosis",
                paper_ids=["doc_2"],
                section_ids=["sec_2"],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            ),
            RelationshipResponse(
                id="rel_3",
                source_entity="apoptosis",
                target_entity="cancer",
                relationship_type=RelationshipType.PREVENTS,
                relationship_strength=0.8,
                description="apoptosis prevents cancer",
                paper_ids=["doc_3"],
                section_ids=["sec_3"],
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_traverse_graph_bfs_single_hop(self, traversal_service, sample_relationships):
        """Test BFS traversal for single hop"""
        start_entity = EntityResponse(
            id="entity_1",
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        with patch('app.services.graph_traversal_service.RelationshipCollection.get_relationships_by_entity') as mock_get_rel:
            mock_get_rel.return_value = sample_relationships[:2]  # p53 -> cancer, p53 -> apoptosis
            
            with patch.object(traversal_service, '_get_entity_by_name') as mock_get_entity:
                mock_get_entity.side_effect = [
                    EntityResponse(id="e2", entity_name="cancer", entity_type=EntityType.DISEASE, 
                                 entity_category=EntityCategory.CONDITIONS_AND_STATES, aliases=[], 
                                 paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                                 created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z"),
                    EntityResponse(id="e3", entity_name="apoptosis", entity_type=EntityType.PHYSIOLOGICAL_PROCESS, 
                                 entity_category=EntityCategory.BIOLOGICAL_ENTITIES, aliases=[], 
                                 paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                                 created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z")
                ]
                
                with patch.object(traversal_service, '_get_path_entities') as mock_path_entities:
                    mock_path_entities.return_value = []
                    
                    with patch.object(traversal_service, '_get_path_relationships') as mock_path_rels:
                        mock_path_rels.return_value = []
                        
                        with patch.object(traversal_service, '_calculate_path_strength') as mock_strength:
                            mock_strength.return_value = 0.9
                            
                            paths = await traversal_service.traverse_graph([start_entity], max_hops=1)
                            
                            assert len(paths) == 2
                            assert all(path.metadata.get("hop_count") == 1 for path in paths)
    
    @pytest.mark.asyncio
    async def test_traverse_graph_bfs_multi_hop(self, traversal_service, sample_relationships):
        """Test BFS traversal for multiple hops"""
        start_entity = EntityResponse(
            id="entity_1",
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        with patch('app.services.graph_traversal_service.RelationshipCollection.get_relationships_by_entity') as mock_get_rel:
            # First call: p53 relationships, second call: apoptosis relationships
            mock_get_rel.side_effect = [
                sample_relationships[:2],  # p53 -> cancer, p53 -> apoptosis
                [sample_relationships[2]]  # apoptosis -> cancer
            ]
            
            with patch.object(traversal_service, '_get_entity_by_name') as mock_get_entity:
                mock_get_entity.side_effect = [
                    EntityResponse(id="e2", entity_name="cancer", entity_type=EntityType.DISEASE, 
                                 entity_category=EntityCategory.CONDITIONS_AND_STATES, aliases=[], 
                                 paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                                 created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z"),
                    EntityResponse(id="e3", entity_name="apoptosis", entity_type=EntityType.PHYSIOLOGICAL_PROCESS, 
                                 entity_category=EntityCategory.BIOLOGICAL_ENTITIES, aliases=[], 
                                 paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                                 created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z"),
                    EntityResponse(id="e2", entity_name="cancer", entity_type=EntityType.DISEASE, 
                                 entity_category=EntityCategory.CONDITIONS_AND_STATES, aliases=[], 
                                 paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                                 created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z")
                ]
                
                with patch.object(traversal_service, '_get_path_entities') as mock_path_entities:
                    mock_path_entities.return_value = []
                    
                    with patch.object(traversal_service, '_get_path_relationships') as mock_path_rels:
                        mock_path_rels.return_value = []
                        
                        with patch.object(traversal_service, '_calculate_path_strength') as mock_strength:
                            mock_strength.return_value = 0.8
                            
                            paths = await traversal_service.traverse_graph([start_entity], max_hops=2)
                            
                            # Should find 1-hop paths (p53 -> cancer, p53 -> apoptosis)
                            # and 2-hop paths (p53 -> apoptosis -> cancer)
                            assert len(paths) >= 2
                            
                            # Check that we have both 1-hop and 2-hop paths
                            hop_counts = [path.metadata.get("hop_count", 0) for path in paths]
                            assert 1 in hop_counts
                            assert 2 in hop_counts
    
    @pytest.mark.asyncio
    async def test_traverse_graph_min_strength_filtering(self, traversal_service, sample_relationships):
        """Test that traversal respects minimum strength threshold"""
        start_entity = EntityResponse(
            id="entity_1",
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        # Create relationships with different strengths
        weak_relationship = RelationshipResponse(
            id="rel_weak",
            source_entity="p53",
            target_entity="weak_target",
            relationship_type=RelationshipType.ASSOCIATED_WITH,
            relationship_strength=0.3,  # Below threshold
            description="Weak association",
            paper_ids=[],
            section_ids=[],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        with patch('app.services.graph_traversal_service.RelationshipCollection.get_relationships_by_entity') as mock_get_rel:
            mock_get_rel.return_value = [sample_relationships[0], weak_relationship]
            
            with patch.object(traversal_service, '_get_entity_by_name') as mock_get_entity:
                mock_get_entity.return_value = EntityResponse(
                    id="e2", entity_name="cancer", entity_type=EntityType.DISEASE, 
                    entity_category=EntityCategory.CONDITIONS_AND_STATES, aliases=[], 
                    paper_ids=[], section_ids=[], frequency=1, entity_description="", 
                    created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z"
                )
                
                with patch.object(traversal_service, '_get_path_entities') as mock_path_entities:
                    mock_path_entities.return_value = []
                    
                    with patch.object(traversal_service, '_get_path_relationships') as mock_path_rels:
                        mock_path_rels.return_value = []
                        
                        with patch.object(traversal_service, '_calculate_path_strength') as mock_strength:
                            mock_strength.return_value = 0.9
                            
                            # Traverse with min_strength=0.5
                            paths = await traversal_service.traverse_graph([start_entity], max_hops=1, min_strength=0.5)
                            
                            # Should only find paths with strong relationships (>= 0.5)
                            assert len(paths) == 1
                            assert paths[0].path == ["p53", "cancer"]


class TestPathFinding:
    """Test path finding between entities"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def traversal_service(self, mock_db):
        """Graph traversal service instance"""
        return GraphTraversalService(mock_db)
    
    @pytest.mark.asyncio
    async def test_find_paths_between_entities_direct(self, traversal_service):
        """Test finding direct paths between entities"""
        source_entity = EntityResponse(
            id="entity_1",
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        target_entity = EntityResponse(
            id="entity_2",
            entity_name="cancer",
            entity_type=EntityType.DISEASE,
            entity_category=EntityCategory.CONDITIONS_AND_STATES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        direct_relationship = RelationshipResponse(
            id="rel_1",
            source_entity="p53",
            target_entity="cancer",
            relationship_type=RelationshipType.PREVENTS,
            relationship_strength=0.9,
            description="p53 prevents cancer",
            paper_ids=["doc_1"],
            section_ids=["sec_1"],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        with patch('app.services.graph_traversal_service.RelationshipCollection.find_relationships_between_entities') as mock_find_rel:
            mock_find_rel.return_value = [direct_relationship]
            
            with patch.object(traversal_service, '_get_path_entities') as mock_path_entities:
                mock_path_entities.return_value = []
                
                paths = await traversal_service.find_paths_between_entities(
                    [source_entity], [target_entity], max_hops=3
                )
                
                assert len(paths) >= 1
                direct_paths = [p for p in paths if p.metadata.get("hop_count") == 1]
                assert len(direct_paths) == 1
                assert direct_paths[0].path == ["p53", "cancer"]
                assert direct_paths[0].total_strength == 0.9
    
    @pytest.mark.asyncio
    async def test_find_paths_between_entities_empty_inputs(self, traversal_service):
        """Test handling of empty source or target entities"""
        source_entity = EntityResponse(
            id="entity_1",
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        # Test empty target entities
        paths = await traversal_service.find_paths_between_entities([source_entity], [], max_hops=3)
        assert len(paths) == 0
        
        # Test empty source entities
        paths = await traversal_service.find_paths_between_entities([], [source_entity], max_hops=3)
        assert len(paths) == 0


class TestPathScoring:
    """Test path scoring algorithms"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def traversal_service(self, mock_db):
        """Graph traversal service instance"""
        return GraphTraversalService(mock_db)
    
    @pytest.fixture
    def sample_path(self):
        """Sample path for scoring"""
        return GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {
                    "source_entity": "p53",
                    "target_entity": "cancer",
                    "relationship_type": "prevents",
                    "relationship_strength": 0.9,
                    "paper_ids": ["doc_1", "doc_2", "doc_3"]
                }
            ],
            total_strength=0.9,
            metadata={"hop_count": 1}
        )
    
    def test_score_path_high_quality(self, traversal_service, sample_path):
        """Test scoring of high-quality path"""
        score = traversal_service.score_path(sample_path)
        
        assert isinstance(score, PathScore)
        assert score.path == sample_path
        assert score.path_strength == 0.9
        assert score.evidence_count == 3  # 3 papers
        assert score.hop_count == 1
        assert score.relevance_score > 0.6  # Should be reasonably high
        assert score.confidence > 0.8  # Should be high
    
    def test_score_path_low_quality(self, traversal_service):
        """Test scoring of low-quality path"""
        low_quality_path = GraphPath(
            path=["entity1", "entity2", "entity3", "entity4"],  # 3 hops
            entities=[],
            relationships=[
                {
                    "relationship_type": "associated_with",
                    "relationship_strength": 0.3,
                    "paper_ids": []  # No evidence
                },
                {
                    "relationship_type": "associated_with", 
                    "relationship_strength": 0.4,
                    "paper_ids": []
                },
                {
                    "relationship_type": "associated_with",
                    "relationship_strength": 0.2,
                    "paper_ids": []
                }
            ],
            total_strength=0.024,  # 0.3 * 0.4 * 0.2
            metadata={"hop_count": 3}
        )
        
        score = traversal_service.score_path(low_quality_path)
        
        assert score.path_strength == 0.024
        assert score.evidence_count == 0  # No papers
        assert score.hop_count == 3
        assert score.relevance_score < 0.3  # Should be low
        assert score.confidence < 0.7  # Should be low (adjusted for noisy-OR calculation)
    
    def test_calculate_relationship_relevance(self, traversal_service):
        """Test relationship relevance calculation"""
        path = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {"relationship_type": "prevents"},  # Weight: 1.0
                {"relationship_type": "activates"}   # Weight: 1.0
            ],
            total_strength=0.9,
            metadata={}
        )
        
        relevance = traversal_service._calculate_relationship_relevance(path)
        assert relevance == 1.0  # Average of 1.0 and 1.0 for PREVENTS and ACTIVATES
    
    def test_calculate_path_length_factor(self, traversal_service):
        """Test path length factor calculation"""
        assert traversal_service._calculate_path_length_factor(1) == 1.0
        assert traversal_service._calculate_path_length_factor(2) == 0.8
        assert traversal_service._calculate_path_length_factor(3) == 0.6
        assert traversal_service._calculate_path_length_factor(4) == 0.4
    
    def test_calculate_noisy_or_confidence(self, traversal_service):
        """Test noisy-OR confidence calculation"""
        path = GraphPath(
            path=["p53", "cancer"],
            entities=[],
            relationships=[
                {"relationship_strength": 0.8},
                {"relationship_strength": 0.6}
            ],
            total_strength=0.48,
            metadata={}
        )
        
        confidence = traversal_service._calculate_noisy_or_confidence(path)
        # Formula: 1 - (1-0.8) * (1-0.6) = 1 - 0.2 * 0.4 = 1 - 0.08 = 0.92
        expected = 1.0 - (1.0 - 0.8) * (1.0 - 0.6)
        assert abs(confidence - expected) < 0.001
        assert confidence <= 0.99  # Should be capped at 0.99
    
    def test_score_path_empty_relationships(self, traversal_service):
        """Test scoring path with no relationships"""
        empty_path = GraphPath(
            path=["entity1"],
            entities=[],
            relationships=[],
            total_strength=0.0,
            metadata={}
        )
        
        score = traversal_service.score_path(empty_path)
        
        assert score.path_strength == 0.0
        assert score.evidence_count == 0
        assert score.relevance_score >= 0.0  # May have some default scoring
        assert score.confidence == 0.0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = Mock()
        db.entities = Mock()
        db.relationships = Mock()
        return db
    
    @pytest.fixture
    def traversal_service(self, mock_db):
        """Graph traversal service instance"""
        return GraphTraversalService(mock_db)
    
    @pytest.mark.asyncio
    async def test_find_entities_database_error(self, traversal_service):
        """Test handling of database errors during entity matching"""
        analysis = QueryAnalysis(
            query="test query",
            intent=QueryIntent.CAUSAL,
            complexity=QueryComplexity.MODERATE,
            entities=[EntityInfo(name="test", type="gene", confidence=0.9)],
            recommended_strategy=RetrievalStrategy.GRAPH_FIRST,
            confidence=0.85
        )
        
        with patch('app.services.graph_traversal_service.EntityCollection.find_similar_entities_by_name') as mock_find:
            mock_find.side_effect = Exception("Database connection error")
            
            matches = await traversal_service.find_entities_in_query("test query", analysis)
            
            # Should return empty list on error
            assert len(matches) == 0
    
    @pytest.mark.asyncio
    async def test_traverse_graph_database_error(self, traversal_service):
        """Test handling of database errors during traversal"""
        start_entity = EntityResponse(
            id="entity_1",
            entity_name="test",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            aliases=[],
            paper_ids=[],
            section_ids=[],
            frequency=1,
            entity_description="Test entity",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        with patch('app.services.graph_traversal_service.RelationshipCollection.get_relationships_by_entity') as mock_get_rel:
            mock_get_rel.side_effect = Exception("Database error")
            
            paths = await traversal_service.traverse_graph([start_entity], max_hops=2)
            
            # Should return empty list on error
            assert len(paths) == 0
    
    def test_score_path_malformed_data(self, traversal_service):
        """Test scoring with malformed path data"""
        # Create a valid GraphPath but with minimal data
        malformed_path = GraphPath(
            path=[],  # Empty path
            entities=[],  # Empty entities
            relationships=[],  # Empty relationships
            total_strength=0.0,  # Zero strength
            metadata={}
        )
        
        score = traversal_service.score_path(malformed_path)
        
        # Should return default values without crashing
        assert score.path_strength == 0.0
        assert score.evidence_count == 0
        assert score.relevance_score >= 0.0  # May have some default scoring
        assert score.confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
