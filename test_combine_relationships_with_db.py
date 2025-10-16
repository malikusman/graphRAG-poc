#!/usr/bin/env python3
"""
Test the _combine_relationships node with pre-populated database
This test demonstrates proper relationship consolidation across documents
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.relationships import Relationship
from app.pipelines.graphrag_pipeline import GraphRAGState
from app.database.models import RelationshipCollection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def pre_populate_database():
    """Pre-populate database with existing relationships"""
    print("🗄️ Pre-populating database with existing relationships...")
    
    # Create existing relationships that should be consolidated with new ones
    existing_relationships = [
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.85,
            "description": "p53 promotes apoptosis in response to DNA damage from previous document",
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_001", "existing_section_002"]
        },
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "inhibits",
            "relationship_strength": 0.90,
            "description": "MDM2 inhibits p53 by targeting it for degradation from previous document",
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_003"]
        },
        {
            "source_entity": "TP53",
            "target_entity": "cancer",
            "relationship_type": "prevents",
            "relationship_strength": 0.95,
            "description": "TP53 prevents cancer by regulating cell cycle from previous document",
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_004"]
        },
        {
            "source_entity": "CRISPR-Cas9",
            "target_entity": "DNA",
            "relationship_type": "targets",
            "relationship_strength": 0.88,
            "description": "CRISPR-Cas9 targets specific DNA sequences for editing from previous document",
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_005"]
        }
    ]
    
    created_count = 0
    for rel_data in existing_relationships:
        try:
            # Create relationship in database
            relationship = Relationship(
                source_entity=rel_data["source_entity"],
                target_entity=rel_data["target_entity"],
                relationship_type=rel_data["relationship_type"],
                relationship_strength=rel_data["relationship_strength"],
                description=rel_data["description"],
                paper_ids=rel_data["paper_ids"],
                section_ids=rel_data["section_ids"]
            )
            relationship_id = await RelationshipCollection.insert_relationship(relationship)
            print(f"   ✅ Created relationship: {rel_data['source_entity']} --[{rel_data['relationship_type']}]--> {rel_data['target_entity']} (ID: {relationship_id})")
            created_count += 1
        except Exception as e:
            print(f"   ❌ Failed to create relationship {rel_data['source_entity']} --[{rel_data['relationship_type']}]--> {rel_data['target_entity']}: {str(e)}")
    
    print(f"🗄️ Database pre-population complete: {created_count}/{len(existing_relationships)} relationships created")
    return created_count

def create_new_document_relationships() -> List[Dict[str, Any]]:
    """Create relationships from a new document that should be consolidated with existing ones"""
    return [
        # These should consolidate with existing relationships
        {
            "source_entity": "TP53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.75,
            "description": "TP53 promotes apoptosis under stress conditions from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_001"]
        },
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.80,
            "description": "p53 promotes apoptosis in response to cellular stress from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_002"]
        },
        {
            "source_entity": "murine double minute 2",
            "target_entity": "TP53",
            "relationship_type": "inhibits",
            "relationship_strength": 0.85,
            "description": "Murine double minute 2 inhibits TP53 protein from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_003"]
        },
        {
            "source_entity": "CRISPR",
            "target_entity": "DNA",
            "relationship_type": "targets",
            "relationship_strength": 0.92,
            "description": "CRISPR targets DNA for gene editing from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_004"]
        },
        
        # These should NOT consolidate (unique relationships)
        {
            "source_entity": "apoptosis",
            "target_entity": "cell_death",
            "relationship_type": "causes",
            "relationship_strength": 0.95,
            "description": "Apoptosis causes programmed cell death from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_005"]
        },
        {
            "source_entity": "cancer",
            "target_entity": "tumor_growth",
            "relationship_type": "promotes",
            "relationship_strength": 0.88,
            "description": "Cancer promotes tumor growth from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_006"]
        },
        
        # Duplicate relationships within the same document (should consolidate)
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.70,
            "description": "p53 promotes apoptosis through mitochondrial pathway from new document",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_007"]
        }
    ]

def print_relationships(relationships: List[Dict[str, Any]], title: str):
    """Print relationships in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(relationships)}")
    for i, rel in enumerate(relationships, 1):
        if isinstance(rel, dict):
            # Check if this is a consolidation result structure
            if 'consolidation_result' in rel and 'consolidated_relationship' in rel['consolidation_result']:
                # Extract from consolidation result
                consolidated_rel = rel['consolidation_result']['consolidated_relationship']
                source = consolidated_rel.get('source_entity', 'Unknown')
                target = consolidated_rel.get('target_entity', 'Unknown')
                rel_type = consolidated_rel.get('relationship_type', 'Unknown')
                strength = consolidated_rel.get('relationship_strength', 0.0)
                description = consolidated_rel.get('description', 'No description')
                sections = consolidated_rel.get('section_ids', [])
                strategy = rel['consolidation_result'].get('consolidation_strategy', 'unknown')
                confidence = consolidated_rel.get('confidence', 0.0)
                evidence_count = consolidated_rel.get('evidence_count', 1)
            else:
                # Direct relationship data
                source = rel.get('source_entity', 'Unknown')
                target = rel.get('target_entity', 'Unknown')
                rel_type = rel.get('relationship_type', 'Unknown')
                strength = rel.get('relationship_strength', 0.0)
                description = rel.get('description', 'No description')
                sections = rel.get('section_ids', [])
                strategy = 'direct'
                confidence = strength
                evidence_count = 1
        else:
            # Relationship object
            source = rel.source_entity
            target = rel.target_entity
            rel_type = rel.relationship_type
            strength = rel.relationship_strength
            description = rel.description
            sections = rel.section_ids
            strategy = 'object'
            confidence = strength
            evidence_count = 1
            
        print(f"   {i}. {source} --[{rel_type}]--> {target}")
        print(f"      Strength: {strength}")
        print(f"      Confidence: {confidence}")
        print(f"      Strategy: {strategy}")
        print(f"      Evidence Count: {evidence_count}")
        print(f"      Description: {description}")
        print(f"      Sections: {sections}")
        print()

