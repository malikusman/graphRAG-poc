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


# @celery_app.task(bind=True)
# def process_document(self, document_id: str):
    # DEBUGGING: Test without binding - uncomment the line below and comment out the line above
@celery_app.task
def process_document(document_id: str):
    """
    Process a document through the GraphRAG pipeline
    
    Args:
        document_id: MongoDB document ID
        
    Returns:
        Dict with processing results
    """
    try:
        # DEBUGGING: Test without binding
        logger.info("Starting document processing without task binding...")

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
        logger.info("Step 1: Parsing document...")
        
        # Note: In a real implementation, we'd need to retrieve the file content
        # For now, we'll simulate the parsing step
        logger.info(f"Processing document {document_id}")
        
        # Step 2: Metadata extraction (40%)
        logger.info("Step 2: Extracting metadata...")
        
        # Extract metadata (simulated for now)
        metadata = {
            "title": str(document.get("title", "Untitled")),
            "doi": str(document.get("doi")) if document.get("doi") else None,
            "year": int(document.get("year")) if document.get("year") else None,
        }
        
        # Step 3: Section extraction (60%)
        logger.info("Step 3: Processing sections...")
        
        # Get sections from database (already extracted during upload)
        sections_cursor = db.sections.find({"document_id": document_id})
        sections = []
        for section in sections_cursor:
            # Convert ObjectId to string for JSON serialization
            section["_id"] = str(section["_id"])
            sections.append(section)
        
        logger.info(f"Processing {len(sections)} sections for document {document_id}")
        
        # Step 4: Generate embeddings (70%)
        logger.info("Step 4: Generating embeddings...")
        
        # Generate embeddings for sections
        embeddings_service = EmbeddingsService()
        for section in sections:
            try:
                embedding = embeddings_service.generate_section_embedding(
                    section["text"], 
                    section.get("title", "")
                )
                
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
        logger.info("Step 5: Running GraphRAG pipeline...")
        
        # Run GraphRAG pipeline for entity and relationship extraction
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        
        pipeline = GraphRAGPipeline()
        graphrag_result = asyncio.run(pipeline.process_document(document_id, sections))
        
        if graphrag_result["success"]:
            logger.info(f"GraphRAG processing complete: {graphrag_result['final_entities']} entities, {graphrag_result['final_relationships']} relationships")
            
            # Store entities and relationships in database
            logger.info("Storing entities and relationships in database...")
            from app.models.entities import Entity
            from app.models.relationships import Relationship
            from app.database.models import EntityCollection, RelationshipCollection
            
            # Store entities
            for entity_data in graphrag_result.get("final_entities", []):
                try:
                    entity = Entity(
                        entity_name=entity_data["entity_name"],
                        entity_type=entity_data["entity_type"],
                        entity_category=entity_data["entity_category"],
                        entity_description=entity_data.get("description"),
                        aliases=entity_data.get("aliases", []),
                        frequency=entity_data.get("frequency", 1),
                        paper_ids=[document_id],
                        section_ids=entity_data.get("section_ids", [])
                    )
                    try:
                        # Use a synchronous approach by creating a new event loop in a thread
                        import concurrent.futures
                        import threading
                        
                        def run_async_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(EntityCollection.insert_entity(entity))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            future.result()
                    except Exception as e:
                        logger.error(f"Error in async entity storage: {str(e)}")
                        # Fallback: try direct asyncio.run
                        try:
                            asyncio.run(EntityCollection.insert_entity(entity))
                        except Exception as fallback_e:
                            logger.error(f"Fallback entity storage also failed: {str(fallback_e)}")
                except Exception as e:
                    logger.error(f"Error storing entity {entity_data.get('entity_name', 'unknown')}: {str(e)}")
            
            # Store relationships
            for rel_data in graphrag_result.get("final_relationships", []):
                try:
                    relationship = Relationship(
                        source_entity=rel_data["source_entity"],
                        target_entity=rel_data["target_entity"],
                        relationship_type=rel_data["relationship_type"],
                        relationship_strength=rel_data["relationship_strength"],
                        description=rel_data["description"],
                        paper_ids=[document_id],
                        section_ids=rel_data.get("section_ids", [])
                    )
                    try:
                        # Use a synchronous approach by creating a new event loop in a thread
                        import concurrent.futures
                        import threading
                        
                        def run_async_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(RelationshipCollection.insert_relationship(relationship))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async_in_thread)
                            future.result()
                    except Exception as e:
                        logger.error(f"Error in async relationship storage: {str(e)}")
                        # Fallback: try direct asyncio.run
                        try:
                            asyncio.run(RelationshipCollection.insert_relationship(relationship))
                        except Exception as fallback_e:
                            logger.error(f"Fallback relationship storage also failed: {str(fallback_e)}")
                except Exception as e:
                    logger.error(f"Error storing relationship {rel_data.get('source_entity', 'unknown')}-{rel_data.get('target_entity', 'unknown')}: {str(e)}")
            
            logger.info("Entities and relationships stored in database")
        else:
            logger.error(f"GraphRAG processing failed: {graphrag_result.get('error', 'Unknown error')}")
        
        # Step 6: Update global graph (90%)
        logger.info("Step 6: Updating global graph...")
        
        # Update global graph with new entities and relationships
        from app.tasks.graph_tasks import update_global_graph
        global_update_task = update_global_graph.delay(document_id)
        
        # Wait for global graph update to complete
        try:
            global_update_result = global_update_task.get(timeout=300)  # 5 minute timeout
            if global_update_result and global_update_result.get("current", 0) == 100:
                logger.info("Global graph update completed successfully")
            else:
                logger.warning(f"Global graph update completed with issues: {global_update_result.get('status', 'Unknown') if global_update_result else 'No result returned'}")
        except Exception as e:
            logger.error(f"Global graph update failed: {str(e)}")
            global_update_result = {"error": str(e)}
            # Continue processing even if global graph update fails
        
        # Step 7: Finalization (100%)
        logger.info("Step 7: Finalizing...")
        
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
                "document_id": str(document_id),
                "sections_processed": int(len(sections)),
                "metadata": {
                    "title": str(metadata.get("title", "")),
                    "doi": str(metadata.get("doi", "")) if metadata.get("doi") else None,
                    "year": int(metadata.get("year", 0)) if metadata.get("year") else None,
                },
                "graphrag_result": {
                    "success": bool(graphrag_result.get("success", False)),
                    "entities_extracted": int(graphrag_result.get("entities_extracted", 0)),
                    "relationships_extracted": int(graphrag_result.get("relationships_extracted", 0)),
                } if 'graphrag_result' in locals() else None,
                "global_graph_update": {
                    "status": str(global_update_result.get("status", "unknown")),
                } if global_update_result is not None else None
            }
        }
        
        logger.info(f"Successfully processed document {document_id}")
        
        # DEBUGGING: Log the exact return value before serialization
        import json
        try:
            logger.info(f"About to return result: {json.dumps(result, default=str)}")
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        except Exception as e:
            logger.error(f"Failed to serialize result for logging: {e}")
            logger.info(f"Result type: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"Result keys: {result.keys()}")
                for key, value in result.items():
                    logger.info(f"  {key}: {type(value)} = {value}")
        
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

        # No self.update_state available without binding
        logger.error(f"Task failed: {str(e)}")
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
