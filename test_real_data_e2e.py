"""
End-to-End Test with Real Data

This script tests the complete vector search pipeline:
1. Uploads sample documents about CRISPR and p53
2. Waits for processing (embedding generation)
3. Queries the system using our Vector-First Strategy
4. Shows real results with actual similarity scores

Prerequisites:
- MongoDB and Redis running (docker-compose up)
- OpenAI API key configured
"""

import asyncio
import time
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_database, connect_to_mongo, close_mongo_connection
from app.services.retrieval_service import RetrievalService


# Sample documents
SAMPLE_DOCUMENTS = [
    {
        "title": "CRISPR-Cas9: A Revolutionary Gene Editing Tool",
        "content": """
        Abstract:
        CRISPR-Cas9 is a revolutionary gene editing technology that allows scientists to 
        precisely modify DNA sequences in living organisms. Derived from a natural defense 
        mechanism in bacteria, CRISPR-Cas9 consists of two key components: the Cas9 protein, 
        which acts as molecular scissors, and a guide RNA that directs Cas9 to the specific 
        location in the genome that needs to be edited.
        
        Methods:
        The CRISPR-Cas9 system works by using the guide RNA to target specific DNA sequences. 
        Once the Cas9 protein is guided to the correct location, it makes a double-strand break 
        in the DNA. The cell's natural repair mechanisms then kick in, either disrupting the 
        gene or allowing researchers to insert new genetic material.
        
        Results:
        CRISPR-Cas9 has been successfully used to treat genetic diseases, develop new crop 
        varieties, and create animal models for disease research. Its applications in medicine 
        include potential treatments for sickle cell disease, cancer, and HIV.
        """,
        "doi": "10.1000/crispr.2024.001",
        "year": 2024
    },
    {
        "title": "p53: The Guardian of the Genome",
        "content": """
        Abstract:
        The p53 protein, often called the "guardian of the genome," plays a crucial role in 
        preventing cancer by regulating cell division and promoting apoptosis (programmed cell 
        death) when DNA damage is detected. Mutations in the TP53 gene, which encodes p53, 
        are found in more than 50% of human cancers, making it one of the most important 
        tumor suppressor genes.
        
        Methods:
        p53 functions as a transcription factor that activates genes involved in cell cycle 
        arrest, DNA repair, and apoptosis. When cells experience stress or DNA damage, p53 
        levels increase, triggering a cellular response that either repairs the damage or 
        eliminates the damaged cell.
        
        Results:
        Research has shown that restoring p53 function in cancer cells can lead to tumor 
        regression. Therapeutic strategies targeting p53 include gene therapy to reintroduce 
        functional p53, drugs that stabilize mutant p53, and compounds that activate p53 
        pathways.
        """,
        "doi": "10.1000/p53.2023.042",
        "year": 2023
    },
    {
        "title": "Applications of CRISPR in Cancer Treatment",
        "content": """
        Abstract:
        CRISPR gene editing technology is being applied to cancer treatment in innovative ways. 
        Researchers are using CRISPR to modify immune cells to better recognize and attack 
        cancer cells, edit cancer-causing mutations directly, and develop more accurate models 
        for studying cancer biology.
        
        Methods:
        CAR-T cell therapy combined with CRISPR editing allows for the creation of more potent 
        anti-cancer immune cells. CRISPR can be used to knock out genes that inhibit immune 
        response or to insert genes that enhance cancer cell recognition. Additionally, CRISPR 
        can correct mutations in tumor suppressor genes like TP53.
        
        Results:
        Early clinical trials using CRISPR-edited CAR-T cells have shown promising results in 
        treating leukemia and lymphoma. The combination of CRISPR precision with immunotherapy 
        represents a new frontier in personalized cancer treatment.
        """,
        "doi": "10.1000/crispr.cancer.2024.015",
        "year": 2024
    }
]


