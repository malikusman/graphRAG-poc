"""
Graph Traversal Service

This service provides the core engine for navigating the knowledge graph.
It handles entity matching, graph traversal algorithms, and path scoring.

Key Features:
- Entity matching (exact, alias, fuzzy)
- Breadth-First Search (BFS) traversal
- Bidirectional search for finding paths between entities
- Path scoring based on relationship strength and evidence
- Support for multi-hop exploration (1-3 hops)

Example Usage:
    >>> traversal = GraphTraversalService(db)
    >>> entities = await traversal.find_entities_in_query("How does p53 prevent cancer?", analysis)
    >>> paths = await traversal.find_paths_between_entities(entities[0], entities[1], max_hops=3)
    >>> scored_paths = [traversal.score_path(path) for path in paths]
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from app.core.database import AsyncIOMotorDatabase
from app.models.entities import Entity, EntityResponse, EntityType, EntityCategory
from app.models.relationships import Relationship, RelationshipResponse, RelationshipType
from app.models.query_models import GraphPath
from app.services.query_analysis_service import QueryAnalysis, EntityInfo
from app.database.models import EntityCollection, RelationshipCollection

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """
    Represents a match between a query entity and a knowledge graph entity
    
    Attributes:
        query_entity: The entity name from the query (e.g., "TP53")
        matched_entity: The Entity object from the knowledge graph
        match_type: How the match was found ("exact", "alias", "fuzzy")
        confidence: Confidence score (0.0 to 1.0)
        reasoning: Human-readable explanation of the match
    """
    query_entity: str
    matched_entity: EntityResponse
    match_type: str  # "exact", "alias", "fuzzy"
    confidence: float  # 0.0 to 1.0
    reasoning: str = ""


@dataclass
class PathScore:
    """
    Scoring information for a graph path
    
    Attributes:
        path: The GraphPath object
        relevance_score: Overall relevance score (0.0 to 1.0)
        path_strength: Product of relationship strengths
        evidence_count: Total number of papers supporting this path
        hop_count: Number of hops in the path
        relationship_types: Types of relationships in the path
        confidence: Final confidence score
    """
    path: GraphPath
    relevance_score: float
    path_strength: float
    evidence_count: int
    hop_count: int
    relationship_types: List[str] = field(default_factory=list)
    confidence: float = 0.0


class GraphTraversalService:
    """
    Core service for traversing the knowledge graph
    
    This service provides methods to:
    1. Find entities from queries in the knowledge graph
    2. Traverse the graph using BFS algorithms
    3. Find paths between specific entities
    4. Score paths based on strength and evidence
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the graph traversal service
        
        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.entities_collection = db.entities
        self.relationships_collection = db.relationships
        
        # Relationship type weights for scoring (from requirements)
        self.relationship_weights = {
            # High relevance (1.0) - Direct causal/functional relationships
            "causes": 1.0,
            "prevents": 1.0,
            "treats": 1.0,
            "targets": 1.0,
            "inhibits": 1.0,
            "activates": 1.0,
            
            # Medium-high relevance (0.9) - Regulatory relationships
            "regulates": 0.9,
            "induces": 0.9,
            "promotes": 0.9,
            "suppresses": 0.9,
            
            # Medium relevance (0.8) - Interaction relationships
            "interacts_with": 0.8,
            "binds_to": 0.8,
            "uses": 0.8,
            "evaluated_by": 0.8,
            
            # Lower relevance (0.6-0.7) - Association relationships
            "associated_with": 0.7,
            "supports": 0.7,
            "part_of": 0.6,
            "contains": 0.6,
            "located_in": 0.6,
            
            # Default weight for unknown types
            "OTHER": 0.5
        }
        
        logger.info("GraphTraversalService initialized")
    
    async def find_entities_in_query(
        self, 
        query: str, 
        analysis: QueryAnalysis
    ) -> List[EntityMatch]:
        """
        Find entities from the query in the knowledge graph
        
        This method takes entities extracted by QueryAnalysisService and matches
        them against entities in the knowledge graph using multiple strategies:
        1. Exact name matching
        2. Alias matching (entity.aliases contains query entity)
        3. Fuzzy matching (similar names)
        
        Args:
            query: Original user query
            analysis: QueryAnalysis result from QueryAnalysisService
            
        Returns:
            List of EntityMatch objects representing successful matches
            
        Example:
            Query: "How does TP53 prevent cancer?"
            Analysis entities: [
                EntityInfo(name="TP53", type="gene"),
                EntityInfo(name="cancer", type="disease")
            ]
            
            Returns:
            [
                EntityMatch(
                    query_entity="TP53",
                    matched_entity=Entity(entity_name="p53", aliases=["TP53"]),
                    match_type="alias",
                    confidence=0.95
                ),
                EntityMatch(
                    query_entity="cancer",
                    matched_entity=Entity(entity_name="cancer"),
                    match_type="exact",
                    confidence=1.0
                )
            ]
        """
        logger.info(f"Finding entities in query: '{query}'")
        logger.info(f"Analysis entities: {[e.name for e in analysis.entities]}")
        
        matches = []
        
        for entity_info in analysis.entities:
            try:
                # Strategy 1: Exact name match
                exact_match = await self._find_exact_entity_match(entity_info)
                if exact_match:
                    matches.append(exact_match)
                    continue
                
                # Strategy 2: Alias match
                alias_match = await self._find_alias_entity_match(entity_info)
                if alias_match:
                    matches.append(alias_match)
                    continue
                
                # Strategy 3: Fuzzy match (similar names)
                fuzzy_match = await self._find_fuzzy_entity_match(entity_info)
                if fuzzy_match:
                    matches.append(fuzzy_match)
                    continue
                
                logger.warning(f"No match found for entity: {entity_info.name}")
                
            except Exception as e:
                logger.error(f"Error matching entity {entity_info.name}: {e}")
                continue
        
        logger.info(f"Found {len(matches)} entity matches out of {len(analysis.entities)} query entities")
        return matches
    
    async def _find_exact_entity_match(self, entity_info: EntityInfo) -> Optional[EntityMatch]:
        """
        Find exact name match for an entity
        
        Args:
            entity_info: Entity information from query analysis
            
        Returns:
            EntityMatch if found, None otherwise
        """
        try:
            # Try to find by exact entity name
            entities = await EntityCollection.find_similar_entities_by_name(
                entity_info.name, 
                threshold=1.0  # Exact match only
            )
            
            for entity in entities:
                if entity.entity_name.lower() == entity_info.name.lower():
                    return EntityMatch(
                        query_entity=entity_info.name,
                        matched_entity=entity,
                        match_type="exact",
                        confidence=1.0,
                        reasoning=f"Exact name match: '{entity_info.name}' = '{entity.entity_name}'"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in exact entity match for {entity_info.name}: {e}")
            return None
    
    async def _find_alias_entity_match(self, entity_info: EntityInfo) -> Optional[EntityMatch]:
        """
        Find alias match for an entity
        
        Args:
            entity_info: Entity information from query analysis
            
        Returns:
            EntityMatch if found, None otherwise
        """
        try:
            # Search for entities where the query name appears in aliases
            entities = await EntityCollection.find_similar_entities_by_name(
                entity_info.name, 
                threshold=0.8
            )
            
            for entity in entities:
                # Check if query entity is in aliases (case-insensitive)
                aliases_lower = [alias.lower() for alias in entity.aliases]
                if entity_info.name.lower() in aliases_lower:
                    return EntityMatch(
                        query_entity=entity_info.name,
                        matched_entity=entity,
                        match_type="alias",
                        confidence=0.95,
                        reasoning=f"Alias match: '{entity_info.name}' found in aliases of '{entity.entity_name}'"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in alias entity match for {entity_info.name}: {e}")
            return None
    
    async def _find_fuzzy_entity_match(self, entity_info: EntityInfo) -> Optional[EntityMatch]:
        """
        Find fuzzy match for an entity using text similarity
        
        Args:
            entity_info: Entity information from query analysis
            
        Returns:
            EntityMatch if found, None otherwise
        """
        try:
            # Use MongoDB text search for fuzzy matching
            entities = await EntityCollection.find_similar_entities_by_name(
                entity_info.name, 
                threshold=0.7  # Fuzzy match threshold
            )
            
            if entities:
                # Take the first (most similar) match
                entity = entities[0]
                return EntityMatch(
                    query_entity=entity_info.name,
                    matched_entity=entity,
                    match_type="fuzzy",
                    confidence=0.8,
                    reasoning=f"Fuzzy match: '{entity_info.name}' similar to '{entity.entity_name}'"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fuzzy entity match for {entity_info.name}: {e}")
            return None
    
    async def traverse_graph(
        self,
        start_entities: List[EntityResponse],
        max_hops: int = 3,
        min_strength: float = 0.5,
        max_paths: int = 50
    ) -> List[GraphPath]:
        """
        Traverse the knowledge graph from starting entities using BFS
        
        This method explores the graph level by level, finding all paths
        from the starting entities within max_hops distance.
        
        Args:
            start_entities: List of entities to start traversal from
            max_hops: Maximum number of hops to traverse (default: 3)
            min_strength: Minimum relationship strength to follow (default: 0.5)
            max_paths: Maximum number of paths to return (default: 50)
            
        Returns:
            List of GraphPath objects representing discovered paths
            
        Example:
            start_entities = [p53_entity]
            max_hops = 2
            
            Returns paths like:
            - p53 → cancer (1 hop)
            - p53 → apoptosis → cancer (2 hops)
            - p53 → cell_cycle → tumor_growth (2 hops)
        """
        logger.info(f"Starting BFS traversal from {len(start_entities)} entities, max_hops={max_hops}")
        
        if not start_entities:
            logger.warning("No start entities provided for traversal")
            return []
        
        # BFS data structures
        queue = []  # (current_entity, path_so_far, current_hop)
        visited = set()  # Prevent cycles
        paths = []
        
        # Initialize queue with start entities
        for entity in start_entities:
            queue.append((entity, [entity.entity_name], 0))
            visited.add(entity.entity_name)
        
        while queue and len(paths) < max_paths:
            current_entity, current_path, current_hop = queue.pop(0)
            
            # Stop if we've reached max hops
            if current_hop >= max_hops:
                continue
            
            try:
                # Get all relationships for current entity
                relationships = await RelationshipCollection.get_relationships_by_entity(
                    current_entity.entity_name
                )
                
                # Filter by minimum strength
                valid_relationships = [
                    rel for rel in relationships 
                    if rel.relationship_strength >= min_strength
                ]
                
                logger.debug(f"Entity {current_entity.entity_name} has {len(valid_relationships)} valid relationships")
                
                for rel in valid_relationships:
                    # Determine the connected entity
                    if rel.source_entity == current_entity.entity_name:
                        connected_entity_name = rel.target_entity
                    else:
                        connected_entity_name = rel.source_entity
                    
                    # Skip if we've already visited this entity in this path
                    if connected_entity_name in current_path:
                        continue
                    
                    # Build new path
                    new_path = current_path + [connected_entity_name]
                    
                    # Create GraphPath object
                    path = GraphPath(
                        path=new_path,
                        entities=await self._get_path_entities(new_path),
                        relationships=await self._get_path_relationships(new_path),
                        total_strength=await self._calculate_path_strength(new_path),
                        metadata={
                            "hop_count": current_hop + 1,
                            "source_entity": start_entities[0].entity_name,
                            "traversal_type": "bfs",
                            "min_strength": min_strength
                        }
                    )
                    
                    paths.append(path)
                    
                    # Add to queue for further exploration
                    if current_hop + 1 < max_hops:
                        # Get the connected entity object
                        connected_entity = await self._get_entity_by_name(connected_entity_name)
                        if connected_entity:
                            queue.append((connected_entity, new_path, current_hop + 1))
                
            except Exception as e:
                logger.error(f"Error traversing from entity {current_entity.entity_name}: {e}")
                continue
        
        logger.info(f"BFS traversal completed: found {len(paths)} paths")
        return paths
    
    async def find_paths_between_entities(
        self,
        source_entities: List[EntityResponse],
        target_entities: List[EntityResponse],
        max_hops: int = 3,
        min_strength: float = 0.5
    ) -> List[GraphPath]:
        """
        Find all paths connecting source and target entities using bidirectional BFS
        
        This is the key method for relationship queries like:
        "How does p53 prevent cancer?"
        
        Algorithm:
        1. Start BFS from source entities (forward)
        2. Start BFS from target entities (backward)
        3. Find where they meet in the middle
        4. Construct complete paths
        
        Args:
            source_entities: List of source entities to start from
            target_entities: List of target entities to reach
            max_hops: Maximum number of hops allowed
            min_strength: Minimum relationship strength to follow
            
        Returns:
            List of GraphPath objects representing paths between entities
            
        Example:
            source_entities = [p53_entity]
            target_entities = [cancer_entity]
            max_hops = 3
            
            Returns paths like:
            - p53 → cancer (direct)
            - p53 → apoptosis → cancer (2 hops)
            - p53 → cell_cycle → tumor_growth → cancer (3 hops)
        """
        logger.info(f"Finding paths between {len(source_entities)} sources and {len(target_entities)} targets")
        
        if not source_entities or not target_entities:
            logger.warning("Missing source or target entities")
            return []
        
        # Convert entity lists to name sets for efficiency
        source_names = {entity.entity_name for entity in source_entities}
        target_names = {entity.entity_name for entity in target_entities}
        
        # Check for direct connections first
        direct_paths = await self._find_direct_connections(source_entities, target_entities, min_strength)
        
        # Find multi-hop paths using bidirectional BFS
        multi_hop_paths = await self._find_multi_hop_paths(
            source_entities, target_entities, max_hops, min_strength
        )
        
        all_paths = direct_paths + multi_hop_paths
        
        # Sort by path strength (strongest first)
        all_paths.sort(key=lambda p: p.total_strength, reverse=True)
        
        logger.info(f"Found {len(all_paths)} total paths between entities")
        return all_paths
    
    async def _find_direct_connections(
        self,
        source_entities: List[EntityResponse],
        target_entities: List[EntityResponse],
        min_strength: float
    ) -> List[GraphPath]:
        """Find direct (1-hop) connections between entities"""
        direct_paths = []
        
        for source in source_entities:
            for target in target_entities:
                try:
                    relationships = await RelationshipCollection.find_relationships_between_entities(
                        source.entity_name, target.entity_name
                    )
                    
                    for rel in relationships:
                        if rel.relationship_strength >= min_strength:
                            path = GraphPath(
                                path=[source.entity_name, target.entity_name],
                                entities=await self._get_path_entities([source.entity_name, target.entity_name]),
                                relationships=[rel.model_dump()],
                                total_strength=rel.relationship_strength,
                                metadata={
                                    "hop_count": 1,
                                    "connection_type": "direct",
                                    "relationship_type": rel.relationship_type,
                                    "evidence_count": len(rel.paper_ids)
                                }
                            )
                            direct_paths.append(path)
                            
                except Exception as e:
                    logger.error(f"Error finding direct connection between {source.entity_name} and {target.entity_name}: {e}")
                    continue
        
        return direct_paths
    
    async def _find_multi_hop_paths(
        self,
        source_entities: List[EntityResponse],
        target_entities: List[EntityResponse],
        max_hops: int,
        min_strength: float
    ) -> List[GraphPath]:
        """Find multi-hop paths using bidirectional BFS"""
        # For now, use simple BFS from sources
        # TODO: Implement true bidirectional BFS for better performance
        paths = []
        
        for source in source_entities:
            # Get all paths from this source
            source_paths = await self.traverse_graph([source], max_hops, min_strength)
            
            # Filter paths that end at target entities
            target_names = {entity.entity_name for entity in target_entities}
            relevant_paths = [
                path for path in source_paths 
                if path.path[-1] in target_names
            ]
            
            paths.extend(relevant_paths)
        
        return paths
    
    def score_path(self, path: GraphPath) -> PathScore:
        """
        Calculate relevance score for a graph path
        
        Scoring factors (from requirements):
        1. Path strength (40%): Product of relationship strengths
        2. Relationship relevance (30%): Weight of relationship types
        3. Evidence count (20%): Number of papers supporting relationships
        4. Path length penalty (10%): Shorter paths preferred
        
        Args:
            path: GraphPath to score
            
        Returns:
            PathScore object with detailed scoring information
        """
        try:
            # Factor 1: Path strength (40%)
            path_strength = path.total_strength
            
            # Factor 2: Relationship relevance (30%)
            relationship_relevance = self._calculate_relationship_relevance(path)
            
            # Factor 3: Evidence count (20%)
            evidence_count = self._count_path_evidence(path)
            normalized_evidence = min(evidence_count / 10.0, 1.0)  # Normalize to [0,1]
            
            # Factor 4: Path length penalty (10%)
            hop_count = path.metadata.get("hop_count", len(path.path) - 1)
            path_length_factor = self._calculate_path_length_factor(hop_count)
            
            # Calculate final score
            relevance_score = (
                0.4 * path_strength +
                0.3 * relationship_relevance +
                0.2 * normalized_evidence +
                0.1 * path_length_factor
            )
            
            # Ensure score is in [0, 1] range
            relevance_score = max(0.0, min(1.0, relevance_score))
            
            # Calculate confidence using noisy-OR (from requirements)
            confidence = self._calculate_noisy_or_confidence(path)
            
            return PathScore(
                path=path,
                relevance_score=relevance_score,
                path_strength=path_strength,
                evidence_count=evidence_count,
                hop_count=hop_count,
                relationship_types=[rel.get("relationship_type", "") for rel in path.relationships],
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error scoring path: {e}")
            # Return default score
            return PathScore(
                path=path,
                relevance_score=0.0,
                path_strength=0.0,
                evidence_count=0,
                hop_count=0,
                confidence=0.0
            )
    
    def _calculate_relationship_relevance(self, path: GraphPath) -> float:
        """Calculate average relevance of relationships in the path"""
        if not path.relationships:
            return 0.5  # Default
        
        total_weight = 0.0
        count = 0
        
        for rel in path.relationships:
            rel_type = rel.get("relationship_type", "")
            weight = self.relationship_weights.get(rel_type, self.relationship_weights["OTHER"])
            total_weight += weight
            count += 1
        
        return total_weight / count if count > 0 else 0.5
    
    def _count_path_evidence(self, path: GraphPath) -> int:
        """Count total evidence (papers) supporting this path"""
        evidence_count = 0
        
        for rel in path.relationships:
            paper_ids = rel.get("paper_ids", [])
            evidence_count += len(paper_ids)
        
        return evidence_count
    
    def _calculate_path_length_factor(self, hop_count: int) -> float:
        """Calculate path length factor (shorter paths preferred)"""
        if hop_count <= 1:
            return 1.0
        elif hop_count == 2:
            return 0.8
        elif hop_count == 3:
            return 0.6
        else:
            return 0.4  # 4+ hops
    
    def _calculate_noisy_or_confidence(self, path: GraphPath) -> float:
        """
        Calculate confidence using noisy-OR aggregation (from requirements)
        
        Formula: 1 - Π(1 - w_i), capped at 0.99
        """
        if not path.relationships:
            return 0.0
        
        product = 1.0
        for rel in path.relationships:
            strength = rel.get("relationship_strength", 0.0)
            product *= (1.0 - strength)
        
        confidence = 1.0 - product
        return min(confidence, 0.99)  # Cap at 0.99
    
    # Helper methods
    async def _get_entity_by_name(self, entity_name: str) -> Optional[EntityResponse]:
        """Get entity by name from database"""
        try:
            # Use the existing method from EntityCollection
            entities = await EntityCollection.find_similar_entities_by_name(entity_name, threshold=1.0)
            for entity in entities:
                if entity.entity_name.lower() == entity_name.lower():
                    return entity
            return None
        except Exception as e:
            logger.error(f"Error getting entity {entity_name}: {e}")
            return None
    
    async def _get_path_entities(self, entity_names: List[str]) -> List[Dict[str, Any]]:
        """Get entity details for a path"""
        entities = []
        for name in entity_names:
            entity = await self._get_entity_by_name(name)
            if entity:
                entities.append(entity.model_dump())
        return entities
    
    async def _get_path_relationships(self, entity_names: List[str]) -> List[Dict[str, Any]]:
        """Get relationship details for a path"""
        relationships = []
        
        for i in range(len(entity_names) - 1):
            source = entity_names[i]
            target = entity_names[i + 1]
            
            try:
                rels = await RelationshipCollection.find_relationships_between_entities(source, target)
                for rel in rels:
                    relationships.append(rel.model_dump())
            except Exception as e:
                logger.error(f"Error getting relationships between {source} and {target}: {e}")
                continue
        
        return relationships
    
    async def _calculate_path_strength(self, entity_names: List[str]) -> float:
        """Calculate total strength of a path"""
        if len(entity_names) < 2:
            return 0.0
        
        total_strength = 1.0
        
        for i in range(len(entity_names) - 1):
            source = entity_names[i]
            target = entity_names[i + 1]
            
            try:
                rels = await RelationshipCollection.find_relationships_between_entities(source, target)
                if rels:
                    # Use the strongest relationship between these entities
                    max_strength = max(rel.relationship_strength for rel in rels)
                    total_strength *= max_strength
                else:
                    # No relationship found, path is invalid
                    return 0.0
            except Exception as e:
                logger.error(f"Error calculating strength between {source} and {target}: {e}")
                return 0.0
        
        return total_strength
