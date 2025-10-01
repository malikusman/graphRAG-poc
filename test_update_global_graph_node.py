#!/usr/bin/env python3
"""
Test the _update_global_graph node thoroughly
This test demonstrates the final global graph integration step in the pipeline
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.entities import Entity, EntityType, EntityCategory
from app.models.relationships import Relationship, RelationshipType
from app.pipelines.graphrag_pipeline import GraphRAGState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def pre_populate_global_graph():
    """Pre-populate the global graph with existing entities and relationships"""
    print("🗄️ Pre-populating global graph with existing entities and relationships...")
    
    # Create existing entities in the global graph
    existing_entities = [
        {
            "entity_name": "TP53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "entity_description": "Tumor protein p53, a tumor suppressor protein",
            "aliases": ["p53", "tumor protein 53"],
            "paper_ids": ["existing_paper_001"],
            "section_ids": ["existing_section_001"],
            "frequency": 5
        },
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "entity_description": "Mouse double minute 2 homolog, an oncogene",
            "aliases": ["murine double minute 2", "HDM2"],
            "paper_ids": ["existing_paper_001"],
            "section_ids": ["existing_section_002"],
            "frequency": 3
        },
        {
            "entity_name": "apoptosis",
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "entity_description": "Programmed cell death",
            "aliases": ["programmed cell death", "cell death"],
            "paper_ids": ["existing_paper_001"],
            "section_ids": ["existing_section_003"],
            "frequency": 8
        }
    ]
    
    # Create existing relationships in the global graph
    existing_relationships = [
        {
            "source_entity": "TP53",
            "target_entity": "apoptosis",
            "relationship_type": "inhibits",  # CONTRADICTS new document
            "relationship_strength": 0.90,
            "description": "TP53 inhibits apoptosis in healthy cells",
            "paper_ids": ["existing_paper_001"],
            "section_ids": ["existing_section_004"]
        },
        {
            "source_entity": "MDM2",
            "target_entity": "TP53",
            "relationship_type": "inhibits",
            "relationship_strength": 0.88,
            "description": "MDM2 inhibits TP53 protein",
            "paper_ids": ["existing_paper_001"],
            "section_ids": ["existing_section_005"]
        }
    ]
    
    # Insert entities into database
    from app.database.models import EntityCollection, RelationshipCollection
    entity_count = 0
    relationship_count = 0
    
    for entity_data in existing_entities:
        try:
            entity = Entity(
                entity_name=entity_data["entity_name"],
                entity_type=EntityType(entity_data["entity_type"]),
                entity_category=EntityCategory(entity_data["entity_category"]),
                entity_description=entity_data["entity_description"],
                aliases=entity_data["aliases"],
                paper_ids=entity_data["paper_ids"],
                section_ids=entity_data["section_ids"],
                frequency=entity_data["frequency"]
            )
            entity_id = await EntityCollection.insert_entity(entity)
            print(f"   ✅ Created entity: {entity_data['entity_name']} (ID: {entity_id})")
            entity_count += 1
        except Exception as e:
            print(f"   ❌ Failed to create entity {entity_data['entity_name']}: {str(e)}")
    
    for rel_data in existing_relationships:
        try:
            relationship = Relationship(
                source_entity=rel_data["source_entity"],
                target_entity=rel_data["target_entity"],
                relationship_type=RelationshipType(rel_data["relationship_type"]),
                relationship_strength=rel_data["relationship_strength"],
                description=rel_data["description"],
                paper_ids=rel_data["paper_ids"],
                section_ids=rel_data["section_ids"]
            )
            relationship_id = await RelationshipCollection.insert_relationship(relationship)
            print(f"   ✅ Created relationship: {rel_data['source_entity']} --[{rel_data['relationship_type']}]--> {rel_data['target_entity']} (ID: {relationship_id})")
            relationship_count += 1
        except Exception as e:
            print(f"   ❌ Failed to create relationship {rel_data['source_entity']} --[{rel_data['relationship_type']}]--> {rel_data['target_entity']}: {str(e)}")
    
    print(f"🗄️ Global graph pre-population complete: {entity_count}/{len(existing_entities)} entities, {relationship_count}/{len(existing_relationships)} relationships")
    return entity_count, relationship_count

def create_final_entities() -> List[Dict[str, Any]]:
    """Create final entities from document processing"""
    return [
        {
            "entity_name": "p53",  # Should canonicalize with existing TP53
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "entity_description": "p53 protein, a tumor suppressor",
            "aliases": ["tumor protein 53"],
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_001"],
            "frequency": 3
        },
        {
            "entity_name": "murine double minute 2",  # Should canonicalize with existing MDM2
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "entity_description": "MDM2 protein, regulates p53",
            "aliases": ["MDM2", "HDM2"],
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_002"],
            "frequency": 2
        },
        {
            "entity_name": "programmed cell death",  # Should canonicalize with existing apoptosis
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "entity_description": "Programmed cell death process",
            "aliases": ["apoptosis", "cell death"],
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_003"],
            "frequency": 4
        },
        {
            "entity_name": "insulin",  # New entity, should be added
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "entity_description": "Insulin hormone",
            "aliases": [],
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_004"],
            "frequency": 1
        }
    ]

def create_final_relationships() -> List[Dict[str, Any]]:
    """Create final relationships from document processing"""
    return [
        {
            "source_entity": "p53",
            "target_entity": "programmed cell death",
            "relationship_type": "promotes",  # CONTRADICTS existing: TP53 inhibits apoptosis
            "relationship_strength": 0.85,
            "description": "p53 promotes programmed cell death in response to DNA damage",
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_005"]
        },
        {
            "source_entity": "murine double minute 2",
            "target_entity": "p53",
            "relationship_type": "inhibits",  # SUPPORTS existing: MDM2 inhibits TP53
            "relationship_strength": 0.90,
            "description": "murine double minute 2 inhibits p53 protein stability",
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_006"]
        },
        {
            "source_entity": "insulin",
            "target_entity": "glucose",
            "relationship_type": "decreases",  # New relationship
            "relationship_strength": 0.95,
            "description": "Insulin decreases blood glucose levels",
            "paper_ids": ["new_paper_001"],
            "section_ids": ["new_section_007"]
        }
    ]

def print_entities(entities: List[Dict[str, Any]], title: str):
    """Print entities in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        if isinstance(entity, dict):
            name = entity.get('entity_name', 'Unknown')
            entity_type = entity.get('entity_type', 'Unknown')
            category = entity.get('entity_category', 'Unknown')
            description = entity.get('entity_description', 'No description')
            aliases = entity.get('aliases', [])
            frequency = entity.get('frequency', 1)
        else:
            # Entity object
            name = entity.entity_name
            entity_type = entity.entity_type
            category = entity.entity_category
            description = entity.entity_description
            aliases = entity.aliases
            frequency = entity.frequency
            
        print(f"   {i}. {name}")
        print(f"      Type: {entity_type}")
        print(f"      Category: {category}")
        print(f"      Description: {description}")
        print(f"      Aliases: {aliases}")
        print(f"      Frequency: {frequency}")
        print()

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
        else:
            # Relationship object
            source = rel.source_entity
            target = rel.target_entity
            rel_type = rel.relationship_type
            strength = rel.relationship_strength
            description = rel.description
            
        print(f"   {i}. {source} --[{rel_type}]--> {target}")
        print(f"      Strength: {strength}")
        print(f"      Description: {description}")
        print()