async def upload_documents():
    """Upload sample documents to the database"""
    print("\n" + "="*70)
    print("STEP 1: Uploading Sample Documents")
    print("="*70 + "\n")
    
    db = await get_database()
    documents_collection = db.documents
    sections_collection = db.sections
    
    uploaded_docs = []
    
    for doc_data in SAMPLE_DOCUMENTS:
        try:
            # Create document
            doc = {
                "title": doc_data["title"],
                "doi": doc_data["doi"],
                "year": doc_data["year"],
                "status": "uploaded",
                "created_at": time.time(),
                "updated_at": time.time()
            }
            
            result = await documents_collection.insert_one(doc)
            doc_id = str(result.inserted_id)
            
            # Create sections from content
            sections_text = doc_data["content"].strip().split("\n\n")
            
            for i, section_text in enumerate(sections_text):
                if section_text.strip():
                    # Determine section type
                    section_type = "other"
                    if "Abstract:" in section_text:
                        section_type = "abstract"
                    elif "Methods:" in section_text:
                        section_type = "methods"
                    elif "Results:" in section_text:
                        section_type = "results"
                    
                    section = {
                        "document_id": doc_id,
                        "title": section_type,
                        "text": section_text.strip(),
                        "year": doc_data["year"],
                        "embedding": None,  # Will be generated
                        "created_at": time.time(),
                        "updated_at": time.time()
                    }
                    
                    await sections_collection.insert_one(section)
            
            uploaded_docs.append({
                "id": doc_id,
                "title": doc_data["title"]
            })
            
            print(f"✓ Uploaded: {doc_data['title']}")
            print(f"  Document ID: {doc_id}")
            print(f"  Sections: {len([s for s in sections_text if s.strip()])}")
            
        except Exception as e:
            print(f"✗ Error uploading {doc_data['title']}: {str(e)}")
    
    print(f"\n✓ Total documents uploaded: {len(uploaded_docs)}")
    return uploaded_docs


async def generate_embeddings():
    """Generate embeddings for all sections"""
    print("\n" + "="*70)
    print("STEP 2: Generating Embeddings")
    print("="*70 + "\n")
    
    from app.services.embeddings import EmbeddingsService
    
    db = await get_database()
    sections_collection = db.sections
    
    # Find sections without embeddings
    sections_cursor = sections_collection.find({"embedding": None})
    sections = await sections_cursor.to_list(length=None)
    
    if not sections:
        print("✓ All sections already have embeddings")
        return 0
    
    print(f"Found {len(sections)} sections needing embeddings\n")
    
    embeddings_service = EmbeddingsService()
    generated_count = 0
    
    for i, section in enumerate(sections, 1):
        try:
            print(f"[{i}/{len(sections)}] Generating embedding for section: {section['title']}")
            
            # Generate embedding
            embedding = embeddings_service.generate_embedding(section["text"])
            
            if embedding:
                # Update section with embedding
                await sections_collection.update_one(
                    {"_id": section["_id"]},
                    {"$set": {"embedding": embedding}}
                )
                generated_count += 1
                print(f"  ✓ Generated ({len(embedding)} dimensions)")
            else:
                print(f"  ✗ Failed to generate embedding")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    print(f"\n✓ Generated embeddings for {generated_count}/{len(sections)} sections")
    return generated_count


