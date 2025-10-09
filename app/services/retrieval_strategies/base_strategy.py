"""
Base class for retrieval strategies

Defines the interface that all retrieval strategies must implement.
This allows the RetrievalService to work with any strategy polymorphically.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

from app.core.database import AsyncIOMotorDatabase
from app.models import QuerySource
from app.services.query_analysis_service import QueryAnalysis

logger = logging.getLogger(__name__)


class BaseRetrievalStrategy(ABC):
    """
    Abstract base class for retrieval strategies.
    
    All retrieval strategies (Vector-First, Graph-First, Hybrid) inherit from this
    and implement the retrieve() method.
    
    This design pattern allows:
    - Easy addition of new strategies
    - Polymorphic usage in RetrievalService
    - Consistent interface across all strategies
    
    Example:
        >>> class MyStrategy(BaseRetrievalStrategy):
        ...     async def retrieve(self, query, analysis, max_results):
        ...         # Custom retrieval logic
        ...         return sources
        
        >>> strategy = MyStrategy(db)
        >>> sources = await strategy.retrieve("What is CRISPR?", analysis, 10)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the retrieval strategy
        
        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.documents_collection = db.documents
        self.sections_collection = db.sections
        self.entities_collection = db.entities
        self.relationships_collection = db.relationships
        
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        analysis: QueryAnalysis,
        max_results: int = 10
    ) -> List[QuerySource]:
        """
        Retrieve relevant sources for the query.
        
        This is the main method that must be implemented by all strategies.
        
        Args:
            query: User's query text
            analysis: Query analysis result from QueryAnalysisService
            max_results: Maximum number of sources to return
        
        Returns:
            List of QuerySource objects with relevance scores
            
        Raises:
            NotImplementedError: If not implemented by subclass
            
        Example Implementation:
            >>> async def retrieve(self, query, analysis, max_results):
            ...     # 1. Perform retrieval (vector search, graph traversal, etc.)
            ...     results = await self._search(query)
            ...     
            ...     # 2. Enrich with metadata
            ...     sources = await self._enrich_results(results)
            ...     
            ...     # 3. Return top N
            ...     return sources[:max_results]
        """
        pass
    
    async def _fetch_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """
        Fetch document metadata from MongoDB.
        
        Helper method for enriching results with document information.
        
        Args:
            document_id: MongoDB ObjectId of the document
        
        Returns:
            Document metadata dictionary or empty dict if not found
            
        Metadata includes:
            - title: Document title
            - doi: Digital Object Identifier
            - year: Publication year
            - status: Processing status
        """
        try:
            from bson import ObjectId
            
            doc = await self.documents_collection.find_one(
                {"_id": ObjectId(document_id)}
            )
            
            if doc:
                return {
                    "title": doc.get("title", "Unknown"),
                    "doi": doc.get("doi"),
                    "year": doc.get("year"),
                    "status": doc.get("status"),
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at")
                }
            else:
                logger.warning(f"Document {document_id} not found")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching document metadata: {str(e)}")
            return {}
    
    def get_strategy_name(self) -> str:
        """
        Get the name of this strategy
        
        Returns:
            Strategy class name
        """
        return self.__class__.__name__
    
    def get_strategy_description(self) -> str:
        """
        Get a description of this strategy
        
        Returns:
            Human-readable description
            
        Note: Override this in subclasses for custom descriptions
        """
        return f"{self.get_strategy_name()}: Base retrieval strategy"

