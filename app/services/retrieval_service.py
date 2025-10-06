"""
Retrieval service for GraphRAG operations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from app.core.database import AsyncIOMotorDatabase
from app.models import QueryResponse, QuerySource, GraphPath
from app.services.query_analysis_service import QueryAnalysisService


class RetrievalService:
    """Service for GraphRAG retrieval operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.documents_collection = db.documents
        self.sections_collection = db.sections
        self.entities_collection = db.entities
        self.relationships_collection = db.relationships
        
        # Initialize Query Analysis Service
        self.query_analyzer = QueryAnalysisService()
    
    async def process_query(
        self,
        query: str,
        max_results: int = 10,
        include_graph: bool = True,
        max_hops: int = 3
    ) -> QueryResponse:
        """Process a GraphRAG query using Query Analysis Service"""
        start_time = time.time()
        
        try:
            # Step 1: Analyze the query using our Query Analysis Service
            analysis = await self.query_analyzer.analyze_query(query)
            
            # Step 2: For now, create a basic response based on analysis
            # In future steps, we'll implement the actual retrieval strategies
            
            # Create a sample source based on query analysis
            sample_sources = []
            if analysis.entities:
                # If entities were found, create a source mentioning them
                entity_names = [entity.name for entity in analysis.entities]
                sample_sources = [
                    QuerySource(
                        document_id="sample_doc_1",
                        document_title=f"Research on {', '.join(entity_names[:2])}",
                        section_id="sample_sec_1",
                        section_type="abstract",
                        content=f"This document discusses {', '.join(entity_names[:2])} and their applications in scientific research.",
                        relevance_score=0.85,
                        doi="10.1000/sample",
                        metadata={
                            "analysis_intent": analysis.intent.value,
                            "analysis_complexity": analysis.complexity.value,
                            "recommended_strategy": analysis.recommended_strategy.value,
                            "confidence": analysis.confidence
                        }
                    )
                ]
            else:
                # Fallback source for queries without specific entities
                sample_sources = [
                    QuerySource(
                        document_id="sample_doc_1",
                        document_title="General Research Document",
                        section_id="sample_sec_1",
                        section_type="abstract",
                        content="This is a general research document that may contain information relevant to your query.",
                        relevance_score=0.70,
                        doi="10.1000/sample",
                        metadata={
                            "analysis_intent": analysis.intent.value,
                            "analysis_complexity": analysis.complexity.value,
                            "recommended_strategy": analysis.recommended_strategy.value,
                            "confidence": analysis.confidence
                        }
                    )
                ]
            
            # Create graph paths if requested
            graph_paths = []
            if include_graph and analysis.entities:
                # Create a simple path based on found entities
                entity_names = [entity.name for entity in analysis.entities]
                if len(entity_names) >= 2:
                    graph_paths = [
                        GraphPath(
                            path=entity_names[:3],  # Use first 3 entities
                            entities=[{"name": name, "confidence": 0.8} for name in entity_names[:3]],
                            relationships=[{"type": "related_to", "strength": 0.7}],
                            total_strength=0.75,
                            metadata={
                                "strategy_used": analysis.recommended_strategy.value,
                                "analysis_confidence": analysis.confidence
                            }
                        )
                    ]
            
            processing_time = time.time() - start_time
            
            # Generate a response based on analysis
            if analysis.entities:
                entity_names = [entity.name for entity in analysis.entities]
                answer = f"Based on your {analysis.intent.value} query about {', '.join(entity_names[:2])}, I found relevant information. "
                answer += f"This appears to be a {analysis.complexity.value} query that would benefit from {analysis.recommended_strategy.value} retrieval strategy."
            else:
                answer = f"Based on your {analysis.intent.value} query, I found some relevant information. "
                answer += f"This appears to be a {analysis.complexity.value} query that would benefit from {analysis.recommended_strategy.value} retrieval strategy."
            
            answer += " (Note: This is using our Query Analysis Service. Full retrieval strategies will be implemented in the next steps.)"
            
            return QueryResponse(
                query=query,
                answer=answer,
                sources=sample_sources,
                graph_paths=graph_paths,
                processing_time=processing_time,
                confidence=analysis.confidence,
                metadata={
                    "analysis_intent": analysis.intent.value,
                    "analysis_complexity": analysis.complexity.value,
                    "recommended_strategy": analysis.recommended_strategy.value,
                    "entities_found": [{"name": e.name, "type": e.type, "confidence": e.confidence} for e in analysis.entities]
                }
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Return error response
            return QueryResponse(
                query=query,
                answer=f"I encountered an error while processing your query: {str(e)}",
                sources=[],
                graph_paths=[],
                processing_time=processing_time,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def list_entities(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List entities in the knowledge graph"""
        query = {}
        if entity_type:
            query["entity_type"] = entity_type
        
        cursor = self.entities_collection.find(query).limit(limit)
        entities = []
        async for entity in cursor:
            entities.append(entity)
        return entities
    
    async def list_relationships(
        self,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
        relationship_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List relationships in the knowledge graph"""
        query = {}
        if source_entity:
            query["source_entity"] = source_entity
        if target_entity:
            query["target_entity"] = target_entity
        if relationship_type:
            query["relationship_type"] = relationship_type
        
        cursor = self.relationships_collection.find(query).limit(limit)
        relationships = []
        async for relationship in cursor:
            relationships.append(relationship)
        return relationships

