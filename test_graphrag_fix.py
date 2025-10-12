"""
Test script to verify GraphRAG section_ids bug fix

This script:
1. Uploads a test document
2. Waits for processing to complete
3. Checks the database to verify entities and relationships were stored
4. Displays detailed results
"""

import asyncio
import httpx
import tempfile
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint

# Configuration
API_BASE = "http://localhost:8000"
MONGODB_URL = "mongodb://localhost:27017/sagewrite"

# Test document content
TEST_DOCUMENT = {
    "title": "CRISPR-Cas9 Gene Editing for Cancer Therapy",
    "doi": "10.1234/crispr-cancer-2024",
    "year": 2024,
    "authors": ["Dr. Jane Smith", "Dr. John Doe"],
    "content": """
CRISPR-Cas9 Gene Editing for Cancer Therapy

Abstract:
CRISPR-Cas9 technology has emerged as a revolutionary tool for cancer treatment. This gene editing system allows precise modifications to DNA, enabling researchers to target cancer-causing mutations. The CRISPR system uses a guide RNA to direct the Cas9 enzyme to specific DNA sequences, where it creates double-strand breaks. These breaks can be repaired in ways that disable oncogenes or activate tumor suppressor genes like TP53.

Methods:
We employed CRISPR-Cas9 to edit cancer cells in vitro. The guide RNAs were designed to target specific oncogenes including MYC and RAS. TP53, a critical tumor suppressor, was restored in cells where it had been inactivated. The Cas9 enzyme was delivered using viral vectors. Cancer cell proliferation was measured before and after editing. Apoptosis rates were also assessed.

Results:
CRISPR editing successfully targeted oncogenes, resulting in reduced cancer cell proliferation. TP53 restoration led to increased apoptosis in cancer cells. The treatment showed promising results with minimal off-target effects. Cells treated with CRISPR showed 60% reduction in proliferation compared to controls.

Discussion:
CRISPR-Cas9 offers a precise method for cancer treatment by directly targeting genetic mutations. The ability to restore TP53 function is particularly important as TP53 mutations are found in over 50% of cancers. This approach could complement traditional chemotherapy and radiation therapy. Future work will focus on in vivo studies and clinical trials.

Conclusion:
CRISPR-Cas9 gene editing represents a promising therapeutic approach for cancer treatment. The technology allows targeted correction of cancer-causing mutations and restoration of tumor suppressor functions. Further research is needed to optimize delivery methods and assess long-term safety.
"""
}


async def upload_document():
    """Upload a document and return its ID"""
    print("\n" + "="*80)
    print("📤 STEP 1: Uploading Test Document")
    print("="*80)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(f"Title: {TEST_DOCUMENT['title']}\n")
        f.write(f"DOI: {TEST_DOCUMENT['doi']}\n")
        f.write(f"Year: {TEST_DOCUMENT['year']}\n")
        f.write(f"Authors: {', '.join(TEST_DOCUMENT['authors'])}\n\n")
        f.write(TEST_DOCUMENT['content'])
        temp_file = f.name
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Upload file
            with open(temp_file, 'rb') as f:
                files = {'file': ('test_crispr.txt', f, 'text/plain')}
                response = await client.post(f"{API_BASE}/api/v1/documents/upload", files=files)
            
            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.text}")
            
            data = response.json()
            document_id = data["_id"]
            
            print(f"✅ Document uploaded successfully")
            print(f"   Document ID: {document_id}")
            return document_id
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


async def wait_for_processing(document_id: str, max_wait: int = 180):
    """Wait for document processing to complete"""
    print("\n" + "="*80)
    print(f"⏳ STEP 2: Waiting for Processing (max {max_wait}s)")
    print("="*80)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.sagewrite
    
    elapsed = 0
    check_interval = 5
    
    while elapsed < max_wait:
        sections_count = await db.sections.count_documents({"document_id": document_id})
        entities_count = await db.entities.count_documents({"paper_id": document_id})
        relationships_count = await db.relationships.count_documents({"paper_id": document_id})
        
        print(f"   [{elapsed:3d}s] Sections: {sections_count}, Entities: {entities_count}, Relationships: {relationships_count}")
        
        # Check if processing is complete
        if sections_count > 0:
            # Check for embeddings
            section_with_embedding = await db.sections.find_one({
                "document_id": document_id,
                "embedding": {"$exists": True, "$ne": None}
            })
            
            if section_with_embedding and entities_count > 0 and relationships_count > 0:
                print(f"\n✅ Processing complete! ({elapsed}s)")
                print(f"   Sections: {sections_count}")
                print(f"   Entities: {entities_count}")
                print(f"   Relationships: {relationships_count}")
                client.close()
                return True
        
        await asyncio.sleep(check_interval)
        elapsed += check_interval
    
    client.close()
    print(f"\n⚠️  Timeout after {max_wait}s")
    return False


