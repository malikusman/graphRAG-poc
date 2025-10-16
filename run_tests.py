#!/usr/bin/env python3
"""
Simple test runner for multi-document GraphRAG testing
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def main():
    """Run the multi-document tests"""
    print("🧪 Multi-Document GraphRAG Test Runner")
    print("=" * 50)
    
    # Check if test documents exist
    test_docs_dir = Path("test_documents")
    if not test_docs_dir.exists():
        print("❌ Test documents directory not found!")
        print("Please ensure test_documents/ directory exists with the test files.")
        return
    
    # Check if test documents are present
    required_docs = [
        "crispr_genome_editing.txt",
        "cas9_gene_therapy.txt", 
        "crispr_offtarget_analysis.txt",
        "tp53_tumor_suppressor.txt",
        "tp53_mutations_cancer.txt",
        "metformin_cancer_treatment.txt"
    ]
    
    missing_docs = []
    for doc in required_docs:
        if not (test_docs_dir / doc).exists():
            missing_docs.append(doc)
    
    if missing_docs:
        print("❌ Missing test documents:")
        for doc in missing_docs:
            print(f"   - {doc}")
        return
    
    print("✅ All test documents found!")
    
    # Import and run the test
    try:
        from test_multi_document_processing import main as run_tests
        results = await run_tests()
        
        if results.get("overall_success"):
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n⚠️ Some tests failed. Check the results for details.")
            
    except ImportError as e:
        print(f"❌ Error importing test module: {e}")
        print("Make sure all dependencies are installed.")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

if __name__ == "__main__":
    asyncio.run(main())
