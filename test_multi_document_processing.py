#!/usr/bin/env python3
"""
Test script for multi-document GraphRAG processing
Tests entity canonicalization, contradiction detection, and global graph consistency
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any

import httpx
from bson import ObjectId

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENTS_DIR = Path("test_documents")
TEST_DOCUMENTS = [
    "crispr_genome_editing.txt",
    "cas9_gene_therapy.txt", 
    "crispr_offtarget_analysis.txt",
    "tp53_tumor_suppressor.txt",
    "tp53_mutations_cancer.txt",
    "metformin_cancer_treatment.txt"
]

class MultiDocumentTester:
    """Test class for multi-document GraphRAG processing"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
        self.uploaded_documents = []
        self.test_results = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def upload_document(self, file_path: Path) -> Dict[str, Any]:
        """Upload a test document"""
        print(f"📄 Uploading {file_path.name}...")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/plain')}
            response = await self.client.post(f"{self.base_url}/api/v1/documents/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            self.uploaded_documents.append(result)
            print(f"✅ Uploaded {file_path.name} - Document ID: {result.get('_id', 'N/A')}")
            return result
        else:
            print(f"❌ Failed to upload {file_path.name}: {response.text}")
            return {}
    
    async def wait_for_processing(self, document_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for document processing to complete"""
        print(f"⏳ Waiting for document {document_id} to process...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(f"{self.base_url}/api/v1/documents/{document_id}/status")
                
                if response.status_code == 200:
                    status = response.json()
                    print(f"📊 Status: {status.get('status', 'Unknown')}")
                    
                    if status.get('status') == 'processed':
                        print(f"✅ Document {document_id} processed successfully!")
                        return status
                    elif status.get('status') == 'failed':
                        print(f"❌ Document {document_id} processing failed!")
                        return status
                else:
                    print(f"⚠️ Status endpoint returned {response.status_code}, continuing to wait...")
            except Exception as e:
                print(f"⚠️ Error checking status: {str(e)}, continuing to wait...")
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        print(f"⏰ Timeout waiting for document {document_id}")
        return {}
    
    async def get_document_entities(self, document_id: str) -> List[Dict[str, Any]]:
        """Get entities for a document"""
        response = await self.client.get(f"{self.base_url}/api/v1/documents/{document_id}/entities")
        if response.status_code == 200:
            return response.json()
        return []
    
    async def get_document_relationships(self, document_id: str) -> List[Dict[str, Any]]:
        """Get relationships for a document"""
        response = await self.client.get(f"{self.base_url}/api/v1/documents/{document_id}/relationships")
        if response.status_code == 200:
            return response.json()
        return []
    
    async def get_global_entities(self) -> List[Dict[str, Any]]:
        """Get global entities across all documents"""
        # For now, return empty list since this endpoint might not be implemented yet
        return []
    
    async def get_global_relationships(self) -> List[Dict[str, Any]]:
        """Get global relationships across all documents"""
        # For now, return empty list since this endpoint might not be implemented yet
        return []
    
    async def test_entity_canonicalization(self) -> Dict[str, Any]:
        """Test entity canonicalization across documents"""
        print("\n🔗 Testing Entity Canonicalization...")
        
        # Expected entity merges
        expected_merges = {
            "CRISPR-Cas9": ["CRISPR-Cas9", "Cas9", "CRISPR"],
            "TP53": ["TP53", "p53"],
            "Metformin": ["Metformin", "1,1-dimethylbiguanide"]
        }
        
        global_entities = await self.get_global_entities()
        
        results = {
            "total_entities": len(global_entities),
            "expected_merges": expected_merges,
            "actual_merges": {},
            "canonicalization_success": True,
            "errors": []
        }
        
        # Check for expected canonicalizations
        for canonical_name, aliases in expected_merges.items():
            found_entity = None
            for entity in global_entities:
                if entity.get("entity_name") == canonical_name:
                    found_entity = entity
                    break
            
            if found_entity:
                entity_aliases = found_entity.get("aliases", [])
                missing_aliases = [alias for alias in aliases if alias not in entity_aliases and alias != canonical_name]
                
                if missing_aliases:
                    results["errors"].append(f"Missing aliases for {canonical_name}: {missing_aliases}")
                    results["canonicalization_success"] = False
                
                results["actual_merges"][canonical_name] = {
                    "aliases": entity_aliases,
                    "frequency": found_entity.get("frequency", 0),
                    "paper_count": len(found_entity.get("paper_ids", []))
                }
            else:
                results["errors"].append(f"Canonical entity {canonical_name} not found")
                results["canonicalization_success"] = False
        
        print(f"📊 Canonicalization Results:")
        print(f"   Total Global Entities: {results['total_entities']}")
        print(f"   Expected Merges: {len(expected_merges)}")
        print(f"   Successful Merges: {len(results['actual_merges'])}")
        print(f"   Errors: {len(results['errors'])}")
        
        return results
    
    async def test_contradiction_detection(self) -> Dict[str, Any]:
        """Test contradiction detection across documents"""
        print("\n⚠️ Testing Contradiction Detection...")
        
        global_relationships = await self.get_global_relationships()
        
        # Look for expected contradictions
        expected_contradictions = [
            {
                "source": "TP53",
                "target": "apoptosis", 
                "contradicting_types": ["increases", "decreases"]
            },
            {
                "source": "CRISPR-Cas9",
                "target": "off-target effects",
                "contradicting_types": ["has", "prevents"]
            }
        ]
        
        results = {
            "total_relationships": len(global_relationships),
            "expected_contradictions": expected_contradictions,
            "detected_contradictions": [],
            "contradiction_detection_success": True,
            "errors": []
        }
        
        # Check for contradictions
        for expected_cont in expected_contradictions:
            source = expected_cont["source"]
            target = expected_cont["target"]
            contradicting_types = expected_cont["contradicting_types"]
            
            # Find relationships between these entities
            related_rels = []
            for rel in global_relationships:
                if ((rel.get("source_entity") == source and rel.get("target_entity") == target) or
                    (rel.get("source_entity") == target and rel.get("target_entity") == source)):
                    related_rels.append(rel)
            
            # Check for contradictory relationship types
            rel_types = [rel.get("relationship_type") for rel in related_rels]
            found_contradiction = any(ct in rel_types for ct in contradicting_types)
            
            if found_contradiction:
                results["detected_contradictions"].append({
                    "source": source,
                    "target": target,
                    "relationship_types": rel_types,
                    "relationships": related_rels
                })
            else:
                results["errors"].append(f"No contradiction found for {source} -> {target}")
        
        print(f"📊 Contradiction Detection Results:")
        print(f"   Total Global Relationships: {results['total_relationships']}")
        print(f"   Expected Contradictions: {len(expected_contradictions)}")
        print(f"   Detected Contradictions: {len(results['detected_contradictions'])}")
        print(f"   Errors: {len(results['errors'])}")
        
        return results
    
    async def test_global_graph_consistency(self) -> Dict[str, Any]:
        """Test global graph consistency"""
        print("\n🌐 Testing Global Graph Consistency...")
        
        global_entities = await self.get_global_entities()
        global_relationships = await self.get_global_relationships()
        
        results = {
            "total_entities": len(global_entities),
            "total_relationships": len(global_relationships),
            "orphaned_entities": [],
            "inconsistent_relationships": [],
            "consistency_score": 0.0,
            "errors": []
        }
        
        # Check for orphaned entities (entities with no relationships)
        entity_names = {entity.get("entity_name") for entity in global_entities}
        relationship_entities = set()
        
        for rel in global_relationships:
            relationship_entities.add(rel.get("source_entity"))
            relationship_entities.add(rel.get("target_entity"))
        
        orphaned_entities = entity_names - relationship_entities
        results["orphaned_entities"] = list(orphaned_entities)
        
        # Check for inconsistent relationships (same entities, very different strengths)
        relationship_groups = {}
        for rel in global_relationships:
            key = f"{rel.get('source_entity')}_{rel.get('target_entity')}_{rel.get('relationship_type')}"
            if key not in relationship_groups:
                relationship_groups[key] = []
            relationship_groups[key].append(rel)
        
        inconsistent_relationships = []
        for key, rels in relationship_groups.items():
            if len(rels) > 1:
                strengths = [rel.get("relationship_strength", 0) for rel in rels]
                max_strength = max(strengths)
                min_strength = min(strengths)
                
                if max_strength - min_strength > 0.5:  # Large strength difference
                    inconsistent_relationships.append({
                        "key": key,
                        "strength_range": [min_strength, max_strength],
                        "relationships": rels
                    })
        
        results["inconsistent_relationships"] = inconsistent_relationships
        
        # Calculate consistency score
        total_issues = len(orphaned_entities) + len(inconsistent_relationships)
        max_possible_issues = len(global_entities) + len(global_relationships)
        results["consistency_score"] = 1.0 - (total_issues / max_possible_issues) if max_possible_issues > 0 else 1.0
        
        print(f"📊 Global Graph Consistency Results:")
        print(f"   Total Entities: {results['total_entities']}")
        print(f"   Total Relationships: {results['total_relationships']}")
        print(f"   Orphaned Entities: {len(results['orphaned_entities'])}")
        print(f"   Inconsistent Relationships: {len(results['inconsistent_relationships'])}")
        print(f"   Consistency Score: {results['consistency_score']:.2f}")
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive multi-document test"""
        print("🚀 Starting Comprehensive Multi-Document GraphRAG Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Upload all test documents
        print("\n📚 Step 1: Uploading Test Documents")
        print("-" * 40)
        
        for doc_file in TEST_DOCUMENTS:
            doc_path = TEST_DOCUMENTS_DIR / doc_file
            if doc_path.exists():
                await self.upload_document(doc_path)
            else:
                print(f"❌ Test document not found: {doc_path}")
        
        # Step 2: Wait for all documents to process
        print("\n⏳ Step 2: Waiting for Document Processing")
        print("-" * 40)
        
        for doc in self.uploaded_documents:
            doc_id = doc.get("id")
            if doc_id:
                await self.wait_for_processing(doc_id)
        
        # Step 3: Test entity canonicalization
        print("\n🔗 Step 3: Testing Entity Canonicalization")
        print("-" * 40)
        
        canonicalization_results = await self.test_entity_canonicalization()
        self.test_results["canonicalization"] = canonicalization_results
        
        # Step 4: Test contradiction detection
        print("\n⚠️ Step 4: Testing Contradiction Detection")
        print("-" * 40)
        
        contradiction_results = await self.test_contradiction_detection()
        self.test_results["contradiction_detection"] = contradiction_results
        
        # Step 5: Test global graph consistency
        print("\n🌐 Step 5: Testing Global Graph Consistency")
        print("-" * 40)
        
        consistency_results = await self.test_global_graph_consistency()
        self.test_results["global_consistency"] = consistency_results
        
        # Step 6: Generate summary report
        print("\n📊 Step 6: Test Summary Report")
        print("-" * 40)
        
        total_time = time.time() - start_time
        
        summary = {
            "test_duration": total_time,
            "documents_processed": len(self.uploaded_documents),
            "overall_success": (
                canonicalization_results.get("canonicalization_success", False) and
                contradiction_results.get("contradiction_detection_success", False) and
                consistency_results.get("consistency_score", 0) > 0.8
            ),
            "results": self.test_results
        }
        
        print(f"⏱️ Total Test Duration: {total_time:.2f} seconds")
        print(f"📄 Documents Processed: {summary['documents_processed']}")
        print(f"✅ Overall Success: {summary['overall_success']}")
        
        return summary

async def main():
    """Main test function"""
    async with MultiDocumentTester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to test_results.json")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