async def verify_database_contents(document_id: str):
    """Verify and display database contents"""
    print("\n" + "="*80)
    print("🔍 STEP 3: Verifying Database Contents")
    print("="*80)
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.sagewrite
    
    # Check sections
    print("\n📄 SECTIONS:")
    sections = await db.sections.find({"document_id": document_id}).to_list(100)
    for i, section in enumerate(sections, 1):
        has_embedding = 'embedding' in section and section['embedding'] is not None
        embedding_len = len(section.get('embedding', [])) if has_embedding else 0
        print(f"   {i}. Type: {section.get('type', 'unknown'):15s} | "
              f"Embedding: {'✓' if has_embedding else '✗'} ({embedding_len} dims) | "
              f"Length: {len(section.get('text', ''))} chars")
    
    # Check entities
    print("\n👤 ENTITIES:")
    entities = await db.entities.find({"paper_id": document_id}).to_list(100)
    print(f"   Total: {len(entities)} entities")
    
    # Group by type
    from collections import Counter
    entity_types = Counter(e.get('entity_type', 'unknown') for e in entities)
    print(f"   By type:")
    for entity_type, count in entity_types.most_common():
        print(f"      - {entity_type}: {count}")
    
    # Show sample entities
    print(f"\n   Sample entities:")
    for i, entity in enumerate(entities[:10], 1):
        section_ids = entity.get('section_ids', [])
        print(f"      {i}. {entity['entity_name']} ({entity['entity_type']}) "
              f"- {len(section_ids)} section(s)")
    
    # Check relationships
    print("\n🔗 RELATIONSHIPS:")
    relationships = await db.relationships.find({"paper_id": document_id}).to_list(100)
    print(f"   Total: {len(relationships)} relationships")
    
    # Group by type
    rel_types = Counter(r.get('relationship_type', 'unknown') for r in relationships)
    print(f"   By type:")
    for rel_type, count in rel_types.most_common():
        print(f"      - {rel_type}: {count}")
    
    # Show sample relationships
    print(f"\n   Sample relationships:")
    for i, rel in enumerate(relationships[:10], 1):
        section_ids = rel.get('section_ids', [])
        paper_ids = rel.get('paper_ids', [])
        print(f"      {i}. {rel['source_entity']} --[{rel['relationship_type']}]--> "
              f"{rel['target_entity']} (strength: {rel.get('relationship_strength', 0):.2f})")
        print(f"          Sections: {len(section_ids)}, Papers: {len(paper_ids)}")
    
    # Verify section_ids and paper_ids fields exist and are not empty
    print("\n✅ VERIFICATION:")
    entities_with_section_ids = sum(1 for e in entities if e.get('section_ids'))
    relationships_with_section_ids = sum(1 for r in relationships if r.get('section_ids'))
    relationships_with_paper_ids = sum(1 for r in relationships if r.get('paper_ids'))
    
    print(f"   Entities with section_ids: {entities_with_section_ids}/{len(entities)}")
    print(f"   Relationships with section_ids: {relationships_with_section_ids}/{len(relationships)}")
    print(f"   Relationships with paper_ids: {relationships_with_paper_ids}/{len(relationships)}")
    
    if relationships_with_section_ids == len(relationships) and relationships_with_paper_ids == len(relationships):
        print(f"\n✅ SUCCESS: All relationships have section_ids and paper_ids!")
    else:
        print(f"\n⚠️  WARNING: Some relationships missing section_ids or paper_ids")
    
    client.close()
    
    return {
        "sections": len(sections),
        "entities": len(entities),
        "relationships": len(relationships),
        "entities_with_section_ids": entities_with_section_ids,
        "relationships_with_section_ids": relationships_with_section_ids,
        "relationships_with_paper_ids": relationships_with_paper_ids
    }


async def main():
    """Main test flow"""
    print("\n" + "="*80)
    print("🧪 GraphRAG section_ids Bug Fix - Verification Test")
    print("="*80)
    
    try:
        # Step 1: Upload document
        document_id = await upload_document()
        
        # Step 2: Wait for processing
        processing_complete = await wait_for_processing(document_id, max_wait=180)
        
        if not processing_complete:
            print("\n⚠️  Processing did not complete in time")
            print("   This might be normal for large documents or slow API responses")
            print("   Proceeding to check what was processed...")
        
        # Step 3: Verify database contents
        results = await verify_database_contents(document_id)
        
        # Final summary
        print("\n" + "="*80)
        print("📊 FINAL SUMMARY")
        print("="*80)
        print(f"   Document ID: {document_id}")
        print(f"   Sections: {results['sections']}")
        print(f"   Entities: {results['entities']}")
        print(f"   Relationships: {results['relationships']}")
        print(f"\n   Bug Fix Verification:")
        print(f"   ✅ section_ids field: {results['relationships_with_section_ids']}/{results['relationships']}")
        print(f"   ✅ paper_ids field: {results['relationships_with_paper_ids']}/{results['relationships']}")
        
        if results['relationships'] > 0 and \
           results['relationships_with_section_ids'] == results['relationships'] and \
           results['relationships_with_paper_ids'] == results['relationships']:
            print(f"\n🎉 TEST PASSED: GraphRAG section_ids bug is FIXED!")
        else:
            print(f"\n⚠️  TEST INCOMPLETE: Check the logs for errors")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