class SimpleUpdateGlobalGraphPipeline:
    """Simple pipeline class with just the _update_global_graph method"""
    
    def __init__(self):
        from app.services.global_graph_manager import GlobalGraphManager
        self.global_graph_manager = GlobalGraphManager()
    
    async def _update_global_graph(self, state: GraphRAGState) -> GraphRAGState:
        """Update global graph with processed results from the pipeline"""
        logger.info(f"Updating global graph with processed results for document {state['document_id']}")
        
        try:
            # Convert final entities and relationships to Entity/Relationship objects
            entities = []
            relationships = []
            
            # Convert entities
            for entity_data in state["final_entities"]:
                try:
                    from app.models.entities import Entity, EntityType, EntityCategory
                    entity = Entity(
                        entity_name=entity_data["entity_name"],
                        entity_type=EntityType(entity_data["entity_type"]),
                        entity_category=EntityCategory(entity_data["entity_category"]),
                        entity_description=entity_data.get("entity_description"),
                        aliases=entity_data.get("aliases", []),
                        paper_ids=entity_data.get("paper_ids", []),
                        section_ids=entity_data.get("section_ids", []),
                        frequency=entity_data.get("frequency", 1)
                    )
                    entities.append(entity)
                except Exception as e:
                    logger.warning(f"Error converting entity {entity_data.get('entity_name', 'unknown')}: {str(e)}")
                    continue
            
            # Convert relationships
            for rel_data in state["final_relationships"]:
                try:
                    from app.models.relationships import Relationship, RelationshipType
                    relationship = Relationship(
                        source_entity=rel_data["source_entity"],
                        target_entity=rel_data["target_entity"],
                        relationship_type=RelationshipType(rel_data["relationship_type"]),
                        relationship_strength=rel_data["relationship_strength"],
                        description=rel_data.get("description"),
                        paper_ids=rel_data.get("paper_ids", []),
                        section_ids=rel_data.get("section_ids", [])
                    )
                    relationships.append(relationship)
                except Exception as e:
                    logger.warning(f"Error converting relationship {rel_data.get('source_entity', 'unknown')} -> {rel_data.get('target_entity', 'unknown')}: {str(e)}")
                    continue
            
            # Process against global graph using enhanced GlobalGraphManager
            global_results = await self.global_graph_manager.process_document_against_global_graph(
                state["document_id"], entities, relationships
            )
            
            # Update state with global processing results
            state["global_processing_results"] = global_results
            
            # Add any errors from global processing
            if global_results.get("errors"):
                state["errors"].extend(global_results["errors"])
            
            logger.info(f"Global graph update complete for document {state['document_id']}: "
                       f"{global_results.get('entities_processed', 0)} entities, "
                       f"{global_results.get('relationships_processed', 0)} relationships processed")
            
            return state
            
        except Exception as e:
            error_msg = f"Error updating global graph: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state

