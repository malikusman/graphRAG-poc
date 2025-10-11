"""
Hybrid Retrieval Strategy

Combines Vector-First and Graph-First strategies to leverage both semantic similarity
and structural knowledge graph traversal. This strategy is ideal for complex queries
that benefit from multiple retrieval perspectives.

Key Features:
- Parallel execution of both strategies using asyncio
- Intelligent result fusion with deduplication
- Confidence-based weighting and ranking
- Graceful degradation if one strategy fails

Architecture:
    Query → [Vector-First ∥ Graph-First] → Merge → Deduplicate → Rank → Results
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import logging
from collections import defaultdict

from app.core.database import AsyncIOMotorDatabase
from app.models import QuerySource
from app.services.query_analysis_service import QueryAnalysis, QueryIntent
from app.services.retrieval_strategies.base_strategy import BaseRetrievalStrategy
from app.services.retrieval_strategies.vector_first_strategy import VectorFirstStrategy
from app.services.retrieval_strategies.graph_first_strategy import GraphFirstStrategy
from app.utils.vector_utils import cosine_similarity

logger = logging.getLogger(__name__)


class HybridStrategy(BaseRetrievalStrategy):
    """
    Hybrid retrieval strategy that combines Vector-First and Graph-First approaches.
    
    This strategy executes both vector search and graph traversal in parallel,
    then intelligently merges and ranks the results. Sources found by both strategies
    receive a confidence boost, as agreement between different retrieval methods
    indicates higher relevance.
    
    Example:
        >>> strategy = HybridStrategy(db)
        >>> sources = await strategy.retrieve(
        ...     query="Compare CRISPR and traditional gene therapy",
        ...     analysis=analysis,
        ...     max_results=10
        ... )
        >>> # Returns merged results from vector + graph search
    
    Attributes:
        vector_strategy: Vector-First retrieval strategy
        graph_strategy: Graph-First retrieval strategy
        vector_weight: Weight for vector confidence (0.0-1.0)
        graph_weight: Weight for graph confidence (0.0-1.0)
        dedup_threshold: Content similarity threshold for deduplication
    """
    
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
        dedup_threshold: float = 0.85,
        agreement_boost: float = 0.1
    ):
        """
        Initialize Hybrid Strategy.
        
        Args:
            db: MongoDB database connection
            vector_weight: Weight for vector confidence scores (default: 0.6)
            graph_weight: Weight for graph confidence scores (default: 0.4)
            dedup_threshold: Content similarity threshold for deduplication (default: 0.85)
            agreement_boost: Bonus multiplier when both strategies agree (default: 0.1 = 10%)
        """
        super().__init__(db)
        
        # Initialize both strategies
        self.vector_strategy = VectorFirstStrategy(db)
        self.graph_strategy = GraphFirstStrategy(db)
        
        # Configuration
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
        self.dedup_threshold = dedup_threshold
        self.agreement_boost = agreement_boost
        
        # Validate weights
        if not (0 <= vector_weight <= 1 and 0 <= graph_weight <= 1):
            raise ValueError("Weights must be between 0 and 1")
        if abs(vector_weight + graph_weight - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: vector={vector_weight}, graph={graph_weight}")
        
        logger.info(f"HybridStrategy initialized: vector_weight={vector_weight}, "
                   f"graph_weight={graph_weight}, dedup_threshold={dedup_threshold}")
    
    async def retrieve(
        self,
        query: str,
        analysis: QueryAnalysis,
        max_results: int = 10,
        **kwargs
    ) -> List[QuerySource]:
        """
        Execute hybrid retrieval strategy.
        
        Process:
        1. Run Vector-First and Graph-First strategies in parallel
        2. Merge results from both strategies
        3. Deduplicate sources (exact + fuzzy matching)
        4. Aggregate confidence scores with weighted combination
        5. Re-rank and limit to max_results
        
        Args:
            query: User's query text
            analysis: QueryAnalysis result
            max_results: Maximum number of sources to return
            **kwargs: Additional parameters passed to strategies
        
        Returns:
            List of QuerySource objects, ranked by combined confidence
        """
        start_time = datetime.now()
        
        logger.info(f"Starting Hybrid retrieval for query: '{query}' (max_results={max_results})")
        logger.info(f"Query analysis: intent={analysis.intent.value}, "
                   f"complexity={analysis.complexity.value}, {len(analysis.entities)} entities")
        
        try:
            # Step 1: Execute both strategies in parallel
            vector_sources, graph_sources = await self._execute_parallel_strategies(
                query, analysis, max_results, **kwargs
            )
            
            logger.info(f"Parallel execution complete: vector={len(vector_sources)}, "
                       f"graph={len(graph_sources)} sources")
            
            # Handle empty results
            if not vector_sources and not graph_sources:
                logger.warning("Both strategies returned empty results")
                return []
            
            # Step 2: Merge results from both strategies
            merged_sources = self._merge_results(vector_sources, graph_sources)
            logger.info(f"Merged {len(merged_sources)} total sources")
            
            # Step 3: Deduplicate sources
            deduplicated_sources = self._deduplicate_sources(merged_sources)
            logger.info(f"After deduplication: {len(deduplicated_sources)} unique sources")
            
            # Step 4: Re-rank sources
            ranked_sources = self._rank_sources(deduplicated_sources, analysis)
            
            # Step 5: Limit to max_results
            final_sources = ranked_sources[:max_results]
            
            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Hybrid retrieval complete: {len(final_sources)} sources "
                       f"(duration={duration:.2f}s)")
            
            # Log strategy distribution
            vector_only = sum(1 for s in final_sources if s.metadata.get("retrieval_strategy") == "vector")
            graph_only = sum(1 for s in final_sources if s.metadata.get("retrieval_strategy") == "graph")
            both = sum(1 for s in final_sources if s.metadata.get("retrieval_strategy") == "hybrid")
            
            logger.info(f"Strategy distribution: vector_only={vector_only}, "
                       f"graph_only={graph_only}, both={both}")
            
            return final_sources
            
        except Exception as e:
            logger.error(f"Error in Hybrid retrieval: {e}", exc_info=True)
            return []
    
    async def _execute_parallel_strategies(
        self,
        query: str,
        analysis: QueryAnalysis,
        max_results: int,
        **kwargs
    ) -> Tuple[List[QuerySource], List[QuerySource]]:
        """
        Execute both strategies in parallel using asyncio.gather.
        
        This method runs Vector-First and Graph-First strategies simultaneously
        to minimize latency. If one strategy fails, the other continues.
        
        Args:
            query: User's query text
            analysis: QueryAnalysis result
            max_results: Maximum results per strategy
            **kwargs: Additional parameters for strategies
        
        Returns:
            Tuple of (vector_sources, graph_sources)
        """
        logger.info("Executing Vector-First and Graph-First in parallel...")
        
        # Create tasks for parallel execution
        vector_task = asyncio.create_task(
            self._safe_retrieve(self.vector_strategy, query, analysis, max_results, **kwargs)
        )
        graph_task = asyncio.create_task(
            self._safe_retrieve(self.graph_strategy, query, analysis, max_results, **kwargs)
        )
        
        # Wait for both to complete
        vector_sources, graph_sources = await asyncio.gather(vector_task, graph_task)
        
        return vector_sources, graph_sources
    
    async def _safe_retrieve(
        self,
        strategy: BaseRetrievalStrategy,
        query: str,
        analysis: QueryAnalysis,
        max_results: int,
        **kwargs
    ) -> List[QuerySource]:
        """
        Safely execute a strategy's retrieve method with error handling.
        
        Args:
            strategy: The retrieval strategy to execute
            query: User's query text
            analysis: QueryAnalysis result
            max_results: Maximum number of results
            **kwargs: Additional parameters
        
        Returns:
            List of QuerySource objects, or empty list if strategy fails
        """
        try:
            sources = await strategy.retrieve(query, analysis, max_results, **kwargs)
            logger.info(f"{strategy.get_strategy_name()} returned {len(sources)} sources")
            return sources
        except Exception as e:
            logger.error(f"Error in {strategy.get_strategy_name()}: {e}", exc_info=True)
            return []
    
    def _merge_results(
        self,
        vector_sources: List[QuerySource],
        graph_sources: List[QuerySource]
    ) -> List[QuerySource]:
        """
        Merge results from both strategies.
        
        This method combines sources from vector and graph strategies, tagging
        each with its origin. Sources will be deduplicated in a later step.
        
        Strategy:
        - Add all vector sources with 'vector' tag
        - Add all graph sources with 'graph' tag
        - Deduplication happens later in _deduplicate_sources()
        
        Args:
            vector_sources: Sources from Vector-First strategy
            graph_sources: Sources from Graph-First strategy
        
        Returns:
            Combined list of sources with origin tags
        """
        merged = []
        
        # Add vector sources with tag
        for source in vector_sources:
            source.metadata["retrieval_strategy"] = "vector"
            source.metadata["vector_confidence"] = source.relevance_score
            merged.append(source)
        
        # Add graph sources with tag
        for source in graph_sources:
            source.metadata["retrieval_strategy"] = "graph"
            source.metadata["graph_confidence"] = source.relevance_score
            merged.append(source)
        
        logger.debug(f"Merged {len(vector_sources)} vector + {len(graph_sources)} graph sources")
        
        return merged
    
    def _deduplicate_sources(
        self,
        sources: List[QuerySource]
    ) -> List[QuerySource]:
        """
        Remove duplicate sources using exact and fuzzy matching.
        
        Deduplication Methods:
        1. Exact Match: Same section_id (if available)
        2. Fuzzy Match: High content similarity (> dedup_threshold)
        
        When duplicates are found:
        - Aggregate confidence from both strategies
        - Merge metadata
        - Combine graph_paths if present
        - Keep the version with higher combined confidence
        
        Args:
            sources: List of QuerySource objects (potentially with duplicates)
        
        Returns:
            Deduplicated list of QuerySource objects
        """
        if not sources:
            return []
        
        logger.info(f"Deduplicating {len(sources)} sources...")
        
        # Track unique sources
        unique_sources: List[QuerySource] = []
        seen_section_ids: Set[str] = set()
        
        # Group sources by section_id for exact matching
        section_id_groups: Dict[str, List[QuerySource]] = defaultdict(list)
        sources_without_id: List[QuerySource] = []
        
        for source in sources:
            section_id = source.metadata.get("section_id")
            if section_id:
                section_id_groups[section_id].append(source)
            else:
                sources_without_id.append(source)
        
        # Process groups with same section_id
        for section_id, group in section_id_groups.items():
            if len(group) == 1:
                # No duplicates
                unique_sources.append(group[0])
            else:
                # Found duplicates - merge them
                merged_source = self._merge_duplicate_sources(group)
                unique_sources.append(merged_source)
                logger.debug(f"Merged {len(group)} sources with section_id={section_id}")
        
        # Process sources without section_id (fuzzy matching by content)
        for source in sources_without_id:
            duplicate_found = False
            
            # Check against existing unique sources
            for existing in unique_sources:
                if self._is_content_duplicate(source, existing):
                    # Found a fuzzy duplicate - merge them
                    merged_source = self._merge_duplicate_sources([existing, source])
                    # Replace existing with merged
                    idx = unique_sources.index(existing)
                    unique_sources[idx] = merged_source
                    duplicate_found = True
                    logger.debug(f"Merged duplicate by content similarity")
                    break
            
            if not duplicate_found:
                unique_sources.append(source)
        
        removed_count = len(sources) - len(unique_sources)
        logger.info(f"Deduplication complete: removed {removed_count} duplicates, "
                   f"{len(unique_sources)} unique sources remain")
        
        return unique_sources
    
    def _is_content_duplicate(
        self,
        source1: QuerySource,
        source2: QuerySource
    ) -> bool:
        """
        Check if two sources are duplicates based on content similarity.
        
        Uses cosine similarity on content embeddings (if available) or
        simple text comparison as fallback.
        
        Args:
            source1: First QuerySource
            source2: Second QuerySource
        
        Returns:
            True if sources are duplicates (similarity > dedup_threshold)
        """
        # Check if both have embeddings
        emb1 = source1.metadata.get("embedding")
        emb2 = source2.metadata.get("embedding")
        
        if emb1 and emb2:
            similarity = cosine_similarity(emb1, emb2)
            return similarity > self.dedup_threshold
        
        # Fallback: simple text comparison
        content1 = source1.content.strip().lower()
        content2 = source2.content.strip().lower()
        
        # Check for exact match or one contains the other
        if content1 == content2:
            return True
        if content1 in content2 or content2 in content1:
            return True
        
        return False
    
    def _merge_duplicate_sources(
        self,
        duplicates: List[QuerySource]
    ) -> QuerySource:
        """
        Merge multiple duplicate sources into a single source.
        
        Strategy:
        - Use the first source as the base
        - Aggregate confidence scores from all duplicates
        - Merge metadata from all sources
        - Combine graph_paths if present
        - Tag as 'hybrid' if from both strategies
        
        Args:
            duplicates: List of duplicate QuerySource objects
        
        Returns:
            Single merged QuerySource
        """
        if len(duplicates) == 1:
            return duplicates[0]
        
        # Use first source as base
        base_source = duplicates[0]
        
        # Check if duplicates come from different strategies
        strategies = set(s.metadata.get("retrieval_strategy") for s in duplicates)
        is_hybrid = len(strategies) > 1
        
        # Aggregate confidence
        vector_conf = None
        graph_conf = None
        
        for source in duplicates:
            if "vector_confidence" in source.metadata:
                vector_conf = max(vector_conf or 0, source.metadata["vector_confidence"])
            if "graph_confidence" in source.metadata:
                graph_conf = max(graph_conf or 0, source.metadata["graph_confidence"])
        
        # Calculate combined confidence
        combined_confidence = self._calculate_combined_confidence(vector_conf, graph_conf)
        
        # Merge metadata
        merged_metadata = base_source.metadata.copy()
        
        if vector_conf is not None:
            merged_metadata["vector_confidence"] = vector_conf
        if graph_conf is not None:
            merged_metadata["graph_confidence"] = graph_conf
        
        # Tag as hybrid if from both strategies
        if is_hybrid:
            merged_metadata["retrieval_strategy"] = "hybrid"
            merged_metadata["strategy_agreement"] = True
        
        # Merge graph_paths
        all_paths = []
        for source in duplicates:
            source_paths = source.metadata.get("graph_paths", [])
            if source_paths:
                all_paths.extend(source_paths)
        
        if all_paths:
            merged_metadata["graph_paths"] = all_paths
        
        # Create merged source
        merged_source = QuerySource(
            content=base_source.content,
            document_id=base_source.document_id,
            document_title=base_source.document_title,
            section_id=base_source.section_id,
            section_type=base_source.section_type,
            relevance_score=combined_confidence,
            doi=base_source.doi,
            metadata=merged_metadata
        )
        
        return merged_source
    
    def _calculate_combined_confidence(
        self,
        vector_conf: Optional[float],
        graph_conf: Optional[float]
    ) -> float:
        """
        Calculate combined confidence score from vector and graph confidences.
        
        Strategy:
        - Vector-only: Use vector confidence
        - Graph-only: Use graph confidence
        - Both: Weighted combination + agreement boost
        
        Formula (when both present):
            base_conf = (vector_conf × vector_weight) + (graph_conf × graph_weight)
            if both > 0.7: boost by agreement_boost (default 10%)
        
        Args:
            vector_conf: Confidence from vector strategy (or None)
            graph_conf: Confidence from graph strategy (or None)
        
        Returns:
            Combined confidence score (0.0-1.0)
        """
        # Only vector confidence
        if vector_conf is not None and graph_conf is None:
            return vector_conf
        
        # Only graph confidence
        if graph_conf is not None and vector_conf is None:
            return graph_conf
        
        # Both confidences present
        if vector_conf is not None and graph_conf is not None:
            # Weighted combination
            base_confidence = (vector_conf * self.vector_weight) + (graph_conf * self.graph_weight)
            
            # Apply agreement boost if both have high confidence
            if vector_conf > 0.7 and graph_conf > 0.7:
                boosted_confidence = base_confidence * (1 + self.agreement_boost)
                final_confidence = min(1.0, boosted_confidence)
                logger.debug(f"Agreement boost applied: {base_confidence:.3f} → {final_confidence:.3f}")
                return final_confidence
            
            return base_confidence
        
        # Fallback (should not happen)
        return 0.5
    
    def _rank_sources(
        self,
        sources: List[QuerySource],
        analysis: QueryAnalysis
    ) -> List[QuerySource]:
        """
        Re-rank sources based on combined confidence and other factors.
        
        Ranking Factors:
        1. Combined confidence score (primary)
        2. Strategy diversity bonus (sources from both strategies)
        3. Query intent alignment
        4. Graph path quality (if present)
        
        Args:
            sources: List of QuerySource objects
            analysis: QueryAnalysis result
        
        Returns:
            Sorted list of QuerySource objects (highest confidence first)
        """
        if not sources:
            return []
        
        logger.info(f"Ranking {len(sources)} sources...")
        
        # Calculate ranking score for each source
        scored_sources = []
        
        for source in sources:
            base_score = source.relevance_score
            
            # Bonus for hybrid sources (found by both strategies)
            if source.metadata.get("retrieval_strategy") == "hybrid":
                base_score *= 1.05  # 5% bonus
                logger.debug(f"Applied hybrid bonus to source: {source.document_title[:50]}...")
            
            # Bonus for graph paths (structural evidence)
            graph_paths = source.metadata.get("graph_paths", [])
            if graph_paths and len(graph_paths) > 0:
                path_bonus = min(0.05 * len(graph_paths), 0.15)  # Up to 15% bonus
                base_score *= (1 + path_bonus)
            
            # Intent alignment bonus
            if analysis.intent == QueryIntent.CAUSAL and graph_paths:
                base_score *= 1.05  # Causal queries benefit from graph paths
            elif analysis.intent == QueryIntent.FACTUAL and source.metadata.get("vector_confidence"):
                base_score *= 1.05  # Factual queries benefit from semantic match
            
            scored_sources.append((base_score, source))
        
        # Sort by score (descending)
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        
        # Extract sources
        ranked_sources = [source for _, source in scored_sources]
        
        if ranked_sources:
            logger.info(f"Ranking complete: top relevance_score={ranked_sources[0].relevance_score:.3f}")
        
        return ranked_sources
    
    def get_strategy_name(self) -> str:
        """Returns the name of the strategy"""
        return "HybridStrategy"
    
    def __str__(self) -> str:
        """String representation of the strategy"""
        return (f"HybridStrategy: Combines Vector-First (semantic search) and "
                f"Graph-First (entity traversal) strategies. "
                f"Weights: vector={self.vector_weight}, graph={self.graph_weight}")

