"""
Graph-First Strategy Implementation

This strategy retrieves information by traversing the knowledge graph:
1. Finds entities mentioned in the query
2. Determines query type (single entity, entity pair, multi-entity)
3. Traverses relationships to find relevant paths
4. Converts graph paths to document sources
5. Returns QuerySource objects with graph path metadata

Best for:
- Relationship queries: "How does X affect Y?"
- Comparative queries: "Compare X and Y"
- Exploratory queries: "What does X interact with?"
- Causal queries: "Why does X cause Y?"

Example Usage:
    >>> strategy = GraphFirstStrategy(db)
    >>> sources = await strategy.retrieve(
    ...     query="How does p53 prevent cancer?",
    ...     analysis=QueryAnalysis(...),
    ...     max_results=10
    ... )
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.core.database import AsyncIOMotorDatabase
from app.models import QuerySource
from app.models.query_models import GraphPath
from app.services.query_analysis_service import QueryAnalysis, EntityInfo, QueryIntent, QueryComplexity
from app.services.graph_traversal_service import GraphTraversalService, EntityMatch, PathScore
from app.services.retrieval_strategies.base_strategy import BaseRetrievalStrategy

logger = logging.getLogger(__name__)


@dataclass
class QueryType:
    """Types of queries that Graph-First Strategy can handle"""
    SINGLE_ENTITY = "single_entity"        # "What does CRISPR do?"
    ENTITY_PAIR = "entity_pair"            # "How does p53 affect cancer?"
    MULTI_ENTITY = "multi_entity"          # "How are p53, BRCA1, and cancer related?"
    EXPLORATION = "exploration"            # "What cancer treatments exist?"


class GraphFirstStrategy(BaseRetrievalStrategy):
    """
    Graph-First retrieval strategy using knowledge graph traversal
    
    This strategy is optimized for relationship-based queries where understanding
    how entities connect is more important than semantic similarity.
    
    Query Types Handled:
    1. Single Entity: Explore connections from one entity
    2. Entity Pair: Find paths between two entities  
    3. Multi Entity: Analyze relationships among multiple entities
    4. Exploration: General graph exploration without specific targets
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize Graph-First Strategy
        
        Args:
            db: MongoDB database connection
        """
        super().__init__(db)
        self.graph_traversal = GraphTraversalService(db)
        
        logger.info("GraphFirstStrategy initialized with GraphTraversalService")
    
    async def retrieve(
        self,
        query: str,
        analysis: QueryAnalysis,
        max_results: int = 10,
        min_strength: float = 0.5,
        max_hops: int = 3,
        **kwargs
    ) -> List[QuerySource]:
        """
        Main retrieval method using graph traversal
        
        Process:
        1. Find entities in the query using GraphTraversalService
        2. Determine query type based on entity count and intent
        3. Execute appropriate traversal strategy
        4. Convert graph paths to QuerySource objects
        5. Return ranked sources with graph metadata
        
        Args:
            query: Original user query
            analysis: QueryAnalysis result from QueryAnalysisService
            max_results: Maximum number of sources to return
            min_strength: Minimum relationship strength to follow
            max_hops: Maximum number of hops for traversal
            **kwargs: Additional parameters
            
        Returns:
            List of QuerySource objects with graph path information
            
        Example:
            Query: "How does p53 prevent cancer?"
            Process:
            1. Find entities: [p53, cancer]
            2. Query type: ENTITY_PAIR
            3. Find paths: p53 → cancer (direct), p53 → apoptosis → cancer (2-hop)
            4. Convert to sources with metadata showing graph paths
        """
        logger.info(f"Graph-First retrieval for query: '{query}'")
        logger.info(f"Analysis: {analysis.intent.value}, {len(analysis.entities)} entities")
        
        try:
            # Step 1: Find entities in the knowledge graph
            entity_matches = await self.graph_traversal.find_entities_in_query(query, analysis)
            
            if not entity_matches:
                logger.warning("No entities found in knowledge graph")
                return []
            
            logger.info(f"Found {len(entity_matches)} entity matches")
            
            # Step 2: Determine query type
            query_type = self._determine_query_type(analysis, entity_matches)
            logger.info(f"Detected query type: {query_type}")
            
            # Step 3: Execute appropriate strategy
            if query_type == QueryType.SINGLE_ENTITY:
                paths, sources = await self._single_entity_exploration(
                    entity_matches[0], max_hops, min_strength, max_results
                )
            elif query_type == QueryType.ENTITY_PAIR:
                paths, sources = await self._entity_pair_path_finding(
                    entity_matches, max_hops, min_strength, max_results
                )
            elif query_type == QueryType.MULTI_ENTITY:
                paths, sources = await self._multi_entity_analysis(
                    entity_matches, max_hops, min_strength, max_results
                )
            else:  # EXPLORATION
                paths, sources = await self._exploration_query(
                    entity_matches, max_hops, min_strength, max_results
                )
            
            # Step 4: Rank and limit results
            ranked_sources = self._rank_sources(sources, analysis)
            final_sources = ranked_sources[:max_results]
            
            logger.info(f"Graph-First retrieval completed: {len(final_sources)} sources")
            return final_sources
            
        except Exception as e:
            logger.error(f"Error in Graph-First retrieval: {e}")
            return []
    
    def _determine_query_type(self, analysis: QueryAnalysis, entity_matches: List[EntityMatch]) -> str:
        """
        Determine what type of graph query this is
        
        Args:
            analysis: Query analysis from QueryAnalysisService
            entity_matches: Successfully matched entities
            
        Returns:
            Query type string
        """
        entity_count = len(entity_matches)
        
        # Single entity queries
        if entity_count == 1:
            if analysis.intent in [QueryIntent.EXPLORATORY, QueryIntent.FACTUAL]:
                return QueryType.SINGLE_ENTITY
            else:
                return QueryType.EXPLORATION
        
        # Multiple entity queries
        elif entity_count == 2:
            if analysis.intent in [QueryIntent.CAUSAL, QueryIntent.COMPARATIVE]:
                return QueryType.ENTITY_PAIR
            else:
                return QueryType.MULTI_ENTITY
        
        # Three or more entities
        elif entity_count >= 3:
            return QueryType.MULTI_ENTITY
        
        # Fallback
        else:
            return QueryType.EXPLORATION
    
    async def _single_entity_exploration(
        self,
        entity_match: EntityMatch,
        max_hops: int,
        min_strength: float,
        max_results: int
    ) -> Tuple[List[GraphPath], List[QuerySource]]:
        """
        Explore connections from a single entity
        
        Used for queries like:
        - "What does CRISPR target?"
        - "What regulates p53?"
        - "What diseases are associated with BRCA1?"
        
        Process:
        1. Start BFS traversal from the entity
        2. Score paths by relevance and strength
        3. Convert paths to sources
        4. Return top results
        
        Args:
            entity_match: The entity to explore from
            max_hops: Maximum traversal depth
            min_strength: Minimum relationship strength
            max_results: Maximum results to return
            
        Returns:
            Tuple of (graph_paths, query_sources)
        """
        logger.info(f"Single entity exploration from: {entity_match.matched_entity.entity_name}")
        
        # Traverse graph from this entity
        paths = await self.graph_traversal.traverse_graph(
            [entity_match.matched_entity],
            max_hops=max_hops,
            min_strength=min_strength,
            max_paths=max_results * 2  # Get more paths to filter
        )
        
        # Score all paths
        scored_paths = []
        for path in paths:
            score = self.graph_traversal.score_path(path)
            scored_paths.append(score)
        
        # Sort by relevance score
        scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
        
        # Convert to sources
        sources = await self._paths_to_sources(scored_paths[:max_results])
        
        logger.info(f"Single entity exploration found {len(sources)} sources")
        return [score.path for score in scored_paths[:max_results]], sources
    
    async def _entity_pair_path_finding(
        self,
        entity_matches: List[EntityMatch],
        max_hops: int,
        min_strength: float,
        max_results: int
    ) -> Tuple[List[GraphPath], List[QuerySource]]:
        """
        Find paths connecting two entities
        
        Used for queries like:
        - "How does p53 prevent cancer?"
        - "What's the relationship between CRISPR and gene therapy?"
        - "How does insulin regulate glucose?"
        
        Process:
        1. Use bidirectional search to find paths between entities
        2. Score paths by strength and relevance
        3. Convert to sources with relationship information
        4. Return ranked results
        
        Args:
            entity_matches: List of matched entities (should be 2)
            max_hops: Maximum path length
            min_strength: Minimum relationship strength
            max_results: Maximum results to return
            
        Returns:
            Tuple of (graph_paths, query_sources)
        """
        if len(entity_matches) < 2:
            logger.warning("Entity pair path finding requires at least 2 entities")
            return [], []
        
        source_entity = entity_matches[0].matched_entity
        target_entity = entity_matches[1].matched_entity
        
        logger.info(f"Finding paths between: {source_entity.entity_name} → {target_entity.entity_name}")
        
        # Find paths between entities
        paths = await self.graph_traversal.find_paths_between_entities(
            [source_entity], [target_entity],
            max_hops=max_hops,
            min_strength=min_strength
        )
        
        # Score all paths
        scored_paths = []
        for path in paths:
            score = self.graph_traversal.score_path(path)
            scored_paths.append(score)
        
        # Sort by relevance score
        scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
        
        # Convert to sources
        sources = await self._paths_to_sources(scored_paths[:max_results])
        
        logger.info(f"Entity pair path finding found {len(sources)} sources")
        return [score.path for score in scored_paths[:max_results]], sources
    
    async def _multi_entity_analysis(
        self,
        entity_matches: List[EntityMatch],
        max_hops: int,
        min_strength: float,
        max_results: int
    ) -> Tuple[List[GraphPath], List[QuerySource]]:
        """
        Analyze relationships among multiple entities
        
        Used for queries like:
        - "How are p53, BRCA1, and cancer related?"
        - "What connects CRISPR, gene therapy, and genetic diseases?"
        - "Compare insulin, glucagon, and diabetes"
        
        Process:
        1. Find all pairwise paths between entities
        2. Identify common connections (hubs)
        3. Build subgraph of related entities
        4. Score by interconnectedness
        
        Args:
            entity_matches: List of matched entities (3 or more)
            max_hops: Maximum path length
            min_strength: Minimum relationship strength
            max_results: Maximum results to return
            
        Returns:
            Tuple of (graph_paths, query_sources)
        """
        if len(entity_matches) < 3:
            logger.warning("Multi-entity analysis requires at least 3 entities")
            return [], []
        
        entity_names = [em.matched_entity.entity_name for em in entity_matches]
        logger.info(f"Multi-entity analysis for: {', '.join(entity_names)}")
        
        # Find all pairwise paths
        all_paths = []
        for i in range(len(entity_matches)):
            for j in range(i + 1, len(entity_matches)):
                source = entity_matches[i].matched_entity
                target = entity_matches[j].matched_entity
                
                paths = await self.graph_traversal.find_paths_between_entities(
                    [source], [target],
                    max_hops=max_hops,
                    min_strength=min_strength
                )
                all_paths.extend(paths)
        
        # Score all paths
        scored_paths = []
        for path in all_paths:
            score = self.graph_traversal.score_path(path)
            # Boost score for paths that connect multiple query entities
            multi_entity_boost = self._calculate_multi_entity_boost(path, entity_names)
            score.relevance_score = min(1.0, score.relevance_score + multi_entity_boost)
            scored_paths.append(score)
        
        # Sort by enhanced relevance score
        scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
        
        # Convert to sources
        sources = await self._paths_to_sources(scored_paths[:max_results])
        
        logger.info(f"Multi-entity analysis found {len(sources)} sources")
        return [score.path for score in scored_paths[:max_results]], sources
    
    async def _exploration_query(
        self,
        entity_matches: List[EntityMatch],
        max_hops: int,
        min_strength: float,
        max_results: int
    ) -> Tuple[List[GraphPath], List[QuerySource]]:
        """
        General exploration query without specific targets
        
        Used for queries like:
        - "What cancer treatments are there?"
        - "Tell me about CRISPR applications"
        - "Recent developments in gene therapy"
        
        Process:
        1. Start from all matched entities
        2. Explore broadly using BFS
        3. Score by entity frequency and path strength
        4. Return diverse results
        
        Args:
            entity_matches: List of matched entities
            max_hops: Maximum traversal depth
            min_strength: Minimum relationship strength
            max_results: Maximum results to return
            
        Returns:
            Tuple of (graph_paths, query_sources)
        """
        logger.info(f"Exploration query from {len(entity_matches)} entities")
        
        entities = [em.matched_entity for em in entity_matches]
        
        # Traverse from all entities
        all_paths = []
        for entity in entities:
            paths = await self.graph_traversal.traverse_graph(
                [entity],
                max_hops=max_hops,
                min_strength=min_strength,
                max_paths=max_results
            )
            all_paths.extend(paths)
        
        # Score all paths
        scored_paths = []
        for path in all_paths:
            score = self.graph_traversal.score_path(path)
            # Boost score for exploration diversity
            diversity_boost = self._calculate_diversity_boost(path, entities)
            score.relevance_score = min(1.0, score.relevance_score + diversity_boost)
            scored_paths.append(score)
        
        # Sort by enhanced relevance score
        scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
        
        # Convert to sources
        sources = await self._paths_to_sources(scored_paths[:max_results])
        
        logger.info(f"Exploration query found {len(sources)} sources")
        return [score.path for score in scored_paths[:max_results]], sources
    
    async def _paths_to_sources(
        self,
        scored_paths: List[PathScore]
    ) -> List[QuerySource]:
        """
        Convert graph paths to QuerySource objects
        
        Process:
        1. Extract paper_ids and section_ids from relationships
        2. Fetch document and section metadata
        3. Build QuerySource objects with graph metadata
        4. Calculate relevance scores from path scores
        
        Args:
            scored_paths: List of scored graph paths
            
        Returns:
            List of QuerySource objects
        """
        sources = []
        
        for path_score in scored_paths:
            path = path_score.path
            
            # Extract all unique paper_ids and section_ids from relationships
            paper_ids = set()
            section_ids = set()
            
            for rel in path.relationships:
                paper_ids.update(rel.get("paper_ids", []))
                section_ids.update(rel.get("section_ids", []))
            
            # Create QuerySource for each unique document
            for paper_id in paper_ids:
                try:
                    # Fetch document metadata
                    doc_metadata = await self._fetch_document_metadata(paper_id)
                    
                    # Find sections for this document
                    doc_sections = [sid for sid in section_ids if sid.startswith(f"{paper_id}_")]
                    
                    for section_id in doc_sections:
                        section_metadata = await self._fetch_section_metadata(section_id)
                        
                        source = QuerySource(
                            document_id=paper_id,
                            document_title=doc_metadata.get("title", "Unknown Document"),
                            section_id=section_id,
                            section_type=section_metadata.get("section_type", "unknown"),
                            content=section_metadata.get("text", ""),
                            relevance_score=path_score.relevance_score,
                            doi=doc_metadata.get("doi"),
                            metadata={
                                "strategy_used": "graph_first",
                                "strategy_confidence": path_score.confidence,
                                "graph_path": path.path,
                                "path_strength": path_score.path_strength,
                                "evidence_count": path_score.evidence_count,
                                "hop_count": path_score.hop_count,
                                "relationship_types": path_score.relationship_types,
                                "traversal_type": "graph_first"
                            }
                        )
                        sources.append(source)
                        
                except Exception as e:
                    logger.error(f"Error converting path to source for paper {paper_id}: {e}")
                    continue
        
        return sources
    
    async def _fetch_section_metadata(self, section_id: str) -> Dict[str, Any]:
        """
        Fetch section metadata from database
        
        Args:
            section_id: Section identifier
            
        Returns:
            Section metadata dictionary
        """
        try:
            section = await self.sections_collection.find_one({"_id": section_id})
            if section:
                return {
                    "text": section.get("text", ""),
                    "section_type": section.get("section_type", "unknown"),
                    "title": section.get("title", "")
                }
        except Exception as e:
            logger.error(f"Error fetching section metadata for {section_id}: {e}")
        
        return {"text": "", "section_type": "unknown", "title": ""}
    
    def _calculate_multi_entity_boost(self, path: GraphPath, entity_names: List[str]) -> float:
        """
        Calculate boost score for paths connecting multiple query entities
        
        Args:
            path: Graph path to evaluate
            entity_names: Names of entities in the original query
            
        Returns:
            Boost score (0.0 to 0.2)
        """
        path_entities = set(path.path)
        query_entities = set(entity_names)
        
        # Count how many query entities are in this path
        connected_count = len(path_entities.intersection(query_entities))
        
        # Boost based on connectivity
        if connected_count >= 3:
            return 0.2
        elif connected_count == 2:
            return 0.1
        else:
            return 0.0
    
    def _calculate_diversity_boost(self, path: GraphPath, entities: List) -> float:
        """
        Calculate boost score for exploration diversity
        
        Args:
            path: Graph path to evaluate
            entities: Starting entities
            
        Returns:
            Boost score (0.0 to 0.15)
        """
        # Boost longer paths for exploration (more diverse)
        hop_count = path.metadata.get("hop_count", 0)
        
        if hop_count >= 3:
            return 0.15
        elif hop_count == 2:
            return 0.1
        else:
            return 0.05
    
    def _rank_sources(self, sources: List[QuerySource], analysis: QueryAnalysis) -> List[QuerySource]:
        """
        Rank sources based on multiple factors
        
        Args:
            sources: List of QuerySource objects
            analysis: Original query analysis
            
        Returns:
            Ranked list of QuerySource objects
        """
        # Sort by relevance score (already calculated)
        ranked = sorted(sources, key=lambda s: s.relevance_score, reverse=True)
        
        # Apply additional ranking factors
        for source in ranked:
            # Boost for high-confidence paths
            confidence_boost = source.metadata.get("strategy_confidence", 0.0) * 0.1
            
            # Boost for shorter paths (more direct)
            hop_penalty = source.metadata.get("hop_count", 0) * 0.05
            
            # Final score
            source.relevance_score = min(1.0, source.relevance_score + confidence_boost - hop_penalty)
        
        # Re-sort with final scores
        return sorted(ranked, key=lambda s: s.relevance_score, reverse=True)
    
    def get_strategy_name(self) -> str:
        """Returns the name of the strategy"""
        return "GraphFirstStrategy"
