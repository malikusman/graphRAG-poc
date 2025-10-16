#!/usr/bin/env python3
"""
Fresh GraphRAG Pipeline Test - Skip embeddings, focus on entities/relationships
"""

import asyncio
import aiohttp
import os
import time
from pathlib import Path

# Set environment variables
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/sagewrite"

API_BASE = "http://localhost:8000/api/v1"

async def upload_document(session, file_path, title):
    """Upload a single document"""
    print(f"\n📤 Uploading: {title}")
    
    file_path_obj = Path(file_path)
    
    # Prepare form data
    data = aiohttp.FormData()
    data.add_field('title', title)
    data.add_field('doi', f"10.1234/{file_path_obj.stem}-2024")
    data.add_field('year', '2024')
    
    with open(file_path, 'rb') as f:
        data.add_field('file', f, filename=file_path_obj.name, content_type='text/plain')
        
        async with session.post(f"{API_BASE}/documents/upload", data=data) as response:
            if response.status == 200:
                result = await response.json()
                doc_id = result.get('_id')
                print(f"✅ Uploaded successfully: {doc_id}")
                return doc_id
            else:
                error = await response.text()
                print(f"❌ Upload failed: {error}")
                return None

async def check_processing_status(session, doc_id):
    """Check if document processing is complete"""
    async with session.get(f"{API_BASE}/documents/{doc_id}/status") as response:
        if response.status == 200:
            result = await response.json()
            return result.get('status')
        return None

async def analyze_document_results(doc_id, title):
    """Analyze entities and relationships for a specific document"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient('mongodb://localhost:27017/sagewrite')
    db = client.sagewrite
    
    # Get entities for this document
    entities = await db.entities.find({"paper_ids": doc_id}).to_list(100)
    
    # Get relationships for this document
    relationships = await db.relationships.find({"paper_ids": doc_id}).to_list(100)
    
    print(f"\n📄 {title}")
    print(f"   Document ID: {doc_id}")
    print(f"   Entities: {len(entities)}")
    print(f"   Relationships: {len(relationships)}")
    
    if entities:
        print(f"\n   👤 ENTITIES:")
        for i, entity in enumerate(entities, 1):
            aliases = entity.get('aliases', [])
            alias_str = f" (aliases: {', '.join(aliases[:2])})" if aliases else ""
            print(f"     {i:2d}. {entity.get('entity_name')} ({entity.get('entity_type')}){alias_str}")
    
    if relationships:
        print(f"\n   🔗 RELATIONSHIPS:")
        for i, rel in enumerate(relationships, 1):
            strength = rel.get('relationship_strength', 0)
            print(f"     {i:2d}. {rel.get('source_entity')} --[{rel.get('relationship_type')}]--> {rel.get('target_entity')} (strength: {strength:.2f})")
    
    client.close()
    return len(entities), len(relationships)

async def main():
    """Main function to upload all documents and analyze results"""
    print("=" * 80)
    print("🧪 FRESH GRAPHRAG PIPELINE TEST (gpt-5-nano)")
    print("=" * 80)
    
    # Document files and titles
    documents = [
        ("test_docs/neuroscience_alzheimers.txt", "Alzheimer's Disease: Amyloid Beta and Tau Interactions"),
        ("test_docs/immunology_covid.txt", "SARS-CoV-2 Spike Protein and ACE2 Binding Mechanisms"),
        ("test_docs/ecology_climate.txt", "Ocean Acidification Effects on Coral Reef Ecosystems"),
        ("test_docs/physics_quantum.txt", "Quantum Entanglement and Superposition in Quantum Computing")
    ]
    
    async with aiohttp.ClientSession() as session:
        # Upload all documents
        print("\n📤 STEP 1: Uploading Documents")
        print("-" * 40)
        
        doc_ids = []
        for file_path, title in documents:
            if Path(file_path).exists():
                doc_id = await upload_document(session, file_path, title)
                if doc_id:
                    doc_ids.append((doc_id, title))
            else:
                print(f"❌ File not found: {file_path}")
        
        if not doc_ids:
            print("❌ No documents uploaded successfully")
            return
        
        print(f"\n✅ Successfully uploaded {len(doc_ids)} documents")
        
        # Monitor processing
        print(f"\n⏳ STEP 2: Monitoring Processing (max 300s)")
        print("-" * 40)
        
        start_time = time.time()
        max_wait = 300  # 5 minutes
        
        while time.time() - start_time < max_wait:
            all_complete = True
            status_summary = {}
            
            for doc_id, title in doc_ids:
                status = await check_processing_status(session, doc_id)
                if status:
                    status_summary[doc_id] = status
                    if status not in ['processed', 'failed']:
                        all_complete = False
                else:
                    all_complete = False
            
            # Print status
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed:3d}s] ", end="")
            for doc_id, status in status_summary.items():
                print(f"{doc_id[:8]}={status[:10]:<10} ", end="")
            print()
            
            if all_complete:
                print(f"\n✅ All documents processed in {elapsed}s!")
                break
            
            await asyncio.sleep(10)
        else:
            print(f"\n⚠️  Timeout after {max_wait}s")
        
        # Analyze results for each document
        print(f"\n🔍 STEP 3: Analyzing Results by Document")
        print("=" * 80)
        
        total_entities = 0
        total_relationships = 0
        
        for doc_id, title in doc_ids:
            entities_count, relationships_count = await analyze_document_results(doc_id, title)
            total_entities += entities_count
            total_relationships += relationships_count
        
        # Overall summary
        print(f"\n📊 OVERALL SUMMARY")
        print("=" * 80)
        print(f"   Documents Processed: {len(doc_ids)}")
        print(f"   Total Entities: {total_entities}")
        print(f"   Total Relationships: {total_relationships}")
        print(f"   Average Entities per Document: {total_entities/len(doc_ids):.1f}")
        print(f"   Average Relationships per Document: {total_relationships/len(doc_ids):.1f}")

if __name__ == "__main__":
    asyncio.run(main())

