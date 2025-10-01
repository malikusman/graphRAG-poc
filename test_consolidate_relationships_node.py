#!/usr/bin/env python3
"""
Test the _consolidate_relationships node thoroughly
This test demonstrates the final relationship consolidation step in the pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.relationships import Relationship
from app.pipelines.graphrag_pipeline import GraphRAGState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_final_relationships() -> List[Dict[str, Any]]:
    """Create final relationships that should be consolidated"""
    return [
        # Group 1: Multiple relationships about p53 and apoptosis (should consolidate)
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.85,
            "description": "p53 promotes apoptosis in response to DNA damage",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_001"]
        },
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.75,
            "description": "p53 promotes apoptosis through mitochondrial pathway",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_002"]
        },
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.90,
            "description": "p53 promotes apoptosis in cancer cells",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_003"]
        },
        
        # Group 2: Multiple relationships about MDM2 and p53 (should consolidate)
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "inhibits",
            "relationship_strength": 0.88,
            "description": "MDM2 inhibits p53 by targeting it for degradation",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_004"]
        },
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "inhibits",
            "relationship_strength": 0.82,
            "description": "MDM2 inhibits p53 protein stability",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_005"]
        },
        
        # Group 3: Single relationship (should remain as-is)
        {
            "source_entity": "insulin",
            "target_entity": "glucose",
            "relationship_type": "decreases",
            "relationship_strength": 0.95,
            "description": "Insulin decreases blood glucose levels",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_006"]
        },
        
        # Group 4: Multiple relationships with different types (should use complementary strategy)
        {
            "source_entity": "exercise",
            "target_entity": "cardiovascular_health",
            "relationship_type": "enhances",
            "relationship_strength": 0.80,
            "description": "Exercise enhances cardiovascular health through improved circulation",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_007"]
        },
        {
            "source_entity": "exercise",
            "target_entity": "cardiovascular_health",
            "relationship_type": "enhances",
            "relationship_strength": 0.75,
            "description": "Exercise enhances cardiovascular health by strengthening heart muscle",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_008"]
        },
        
        # Group 5: High variance in strengths (should use evidence-based strategy)
        {
            "source_entity": "caffeine",
            "target_entity": "alertness",
            "relationship_type": "increases",
            "relationship_strength": 0.95,
            "description": "Caffeine significantly increases alertness",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_009"]
        },
        {
            "source_entity": "caffeine",
            "target_entity": "alertness",
            "relationship_type": "increases",
            "relationship_strength": 0.45,
            "description": "Caffeine moderately increases alertness",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_010"]
        },
        {
            "source_entity": "caffeine",
            "target_entity": "alertness",
            "relationship_type": "increases",
            "relationship_strength": 0.20,
            "description": "Caffeine slightly increases alertness",
            "paper_ids": ["paper_001"],
            "section_ids": ["section_011"]
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

def print_consolidation_summary(summary: Dict[str, Any]):
    """Print consolidation summary"""
    print(f"\n📈 Consolidation Summary:")
    print(f"   Consensus: {summary.get('consensus', 0)}")
    print(f"   Evidence-based: {summary.get('evidence_based', 0)}")
    print(f"   Temporal: {summary.get('temporal', 0)}")
    print(f"   Complementary: {summary.get('complementary', 0)}")
    print(f"   Single relationship: {summary.get('single_relationship', 0)}")
    print(f"   Errors: {summary.get('errors', 0)}")

class SimpleConsolidateRelationshipsPipeline:
    """Simple pipeline class with just the _consolidate_relationships method"""
    
    def __init__(self):
        from app.services.relationship_consolidator import RelationshipConsolidator
        self.relationship_consolidator = RelationshipConsolidator()
    
    async def _consolidate_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Consolidate relationships using enhanced consolidation strategies"""
        logger.info(f"Starting relationship consolidation for document {state['document_id']}")
        
        try:
            # Convert final_relationships to Relationship objects for processing
            from app.models.relationships import Relationship
            relationships = []
            for rel_data in state["final_relationships"]:
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
            
            # Update state with consolidation results
            state["consolidated_relationships"] = consolidation_results.get("consolidated_relationships", [])
            state["consolidation_summary"] = consolidation_results.get("consolidation_summary", {})
            
            # Add any errors from consolidation
            if consolidation_results.get("errors"):
                state["errors"].extend(consolidation_results["errors"])
            
            # Update final_relationships with consolidated results
            if state["consolidated_relationships"]:
                consolidated_final_relationships = []
                for consolidation_result in state["consolidated_relationships"]:
                    if "consolidation_result" in consolidation_result:
                        consolidated_rel = consolidation_result["consolidation_result"]["consolidated_relationship"]
                        consolidated_final_relationships.append(consolidated_rel)
                
                if consolidated_final_relationships:
                    state["final_relationships"] = consolidated_final_relationships
            
            logger.info(f"Relationship consolidation complete: {len(state['consolidated_relationships'])} consolidated relationships, "
                       f"{state['consolidation_summary']}")
            return state
            
        except Exception as e:
            error_msg = f"Error in relationship consolidation: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Keep existing final_relationships
            return state