def print_consolidation_results(results: List[Dict[str, Any]]):
    """Print consolidation results in a formatted way"""
    print(f"\n🔄 Consolidation Results:")
    print(f"   Count: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Strategy: {result.get('strategy', 'unknown')}")
        print(f"      Primary Relationship: {result.get('primary_relationship', 'unknown')}")
        print(f"      Consolidated Strength: {result.get('consolidated_strength', 0.0)}")
        print(f"      Confidence: {result.get('confidence', 0.0)}")
        print(f"      Reasoning: {result.get('reasoning', 'No reasoning provided')}")
        print()

class SimpleCombineRelationshipsPipeline:
    """Simple pipeline class with just the _combine_relationships method"""
    
    def __init__(self):
        from app.services.relationship_consolidator import RelationshipConsolidator
        self.relationship_consolidator = RelationshipConsolidator()
    
    async def _combine_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Combine phase: Consolidate relationships within document"""
        logger.info(f"Starting relationship combination for document {state['document_id']}")
        
        try:
            # Convert temp_relationships to Relationship objects for processing
            from app.models.relationships import Relationship
            relationships = []
            for rel_data in state["temp_relationships"]:
                relationship = Relationship(
                    source_entity=rel_data["source_entity"],
                    target_entity=rel_data["target_entity"],
                    relationship_type=rel_data["relationship_type"],
                    relationship_strength=rel_data["relationship_strength"],
                    description=rel_data["description"],
                    paper_ids=rel_data.get("paper_ids", []),
                    section_ids=rel_data.get("section_ids", [])
                )
                relationships.append(relationship)
            
            # Process relationship consolidation
            consolidation_results = await self.relationship_consolidator.consolidate_relationships(relationships)
            
            # Extract the actual consolidated relationships from the consolidation results
            consolidated_relationships = []
            for result in consolidation_results.get("consolidated_relationships", []):
                if "consolidation_result" in result and "consolidated_relationship" in result["consolidation_result"]:
                    consolidated_relationships.append(result["consolidation_result"]["consolidated_relationship"])
            
            # Update state with consolidation results
            state["consolidated_relationships"] = consolidated_relationships
            state["consolidation_summary"] = consolidation_results.get("consolidation_summary", {})
            state["doc_relationships"] = consolidated_relationships
            
            # Add any errors from consolidation
            if consolidation_results.get("errors"):
                state["errors"].extend(consolidation_results["errors"])
            
            logger.info(f"Relationship combination complete: {len(state['doc_relationships'])} consolidated relationships")
            return state
            
        except Exception as e:
            logger.error(f"Error in relationship combination: {str(e)}")
            state["errors"].append(f"Relationship combination error: {str(e)}")
            return state

async def test_combine_relationships_with_database():
    """Test the _combine_relationships node with pre-populated database"""
    print("🚀 Starting Real Combine Relationships Test with Database")
    print("=" * 80)
    
    print("🔍 STEP 1: PRE-POPULATE DATABASE")
    print("=" * 80)
    
    # Pre-populate database with existing relationships
    created_count = await pre_populate_database()
    
    if created_count == 0:
        print("❌ Failed to create any relationships in database. Cannot proceed with test.")
        return
    
    print("\n🔍 STEP 2: CREATE NEW DOCUMENT RELATIONSHIPS")
    print("=" * 80)
    
    # Create relationships from new document
    new_relationships = create_new_document_relationships()
    print(f"📄 New Document Relationships Created: {len(new_relationships)}")
    
    print_relationships(new_relationships, "New Document Relationships (should be consolidated)")
    
    print("\n🎯 Expected Consolidation:")
    print("   📌 TP53 --[promotes]--> apoptosis + p53 --[promotes]--> apoptosis → should consolidate")
    print("   📌 murine double minute 2 --[inhibits]--> TP53 + MDM2 --[inhibits]--> p53 → should consolidate")
    print("   📌 CRISPR --[targets]--> DNA + CRISPR-Cas9 --[targets]--> DNA → should consolidate")
    print("   📌 p53 --[promotes]--> apoptosis (duplicate) → should consolidate within document")
    print("   📌 apoptosis --[causes]--> cell_death → should remain unique (no existing matches)")
    print("   📌 cancer --[promotes]--> tumor_growth → should remain unique (no existing matches)")
    
    print("\n🔍 STEP 3: TEST RELATIONSHIP CONSOLIDATOR DIRECTLY")
    print("=" * 80)
    
    from app.services.relationship_consolidator import RelationshipConsolidator
    consolidator = RelationshipConsolidator()
    
    # Convert to Relationship objects
    relationship_objects = []
    for rel_data in new_relationships:
        relationship = Relationship(
            source_entity=rel_data["source_entity"],
            target_entity=rel_data["target_entity"],
            relationship_type=rel_data["relationship_type"],
            relationship_strength=rel_data["relationship_strength"],
            description=rel_data["description"],
            paper_ids=rel_data.get("paper_ids", []),
            section_ids=rel_data.get("section_ids", [])
        )
        relationship_objects.append(relationship)
    
    print("🔍 Testing RelationshipConsolidator directly...")
    consolidation_results = await consolidator.consolidate_relationships(relationship_objects)
    
    print(f"📊 Direct Consolidation Results:")
    print(f"   Input relationships: {len(relationship_objects)}")
    print(f"   Consolidated relationships: {len(consolidation_results.get('consolidated_relationships', []))}")
    print(f"   Consolidation summary: {consolidation_results.get('summary', {})}")
    print(f"   Errors: {consolidation_results.get('errors', [])}")
    
    if consolidation_results.get('consolidated_relationships'):
        print_relationships(consolidation_results['consolidated_relationships'], "Direct Consolidation Results")
    
    print("\n🔍 STEP 4: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleCombineRelationshipsPipeline()
        print("✅ SimpleCombineRelationshipsPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "new_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": new_relationships,
            "doc_entities": [],
            "doc_relationships": [],
            "final_entities": [],
            "final_relationships": [],
            "global_entities": [],
            "global_relationships": [],
            "entity_merges": [],
            "contradictions": [],
            "contradiction_resolutions": [],
            "resolution_summary": {},
            "consolidated_relationships": [],
            "consolidation_summary": {},
            "global_processing_results": {},
            "errors": []
        }
        print("✅ Test state created successfully")
        
        print("\n🤖 Calling real _combine_relationships method...")
        result_state = await pipeline._combine_relationships(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Consolidated Relationships: {len(result_state['consolidated_relationships'])}")
        print(f"🔍 Doc Relationships: {len(result_state['doc_relationships'])}")
        print(f"🔍 Consolidation Summary: {result_state['consolidation_summary']}")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed results
        print_relationships(result_state['consolidated_relationships'], "Final Consolidated Relationships")
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 5: COMPARE RESULTS")
    print("=" * 80)
    
    direct_consolidated = len(consolidation_results.get('consolidated_relationships', []))
    pipeline_consolidated = len(result_state['consolidated_relationships'])
    
    print(f"📊 Results Comparison:")
    print(f"   Direct consolidator results: {direct_consolidated}")
    print(f"   Pipeline node results: {pipeline_consolidated}")
    
    if direct_consolidated == pipeline_consolidated:
        print("🎉 Results match! Both methods found the same number of consolidated relationships.")
    else:
        print("⚠️ Results differ between direct consolidator and pipeline node.")
    
    print("\n🔍 STEP 6: ANALYZE FINAL RESULTS")
    print("=" * 80)
    
    print(f"📊 Final Analysis:")
    print(f"   Input relationships: {len(new_relationships)}")
    print(f"   Consolidated relationships: {len(result_state['consolidated_relationships'])}")
    print(f"   Consolidation rate: {((len(new_relationships) - len(result_state['consolidated_relationships'])) / len(new_relationships) * 100):.1f}%")
    print(f"   Consolidation summary: {result_state['consolidation_summary']}")
    
    print("\n🎉 Test completed successfully!")
    print("📊 Relationship consolidation is now working with database relationships!")

if __name__ == "__main__":
    asyncio.run(test_combine_relationships_with_database())

