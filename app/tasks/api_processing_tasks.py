"""
Celery tasks for processing external API data through GraphRAG pipeline
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from app.tasks.celery_app import celery_app
from app.core.database import get_sync_database
from app.services.api_data_adapter import APIDataAdapter
from app.pipelines.graphrag_pipeline import GraphRAGPipeline
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task
def process_api_sections(api_endpoint: str = "/sections/for-mapping/", 
                        api_token: str = None,
                        max_sections: int = 5):
    """
    Process sections from external API through GraphRAG pipeline
    
    Args:
        api_endpoint: API endpoint to fetch sections from
        api_token: Bearer token for API authentication
        max_sections: Maximum number of sections to process
        
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting API section processing for endpoint: {api_endpoint}")
        
        # Step 1: Initialize API data adapter (20%)
        logger.info("Step 1: Initializing API data adapter...")
        
        adapter = APIDataAdapter(
            api_token=api_token or getattr(settings, 'EXTERNAL_API_TOKEN', ''),
            max_sections=max_sections
        )
        
        # Step 2: Fetch and prepare sections from API (40%)
        logger.info("Step 2: Fetching sections from external API...")
        
        # Run async method in sync context
        sections = asyncio.run(adapter.get_sections_for_graphrag(api_endpoint))
        
        if not sections:
            return {
                "success": False,
                "error": "No valid sections found from API",
                "sections_fetched": 0,
                "entities_extracted": 0,
                "relationships_extracted": 0
            }
        
        logger.info(f"Successfully fetched {len(sections)} sections from API")
        
        # Step 3: Run GraphRAG pipeline (80%)
        logger.info("Step 3: Running GraphRAG pipeline on API sections...")
        
        # Create a synthetic document ID for API processing
        document_id = f"api_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize GraphRAG pipeline
        pipeline = GraphRAGPipeline()
        
        # Run the pipeline
        graphrag_result = asyncio.run(pipeline.process_document(document_id, sections))
        
        if not graphrag_result["success"]:
            return {
                "success": False,
                "error": f"GraphRAG pipeline failed: {graphrag_result.get('error', 'Unknown error')}",
                "sections_fetched": len(sections),
                "entities_extracted": 0,
                "relationships_extracted": 0
            }
        
        # Step 4: Store results in database (90%)
        logger.info("Step 4: Storing GraphRAG results in database...")
        
        db = get_sync_database()
        entities_stored = 0
        relationships_stored = 0
        
        # Store entities
        for entity_data in graphrag_result.get("final_entities", []):
            try:
                entity_doc = {
                    "entity_name": entity_data["entity_name"],
                    "entity_type": entity_data["entity_type"],
                    "entity_category": entity_data["entity_category"],
                    "entity_description": entity_data.get("entity_description"),
                    "aliases": entity_data.get("aliases", []),
                    "frequency": entity_data.get("frequency", 1),
                    "paper_ids": [document_id],
                    "section_ids": entity_data.get("section_ids", []),
                    "source": "external_api",
                    "created_at": datetime.utcnow()
                }
                
                # Upsert entity
                db.entities.update_one(
                    {
                        "entity_name": entity_doc["entity_name"],
                        "entity_type": entity_doc["entity_type"]
                    },
                    {"$set": entity_doc},
                    upsert=True
                )
                entities_stored += 1
                
            except Exception as e:
                logger.error(f"Error storing entity {entity_data.get('entity_name', 'unknown')}: {str(e)}")
        
        # Store relationships
        for rel_data in graphrag_result.get("final_relationships", []):
            try:
                relationship_doc = {
                    "source_entity": rel_data["source_entity"],
                    "target_entity": rel_data["target_entity"],
                    "relationship_type": rel_data["relationship_type"],
                    "relationship_strength": rel_data["relationship_strength"],
                    "description": rel_data.get("description"),
                    "paper_ids": [document_id],
                    "section_ids": rel_data.get("section_ids", []),
                    "source": "external_api",
                    "created_at": datetime.utcnow()
                }
                
                # Upsert relationship
                db.relationships.update_one(
                    {
                        "source_entity": relationship_doc["source_entity"],
                        "target_entity": relationship_doc["target_entity"],
                        "relationship_type": relationship_doc["relationship_type"]
                    },
                    {"$set": relationship_doc},
                    upsert=True
                )
                relationships_stored += 1
                
            except Exception as e:
                logger.error(f"Error storing relationship: {str(e)}")
        
        # Step 5: Finalize (100%)
        logger.info("Step 5: Finalizing API processing...")
        
        # Prepare result
        result = {
            "success": True,
            "document_id": document_id,
            "sections_fetched": len(sections),
            "sections_processed": len(sections),
            "entities_extracted": graphrag_result.get("entities_extracted", 0),
            "relationships_extracted": graphrag_result.get("relationships_extracted", 0),
            "entities_stored": entities_stored,
            "relationships_stored": relationships_stored,
            "entity_merges": graphrag_result.get("entity_merges", 0),
            "contradictions_detected": graphrag_result.get("contradictions", 0),
            "contradiction_resolutions": graphrag_result.get("contradiction_resolutions", 0),
            "consolidated_relationships": graphrag_result.get("consolidated_relationships", 0),
            "api_endpoint": api_endpoint,
            "processing_time": datetime.utcnow().isoformat(),
            "errors": graphrag_result.get("errors", [])
        }
        
        logger.info(f"Successfully processed API sections: {entities_stored} entities, {relationships_stored} relationships stored")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing API sections: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "sections_fetched": 0,
            "entities_extracted": 0,
            "relationships_extracted": 0
        }


@celery_app.task
def process_api_sections_with_config(config_dict: Dict[str, Any]):
    """
    Process API sections with configuration dictionary
    
    Args:
        config_dict: Configuration containing API settings
        
    Returns:
        Dict with processing results
    """
    try:
        api_endpoint = config_dict.get("endpoint", "/sections/for-mapping/")
        api_token = config_dict.get("token", "")
        max_sections = config_dict.get("max_sections", 5)
        
        return process_api_sections(api_endpoint, api_token, max_sections)
        
    except Exception as e:
        logger.error(f"Error processing API sections with config: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "sections_fetched": 0,
            "entities_extracted": 0,
            "relationships_extracted": 0
        }

