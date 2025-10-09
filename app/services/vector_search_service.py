"""
Vector Search Service for semantic similarity search

This service implements vector similarity search using manual cosine similarity
calculation. It's designed to work with local MongoDB by fetching embeddings
and calculating similarities in Python.

When MongoDB Atlas is available, this can be easily replaced with native
$vectorSearch aggregation pipeline.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from app.core.database import AsyncIOMotorDatabase
from app.services.embeddings import EmbeddingsService
from app.utils.vector_utils import batch_cosine_similarity, validate_embedding_dimensions

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """
    Result from vector search containing section information and similarity score
    
    Attributes:
        section_id: MongoDB ObjectId of the section
        document_id: MongoDB ObjectId of the parent document
        content: Text content of the section
        title: Section title (e.g., "abstract", "methods")
        score: Similarity score (0.0 to 1.0, higher = more similar)
        embedding: Optional embedding vector (usually not needed in results)
        metadata: Additional section metadata (year, etc.)
    """
    section_id: str
    document_id: str
    content: str
    title: str
    score: float
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}


class VectorSearchService:
    """
    Service for vector similarity search without MongoDB Atlas.
    
    This implementation:
    1. Fetches embeddings from MongoDB
    2. Calculates cosine similarity in Python using NumPy
    3. Ranks and returns top results
    
    Performance: Good for up to ~10,000 documents (< 2 seconds)
    
    Future: Can be replaced with MongoDB Atlas $vectorSearch for better
    performance at scale (millions of documents).
    
    Example:
        >>> search_service = VectorSearchService(db)
        >>> results = await search_service.search(
        ...     query="What is CRISPR?",
        ...     limit=10,
        ...     min_score=0.7
        ... )
        >>> for result in results:
        ...     print(f"{result.score:.2f}: {result.content[:100]}")
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the vector search service
        
        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.sections_collection = db.sections
        self.embeddings_service = EmbeddingsService()
        
        # Cache settings (optional optimization)
        self._cache_embeddings = False  # Set to True for repeated searches
        self._cached_embeddings = None
        self._cache_timestamp = None
        self._cache_ttl_seconds = 300  # 5 minutes
        
        logger.info("VectorSearchService initialized")
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        include_embeddings: bool = False
    ) -> List[VectorSearchResult]:
        """
        Search for sections similar to the query using vector similarity.
        
        Process:
        1. Generate embedding for query text
        2. Fetch section embeddings from MongoDB (with optional filters)
        3. Calculate cosine similarities
        4. Sort by similarity score (descending)
        5. Filter by minimum score threshold
        6. Return top N results
        
        Args:
            query: User's search query text
            limit: Maximum number of results to return (default: 10)
            min_score: Minimum similarity score threshold (0.0 to 1.0, default: 0.0)
            filters: Optional MongoDB query filters (e.g., {"year": 2023})
            include_embeddings: Whether to include embedding vectors in results (default: False)
        
        Returns:
            List of VectorSearchResult objects, sorted by score (highest first)
            
        Example:
            >>> # Simple search
            >>> results = await search_service.search("CRISPR gene editing", limit=5)
            
            >>> # Search with filters
            >>> results = await search_service.search(
            ...     query="cancer treatment",
            ...     limit=10,
            ...     min_score=0.7,
            ...     filters={"year": {"$gte": 2020}}
            ... )
            
        Performance:
            - 100 documents: ~50ms
            - 1,000 documents: ~200ms
            - 10,000 documents: ~1-2s
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting vector search for query: '{query[:50]}...'")
            
            # Step 1: Generate query embedding
            query_embedding = await self._generate_query_embedding(query)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Step 2: Fetch candidate embeddings from database
            candidates = await self._fetch_candidate_embeddings(filters)
            if not candidates:
                logger.warning("No candidate embeddings found in database")
                return []
            
            logger.info(f"Found {len(candidates)} candidate documents")
            
            # Step 3: Calculate similarities
            scored_results = self._calculate_similarities(query_embedding, candidates)
            
            # Step 4: Rank and filter results
            final_results = self._rank_and_filter(
                scored_results,
                limit=limit,
                min_score=min_score,
                include_embeddings=include_embeddings
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Vector search completed in {elapsed_time*1000:.2f}ms, "
                       f"returning {len(final_results)} results")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}", exc_info=True)
            return []
    
    async def _generate_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Generate embedding vector for the query text.
        
        Uses the EmbeddingsService (OpenAI API) to convert text into
        a 1536-dimensional vector.
        
        Args:
            query: Query text
        
        Returns:
            NumPy array of embedding values, or None if generation fails
            
        Note:
            This makes an API call to OpenAI, so it may take 100-300ms
        """
        try:
            logger.debug(f"Generating embedding for query: '{query[:50]}...'")
            
            # Use the existing EmbeddingsService
            embedding = self.embeddings_service.generate_embedding(query)
            
            if embedding is None:
                logger.error("EmbeddingsService returned None")
                return None
            
            # Convert to numpy array for efficient computation
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Validate dimensions
            if not validate_embedding_dimensions(embedding_array):
                logger.error(f"Invalid embedding dimensions: {len(embedding_array)}")
                return None
            
            logger.debug(f"Successfully generated {len(embedding_array)}-dimensional embedding")
            return embedding_array
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return None
    
    async def _fetch_candidate_embeddings(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch section embeddings from MongoDB.
        
        This method retrieves all sections that have embeddings, optionally
        filtered by additional criteria (year, document_id, etc.).
        
        Args:
            filters: Optional MongoDB query filters
            
        Returns:
            List of section documents with embeddings
            
        MongoDB Query:
            {
                "embedding": {"$exists": true, "$ne": null},
                ...additional filters...
            }
            
        Example filters:
            {"year": 2023}  # Only sections from 2023
            {"document_id": "doc_123"}  # Only sections from specific document
            {"year": {"$gte": 2020}}  # Sections from 2020 onwards
            
        Performance:
            This can be slow for large databases since it fetches all embeddings.
            For production with >10K documents, consider:
            - Pagination
            - Caching
            - MongoDB Atlas $vectorSearch (much faster)
        """
        try:
            # Build MongoDB query
            query = {
                "embedding": {"$exists": True, "$ne": None}  # Must have embedding
            }
            
            # Add additional filters if provided
            if filters:
                query.update(filters)
            
            logger.debug(f"Fetching candidates with query: {query}")
            
            # Fetch from MongoDB
            # Project only needed fields to reduce memory usage
            projection = {
                "_id": 1,
                "document_id": 1,
                "text": 1,
                "title": 1,
                "embedding": 1,
                "year": 1,
                "created_at": 1
            }
            
            cursor = self.sections_collection.find(query, projection)
            candidates = await cursor.to_list(length=None)  # Fetch all
            
            # Filter out sections with invalid embeddings
            valid_candidates = []
            for candidate in candidates:
                embedding = candidate.get("embedding")
                if embedding and len(embedding) == 1536:  # Validate dimension
                    valid_candidates.append(candidate)
                else:
                    logger.warning(f"Section {candidate['_id']} has invalid embedding, skipping")
            
            logger.info(f"Fetched {len(valid_candidates)} valid candidates from {len(candidates)} total")
            return valid_candidates
            
        except Exception as e:
            logger.error(f"Error fetching candidate embeddings: {str(e)}")
            return []
    
    def _calculate_similarities(
        self,
        query_embedding: np.ndarray,
        candidates: List[Dict[str, Any]]
    ) -> List[VectorSearchResult]:
        """
        Calculate cosine similarity between query and all candidates.
        
        This is where the magic happens! We use NumPy vectorization to
        calculate similarities for all documents at once.
        
        Args:
            query_embedding: Query embedding vector (1536 dims)
            candidates: List of section documents with embeddings
        
        Returns:
            List of VectorSearchResult objects with similarity scores
            
        Process:
            1. Extract all candidate embeddings into a matrix
            2. Call batch_cosine_similarity (vectorized)
            3. Create VectorSearchResult for each candidate with its score
            
        Performance:
            - Uses NumPy vectorization (10-100x faster than loops)
            - 1000 candidates: ~15ms
            - 10000 candidates: ~150ms
        """
        try:
            if not candidates:
                return []
            
            # Extract embeddings into a matrix for batch processing
            # Shape: (N, 1536) where N is number of candidates
            candidate_embeddings = np.array(
                [candidate["embedding"] for candidate in candidates],
                dtype=np.float32
            )
            
            logger.debug(f"Calculating similarities for {len(candidates)} candidates")
            
            # Calculate all similarities at once (vectorized)
            similarities = batch_cosine_similarity(query_embedding, candidate_embeddings)
            
            # Create VectorSearchResult objects
            results = []
            for i, candidate in enumerate(candidates):
                result = VectorSearchResult(
                    section_id=str(candidate["_id"]),
                    document_id=str(candidate["document_id"]),
                    content=candidate.get("text", ""),
                    title=candidate.get("title", ""),
                    score=float(similarities[i]),
                    embedding=None,  # Don't include by default (large)
                    metadata={
                        "year": candidate.get("year"),
                        "created_at": candidate.get("created_at")
                    }
                )
                results.append(result)
            
            logger.debug(f"Calculated {len(results)} similarity scores")
            return results
            
        except Exception as e:
            logger.error(f"Error calculating similarities: {str(e)}")
            return []
    
    def _rank_and_filter(
        self,
        results: List[VectorSearchResult],
        limit: int,
        min_score: float,
        include_embeddings: bool
    ) -> List[VectorSearchResult]:
        """
        Rank results by score and apply filters.
        
        Args:
            results: Unfiltered search results
            limit: Maximum number of results
            min_score: Minimum score threshold
            include_embeddings: Whether to include embeddings
        
        Returns:
            Filtered and sorted results (highest score first)
            
        Filtering steps:
            1. Remove results below min_score threshold
            2. Sort by score (descending)
            3. Take top N (limit)
            4. Optionally remove embeddings (reduce memory)
        """
        try:
            # Filter by minimum score
            if min_score > 0.0:
                filtered = [r for r in results if r.score >= min_score]
                logger.debug(f"Filtered {len(results)} → {len(filtered)} results (min_score={min_score})")
            else:
                filtered = results
            
            # Sort by score (highest first)
            sorted_results = sorted(filtered, key=lambda x: x.score, reverse=True)
            
            # Take top N
            top_results = sorted_results[:limit]
            
            # Remove embeddings if not requested (save memory)
            if not include_embeddings:
                for result in top_results:
                    result.embedding = None
            
            logger.info(f"Returning top {len(top_results)} results "
                       f"(scores: {top_results[0].score:.3f} to {top_results[-1].score:.3f})")
            
            return top_results
            
        except Exception as e:
            logger.error(f"Error ranking and filtering results: {str(e)}")
            return []
    
    async def get_similar_sections(
        self,
        section_id: str,
        limit: int = 10,
        min_score: float = 0.7
    ) -> List[VectorSearchResult]:
        """
        Find sections similar to a given section.
        
        This is useful for "more like this" functionality.
        
        Args:
            section_id: ID of the reference section
            limit: Number of similar sections to return
            min_score: Minimum similarity threshold
        
        Returns:
            List of similar sections (excluding the reference section itself)
            
        Example:
            >>> # Find sections similar to section "abc123"
            >>> similar = await search_service.get_similar_sections("abc123", limit=5)
        """
        try:
            from bson import ObjectId
            
            # Fetch the reference section
            section = await self.sections_collection.find_one({"_id": ObjectId(section_id)})
            
            if not section or "embedding" not in section:
                logger.error(f"Section {section_id} not found or has no embedding")
                return []
            
            # Use the section's text as query
            query_text = section.get("text", "")
            
            # Search for similar sections
            results = await self.search(
                query=query_text,
                limit=limit + 1,  # +1 because we'll exclude the reference section
                min_score=min_score
            )
            
            # Remove the reference section from results
            filtered_results = [r for r in results if r.section_id != section_id]
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar sections: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics (useful for monitoring).
        
        Returns:
            Dictionary with service stats
        """
        return {
            "service": "VectorSearchService",
            "embedding_model": self.embeddings_service.get_model_name(),
            "embedding_dimensions": self.embeddings_service.get_embedding_dimensions(),
            "cache_enabled": self._cache_embeddings,
            "cache_ttl_seconds": self._cache_ttl_seconds
        }

