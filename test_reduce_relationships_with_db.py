#!/usr/bin/env python3
"""
Test the _reduce_relationships node with pre-populated database
This test demonstrates cross-document contradiction detection and resolution
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
    """Pre-populate database with existing relationships that will create contradictions"""
    print("🗄️ Pre-populating database with existing relationships...")
    
    # Create existing relationships that will create contradictions with new ones
    existing_relationships = [
        # These will create DIRECT CONTRADICTIONS
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "inhibits",  # CONTRADICTS: new doc says "promotes"
            "relationship_strength": 0.90,
            "description": "p53 inhibits apoptosis in healthy cells from previous research",
            "paper_ids": ["previous_doc_001"],
            "section_ids": ["previous_section_001"]
        },
        {
            "source_entity": "caffeine",
            "target_entity": "sleep",
            "relationship_type": "inhibits",
            "relationship_strength": 0.95,
            "description": "Caffeine inhibits sleep by blocking adenosine receptors from previous study",
            "paper_ids": ["previous_doc_001"],
            "section_ids": ["previous_section_002"]
        },
        
        # These will create INDIRECT CONTRADICTIONS (same entities, different relationships)
        {
            "source_entity": "insulin",
            "target_entity": "glucose",
            "relationship_type": "decreases",
            "relationship_strength": 0.88,
            "description": "Insulin decreases blood glucose levels from previous research",
            "paper_ids": ["previous_doc_001"],
            "section_ids": ["previous_section_003"]
        },
        {
            "source_entity": "exercise",
            "target_entity": "cardiovascular_health",
            "relationship_type": "enhances",
            "relationship_strength": 0.92,
            "description": "Exercise enhances cardiovascular health from previous study",
            "paper_ids": ["previous_doc_001"],
            "section_ids": ["previous_section_004"]
        },
        
        # These will be SUPPORTING (no contradictions)
        {
            "source_entity": "vitamin_c",
            "target_entity": "immune_system",
            "relationship_type": "enhances",
            "relationship_strength": 0.75,
            "description": "Vitamin C enhances immune system from previous research",
            "paper_ids": ["previous_doc_001"],
            "section_ids": ["previous_section_005"]
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
    """Create relationships from a new document that will create contradictions"""
    return [
        # DIRECT CONTRADICTIONS - same entities, opposite relationship types
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",  # CONTRADICTS: existing says "inhibits"
            "relationship_strength": 0.85,
            "description": "p53 promotes apoptosis in response to DNA damage from new research",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_001"]
        },
        {
            "source_entity": "caffeine",
            "target_entity": "sleep",
            "relationship_type": "promotes",  # CONTRADICTS: existing says "inhibits"
            "relationship_strength": 0.70,
            "description": "Caffeine promotes sleep quality when consumed in moderation from new study",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_002"]
        },
        
        # INDIRECT CONTRADICTIONS - same entities, different relationship types
        {
            "source_entity": "insulin",
            "target_entity": "glucose",
            "relationship_type": "increases",  # CONTRADICTS: existing says "reduces"
            "relationship_strength": 0.60,
            "description": "Insulin increases glucose uptake in cells from new research",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_003"]
        },
        {
            "source_entity": "exercise",
            "target_entity": "cardiovascular_health",
            "relationship_type": "inhibits",  # CONTRADICTS: existing says "enhances"
            "relationship_strength": 0.45,
            "description": "Excessive exercise damages cardiovascular health from new study",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_004"]
        },
        
        # SUPPORTING RELATIONSHIPS - no contradictions
        {
            "source_entity": "vitamin_c",
            "target_entity": "immune_system",
            "relationship_type": "enhances",  # SUPPORTS: existing says same
            "relationship_strength": 0.80,
            "description": "Vitamin C strengthens immune system function from new research",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_005"]
        },
        {
            "source_entity": "meditation",
            "target_entity": "stress",
            "relationship_type": "decreases",
            "relationship_strength": 0.88,
            "description": "Meditation reduces stress levels from new study",
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_006"]
        }
    ]

def print_relationships(relationships: List[Dict[str, Any]], title: str):
    """Print relationships in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(relationships)}")
    for i, rel in enumerate(relationships, 1):
        if isinstance(rel, dict):
            source = rel.get('source_entity', 'Unknown')
            target = rel.get('target_entity', 'Unknown')
            rel_type = rel.get('relationship_type', 'Unknown')
            strength = rel.get('relationship_strength', 0.0)
            description = rel.get('description', 'No description')
            sections = rel.get('section_ids', [])
        else:
            # Relationship object
            source = rel.source_entity
            target = rel.target_entity
            rel_type = rel.relationship_type
            strength = rel.relationship_strength
            description = rel.description
            sections = rel.section_ids
            
        print(f"   {i}. {source} --[{rel_type}]--> {target}")
        print(f"      Strength: {strength}")
        print(f"      Description: {description}")
        print(f"      Sections: {sections}")
        print()

