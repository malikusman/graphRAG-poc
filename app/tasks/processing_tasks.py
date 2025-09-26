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


@celery_app.task
def process_document(document_id: str):
    """
    Process a document through the enhanced GraphRAG pipeline with global graph integration
    
    Args:
        document_id: MongoDB document ID
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting enhanced document processing for document {document_id}")

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

        # Step 1: File parsing and metadata extraction (20%)
        logger.info("Step 1: Parsing document and extracting metadata...")
        
        # Extract metadata
        metadata = {
            "title": str(document.get("title", "Untitled")),
            "doi": str(document.get("doi")) if document.get("doi") else None,
            "year": int(document.get("year")) if document.get("year") else None,
        }
        
        # Step 2: Section extraction (40%)
        logger.info("Step 2: Processing sections...")
        
        # Get sections from database (already extracted during upload)
        sections_cursor = db.sections.find({"document_id": document_id})
        sections = []
        for section in sections_cursor:
            # Convert ObjectId to string for JSON serialization
            section["_id"] = str(section["_id"])
            sections.append(section)
        
        logger.info(f"Processing {len(sections)} sections for document {document_id}")
        
        # Step 3: Generate embeddings (60%)
        logger.info("Step 3: Generating embeddings...")
        
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
        
        # Step 4: Enhanced GraphRAG processing with global graph integration (80%)
        logger.info("Step 4: Running enhanced GraphRAG pipeline with global graph integration...")
        
        # Run enhanced GraphRAG pipeline
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        
        pipeline = GraphRAGPipeline()
        graphrag_result = asyncio.run(pipeline.process_document(document_id, sections))
        
        if graphrag_result["success"]:
            logger.info(f"Enhanced GraphRAG processing complete: "
                       f"{graphrag_result['entities_extracted']} entities extracted, "
                       f"{graphrag_result['relationships_extracted']} relationships extracted, "
                       f"{graphrag_result['entity_merges']} entity merges, "
                       f"{graphrag_result['contradictions']} contradictions detected, "
                       f"{graphrag_result['contradiction_resolutions']} contradictions resolved, "
                       f"{graphrag_result['consolidated_relationships']} relationships consolidated")
            
            # Step 5: Store enhanced results in database (90%)
            logger.info("Step 5: Storing enhanced entities and relationships in database...")
            
            # Store entities with enhanced data
            entities_stored = 0
            for entity_data in graphrag_result.get("final_entities", []):
                try:
                    from app.models.entities import Entity, EntityType, EntityCategory
                    entity = Entity(
                        entity_name=entity_data["entity_name"],
                        entity_type=EntityType(entity_data["entity_type"]),
                        entity_category=EntityCategory(entity_data["entity_category"]),
                        entity_description=entity_data.get("entity_description"),
                        aliases=entity_data.get("aliases", []),
                        frequency=entity_data.get("frequency", 1),
                        paper_ids=[document_id],
                        section_ids=entity_data.get("section_ids", [])
                    )
                    
                    # Store entity using async wrapper
                    _store_entity_async(entity)
                    entities_stored += 1
                    
                except Exception as e:
                    logger.error(f"Error storing entity {entity_data.get('entity_name', 'unknown')}: {str(e)}")
            
            # Store relationships with enhanced data
            relationships_stored = 0
            for rel_data in graphrag_result.get("final_relationships", []):
                try:
                    from app.models.relationships import Relationship, RelationshipType
                    relationship = Relationship(
                        source_entity=rel_data["source_entity"],
                        target_entity=rel_data["target_entity"],
                        relationship_type=RelationshipType(rel_data["relationship_type"]),
                        relationship_strength=rel_data["relationship_strength"],
                        description=rel_data.get("description"),
                        paper_ids=[document_id],
                        section_ids=rel_data.get("section_ids", [])
                    )
                    
                    # Store relationship using async wrapper
                    _store_relationship_async(relationship)
                    relationships_stored += 1
                    
                except Exception as e:
                    logger.error(f"Error storing relationship {rel_data.get('source_entity', 'unknown')}-{rel_data.get('target_entity', 'unknown')}: {str(e)}")
            
            logger.info(f"Enhanced entities and relationships stored: {entities_stored} entities, {relationships_stored} relationships")
            
            # Step 6: Global graph processing results (95%)
            logger.info("Step 6: Processing global graph integration results...")
            
            global_processing_results = graphrag_result.get("global_processing_results", {})
            global_entities_processed = global_processing_results.get("entities_processed", 0)
            global_relationships_processed = global_processing_results.get("relationships_processed", 0)
            
            logger.info(f"Global graph processing complete: {global_entities_processed} entities, {global_relationships_processed} relationships processed against global graph")
            
        else:
            logger.error(f"Enhanced GraphRAG processing failed: {graphrag_result.get('error', 'Unknown error')}")
            # Set default values for failed processing
            entities_stored = 0
            relationships_stored = 0
            global_entities_processed = 0
            global_relationships_processed = 0
        
        # Step 7: Finalization (100%)
        logger.info("Step 7: Finalizing...")
        
        # Update document status to processed
        db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": DocumentStatus.PROCESSED.value}}
        )

        # Prepare enhanced result
        result = {
            "current": 100,
            "total": 100,
            "status": "Document processed successfully with enhanced GraphRAG pipeline!",
            "result": {
                "document_id": str(document_id),
                "sections_processed": int(len(sections)),
                "metadata": {
                    "title": str(metadata.get("title", "")),
                    "doi": str(metadata.get("doi", "")) if metadata.get("doi") else None,
                    "year": int(metadata.get("year", 0)) if metadata.get("year") else None,
                },
                "enhanced_graphrag_result": {
                    "success": bool(graphrag_result.get("success", False)),
                    "entities_extracted": int(graphrag_result.get("entities_extracted", 0)),
                    "relationships_extracted": int(graphrag_result.get("relationships_extracted", 0)),
                    "entity_merges": int(graphrag_result.get("entity_merges", 0)),
                    "contradictions_detected": int(graphrag_result.get("contradictions", 0)),
                    "contradictions_resolved": int(graphrag_result.get("contradiction_resolutions", 0)),
                    "relationships_consolidated": int(graphrag_result.get("consolidated_relationships", 0)),
                    "resolution_summary": graphrag_result.get("resolution_summary", {}),
                    "consolidation_summary": graphrag_result.get("consolidation_summary", {}),
                } if 'graphrag_result' in locals() else None,
                "database_storage": {
                    "entities_stored": int(entities_stored),
                    "relationships_stored": int(relationships_stored),
                },
                "global_graph_integration": {
                    "entities_processed": int(global_entities_processed),
                    "relationships_processed": int(global_relationships_processed),
                    "global_processing_results": global_processing_results,
                },
                "errors": graphrag_result.get("errors", []) if 'graphrag_result' in locals() else []
            }
        }
        
        logger.info(f"Successfully processed document {document_id} with enhanced pipeline")
        
        # DEBUGGING: Log the exact return value before serialization
        import json
        try:
            logger.info(f"About to return enhanced result: {json.dumps(result, default=str)}")
        except Exception as e:
            logger.error(f"Failed to serialize result for logging: {e}")
        
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

        logger.error(f"Task failed: {str(e)}")
        raise


def _store_entity_async(entity):
    """Helper function to store entity asynchronously in a thread"""
    import concurrent.futures
    import asyncio
    
    def run_async_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            from app.database.models import EntityCollection
            return new_loop.run_until_complete(EntityCollection.insert_entity(entity))
        finally:
            new_loop.close()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_async_in_thread)
        future.result()


def _store_relationship_async(relationship):
    """Helper function to store relationship asynchronously in a thread"""
    import concurrent.futures
    import asyncio
    
    def run_async_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            from app.database.models import RelationshipCollection
            return new_loop.run_until_complete(RelationshipCollection.insert_relationship(relationship))
        finally:
            new_loop.close()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_async_in_thread)
        future.result()


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