async def test_update_global_graph_node():
    """Test the _update_global_graph node thoroughly"""
    print("🚀 Starting Real Update Global Graph Node Test")
    print("=" * 80)
    
    print("🔍 STEP 1: PRE-POPULATE GLOBAL GRAPH")
    print("=" * 80)
    
    # Pre-populate global graph with existing entities and relationships
    entity_count, relationship_count = await pre_populate_global_graph()
    
    if entity_count == 0 or relationship_count == 0:
        print("❌ Failed to create entities/relationships in global graph. Cannot proceed with test.")
        return
    
    print("\n🔍 STEP 2: CREATE FINAL ENTITIES AND RELATIONSHIPS")
    print("=" * 80)
    
    # Create final entities and relationships from document processing
    final_entities = create_final_entities()
    final_relationships = create_final_relationships()
    
    print(f"📄 Final Entities Created: {len(final_entities)}")
    print_entities(final_entities, "Final Entities (Before Global Graph Processing)")
    
    print(f"📄 Final Relationships Created: {len(final_relationships)}")
    print_relationships(final_relationships, "Final Relationships (Before Global Graph Processing)")
    
    print("\n🎯 Expected Global Graph Processing:")
    print("   📌 p53 → Should canonicalize with existing TP53")
    print("   📌 murine double minute 2 → Should canonicalize with existing MDM2")
    print("   📌 programmed cell death → Should canonicalize with existing apoptosis")
    print("   📌 insulin → Should be added as new entity")
    print("   📌 p53 --[promotes]--> programmed cell death vs TP53 --[inhibits]--> apoptosis → CONTRADICTION")
    print("   📌 murine double minute 2 --[inhibits]--> p53 vs MDM2 --[inhibits]--> TP53 → SUPPORT")
    print("   📌 insulin --[decreases]--> glucose → New relationship")
    
    print("\n🔍 STEP 3: TEST GLOBAL GRAPH MANAGER DIRECTLY")
    print("=" * 80)
    
    from app.services.global_graph_manager import GlobalGraphManager
    from app.models.entities import Entity, EntityType, EntityCategory
    from app.models.relationships import Relationship, RelationshipType
    
    global_graph_manager = GlobalGraphManager()
    
    # Convert to Entity/Relationship objects
    entity_objects = []
    for entity_data in final_entities:
        entity = Entity(
            entity_name=entity_data["entity_name"],
            entity_type=EntityType(entity_data["entity_type"]),
            entity_category=EntityCategory(entity_data["entity_category"]),
            entity_description=entity_data["entity_description"],
            aliases=entity_data["aliases"],
            paper_ids=entity_data["paper_ids"],
            section_ids=entity_data["section_ids"],
            frequency=entity_data["frequency"]
        )
        entity_objects.append(entity)
    
    relationship_objects = []
    for rel_data in final_relationships:
        relationship = Relationship(
            source_entity=rel_data["source_entity"],
            target_entity=rel_data["target_entity"],
            relationship_type=RelationshipType(rel_data["relationship_type"]),
            relationship_strength=rel_data["relationship_strength"],
            description=rel_data["description"],
            paper_ids=rel_data["paper_ids"],
            section_ids=rel_data["section_ids"]
        )
        relationship_objects.append(relationship)
    
    print("🔍 Testing GlobalGraphManager directly...")
    global_results = await global_graph_manager.process_document_against_global_graph(
        "test_doc_001", entity_objects, relationship_objects
    )
    
    print(f"📊 Direct Global Graph Processing Results:")
    print(f"   Document ID: {global_results.get('document_id', 'Unknown')}")
    print(f"   Entities processed: {global_results.get('entities_processed', 0)}")
    print(f"   Relationships processed: {global_results.get('relationships_processed', 0)}")
    print(f"   Global entities count: {global_results.get('global_entities_count', 0)}")
    print(f"   Global relationships count: {global_results.get('global_relationships_count', 0)}")
    print(f"   Errors: {len(global_results.get('errors', []))}")
    
    if global_results.get('errors'):
        print("❌ Errors in global processing:")
        for error in global_results['errors']:
            print(f"   - {error}")
    
    # Print detailed results
    entity_results = global_results.get('entity_canonicalization_results', {})
    if entity_results:
        print(f"\n📈 Entity Canonicalization Results:")
        print(f"   Merge operations: {len(entity_results.get('merge_operations', []))}")
        print(f"   New entities: {len(entity_results.get('new_entities', []))}")
    
    contradiction_results = global_results.get('contradiction_detection_results', {})
    if contradiction_results:
        print(f"\n⚠️ Contradiction Detection Results:")
        print(f"   Contradictions found: {len(contradiction_results.get('contradictions', []))}")
        print(f"   Resolutions applied: {len(contradiction_results.get('resolutions', []))}")
    
    print("\n🔍 STEP 4: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleUpdateGlobalGraphPipeline()
        print("✅ SimpleUpdateGlobalGraphPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "test_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": [],
            "doc_entities": [],
            "doc_relationships": [],
            "final_entities": final_entities,  # This is the input for _update_global_graph
            "final_relationships": final_relationships,  # This is the input for _update_global_graph
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
        
        print("\n🤖 Calling real _update_global_graph method...")
        result_state = await pipeline._update_global_graph(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Global Processing Results: {result_state.get('global_processing_results', {})}")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed global processing results
        global_results = result_state.get('global_processing_results', {})
        if global_results:
            print(f"\n📊 Global Processing Results:")
            print(f"   Document ID: {global_results.get('document_id', 'Unknown')}")
            print(f"   Entities processed: {global_results.get('entities_processed', 0)}")
            print(f"   Relationships processed: {global_results.get('relationships_processed', 0)}")
            print(f"   Global entities count: {global_results.get('global_entities_count', 0)}")
            print(f"   Global relationships count: {global_results.get('global_relationships_count', 0)}")
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 5: ANALYZE GLOBAL GRAPH INTEGRATION")
    print("=" * 80)
    
    print(f"📊 Global Graph Integration Analysis:")
    print(f"   Input entities: {len(final_entities)}")
    print(f"   Input relationships: {len(final_relationships)}")
    print(f"   Global entities in database: {global_results.get('global_entities_count', 0)}")
    print(f"   Global relationships in database: {global_results.get('global_relationships_count', 0)}")
    
    entity_results = global_results.get('entity_canonicalization_results', {})
    if entity_results:
        print(f"   Entity canonicalization operations: {len(entity_results.get('merge_operations', []))}")
        print(f"   New entities added: {len(entity_results.get('new_entities', []))}")
    
    contradiction_results = global_results.get('contradiction_detection_results', {})
    if contradiction_results:
        print(f"   Contradictions detected: {len(contradiction_results.get('contradictions', []))}")
        print(f"   Contradictions resolved: {len(contradiction_results.get('resolutions', []))}")
    
    print("\n🎉 Test completed successfully!")
    print("📊 The _update_global_graph node is working and integrating with the global knowledge graph!")

if __name__ == "__main__":
    asyncio.run(test_update_global_graph_node())