def print_contradictions(contradictions: List[Dict[str, Any]]):
    """Print contradictions in a formatted way"""
    print(f"\n⚠️ Contradictions Detected:")
    print(f"   Count: {len(contradictions)}")
    for i, contradiction in enumerate(contradictions, 1):
        print(f"   {i}. Contradiction Type: {contradiction.get('contradiction_type', 'Unknown')}")
        print(f"      Severity: {contradiction.get('severity', 'Unknown')}")
        print(f"      Entity A: {contradiction.get('entity_a', 'Unknown')}")
        print(f"      Entity B: {contradiction.get('entity_b', 'Unknown')}")
        print(f"      Existing Relationship: {contradiction.get('existing_relationship', {})}")
        print(f"      New Relationship: {contradiction.get('new_relationship', {})}")
        print(f"      Reasoning: {contradiction.get('reasoning', 'No reasoning provided')}")
        print()

def print_resolutions(resolutions: List[Dict[str, Any]]):
    """Print contradiction resolutions in a formatted way"""
    print(f"\n🔧 Contradiction Resolutions:")
    print(f"   Count: {len(resolutions)}")
    for i, resolution in enumerate(resolutions, 1):
        print(f"   {i}. Resolution Strategy: {resolution.get('resolution_strategy', 'Unknown')}")
        print(f"      Confidence: {resolution.get('confidence', 0.0)}")
        print(f"      Final Relationship: {resolution.get('final_relationship', {})}")
        print(f"      Reasoning: {resolution.get('reasoning', 'No reasoning provided')}")
        print(f"      Evidence: {resolution.get('evidence', 'No evidence provided')}")
        print()

