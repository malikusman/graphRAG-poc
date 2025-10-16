"""
Vector-First Retrieval Strategy

Uses semantic similarity (vector embeddings) to find relevant documents.
Best for: factual queries, simple questions, content similarity searches.

Example queries that work well:
- "What is CRISPR?"
- "Explain p53 function"
- "Cancer treatment methods"
- "Gene editing applications"
"""

import logging
from typing import List, Dict, Any, Optional
import statistics

from app.core.database import AsyncIOMotorDatabase
from app.models import QuerySource
from app.services.query_analysis_service import QueryAnalysis
from app.services.vector_search_service import VectorSearchService, VectorSearchResult
from app.services.retrieval_strategies.base_strategy import BaseRetrievalStrategy

logger = logging.getLogger(__name__)


class VectorFirstStrategy(BaseRetrievalStrategy):
    """
    Vector-First Retrieval Strategy using semantic similarity search.
    
    Process:
    1. Generate query embedding (via OpenAI)
    2. Search for similar document sections (via VectorSearchService)
    3. Fetch document metadata (title, DOI, year)
    4. Build QuerySource objects with relevance scores
    5. Calculate overall confidence
    
    Advantages:
    - Fast: Single vector search operation
    - Semantic: Understands meaning, not just keywords
    - Simple: No complex graph traversal
    
    Best for:
    - FACTUAL queries: "What is X?"
    - EXPLORATORY queries: "Explain how X works"
    - SIMPLE complexity: Single topic queries
    
    Not ideal for:
    - COMPARATIVE queries: "Compare X vs Y" (use Graph-First)
    - COMPLEX queries: Multiple interconnected concepts (use Hybrid)
    
    Example:
        >>> strategy = VectorFirstStrategy(db)
        >>> analysis = QueryAnalysis(
        ...     intent=QueryIntent.FACTUAL,
        ...     complexity=QueryComplexity.SIMPLE,
        ...     recommended_strategy=RetrievalStrategy.VECTOR_FIRST
        ... )
        >>> sources = await strategy.retrieve("What is CRISPR?", analysis, max_results=5)
        >>> for source in sources:
        ...     print(f"{source.relevance_score:.2f}: {source.document_title}")
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize Vector-First Strategy
        
        Args:
            db: MongoDB database connection
        """
        super().__init__(db)
        
        # Initialize vector search service
        self.vector_search = VectorSearchService(db)
        
        logger.info("VectorFirstStrategy initialized with VectorSearchService")
    
    async def retrieve(
        self,
        query: str,
        analysis: QueryAnalysis,
        max_results: int = 10
    ) -> List[QuerySource]:
        """
        Retrieve sources using vector similarity search.
        
        Flow:
        1. Prepare query (optionally enhance with entities from analysis)
        2. Perform vector search
        3. Enrich results with document metadata
        4. Calculate confidence
        5. Return QuerySource objects
        
        Args:
            query: User's query text
            analysis: Query analysis result (contains entities, intent, etc.)
            max_results: Maximum number of sources to return
        
        Returns:
            List of QuerySource objects, sorted by relevance (highest first)
            
        Example:
            >>> sources = await strategy.retrieve(
            ...     query="What is p53?",
            ...     analysis=analysis,
            ...     max_results=5
            ... )
            >>> # Returns top 5 most relevant sections about p53
        """
        try:
            logger.info(f"Starting Vector-First retrieval for query: '{query[:50]}...'")
            
            # Step 1: Prepare query (optionally enhance)
            prepared_query = self._prepare_query(query, analysis)
            
            # Step 2: Perform vector search
            vector_results = await self._perform_vector_search(
                prepared_query,
                max_results=max_results * 2  # Fetch extra for filtering
            )
            
            if not vector_results:
                logger.warning("No vector search results found")
                return []
            
            logger.info(f"Found {len(vector_results)} vector search results")
            
            # Step 3: Enrich results with document metadata
            sources = await self._enrich_results(vector_results)
            
            # Step 4: Calculate confidence
            confidence = self._calculate_confidence(sources, analysis)
            
            # Add confidence to metadata
            for source in sources:
                source.metadata["strategy_confidence"] = confidence
                source.metadata["strategy_used"] = "vector_first"
            
            # Step 5: Return top N results
            final_sources = sources[:max_results]
            
            logger.info(f"Returning {len(final_sources)} sources with confidence {confidence:.2f}")
            return final_sources
            
        except Exception as e:
            logger.error(f"Error in Vector-First retrieval: {str(e)}", exc_info=True)
            return []
    
    def _prepare_query(self, query: str, analysis: QueryAnalysis) -> str:
        """
        Prepare and optionally enhance the query.
        
        Enhancement strategies:
        - Add entity names from analysis to query
        - Expand abbreviations
        - Add context
        
        For now, we keep it simple and return the original query.
        Future: Could enhance with entities from analysis.
        
        Args:
            query: Original query text
            analysis: Query analysis with extracted entities
        
        Returns:
            Prepared query text
            
        Example Enhancement (future):
            >>> query = "What does CRISPR do?"
            >>> entities = [Entity(name="CRISPR", type="method")]
            >>> prepared = _prepare_query(query, analysis)
            >>> # Could return: "What does CRISPR gene editing do?"
        """
        # For now, just return original query
        # Future enhancement: incorporate entity information
        
        if analysis.entities and len(analysis.entities) > 0:
            # Log entities found for debugging
            entity_names = [e.name for e in analysis.entities]
            logger.debug(f"Query contains entities: {entity_names}")
        
        return query
    
    async def _perform_vector_search(
        self,
        query: str,
        max_results: int
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search using VectorSearchService.
        
        Args:
            query: Query text
            max_results: Number of results to fetch
        
        Returns:
            List of VectorSearchResult objects
            
        Note:
            - Uses min_score of 0.5 to filter out irrelevant results
            - Fetches 2x max_results for better filtering
        """
        try:
            results = await self.vector_search.search(
                query=query,
                limit=max_results,
                min_score=0.5,  # Only return reasonably relevant results
                filters=None  # Could add year filters, etc.
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return []
    
    async def _enrich_results(
        self,
        vector_results: List[VectorSearchResult]
    ) -> List[QuerySource]:
        """
        Enrich vector search results with document metadata.
        
        Takes VectorSearchResult objects and converts them to QuerySource objects
        by fetching document metadata (title, DOI, year).
        
        Args:
            vector_results: Results from vector search
        
        Returns:
            List of QuerySource objects with full metadata
            
        Process:
        1. For each result, fetch document metadata
        2. Build QuerySource object with:
           - document_id, document_title, doi
           - section_id, section_type, content
           - relevance_score (from vector search)
           - metadata (year, etc.)
        """
        sources = []
        
        for result in vector_results:
            try:
                # Fetch document metadata
                doc_metadata = await self._fetch_document_metadata(result.document_id)
                
                # Build QuerySource object
                source = QuerySource(
                    document_id=result.document_id,
                    document_title=doc_metadata.get("title", "Unknown Document"),
                    section_id=result.section_id,
                    section_type=result.title,  # Section title (abstract, methods, etc.)
                    content=result.content,
                    relevance_score=result.score,  # Vector similarity score
                    doi=doc_metadata.get("doi"),
                    metadata={
                        "year": doc_metadata.get("year"),
                        "vector_score": result.score,
                        "document_status": doc_metadata.get("status"),
                        "created_at": str(doc_metadata.get("created_at", ""))
                    }
                )
                
                sources.append(source)
                
            except Exception as e:
                logger.error(f"Error enriching result {result.section_id}: {str(e)}")
                continue
        
        logger.debug(f"Enriched {len(sources)} results with document metadata")
        return sources
    
    def _calculate_confidence(
        self,
        sources: List[QuerySource],
        analysis: QueryAnalysis
    ) -> float:
        """
        Calculate confidence score for the retrieval results.
        
        Confidence is based on:
        1. Top score magnitude (higher = more confident)
        2. Score distribution (tight clustering = more confident)
        3. Number of high-quality results
        4. Query complexity (simple queries = more confident)
        
        Args:
            sources: Retrieved sources with scores
            analysis: Query analysis
        
        Returns:
            Confidence score (0.0 to 1.0)
            
        Confidence levels:
        - > 0.8: Very confident
        - 0.6-0.8: Confident
        - 0.4-0.6: Moderate
        - < 0.4: Low confidence
        
        Example:
            >>> sources = [
            ...     QuerySource(..., relevance_score=0.95),
            ...     QuerySource(..., relevance_score=0.93),
            ...     QuerySource(..., relevance_score=0.91)
            ... ]
            >>> confidence = _calculate_confidence(sources, analysis)
            >>> # Returns ~0.85 (high confidence due to high, consistent scores)
        """
        if not sources:
            return 0.0
        
        try:
            # Extract scores
            scores = [s.relevance_score for s in sources]
            
            # Factor 1: Top score magnitude (weight: 40%)
            top_score = scores[0] if scores else 0.0
            top_score_factor = top_score * 0.4
            
            # Factor 2: Score consistency (weight: 30%)
            # Lower standard deviation = more consistent = higher confidence
            if len(scores) > 1:
                score_std = statistics.stdev(scores)
                # Normalize: std of 0.0 = perfect, std of 0.3 = poor
                consistency_factor = max(0, (0.3 - score_std) / 0.3) * 0.3
            else:
                consistency_factor = 0.15  # Moderate for single result
            
            # Factor 3: Number of high-quality results (weight: 20%)
            high_quality_count = len([s for s in scores if s >= 0.7])
            quality_count_factor = min(1.0, high_quality_count / 5) * 0.2
            
            # Factor 4: Query complexity match (weight: 10%)
            # Simple queries with vector search = high confidence
            complexity_map = {
                "SIMPLE": 1.0,
                "MODERATE": 0.8,
                "COMPLEX": 0.6
            }
            complexity_factor = complexity_map.get(analysis.complexity.value, 0.7) * 0.1
            
            # Combine factors
            confidence = (
                top_score_factor +
                consistency_factor +
                quality_count_factor +
                complexity_factor
            )
            
            # Ensure in range [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            
            logger.debug(f"Confidence calculation: top={top_score_factor:.2f}, "
                        f"consistency={consistency_factor:.2f}, "
                        f"quality={quality_count_factor:.2f}, "
                        f"complexity={complexity_factor:.2f} "
                        f"→ total={confidence:.2f}")
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.5  # Default moderate confidence
    
    def get_strategy_description(self) -> str:
        """Get strategy description"""
        return ("VectorFirstStrategy: Semantic similarity search using vector embeddings. "
                "Best for factual and exploratory queries.")



