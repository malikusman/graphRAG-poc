#!/usr/bin/env python3
"""
Test script for API integration with single section processing and database storage
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.api_data_adapter import APIDataAdapter
from app.core.config import settings

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug logging for all GraphRAG components
logging.getLogger("app.pipelines.graphrag_pipeline").setLevel(logging.DEBUG)
logging.getLogger("app.services.entity_canonicalizer").setLevel(logging.DEBUG)
logging.getLogger("app.services.contradiction_detector").setLevel(logging.DEBUG)
logging.getLogger("app.services.relationship_consolidator").setLevel(logging.DEBUG)
logging.getLogger("app.services.global_graph_manager").setLevel(logging.DEBUG)
logging.getLogger("app.services.openai_service").setLevel(logging.DEBUG)

async def test_single_section_with_db():
    """Test API integration with single section and database storage"""
    
    print("🚀 Starting Single Section API Integration Test with Database")
    print("=" * 80)
    
    # Configuration - Using the new token
    api_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImZKYndxa3ZlTXFhSzVQODlVOHZtTyJ9.eyJlbWFpbCI6Im9sZWtzYW5kci5idXJsYUBjZW50dW0tZC5jb20iLCJpc3MiOiJodHRwczovL2F1dGguc2FnZXdyaXRlLmNvbS8iLCJzdWIiOiJhdXRoMHw2NzdiY2E2ZGY3ZmE1ZTAyYzhkMmMzOWQiLCJhdWQiOlsiaHR0cHM6Ly9hdXRoMC5zYWdld3JpdGUuY29tL2FwaS92MS8iLCJodHRwczovL3NhZ2V3cml0ZS5ldS5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNzYwNTMyMjAxLCJleHAiOjE3NjA2MTg2MDEsInNjb3BlIjoib3BlbmlkIGVtYWlsIGNyZWF0ZTp1c2VycyByZWFkOnVzZXJzIHVwZGF0ZTp1c2VycyBkZWxldGU6dXNlcnMgb2ZmbGluZV9hY2Nlc3MiLCJndHkiOiJwYXNzd29yZCIsImF6cCI6IjZXZUJSb0QxQk5xM1hTZmdjakhmZUlOZVZrVWVjZ1JnIn0.blWgxr6q3XSZy8M6L9-Z9qednnH4F-AZueDsBPEjqyaJv4Rc1OfwlY2jDavFOZjmuwwOqBlDBmUPq0viTkeySwYiNdBWnBQxHqyzoXnp4RV9aU6F3ZdP34rITLPG8QzDkyBOglVs1EhGHbRnMLaW6pm5uZ_Avf-AVyes6QC3QOf_7YK9jF-7MaL6VVi1JMM5II96OxAPUQasIBA346e01Bvo-GBQb4JVEm02uhcLbww68yXB_XVNlmmROAAfXvRbahnijKURyEdyeMsPsRY44aC9RACxJc-mVtOMAXYpzEWcCDGq1dQLM61bJoP0peKIYXYoo19cpPvCtcdBoFfErg"
    
    # Initialize API adapter with single section processing
    adapter = APIDataAdapter(
        api_base_url="https://writing-api.sagewrite.com",
        api_token=api_token
    )
    # Override to process only 1 section
    adapter.max_sections_to_process = 1
    adapter.min_text_length = 50
    
    print(f"📊 Configuration:")
    print(f"   • API Base URL: {adapter.api_base_url}")
    print(f"   • Max Sections: {adapter.max_sections_to_process}")
    print(f"   • Min Text Length: {adapter.min_text_length}")
    print(f"   • API Token: {api_token[:20]}...")
    print()
    
    try:
        # Step 1: Fetch sections from API
        print("📡 Step 1: Fetching sections from API...")
        sections = await adapter.fetch_sections_from_api()
        
        if not sections:
            print("❌ No sections fetched from API")
            return
            
        print(f"✅ Fetched {len(sections)} sections from API")
        for i, section in enumerate(sections):
            text_len = len(section.text) if section.text else 0
            print(f"   {i+1}. {section.title[:50]}... (text: {text_len} chars)")
        print()
        
        # Step 2: Filter and validate sections
        print("🔍 Step 2: Filtering and validating sections...")
        filtered_sections = adapter.filter_valid_sections(sections)
        
        if not filtered_sections:
            print("❌ No sections passed filtering")
            return
            
        print(f"✅ {len(filtered_sections)} sections passed filtering")
        for section in filtered_sections:
            text_len = len(section.text) if section.text else 0
            print(f"   • {section.title[:50]}... (text: {text_len} chars)")
        print()
        
        # Step 3: Limit to 1 section and transform
        print("🔄 Step 3: Limiting to 1 section and transforming for GraphRAG...")
        limited_sections = adapter.limit_sections(filtered_sections)
        transformed_sections = adapter.transform_to_internal_format(limited_sections)
        
        print(f"✅ Transformed {len(transformed_sections)} sections")
        for section in transformed_sections:
            print(f"   • ID: {section['_id']}")
            print(f"   • Title: {section['title']}")
            print(f"   • Text Length: {len(section['text'])}")
            print(f"   • Document ID: {section['document_id']}")
        print()
        
        # Step 4: Process through GraphRAG pipeline (with database)
        print("🧠 Step 4: Processing through GraphRAG pipeline with database storage...")
        
        # Create a unique document ID for this test
        test_doc_id = f"single_section_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Process sections through the pipeline directly
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        from app.models.sections import Section
        
        # Convert transformed sections to Section objects
        section_objects = []
        for section_data in transformed_sections:
            section = Section(
                _id=section_data["_id"],
                document_id=section_data["document_id"],
                title=section_data["title"],
                text=section_data["text"],
                position=section_data.get("position", 0),
                created_at=section_data.get("created_at", datetime.now().isoformat()),
                updated_at=section_data.get("updated_at", datetime.now().isoformat()),
                meta=section_data.get("meta", {})
            )
            section_objects.append(section)
        
        # Initialize and run GraphRAG pipeline with detailed node monitoring
        pipeline = GraphRAGPipeline()
        
        print("🔧 Initializing GraphRAG Pipeline...")
        print(f"   • Document ID: {test_doc_id}")
        print(f"   • Sections to process: {len(section_objects)}")
        print(f"   • Skip embeddings: True")
        print()
        
        # Process document with detailed logging
        print("🧠 Starting GraphRAG Pipeline Execution...")
        print("=" * 60)
        
        result = await pipeline.process_document(
            document_id=test_doc_id,
            sections=transformed_sections  # Use the transformed sections directly
        )
        
        print("=" * 60)
        print("✅ GraphRAG Pipeline Execution Complete!")
        
        print(f"✅ GraphRAG processing complete!")
        print(f"   • Document ID: {test_doc_id}")
        print(f"   • Status: {result.get('status', 'unknown')}")
        print(f"   • Entities Extracted: {result.get('entities_count', 0)}")
        print(f"   • Relationships Extracted: {result.get('relationships_count', 0)}")
        print(f"   • Processing Time: {result.get('processing_time', 'unknown')}")
        print()
        
        # Step 5: Verify database storage
        print("🗄️ Step 5: Verifying database storage...")
        
        # Try to query the database for stored entities and relationships
        try:
            from app.database import get_database
            from app.models.entities import Entity
            from app.models.relationships import Relationship
            
            db = get_database()
            
            # Count entities for this document
            entity_count = await db.entities.count_documents({"document_id": test_doc_id})
            print(f"   • Entities stored in DB: {entity_count}")
            
            # Count relationships for this document  
            relationship_count = await db.relationships.count_documents({"document_id": test_doc_id})
            print(f"   • Relationships stored in DB: {relationship_count}")
            
            # Show sample entities
            if entity_count > 0:
                sample_entities = await db.entities.find({"document_id": test_doc_id}).limit(3).to_list(3)
                print(f"   • Sample entities:")
                for entity in sample_entities:
                    print(f"     - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
            
            # Show sample relationships
            if relationship_count > 0:
                sample_relationships = await db.relationships.find({"document_id": test_doc_id}).limit(3).to_list(3)
                print(f"   • Sample relationships:")
                for rel in sample_relationships:
                    print(f"     - {rel.get('source_entity', 'N/A')} -> {rel.get('relationship_type', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
                    
        except Exception as e:
            print(f"   ❌ Database verification failed: {str(e)}")
        
        print()
        print("🎉 Single Section API Integration Test Complete!")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_single_section_with_db())