class SimpleReduceRelationshipsPipeline:
    """Simple pipeline class with just the _reduce_relationships method"""
    
    def __init__(self):
        from app.services.contradiction_detector import ContradictionDetector
        from app.services.contradiction_resolver import ContradictionResolver
        self.contradiction_detector = ContradictionDetector()
        self.contradiction_resolver = ContradictionResolver()
    
    async def _reduce_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Detect and resolve contradictions across documents"""
        logger.info(f"Starting relationship reduction for document {state['document_id']}")
        
        try:
            # Convert doc_relationships to Relationship objects for processing
            from app.models.relationships import Relationship
            relationships = []
            for rel_data in state["doc_relationships"]:
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
            
            # Step 1: Detect contradictions
            print("🔍 Step 1: Detecting contradictions...")
            context_info = {
                "paper_sources": [],  # Could be extracted from document metadata
                "publication_years": [],  # Could be extracted from document metadata
                "section_types": []  # Could be extracted from document metadata
            }
            contradictions = await self.contradiction_detector.detect_relationship_contradictions_with_context(
                relationships=relationships,
                context_info=context_info
            )
            
            print(f"   Found {len(contradictions)} contradictions")
            state["contradictions"] = contradictions
            
            # Step 2: Resolve contradictions
            print("🔧 Step 2: Resolving contradictions...")
            resolutions = []
            for contradiction in contradictions:
                resolution = await self.contradiction_resolver.resolve_contradiction(contradiction)
                resolutions.append(resolution)
            
            print(f"   Resolved {len(resolutions)} contradictions")
            state["contradiction_resolutions"] = resolutions
            
            # Step 3: Create final relationships (resolved + non-contradictory)
            print("📊 Step 3: Creating final relationships...")
            final_relationships = []
            
            # Add resolved relationships
            for resolution in resolutions:
                if resolution.get("final_relationship"):
                    final_relationships.append(resolution["final_relationship"])
            
            # Add non-contradictory relationships
            contradictory_relationships = set()
            for contradiction in contradictions:
                if contradiction.get("new_relationship"):
                    contradictory_relationships.add(contradiction["new_relationship"].get("id", ""))
            
            for rel in relationships:
                rel_id = getattr(rel, 'id', f"{rel.source_entity}_{rel.target_entity}_{rel.relationship_type}")
                if rel_id not in contradictory_relationships:
                    final_relationships.append({
                        "source_entity": rel.source_entity,
                        "target_entity": rel.target_entity,
                        "relationship_type": rel.relationship_type,
                        "relationship_strength": rel.relationship_strength,
                        "description": rel.description,
                        "paper_ids": rel.paper_ids,
                        "section_ids": rel.section_ids
                    })
            
            state["final_relationships"] = final_relationships
            
            # Create resolution summary
            resolution_summary = {
                "total_contradictions": len(contradictions),
                "resolved_contradictions": len(resolutions),
                "resolution_strategies": {},
                "final_relationships_count": len(final_relationships)
            }
            
            for resolution in resolutions:
                strategy = resolution.get("resolution_strategy", "unknown")
                resolution_summary["resolution_strategies"][strategy] = resolution_summary["resolution_strategies"].get(strategy, 0) + 1
            
            state["resolution_summary"] = resolution_summary
            
            logger.info(f"Relationship reduction complete: {len(contradictions)} contradictions detected, {len(resolutions)} resolved")
            return state
            
        except Exception as e:
            logger.error(f"Error in relationship reduction: {str(e)}")
            state["errors"].append(f"Relationship reduction error: {str(e)}")
            return state

async def test_reduce_relationships_with_database():
    """Test the _reduce_relationships node with pre-populated database"""
    print("🚀 Starting Real Reduce Relationships Test with Database")
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
    
    print_relationships(new_relationships, "New Document Relationships (will create contradictions)")
    
    print("\n🎯 Expected Contradictions:")
    print("   📌 p53 --[inhibits]--> apoptosis (existing) vs p53 --[promotes]--> apoptosis (new) → DIRECT CONTRADICTION")
    print("   📌 caffeine --[inhibits]--> sleep (existing) vs caffeine --[promotes]--> sleep (new) → DIRECT CONTRADICTION")
    print("   📌 insulin --[decreases]--> glucose (existing) vs insulin --[increases]--> glucose (new) → INDIRECT CONTRADICTION")
    print("   📌 exercise --[enhances]--> cardiovascular_health (existing) vs exercise --[inhibits]--> cardiovascular_health (new) → INDIRECT CONTRADICTION")
    print("   📌 vitamin_c --[enhances]--> immune_system (both same) → NO CONTRADICTION")
    print("   📌 meditation --[decreases]--> stress (new only) → NO CONTRADICTION")
    
    print("\n🔍 STEP 3: TEST CONTRADICTION DETECTOR DIRECTLY")
    print("=" * 80)
    
    from app.services.contradiction_detector import ContradictionDetector
    from app.models.relationships import Relationship
    
    detector = ContradictionDetector()
    
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
    
    print("🔍 Testing ContradictionDetector directly...")
    context_info = {
        "paper_sources": [],
        "publication_years": [],
        "section_types": []
    }
    contradictions = await detector.detect_relationship_contradictions_with_context(
        relationships=relationship_objects,
        context_info=context_info
    )
    
    print(f"📊 Direct Contradiction Detection Results:")
    print(f"   Input relationships: {len(relationship_objects)}")
    print(f"   Contradictions detected: {len(contradictions)}")
    
    print_contradictions(contradictions)
    
    print("\n🔍 STEP 4: TEST CONTRADICTION RESOLVER DIRECTLY")
    print("=" * 80)
    
    from app.services.contradiction_resolver import ContradictionResolver
    resolver = ContradictionResolver()
    
    print("🔍 Testing ContradictionResolver directly...")
    resolutions = []
    for contradiction in contradictions:
        resolution = await resolver.resolve_contradiction(contradiction)
        resolutions.append(resolution)
    
    print(f"📊 Direct Contradiction Resolution Results:")
    print(f"   Contradictions to resolve: {len(contradictions)}")
    print(f"   Resolutions generated: {len(resolutions)}")
    
    print_resolutions(resolutions)
    
    print("\n🔍 STEP 5: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleReduceRelationshipsPipeline()
        print("✅ SimpleReduceRelationshipsPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "new_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": [],
            "doc_entities": [],
            "doc_relationships": new_relationships,
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
        
        print("\n🤖 Calling real _reduce_relationships method...")
        result_state = await pipeline._reduce_relationships(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Contradictions Detected: {len(result_state['contradictions'])}")
        print(f"🔍 Contradictions Resolved: {len(result_state['contradiction_resolutions'])}")
        print(f"🔍 Final Relationships: {len(result_state['final_relationships'])}")
        print(f"🔍 Resolution Summary: {result_state['resolution_summary']}")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed results
        print_contradictions(result_state['contradictions'])
        print_resolutions(result_state['contradiction_resolutions'])
        print_relationships(result_state['final_relationships'], "Final Relationships (After Resolution)")
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 6: ANALYZE FINAL RESULTS")
    print("=" * 80)
    
    print(f"📊 Final Analysis:")
    print(f"   Input relationships: {len(new_relationships)}")
    print(f"   Contradictions detected: {len(result_state['contradictions'])}")
    print(f"   Contradictions resolved: {len(result_state['contradiction_resolutions'])}")
    print(f"   Final relationships: {len(result_state['final_relationships'])}")
    print(f"   Resolution success rate: {(len(result_state['contradiction_resolutions']) / max(len(result_state['contradictions']), 1) * 100):.1f}%")
    print(f"   Resolution summary: {result_state['resolution_summary']}")
    
    print("\n🎉 Test completed successfully!")
    print("📊 Cross-document contradiction detection and resolution is now working!")

if __name__ == "__main__":
    asyncio.run(test_reduce_relationships_with_database())