async def test_queries():
    """Test various queries against the system"""
    print("\n" + "="*70)
    print("STEP 3: Testing Queries")
    print("="*70 + "\n")
    
    db = await get_database()
    retrieval_service = RetrievalService(db)
    
    test_queries = [
        "What is CRISPR?",
        "How does p53 prevent cancer?",
        "CRISPR applications in cancer treatment",
        "What is the role of TP53 gene?",
        "Gene editing technologies"
    ]
    
    results_summary = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}: \"{query}\"")
        print('='*70)
        
        try:
            start_time = time.time()
            
            # Execute query
            response = await retrieval_service.process_query(
                query=query,
                max_results=5
            )
            
            elapsed = time.time() - start_time
            
            # Display results
            print(f"\n✓ Query processed in {elapsed*1000:.2f}ms")
            print(f"  Confidence: {response.confidence:.2%}")
            print(f"  Sources found: {len(response.sources)}")
            print(f"  Strategy: {response.metadata.get('strategy_used', 'unknown')}")
            
            if response.sources:
                print(f"\n  Top 3 Sources:")
                for j, source in enumerate(response.sources[:3], 1):
                    print(f"\n  [{j}] {source.document_title}")
                    print(f"      Relevance: {source.relevance_score:.2%}")
                    print(f"      Section: {source.section_type}")
                    print(f"      DOI: {source.doi}")
                    print(f"      Preview: {source.content[:150]}...")
            
            print(f"\n  Answer:")
            print(f"  {response.answer}")
            
            results_summary.append({
                "query": query,
                "sources_count": len(response.sources),
                "confidence": response.confidence,
                "top_score": response.sources[0].relevance_score if response.sources else 0,
                "time_ms": elapsed * 1000
            })
            
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return results_summary


async def print_summary(results_summary):
    """Print summary statistics"""
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70 + "\n")
    
    if not results_summary:
        print("No results to summarize")
        return
    
    print(f"Total queries tested: {len(results_summary)}")
    print(f"\nResults breakdown:")
    print(f"{'Query':<50} {'Sources':<10} {'Confidence':<12} {'Top Score':<12} {'Time (ms)'}")
    print("-" * 100)
    
    for result in results_summary:
        print(f"{result['query']:<50} "
              f"{result['sources_count']:<10} "
              f"{result['confidence']:<12.2%} "
              f"{result['top_score']:<12.2%} "
              f"{result['time_ms']:<10.2f}")
    
    # Averages
    avg_sources = sum(r['sources_count'] for r in results_summary) / len(results_summary)
    avg_confidence = sum(r['confidence'] for r in results_summary) / len(results_summary)
    avg_score = sum(r['top_score'] for r in results_summary) / len(results_summary)
    avg_time = sum(r['time_ms'] for r in results_summary) / len(results_summary)
    
    print("-" * 100)
    print(f"{'AVERAGES':<50} "
          f"{avg_sources:<10.1f} "
          f"{avg_confidence:<12.2%} "
          f"{avg_score:<12.2%} "
          f"{avg_time:<10.2f}")
    
    print("\n" + "="*70)


async def cleanup():
    """Optional: Clean up test data"""
    print("\n" + "="*70)
    print("CLEANUP (Optional)")
    print("="*70 + "\n")
    
    response = input("Do you want to delete the test documents? (y/N): ")
    
    if response.lower() == 'y':
        db = await get_database()
        
        # Count documents
        doc_count = await db.documents.count_documents({})
        section_count = await db.sections.count_documents({})
        
        print(f"\nDeleting {doc_count} documents and {section_count} sections...")
        
        # Delete
        await db.documents.delete_many({})
        await db.sections.delete_many({})
        
        print("✓ Cleanup complete")
    else:
        print("✓ Keeping test data")


async def main():
    """Main test flow"""
    print("\n" + "="*70)
    print("VECTOR SEARCH - END-TO-END TEST WITH REAL DATA")
    print("="*70)
    
    try:
        # Connect to database
        await connect_to_mongo()
        
        # Step 1: Upload documents
        uploaded = await upload_documents()
        
        if not uploaded:
            print("\n✗ No documents uploaded, exiting")
            return
        
        # Step 2: Generate embeddings
        embeddings_generated = await generate_embeddings()
        
        if embeddings_generated == 0:
            print("\n⚠ No embeddings generated (may already exist)")
        
        # Step 3: Test queries
        results = await test_queries()
        
        # Step 4: Summary
        await print_summary(results)
        
        # Step 5: Optional cleanup
        await cleanup()
        
        print("\n✓ End-to-end test complete!")
        
    except Exception as e:
        print(f"\n✗ Error in main flow: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    # Check if OpenAI API key is configured
    from app.core.config import settings
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        print("\n✗ Error: OpenAI API key not configured")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    # Run the test
    asyncio.run(main())

