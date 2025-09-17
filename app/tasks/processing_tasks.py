"""
Celery tasks for document processing
"""

import logging
import asyncio
from typing import Dict, Any
from celery import current_task
from bson import ObjectId

from app.tasks.celery_app import celery_app
from app.core.database import get_sync_database
from app.database.models import DocumentCollection, SectionCollection
from app.models import DocumentStatus
from app.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_document(self, document_id: str):
    """
    Process a document through the GraphRAG pipeline
    
    Args:
        document_id: MongoDB document ID
        
    Returns:
        Dict with processing results
    """
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting document processing..."}
        )

        # Get database connection
        db = get_sync_database()
        
        # Get document from database
        document = db.documents.find_one({"_id": ObjectId(document_id)})
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Update document status to processing
        db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": DocumentStatus.PROCESSING.value}}
        )

        # Step 1: File parsing (20%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Parsing document..."}
        )
        
        # Note: In a real implementation, we'd need to retrieve the file content
        # For now, we'll simulate the parsing step
        logger.info(f"Processing document {document_id}")
        
        # Step 2: Metadata extraction (40%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Extracting metadata..."}
        )
        
        # Extract metadata (simulated for now)
        metadata = {
            "title": document.get("title", "Untitled"),
            "doi": document.get("doi"),
            "year": document.get("year"),
        }
        
        # Step 3: Section extraction (60%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Processing sections..."}
        )
        
        # Get sections from database (already extracted during upload)
        sections_cursor = db.sections.find({"document_id": document_id})
        sections = list(sections_cursor)
        
        logger.info(f"Processing {len(sections)} sections for document {document_id}")
        
        # Step 4: Generate embeddings (70%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 70, "total": 100, "status": "Generating embeddings..."}
        )
        
        # Generate embeddings for sections
        embeddings_service = EmbeddingsService()
        for section in sections:
            try:
                embedding = asyncio.run(embeddings_service.generate_section_embedding(
                    section["text"], 
                    section.get("title", "")
                ))
                
                if embedding:
                    # Update section with embedding
                    db.sections.update_one(
                        {"_id": section["_id"]},
                        {"$set": {"embedding": embedding}}
                    )
                    logger.debug(f"Generated embedding for section {section['_id']}")
                else:
                    logger.warning(f"Failed to generate embedding for section {section['_id']}")
                    
            except Exception as e:
                logger.error(f"Error generating embedding for section {section['_id']}: {str(e)}")
        
        # Step 5: GraphRAG processing (80%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Running GraphRAG pipeline..."}
        )
        
        # Run GraphRAG pipeline for entity and relationship extraction
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        
        pipeline = GraphRAGPipeline()
        graphrag_result = asyncio.run(pipeline.process_document(document_id, sections))
        
        if graphrag_result["success"]:
            logger.info(f"GraphRAG processing complete: {graphrag_result['final_entities']} entities, {graphrag_result['final_relationships']} relationships")
        else:
            logger.error(f"GraphRAG processing failed: {graphrag_result.get('error', 'Unknown error')}")
        
        # Step 6: Finalization (100%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Finalizing..."}
        )
        
        # Update document status to processed
        db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": DocumentStatus.PROCESSED.value}}
        )

        result = {
            "current": 100,
            "total": 100,
            "status": "Document processed successfully!",
            "result": {
                "document_id": document_id,
                "sections_processed": len(sections),
                "metadata": metadata,
                "graphrag_result": graphrag_result if 'graphrag_result' in locals() else None
            }
        }
        
        logger.info(f"Successfully processed document {document_id}")
        return result

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        # Update document status to failed
        try:
            db = get_sync_database()
            db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": DocumentStatus.FAILED.value}}
            )
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")

        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "document_id": document_id}
        )
        raise


@celery_app.task
def cleanup_old_documents():
    """Clean up old processed documents (placeholder)"""
    # This would implement cleanup logic for old documents
    logger.info("Cleanup task executed")
    return "Cleanup completed"


@celery_app.task
def update_entity_frequencies():
    """Update entity frequencies across the knowledge graph"""
    # Placeholder for entity frequency updates
    logger.info("Entity frequency update task executed")
    return "Entity frequencies updated successfully"
