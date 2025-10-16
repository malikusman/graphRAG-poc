#!/usr/bin/env python3
"""
Graph-First Strategy End-to-End Test with Real Data
Tests the complete Graph-First retrieval strategy using real MongoDB data
"""

import asyncio
import httpx
import os
import time
from typing import List, Dict, Any

# Set MongoDB URL for local testing BEFORE importing anything else
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/sagewrite"

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.tasks.processing_tasks import process_document as celery_process_document
from app.models import DocumentStatus
from app.core.config import settings
from app.services.retrieval_strategies.graph_first_strategy import GraphFirstStrategy
from app.services.query_analysis_service import QueryAnalysisService
from bson import ObjectId

async def upload_document(title: str, content: str) -> str:
    """Upload a document and return its ID"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/documents/upload",
            files={
                "file": (f"{title}.txt", content, "text/plain")
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data["_id"]
        else:
            raise Exception(f"Failed to upload document: {response.text}")

async def process_document_task(document_id: str):
    """Process document to generate embeddings and build graph"""
    print(f"Processing document {document_id}...")
    
    # Wait for processing to complete
    max_wait = 60  # 60 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # Check document status
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:8000/api/v1/documents/{document_id}")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    print(f"Document status: {status}")
                    
                    if status == DocumentStatus.COMPLETED.value:
                        print("✅ Document processing completed!")
                        return True
                    elif status == DocumentStatus.FAILED.value:
                        print("❌ Document processing failed!")
                        return False
                        
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Error checking status: {e}")
            await asyncio.sleep(2)
    
    print("⏰ Timeout waiting for processing")
    return False

async def query_graph_system(query: str, db) -> Dict[str, Any]:
    """Query the graph-first system"""
    try:
        # Initialize services
        query_analyzer = QueryAnalysisService()
        graph_strategy = GraphFirstStrategy(db)
        
        print(f"\n🔍 Analyzing query: '{query}'")
        analysis = await query_analyzer.analyze_query(query)
        print(f"   Intent: {analysis.intent.value}")
        print(f"   Complexity: {analysis.complexity.value}")
        print(f"   Entities found: {len(analysis.entities)}")
        for entity in analysis.entities:
            print(f"     - {entity.name} ({entity.type}) - confidence: {entity.confidence:.2f}")
        print(f"   Recommended strategy: {analysis.recommended_strategy.value}")
        
        print(f"\n🚀 Running Graph-First retrieval...")
        start_time = time.time()
        sources = await graph_strategy.retrieve(
            query=query,
            analysis=analysis,
            max_results=5,
            max_hops=3
        )
        processing_time = time.time() - start_time
        
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        print(f"   📊 Sources found: {len(sources)}")
        
        # Display results
        for i, source in enumerate(sources, 1):
            print(f"\n   📄 Source {i}:")
            print(f"      Title: {source.document_title}")
            print(f"      Section: {source.section_type}")
            print(f"      Relevance: {source.relevance_score:.3f}")
            print(f"      DOI: {source.doi or 'N/A'}")
            print(f"      Content preview: {source.content[:150]}...")
            print(f"      Strategy: {source.metadata.get('strategy_used', 'unknown')}")
            if 'confidence' in source.metadata:
                print(f"      Confidence: {source.metadata['confidence']:.3f}")
        
        return {
            "query": query,
            "analysis": analysis,
            "sources": sources,
            "processing_time": processing_time,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error in graph query: {e}")
        return {
            "query": query,
            "error": str(e),
            "success": False
        }

async def cleanup(db):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        # Remove test documents
        result = await db.documents.delete_many({"title": {"$regex": "Graph Test"}})
        print(f"   Removed {result.deleted_count} test documents")
        
        # Remove related sections
        result = await db.sections.delete_many({"document_id": {"$in": [doc["_id"] for doc in await db.documents.find({"title": {"$regex": "Graph Test"}}).to_list(None)]}})
        print(f"   Removed {result.deleted_count} related sections")
        
        # Remove related entities and relationships (if any)
        # Note: In a real cleanup, you'd want to be more careful about this
        
    except Exception as e:
        print(f"   Warning: Cleanup error: {e}")

async def main():
    print("="*70)
    print("GRAPH-FIRST STRATEGY - END-TO-END TEST WITH REAL DATA")
    print("="*70)

    await connect_to_mongo()
    db = await get_database()

    try:
        # Step 1: Upload Sample Documents with Rich Entity Relationships
        print("\n📚 Step 1: Uploading sample documents...")
        
        # Document 1: p53 and Cancer - Rich in causal relationships
        p53_content = """
        p53 is a crucial tumor suppressor protein that plays a central role in preventing cancer.
        
        p53 prevents cancer by:
        1. Detecting DNA damage and activating repair mechanisms
        2. Inducing cell cycle arrest to allow DNA repair
        3. Triggering apoptosis when damage is irreparable
        4. Inhibiting angiogenesis to prevent tumor growth
        
        p53 interacts with MDM2, which regulates p53 stability.
        p53 activates p21, which inhibits cyclin-dependent kinases.
        p53 regulates Bax and Bcl-2 to control apoptosis.
        
        Mutations in p53 are found in over 50% of human cancers.
        p53 deficiency leads to increased cancer susceptibility.
        """
        
        # Document 2: CRISPR and Gene Editing - Rich in method relationships
        crispr_content = """
        CRISPR-Cas9 is a revolutionary gene editing technology.
        
        CRISPR uses:
        1. Guide RNA to target specific DNA sequences
        2. Cas9 nuclease to cut DNA at target sites
        3. DNA repair mechanisms to introduce changes
        
        CRISPR targets genes like BRCA1 and BRCA2 for cancer therapy.
        CRISPR modifies immune cells to treat diseases.
        CRISPR can correct genetic mutations that cause cancer.
        
        CRISPR technology enables precise genome editing.
        CRISPR applications include treating genetic diseases.
        CRISPR research advances cancer treatment strategies.
        """
        
        # Document 3: Cancer Treatment - Rich in treatment relationships
        treatment_content = """
        Cancer treatment strategies involve multiple approaches.
        
        Chemotherapy uses cytotoxic drugs to kill cancer cells.
        Radiotherapy uses ionizing radiation to destroy tumors.
        Immunotherapy activates the immune system to fight cancer.
        
        p53-based therapies target mutant p53 proteins.
        Gene therapy uses CRISPR to correct cancer-causing mutations.
        Targeted therapy inhibits specific cancer-promoting proteins.
        
        Treatment combinations improve patient outcomes.
        Personalized medicine tailors treatment to individual patients.
        """
        
        doc1_id = await upload_document("Graph Test - p53 Cancer Prevention", p53_content)
        doc2_id = await upload_document("Graph Test - CRISPR Gene Editing", crispr_content)
        doc3_id = await upload_document("Graph Test - Cancer Treatment", treatment_content)
        
        print(f"   Uploaded documents: {doc1_id}, {doc2_id}, {doc3_id}")
        
        # Step 2: Process Documents
        print("\n⚙️  Step 2: Processing documents...")
        
        success1 = await process_document_task(doc1_id)
        success2 = await process_document_task(doc2_id)
        success3 = await process_document_task(doc3_id)
        
        if not all([success1, success2, success3]):
            print("❌ Some documents failed to process. Continuing with available data...")
        
        # Wait a bit for graph processing to complete
        print("\n⏳ Waiting for graph processing...")
        await asyncio.sleep(10)
        
        # Step 3: Test Graph-First Queries
        print("\n🔬 Step 3: Testing Graph-First queries...")
        
        test_queries = [
            "How does p53 prevent cancer?",
            "What does CRISPR do?",
            "How does p53 interact with MDM2?",
            "What treatments target p53?",
            "How does CRISPR relate to cancer therapy?"
        ]
        
        results = []
        for query in test_queries:
            result = await query_graph_system(query, db)
            results.append(result)
            await asyncio.sleep(1)  # Brief pause between queries
        
        # Step 4: Summary Statistics
        print("\n📈 Step 4: Summary Statistics")
        print("="*50)
        
        successful_queries = [r for r in results if r["success"]]
        failed_queries = [r for r in results if not r["success"]]
        
        print(f"✅ Successful queries: {len(successful_queries)}/{len(results)}")
        print(f"❌ Failed queries: {len(failed_queries)}")
        
        if successful_queries:
            avg_processing_time = sum(r["processing_time"] for r in successful_queries) / len(successful_queries)
            total_sources = sum(len(r["sources"]) for r in successful_queries)
            avg_sources = total_sources / len(successful_queries)
            
            print(f"⏱️  Average processing time: {avg_processing_time:.2f}s")
            print(f"📊 Total sources found: {total_sources}")
            print(f"📊 Average sources per query: {avg_sources:.1f}")
            
            # Strategy distribution
            strategies = {}
            for result in successful_queries:
                for source in result["sources"]:
                    strategy = source.metadata.get("strategy_used", "unknown")
                    strategies[strategy] = strategies.get(strategy, 0) + 1
            
            print(f"\n🎯 Strategy usage:")
            for strategy, count in strategies.items():
                print(f"   {strategy}: {count} sources")
        
        if failed_queries:
            print(f"\n❌ Failed queries:")
            for result in failed_queries:
                print(f"   '{result['query']}': {result['error']}")
        
        print("\n🎉 Graph-First Strategy test completed!")
        
    except Exception as e:
        print(f"\n✗ Error in main flow: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()
        
        # Ask user about cleanup
        try:
            cleanup_choice = input("\n🧹 Do you want to clean up test data? (y/n): ").lower().strip()
            if cleanup_choice == 'y':
                await connect_to_mongo()
                db = await get_database()
                await cleanup(db)
                await close_mongo_connection()
                print("✅ Cleanup completed!")
            else:
                print("📝 Test data preserved for further analysis")
        except:
            print("📝 Test data preserved (non-interactive mode)")

if __name__ == "__main__":
    asyncio.run(main())