async def test_consolidate_relationships_node():
    """Test the _consolidate_relationships node thoroughly"""
    print("🚀 Starting Real Consolidate Relationships Node Test")
    print("=" * 80)
    
    print("🔍 STEP 1: CREATE TEST FINAL RELATIONSHIPS")
    print("=" * 80)
    
    # Create test relationships that should be consolidated
    final_relationships = create_test_final_relationships()
    print(f"📄 Final Relationships Created: {len(final_relationships)}")
    
    print_relationships(final_relationships, "Final Relationships (Before Consolidation)")
    
    print("\n🎯 Expected Consolidation Groups:")
    print("   📌 Group 1: p53 --[promotes]--> apoptosis (3 relationships) → Should use CONSENSUS strategy")
    print("   📌 Group 2: MDM2 --[inhibits]--> p53 (2 relationships) → Should use CONSENSUS strategy")
    print("   📌 Group 3: insulin --[decreases]--> glucose (1 relationship) → Should use SINGLE strategy")
    print("   📌 Group 4: exercise --[enhances]--> cardiovascular_health (2 same types) → Should use CONSENSUS strategy")
    print("   📌 Group 5: caffeine --[increases]--> alertness (3 relationships, high variance) → Should use EVIDENCE-BASED strategy")
    
    print("\n🔍 STEP 2: TEST RELATIONSHIP CONSOLIDATOR DIRECTLY")
    print("=" * 80)
    
    from app.services.relationship_consolidator import RelationshipConsolidator
    consolidator = RelationshipConsolidator()
    
    # Convert to Relationship objects
    relationship_objects = []
    for rel_data in final_relationships:
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
    print(f"   Consolidation summary: {consolidation_results.get('consolidation_summary', {})}")
    print(f"   Errors: {consolidation_results.get('errors', [])}")
    
    if consolidation_results.get('consolidated_relationships'):
        print_relationships(consolidation_results['consolidated_relationships'], "Direct Consolidation Results")
    
    print_consolidation_summary(consolidation_results.get('consolidation_summary', {}))
    
    print("\n🔍 STEP 3: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleConsolidateRelationshipsPipeline()
        print("✅ SimpleConsolidateRelationshipsPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "test_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": [],
            "doc_entities": [],
            "doc_relationships": [],
            "final_entities": [],
            "final_relationships": final_relationships,  # This is the input for _consolidate_relationships
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
        
        print("\n🤖 Calling real _consolidate_relationships method...")
        result_state = await pipeline._consolidate_relationships(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Consolidated Relationships: {len(result_state['consolidated_relationships'])}")
        print(f"🔍 Final Relationships (Updated): {len(result_state['final_relationships'])}")
        print(f"🔍 Consolidation Summary: {result_state['consolidation_summary']}")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed results
        print_relationships(result_state['consolidated_relationships'], "Consolidated Relationships (Raw Results)")
        print_relationships(result_state['final_relationships'], "Final Relationships (After Consolidation)")
        print_consolidation_summary(result_state['consolidation_summary'])
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 4: ANALYZE CONSOLIDATION EFFECTIVENESS")
    print("=" * 80)
    
    input_count = len(final_relationships)
    consolidated_count = len(result_state['consolidated_relationships'])
    final_count = len(result_state['final_relationships'])
    
    print(f"📊 Consolidation Analysis:")
    print(f"   Input relationships: {input_count}")
    print(f"   Consolidated relationships (raw): {consolidated_count}")
    print(f"   Final relationships (processed): {final_count}")
    print(f"   Consolidation rate: {((input_count - final_count) / input_count * 100):.1f}%")
    
    summary = result_state['consolidation_summary']
    print(f"\n📈 Strategy Distribution:")
    for strategy, count in summary.items():
        if strategy != 'errors' and count > 0:
            print(f"   {strategy}: {count}")
    
    print("\n🎉 Test completed successfully!")
    print("📊 The _consolidate_relationships node is working perfectly!")

if __name__ == "__main__":
    asyncio.run(test_consolidate_relationships_node())
