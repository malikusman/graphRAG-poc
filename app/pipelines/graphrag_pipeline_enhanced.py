"""
Enhanced LangGraph pipeline for GraphRAG Map-Combine-Reduce processing
with detailed logging for each node
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

from app.core.config import settings
from app.configs.schemas import load_prompt, ENTITY_CATEGORIES, RELATIONSHIP_TYPES
from app.services.entity_canonicalizer import EntityCanonicalizer
from app.services.contradiction_detector import ContradictionDetector
from app.services.contradiction_resolver import ContradictionResolver
from app.services.relationship_consolidator import RelationshipConsolidator
from app.services.global_graph_manager import GlobalGraphManager
from app.utils.math_utils import calculate_noisy_or_strength

logger = logging.getLogger(__name__)


class GraphRAGState(TypedDict):
    """State for GraphRAG pipeline"""
    document_id: str
    sections: List[Dict[str, Any]]
    temp_entities: List[Dict[str, Any]]
    temp_relationships: List[Dict[str, Any]]
    doc_entities: List[Dict[str, Any]]
    doc_relationships: List[Dict[str, Any]]
    final_entities: List[Dict[str, Any]]
    final_relationships: List[Dict[str, Any]]
    # NEW FIELDS FOR MULTI-DOCUMENT PROCESSING:
    global_entities: List[Dict[str, Any]]      # Existing global entities
    global_relationships: List[Dict[str, Any]] # Existing global relationships
    entity_merges: List[Dict[str, Any]]        # Entity merge operations
    contradictions: List[Dict[str, Any]]       # Detected contradictions
    contradiction_resolutions: List[Dict[str, Any]]  # Contradiction resolution results
    resolution_summary: Dict[str, Any]         # Summary of resolution strategies used
    consolidated_relationships: List[Dict[str, Any]]  # Consolidated relationship results
    consolidation_summary: Dict[str, Any]      # Summary of consolidation strategies used
    global_processing_results: Dict[str, Any]  # Global graph processing results
    errors: List[str]


class EnhancedGraphRAGPipeline:
    """Enhanced GraphRAG processing pipeline with detailed logging"""
    
    def __init__(self):
        """Initialize the pipeline with LLM and prompts"""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Load prompts
        self.entity_prompt_config = load_prompt("entity_extraction", "map")
        self.relationship_prompt_config = load_prompt("relationship_extraction", "map")
        
        # Create prompt templates
        self.entity_prompt = ChatPromptTemplate.from_template(
            self.entity_prompt_config["user_prompt"]
        )
        self.relationship_prompt = ChatPromptTemplate.from_template(
            self.relationship_prompt_config["user_prompt"]
        )
        
        # Create output parsers
        self.entity_parser = JsonOutputParser()
        self.relationship_parser = JsonOutputParser()
        
        # Initialize Reduce phase services
        self.entity_canonicalizer = EntityCanonicalizer()
        self.contradiction_detector = ContradictionDetector()
        self.contradiction_resolver = ContradictionResolver()
        self.relationship_consolidator = RelationshipConsolidator()
        self.global_graph_manager = GlobalGraphManager()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph pipeline"""
        workflow = StateGraph(GraphRAGState)
        
        # Add nodes
        workflow.add_node("map_entities", self._map_entities)
        workflow.add_node("map_relationships", self._map_relationships)
        workflow.add_node("combine_entities", self._combine_entities)
        workflow.add_node("combine_relationships", self._combine_relationships)
        workflow.add_node("reduce_entities", self._reduce_entities)
        workflow.add_node("reduce_relationships", self._reduce_relationships)
        workflow.add_node("consolidate_relationships", self._consolidate_relationships)
        workflow.add_node("update_global_graph", self._update_global_graph)
        
        # Add edges
        workflow.set_entry_point("map_entities")
        workflow.add_edge("map_entities", "map_relationships")
        workflow.add_edge("map_relationships", "combine_entities")
        workflow.add_edge("combine_entities", "combine_relationships")
        workflow.add_edge("combine_relationships", "reduce_entities")
        workflow.add_edge("reduce_entities", "reduce_relationships")
        workflow.add_edge("reduce_relationships", "consolidate_relationships")
        workflow.add_edge("consolidate_relationships", "update_global_graph")
        workflow.add_edge("update_global_graph", END)
        
        return workflow.compile()
    
    def _log_entities_detailed(self, entities: List[Dict[str, Any]], title: str):
        """Log entities with detailed information"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📋 {title} ({len(entities)} total)")
        logger.info(f"{'='*60}")
        
        for i, entity in enumerate(entities, 1):
            logger.info(f"{i}. {entity.get('entity_name', 'N/A')}")
            logger.info(f"   Type: {entity.get('entity_type', 'N/A')}")
            logger.info(f"   Category: {entity.get('entity_category', 'N/A')}")
            logger.info(f"   Description: {entity.get('description', entity.get('entity_description', 'N/A'))[:150]}...")
            logger.info(f"   Frequency: {entity.get('frequency', 1)}")
            logger.info(f"   Aliases: {entity.get('aliases', [])}")
            logger.info(f"   Section IDs: {entity.get('section_ids', [])}")
            logger.info(f"   Document ID: {entity.get('document_id', 'N/A')}")
            logger.info("")
    
    def _log_relationships_detailed(self, relationships: List[Dict[str, Any]], title: str):
        """Log relationships with detailed information"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔗 {title} ({len(relationships)} total)")
        logger.info(f"{'='*60}")
        
        for i, rel in enumerate(relationships, 1):
            logger.info(f"{i}. {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
            logger.info(f"   Type: {rel.get('relationship_type', 'N/A')}")
            logger.info(f"   Strength: {rel.get('relationship_strength', 'N/A')}")
            logger.info(f"   Description: {rel.get('description', 'N/A')[:150]}...")
            logger.info(f"   Section IDs: {rel.get('section_ids', [])}")
            logger.info(f"   Document ID: {rel.get('document_id', 'N/A')}")
            logger.info("")
    
    async def _map_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Map phase: Extract entities from sections with detailed logging"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 1: MAP ENTITIES")
        logger.info(f"{'='*80}")
        logger.info(f"Processing {len(state['sections'])} sections for entity extraction...")
        
        temp_entities = []
        errors = []
        
        for section_idx, section in enumerate(state["sections"], 1):
            logger.info(f"\n📄 Processing Section {section_idx}: {section.get('title', 'Untitled')}")
            logger.info(f"Text length: {len(section['text'])} characters")
            
            try:
                # Create entity extraction chain
                entity_chain = self.entity_prompt | self.llm | self.entity_parser
                
                # Extract entities from section
                result = await entity_chain.ainvoke({
                    "section_text": section["text"],
                    "section_title": section.get("title", "")
                })
                
                logger.info(f"Raw LLM result: {json.dumps(result, indent=2)}")
                
                # Process extracted entities
                if "entities" in result:
                    section_entities = []
                    for entity in result["entities"]:
                        entity["document_id"] = state["document_id"]
                        entity["section_id"] = str(section["_id"])
                        entity["provenance"] = entity.get("provenance", section["text"][:200])
                        temp_entities.append(entity)
                        section_entities.append(entity)
                    
                    logger.info(f"✅ Extracted {len(section_entities)} entities from this section:")
                    for entity in section_entities:
                        logger.info(f"  - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
                else:
                    logger.warning(f"⚠️ No entities found in section {section['_id']}")
                
            except Exception as e:
                error_msg = f"Error extracting entities from section {section['_id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        state["temp_entities"] = temp_entities
        state["errors"].extend(errors)
        
        # Log all extracted entities
        self._log_entities_detailed(temp_entities, "ALL EXTRACTED ENTITIES")
        
        logger.info(f"\n✅ MAP ENTITIES COMPLETE: {len(temp_entities)} entities extracted")
        return state
    
    async def _map_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Map phase: Extract relationships from sections with detailed logging"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 2: MAP RELATIONSHIPS")
        logger.info(f"{'='*80}")
        logger.info(f"Processing {len(state['sections'])} sections for relationship extraction...")
        
        temp_relationships = []
        errors = []
        
        for section_idx, section in enumerate(state["sections"], 1):
            logger.info(f"\n📄 Processing Section {section_idx}: {section.get('title', 'Untitled')}")
            
            try:
                # Get entities from this section
                section_entities = [e for e in state["temp_entities"] if e["section_id"] == str(section["_id"])]
                
                logger.info(f"Found {len(section_entities)} entities in this section:")
                for entity in section_entities:
                    logger.info(f"  - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
                
                if len(section_entities) < 2:
                    logger.warning(f"⚠️ Need at least 2 entities for relationships, skipping section {section['_id']}")
                    continue
                
                # Create entities list for prompt
                entities_list = [f"- {e['entity_name']} ({e['entity_type']})" for e in section_entities]
                entities_text = "\n".join(entities_list)
                
                # Create relationship extraction chain
                relationship_chain = self.relationship_prompt | self.llm | self.relationship_parser
                
                # Extract relationships from section
                result = await relationship_chain.ainvoke({
                    "section_text": section["text"],
                    "section_title": section.get("title", ""),
                    "entities_list": entities_text
                })
                
                logger.info(f"Raw LLM result: {json.dumps(result, indent=2)}")
                
                # Process extracted relationships
                if "relationships" in result:
                    section_relationships = []
                    for rel in result["relationships"]:
                        rel["document_id"] = state["document_id"]
                        rel["section_id"] = str(section["_id"])
                        rel["provenance"] = rel.get("provenance", section["text"][:200])
                        temp_relationships.append(rel)
                        section_relationships.append(rel)
                    
                    logger.info(f"✅ Extracted {len(section_relationships)} relationships from this section:")
                    for rel in section_relationships:
                        logger.info(f"  - {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')} ({rel.get('relationship_type', 'N/A')})")
                else:
                    logger.warning(f"⚠️ No relationships found in section {section['_id']}")
                
            except Exception as e:
                error_msg = f"Error extracting relationships from section {section['_id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        state["temp_relationships"] = temp_relationships
        state["errors"].extend(errors)
        
        # Log all extracted relationships
        self._log_relationships_detailed(temp_relationships, "ALL EXTRACTED RELATIONSHIPS")
        
        logger.info(f"\n✅ MAP RELATIONSHIPS COMPLETE: {len(temp_relationships)} relationships extracted")
        return state
    
    async def _combine_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Combine phase: Merge entities within document with detailed logging"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 3: COMBINE ENTITIES")
        logger.info(f"{'='*80}")
        logger.info(f"Combining {len(state['temp_entities'])} extracted entities...")
        
        # Group entities by name and type
        entity_groups = {}
        for entity in state["temp_entities"]:
            key = (entity["entity_name"], entity["entity_type"])
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)
        
        logger.info(f"Found {len(entity_groups)} unique entity groups:")
        for (name, entity_type), entities in entity_groups.items():
            logger.info(f"  - {name} ({entity_type}): {len(entities)} instances")
        
        # Merge entities
        doc_entities = []
        for (name, entity_type), entities in entity_groups.items():
            # Combine aliases
            all_aliases = set()
            for entity in entities:
                all_aliases.update(entity.get("aliases", []))
            
            # Select best description (longest/most detailed)
            best_entity = max(entities, key=lambda e: len(e.get("description", "")))
            
            # Create merged entity
            merged_entity = {
                "entity_name": name,
                "entity_type": entity_type,
                "entity_category": best_entity["entity_category"],
                "aliases": list(all_aliases),
                "description": best_entity["description"],
                "frequency": len(entities),
                "document_id": state["document_id"],
                "section_ids": [e["section_id"] for e in entities],
                "provenance": [e["provenance"] for e in entities]
            }
            
            doc_entities.append(merged_entity)
        
        state["doc_entities"] = doc_entities
        
        # Log combined entities
        self._log_entities_detailed(doc_entities, "COMBINED ENTITIES")
        
        logger.info(f"\n✅ COMBINE ENTITIES COMPLETE: {len(doc_entities)} unique entities")
        return state
    
    async def _combine_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Combine phase: Merge relationships within document with detailed logging"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 4: COMBINE RELATIONSHIPS")
        logger.info(f"{'='*80}")
        logger.info(f"Combining {len(state['temp_relationships'])} extracted relationships...")
        
        # Group relationships by source, target, and type
        rel_groups = {}
        for rel in state["temp_relationships"]:
            key = (rel["source_entity"], rel["target_entity"], rel["relationship_type"])
            if key not in rel_groups:
                rel_groups[key] = []
            rel_groups[key].append(rel)
        
        logger.info(f"Found {len(rel_groups)} unique relationship groups:")
        for (source, target, rel_type), relationships in rel_groups.items():
            logger.info(f"  - {source} -> {target} ({rel_type}): {len(relationships)} instances")
        
        # Merge relationships using noisy-OR
        doc_relationships = []
        for (source, target, rel_type), relationships in rel_groups.items():
            # Calculate noisy-OR strength using proper formula
            strengths = [rel["relationship_strength"] for rel in relationships]
            noisy_or_strength = calculate_noisy_or_strength(strengths)
            
            logger.info(f"Merging {source} -> {target} ({rel_type}):")
            logger.info(f"  Individual strengths: {strengths}")
            logger.info(f"  Noisy-OR result: {noisy_or_strength}")
            
            # Combine descriptions
            descriptions = [rel["description"] for rel in relationships]
            combined_description = "; ".join(set(descriptions))
            
            # Collect section_ids and paper_ids from all relationships
            section_ids = []
            paper_ids = []
            for rel in relationships:
                if "section_id" in rel:
                    section_ids.append(rel["section_id"])
                elif "section_ids" in rel:
                    section_ids.extend(rel["section_ids"])
                
                if "document_id" in rel:
                    paper_ids.append(rel["document_id"])
                elif "paper_ids" in rel:
                    paper_ids.extend(rel["paper_ids"])
            
            # Remove duplicates
            section_ids = list(set(section_ids))
            paper_ids = list(set(paper_ids))
            
            # Create merged relationship
            merged_rel = {
                "source_entity": source,
                "target_entity": target,
                "relationship_type": rel_type,
                "relationship_strength": noisy_or_strength,
                "description": combined_description,
                "document_id": state["document_id"],
                "section_ids": section_ids,
                "paper_ids": paper_ids
            }
            
            doc_relationships.append(merged_rel)
        
        state["doc_relationships"] = doc_relationships
        
        # Log combined relationships
        self._log_relationships_detailed(doc_relationships, "COMBINED RELATIONSHIPS")
        
        logger.info(f"\n✅ COMBINE RELATIONSHIPS COMPLETE: {len(doc_relationships)} unique relationships")
        return state
    
    async def _reduce_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Canonicalize entities across documents with detailed logging"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 5: REDUCE ENTITIES")
        logger.info(f"{'='*80}")
        logger.info(f"Canonicalizing {len(state['doc_entities'])} entities...")
        
        try:
            # Convert doc_entities to Entity objects for processing
            from app.models.entities import Entity
            entities = []
            for entity_data in state["doc_entities"]:
                entity = Entity(
                    entity_name=entity_data["entity_name"],
                    entity_type=entity_data["entity_type"],
                    entity_category=entity_data["entity_category"],
                    aliases=entity_data.get("aliases", []),
                    entity_description=entity_data.get("description", ""),
                    frequency=entity_data.get("frequency", 1),
                    paper_ids=entity_data.get("paper_ids", []),
                    section_ids=entity_data.get("section_ids", [])
                )
                entities.append(entity)
            
            # Process entity canonicalization
            canonicalization_results = await self.entity_canonicalizer.process_entity_canonicalization(entities)
            
            logger.info(f"Canonicalization results:")
            logger.info(f"  - Merge operations: {len(canonicalization_results.get('merge_operations', []))}")
            logger.info(f"  - Canonical entities: {len(canonicalization_results.get('canonical_entities', []))}")
            
            # Log merge operations
            if canonicalization_results.get("merge_operations"):
                logger.info(f"\n🔄 ENTITY MERGES:")
                for i, merge in enumerate(canonicalization_results["merge_operations"], 1):
                    logger.info(f"  {i}. {merge}")
            else:
                logger.info(f"\n🔄 ENTITY MERGES: None")
            
            # Update state with canonicalization results
            state["entity_merges"] = canonicalization_results.get("merge_operations", [])
            state["final_entities"] = canonicalization_results.get("canonical_entities", [])
            
            # Add any errors from canonicalization
            if canonicalization_results.get("errors"):
                state["errors"].extend(canonicalization_results["errors"])
            
            # Log final entities
            self._log_entities_detailed(state["final_entities"], "REDUCED ENTITIES")
            
            logger.info(f"\n✅ REDUCE ENTITIES COMPLETE: {len(state['final_entities'])} final entities, {len(state['entity_merges'])} merges")
            return state
            
        except Exception as e:
            error_msg = f"Error in entity reduction: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Fallback to original entities
            state["final_entities"] = state["doc_entities"]
            return state
    
    async def _reduce_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Enhanced relationship processing with contradiction detection and resolution"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 6: REDUCE RELATIONSHIPS")
        logger.info(f"{'='*80}")
        logger.info(f"Processing {len(state['doc_relationships'])} relationships for contradictions...")
        
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
            
            # Prepare context information for enhanced analysis
            context_info = {
                "document_id": state["document_id"],
                "publication_year": None,
                "paper_source": "unknown",
                "section_types": list(set([section.get("type", "unknown") for section in state.get("sections", [])]))
            }
            
            # Process enhanced contradiction detection with resolver
            contradiction_results = await self.contradiction_detector.process_contradiction_detection_with_resolver(
                relationships, 
                context_info, 
                self.contradiction_resolver
            )
            
            logger.info(f"Contradiction detection results:")
            logger.info(f"  - Contradictions found: {len(contradiction_results.get('contradictions', []))}")
            logger.info(f"  - Resolutions applied: {len(contradiction_results.get('resolutions', []))}")
            
            # Log contradictions
            if contradiction_results.get("contradictions"):
                logger.info(f"\n⚠️ CONTRADICTIONS DETECTED:")
                for i, contradiction in enumerate(contradiction_results["contradictions"], 1):
                    logger.info(f"  {i}. {contradiction}")
            else:
                logger.info(f"\n⚠️ CONTRADICTIONS: None detected")
            
            # Log resolutions
            if contradiction_results.get("resolutions"):
                logger.info(f"\n✅ CONTRADICTION RESOLUTIONS:")
                for i, resolution in enumerate(contradiction_results["resolutions"], 1):
                    logger.info(f"  {i}. {resolution}")
            else:
                logger.info(f"\n✅ CONTRADICTION RESOLUTIONS: None")
            
            # Update state with enhanced contradiction results
            state["contradictions"] = contradiction_results.get("contradictions", [])
            state["contradiction_resolutions"] = contradiction_results.get("resolutions", [])
            state["resolution_summary"] = contradiction_results.get("resolution_summary", {})
            
            # Add any errors from contradiction detection
            if contradiction_results.get("errors"):
                state["errors"].extend(contradiction_results["errors"])
            
            # Apply resolved relationships to final relationships
            final_relationships = state["doc_relationships"].copy()
            
            # Update relationships based on resolution results
            if contradiction_results.get("resolutions"):
                for resolution in contradiction_results["resolutions"]:
                    if resolution.get("resolution") == "evidence_based" or resolution.get("resolution") == "consensus_based":
                        chosen_rel = resolution.get("chosen_relationship")
                        if chosen_rel:
                            # Update the chosen relationship in final_relationships
                            for i, final_rel in enumerate(final_relationships):
                                if (final_rel["source_entity"] == chosen_rel.get("source_entity") and
                                    final_rel["target_entity"] == chosen_rel.get("target_entity") and
                                    final_rel["relationship_type"] == chosen_rel.get("relationship_type")):
                                    # Update with resolved relationship data
                                    final_relationships[i].update({
                                        "relationship_strength": chosen_rel.get("relationship_strength", final_rel["relationship_strength"]),
                                        "description": chosen_rel.get("description", final_rel["description"]),
                                        "resolution_applied": True,
                                        "resolution_confidence": resolution.get("confidence", 0.0)
                                    })
                                    break
            
            state["final_relationships"] = final_relationships
            
            # Log final relationships
            self._log_relationships_detailed(state["final_relationships"], "REDUCED RELATIONSHIPS")
            
            logger.info(f"\n✅ REDUCE RELATIONSHIPS COMPLETE: {len(state['final_relationships'])} final relationships, "
                       f"{len(state['contradictions'])} contradictions, {len(state['contradiction_resolutions'])} resolutions")
            return state
            
        except Exception as e:
            error_msg = f"Error in enhanced relationship reduction: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Fallback to original relationships
            state["final_relationships"] = state["doc_relationships"]
            return state
    
    async def _consolidate_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Consolidate relationships using enhanced consolidation strategies"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 7: CONSOLIDATE RELATIONSHIPS")
        logger.info(f"{'='*80}")
        logger.info(f"Consolidating {len(state['final_relationships'])} relationships...")
        
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
            
            logger.info(f"Consolidation results:")
            logger.info(f"  - Consolidated relationships: {len(consolidation_results.get('consolidated_relationships', []))}")
            logger.info(f"  - Summary: {consolidation_results.get('consolidation_summary', {})}")
            
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
            
            # Log final consolidated relationships
            self._log_relationships_detailed(state["final_relationships"], "CONSOLIDATED RELATIONSHIPS")
            
            logger.info(f"\n✅ CONSOLIDATE RELATIONSHIPS COMPLETE: {len(state['consolidated_relationships'])} consolidated relationships")
            return state
            
        except Exception as e:
            error_msg = f"Error in relationship consolidation: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Keep existing final_relationships
            return state
    
    async def _update_global_graph(self, state: GraphRAGState) -> GraphRAGState:
        """Update global graph with processed results from the pipeline"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 NODE 8: UPDATE GLOBAL GRAPH")
        logger.info(f"{'='*80}")
        logger.info(f"Updating global graph with {len(state['final_entities'])} entities and {len(state['final_relationships'])} relationships...")
        
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
            
            logger.info(f"Global graph processing results:")
            logger.info(f"  - Entities processed: {global_results.get('entities_processed', 0)}")
            logger.info(f"  - Relationships processed: {global_results.get('relationships_processed', 0)}")
            logger.info(f"  - New entities added: {global_results.get('new_entities_added', 0)}")
            logger.info(f"  - New relationships added: {global_results.get('new_relationships_added', 0)}")
            logger.info(f"  - Entities updated: {global_results.get('entities_updated', 0)}")
            logger.info(f"  - Relationships updated: {global_results.get('relationships_updated', 0)}")
            
            # Update state with global processing results
            state["global_processing_results"] = global_results
            
            # Add any errors from global processing
            if global_results.get("errors"):
                state["errors"].extend(global_results["errors"])
            
            logger.info(f"\n✅ UPDATE GLOBAL GRAPH COMPLETE")
            
            return state
            
        except Exception as e:
            error_msg = f"Error updating global graph: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    async def process_document(self, document_id: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a document through the enhanced GraphRAG pipeline with detailed logging
        
        Args:
            document_id: Document ID
            sections: List of sections to process
            
        Returns:
            Processing results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 STARTING ENHANCED GRAPHRAG PIPELINE")
        logger.info(f"{'='*80}")
        logger.info(f"Document ID: {document_id}")
        logger.info(f"Sections to process: {len(sections)}")
        
        # Load global graph state
        try:
            global_state = await self.global_graph_manager.load_global_graph_state()
            if global_state.get("error"):
                logger.warning(f"Failed to load global graph state: {global_state['error']}")
                global_entities = []
                global_relationships = []
            else:
                global_entities = global_state["global_entities"]
                global_relationships = global_state["global_relationships"]
                logger.info(f"Loaded global graph state: {len(global_entities)} entities, {len(global_relationships)} relationships")
        except Exception as e:
            logger.error(f"Error loading global graph state: {str(e)}")
            global_entities = []
            global_relationships = []
        
        # Initialize state with global graph data
        initial_state = GraphRAGState(
            document_id=document_id,
            sections=sections,
            temp_entities=[],
            temp_relationships=[],
            doc_entities=[],
            doc_relationships=[],
            final_entities=[],
            final_relationships=[],
            # GLOBAL GRAPH INTEGRATION:
            global_entities=global_entities,
            global_relationships=global_relationships,
            entity_merges=[],
            contradictions=[],
            contradiction_resolutions=[],
            resolution_summary={},
            consolidated_relationships=[],
            consolidation_summary={},
            global_processing_results={},
            errors=[]
        )
        
        # Run the pipeline
        try:
            result = await self.graph.ainvoke(initial_state)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info(f"{'='*80}")
            
            return {
                "success": True,
                "document_id": document_id,
                "entities_extracted": len(result["temp_entities"]),
                "relationships_extracted": len(result["temp_relationships"]),
                "final_entities": result["final_entities"],
                "final_relationships": result["final_relationships"],
                "entity_merges": len(result["entity_merges"]),
                "contradictions": len(result["contradictions"]),
                "contradiction_resolutions": len(result["contradiction_resolutions"]),
                "resolution_summary": result["resolution_summary"],
                "consolidated_relationships": len(result["consolidated_relationships"]),
                "consolidation_summary": result["consolidation_summary"],
                "global_processing_results": result.get("global_processing_results", {}),
                "errors": result["errors"]
            }
            
        except Exception as e:
            logger.error(f"Error in GraphRAG pipeline: {str(e)}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
                "entities_extracted": 0,
                "relationships_extracted": 0,
                "final_entities": [],
                "final_relationships": []
            }

