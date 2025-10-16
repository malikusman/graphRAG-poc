"""
Query API endpoints for GraphRAG
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_database
from app.services.retrieval_service import RetrievalService

router = APIRouter()


class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    max_results: int = 10
    include_graph: bool = True
    max_hops: int = 3


class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    graph_paths: List[Dict[str, Any]] = []
    processing_time: float


@router.post("/search", response_model=QueryResponse)
async def search_documents(
    request: QueryRequest,
    db=Depends(get_database)
):
    """Search documents using GraphRAG"""
    try:
        retrieval_service = RetrievalService(db)
        
        # Process the query
        result = await retrieval_service.process_query(
            query=request.query,
            max_results=request.max_results,
            include_graph=request.include_graph,
            max_hops=request.max_hops
        )
        
        # Convert QueryResponse to dict format for API
        return {
            "query": result.query,
            "answer": result.answer,
            "sources": [
                {
                    "document_id": source.document_id,
                    "document_title": source.document_title,
                    "section_id": source.section_id,
                    "section_type": source.section_type,
                    "content": source.content,
                    "relevance_score": source.relevance_score,
                    "doi": source.doi,
                    "metadata": source.metadata
                }
                for source in result.sources
            ],
            "graph_paths": [
                {
                    "path": path.path,
                    "entities": path.entities,
                    "relationships": path.relationships,
                    "total_strength": path.total_strength,
                    "metadata": path.metadata
                }
                for path in result.graph_paths
            ],
            "processing_time": result.processing_time,
            "confidence": result.confidence,
            "metadata": result.metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/entities")
async def list_entities(
    entity_type: str = None,
    limit: int = 100,
    db=Depends(get_database)
):
    """List entities in the knowledge graph"""
    try:
        retrieval_service = RetrievalService(db)
        entities = await retrieval_service.list_entities(
            entity_type=entity_type,
            limit=limit
        )
        
        return {"entities": entities}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list entities: {str(e)}"
        )


@router.get("/relationships")
async def list_relationships(
    source_entity: str = None,
    target_entity: str = None,
    relationship_type: str = None,
    limit: int = 100,
    db=Depends(get_database)
):
    """List relationships in the knowledge graph"""
    try:
        retrieval_service = RetrievalService(db)
        relationships = await retrieval_service.list_relationships(
            source_entity=source_entity,
            target_entity=target_entity,
            relationship_type=relationship_type,
            limit=limit
        )
        
        return {"relationships": relationships}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list relationships: {str(e)}"
        )

