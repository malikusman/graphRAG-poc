"""
LangGraph pipeline for GraphRAG Map-Combine-Reduce processing
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
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


class GraphRAGPipeline:
    """Main GraphRAG processing pipeline using LangGraph"""
    
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
        workflow.add_node("update_global_graph", self._update_global_graph)  # NEW: Global graph integration
        
        # Add edges
        workflow.set_entry_point("map_entities")
        workflow.add_edge("map_entities", "map_relationships")
        workflow.add_edge("map_relationships", "combine_entities")
        workflow.add_edge("combine_entities", "combine_relationships")
        workflow.add_edge("combine_relationships", "reduce_entities")
        workflow.add_edge("reduce_entities", "reduce_relationships")
        workflow.add_edge("reduce_relationships", "consolidate_relationships")
        workflow.add_edge("consolidate_relationships", "update_global_graph")  # NEW: Global graph update
        workflow.add_edge("update_global_graph", END)  # NEW: End after global graph update
        
        return workflow.compile()
    
    @traceable(name="map_entities", tags=["map", "entity_extraction"])
    async def _map_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Map phase: Extract entities from sections"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "map_entities",
                "document_id": state["document_id"],
                "num_sections": len(state["sections"])
            })
        
        logger.info(f"Starting entity extraction for document {state['document_id']}")
        
        temp_entities = []
        errors = []
        
        for section in state["sections"]:
            try:
                # Create entity extraction chain
                entity_chain = self.entity_prompt | self.llm | self.entity_parser
                
                # Extract entities from section
                result = await entity_chain.ainvoke({
                    "section_text": section["text"],
                    "section_title": section.get("title", "")
                })
                
                # Process extracted entities
                if "entities" in result:
                    for entity in result["entities"]:
                        entity["document_id"] = state["document_id"]
                        entity["section_id"] = str(section["_id"])
                        entity["provenance"] = entity.get("provenance", section["text"][:200])
                        temp_entities.append(entity)
                
                logger.debug(f"Extracted {len(result.get('entities', []))} entities from section {section['_id']}")
                
            except Exception as e:
                error_msg = f"Error extracting entities from section {section['_id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        state["temp_entities"] = temp_entities
        state["errors"].extend(errors)
        
        # Add output metadata
        if run:
            run.add_metadata({
                "entities_extracted": len(temp_entities),
                "errors_count": len(errors)
            })
        
        logger.info(f"Entity extraction complete: {len(temp_entities)} entities extracted")
        return state
    
    @traceable(name="map_relationships", tags=["map", "relationship_extraction"])
    async def _map_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Map phase: Extract relationships from sections"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "map_relationships",
                "document_id": state["document_id"],
                "num_sections": len(state["sections"])
            })
        
        logger.info(f"Starting relationship extraction for document {state['document_id']}")
        
        temp_relationships = []
        errors = []
        
        for section in state["sections"]:
            try:
                # Get entities from this section
                section_entities = [e for e in state["temp_entities"] if e["section_id"] == str(section["_id"])]
                
                if len(section_entities) < 2:
                    continue  # Need at least 2 entities for relationships
                
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
                
                # Process extracted relationships
                if "relationships" in result:
                    for rel in result["relationships"]:
                        rel["document_id"] = state["document_id"]
                        rel["section_id"] = str(section["_id"])
                        rel["provenance"] = rel.get("provenance", section["text"][:200])
                        temp_relationships.append(rel)
                
                logger.debug(f"Extracted {len(result.get('relationships', []))} relationships from section {section['_id']}")
                
            except Exception as e:
                error_msg = f"Error extracting relationships from section {section['_id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        state["temp_relationships"] = temp_relationships
        state["errors"].extend(errors)
        
        # Add output metadata
        if run:
            run.add_metadata({
                "relationships_extracted": len(temp_relationships),
                "errors_count": len(errors)
            })
        
        logger.info(f"Relationship extraction complete: {len(temp_relationships)} relationships extracted")
        return state
    
    @traceable(name="combine_entities", tags=["combine", "entity_processing"])
    async def _combine_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Combine phase: Merge entities within document"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "combine_entities",
                "document_id": state["document_id"],
                "temp_entities_count": len(state["temp_entities"])
            })
        
        logger.info(f"Starting entity combination for document {state['document_id']}")
        
        # Group entities by name and type
        entity_groups = {}
        for entity in state["temp_entities"]:
            key = (entity["entity_name"], entity["entity_type"])
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)
        
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
        
        # Add output metadata
        if run:
            run.add_metadata({
                "unique_entities": len(doc_entities),
                "reduction_ratio": len(doc_entities) / max(len(state["temp_entities"]), 1)
            })
        
        logger.info(f"Entity combination complete: {len(doc_entities)} unique entities")
        return state
    
    @traceable(name="combine_relationships", tags=["combine", "relationship_processing"])
    async def _combine_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Combine phase: Merge relationships within document"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "combine_relationships",
                "document_id": state["document_id"],
                "temp_relationships_count": len(state["temp_relationships"])
            })
        
        logger.info(f"Starting relationship combination for document {state['document_id']}")
        
        # Group relationships by source, target, and type
        rel_groups = {}
        for rel in state["temp_relationships"]:
            key = (rel["source_entity"], rel["target_entity"], rel["relationship_type"])
            if key not in rel_groups:
                rel_groups[key] = []
            rel_groups[key].append(rel)
        
        # Merge relationships using noisy-OR
        doc_relationships = []
        for (source, target, rel_type), relationships in rel_groups.items():
            # Calculate noisy-OR strength using proper formula
            strengths = [rel["relationship_strength"] for rel in relationships]
            noisy_or_strength = calculate_noisy_or_strength(strengths)
            
            # Combine descriptions
            descriptions = [rel["description"] for rel in relationships]
            combined_description = "; ".join(set(descriptions))
            
            # Collect section_ids and paper_ids from all relationships
            # Note: extracted relationships have "section_id" (singular) and "document_id"
            section_ids = []
            paper_ids = []
            for rel in relationships:
                # Handle both singular and plural forms
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
        
        # Add output metadata
        if run:
            run.add_metadata({
                "unique_relationships": len(doc_relationships),
                "reduction_ratio": len(doc_relationships) / max(len(state["temp_relationships"]), 1)
            })
        
        logger.info(f"Relationship combination complete: {len(doc_relationships)} unique relationships")
        return state
    
    @traceable(name="reduce_entities", tags=["reduce", "canonicalization"])
    async def _reduce_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Canonicalize entities across documents"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "reduce_entities",
                "document_id": state["document_id"],
                "entities_before": len(state["doc_entities"]),
                "canonicalization_strategy": "fuzzy_matching"
            })
        
        logger.info(f"Starting entity reduction for document {state['document_id']}")
        
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
            
            # Update state with canonicalization results
            state["entity_merges"] = canonicalization_results.get("merge_operations", [])
            state["final_entities"] = canonicalization_results.get("canonical_entities", [])
            
            # Add any errors from canonicalization
            if canonicalization_results.get("errors"):
                state["errors"].extend(canonicalization_results["errors"])
            
            # Add output metadata
            if run:
                run.add_metadata({
                    "entities_after": len(state["final_entities"]),
                    "reduction_ratio": len(state["final_entities"]) / max(len(state["doc_entities"]), 1),
                    "merges_performed": len(state["entity_merges"])
                })
            
            logger.info(f"Entity reduction complete: {len(state['final_entities'])} final entities, {len(state['entity_merges'])} merges")
            return state
            
        except Exception as e:
            error_msg = f"Error in entity reduction: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Fallback to original entities
            state["final_entities"] = state["doc_entities"]
            return state
    
    @traceable(name="reduce_relationships", tags=["reduce", "relationship_deduplication"])
    async def _reduce_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Enhanced relationship processing with contradiction detection and resolution"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "reduce_relationships",
                "document_id": state["document_id"],
                "relationships_before": len(state["doc_relationships"])
            })
        logger.info(f"Starting enhanced relationship reduction for document {state['document_id']}")
        
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
                "publication_year": None,  # Could be extracted from document metadata
                "paper_source": "unknown",  # Could be extracted from document metadata
                "section_types": list(set([section.get("type", "unknown") for section in state.get("sections", [])]))
            }
            
            # Process enhanced contradiction detection with resolver
            contradiction_results = await self.contradiction_detector.process_contradiction_detection_with_resolver(
                relationships, 
                context_info, 
                self.contradiction_resolver
            )
            
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
            
            # Add output metadata
            if run:
                run.add_metadata({
                    "relationships_after": len(state["final_relationships"]),
                    "contradictions_found": len(state["contradictions"]),
                    "resolutions_applied": len(state["contradiction_resolutions"])
                })
            
            logger.info(f"Enhanced relationship reduction complete: {len(state['final_relationships'])} final relationships, "
                       f"{len(state['contradictions'])} contradictions, {len(state['contradiction_resolutions'])} resolutions")
            return state
            
        except Exception as e:
            error_msg = f"Error in enhanced relationship reduction: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Fallback to original relationships
            state["final_relationships"] = state["doc_relationships"]
            return state
    
    @traceable(name="consolidate_relationships", tags=["consolidate", "noisy_or"])
    async def _consolidate_relationships(self, state: GraphRAGState) -> GraphRAGState:
        """Consolidate relationships using enhanced consolidation strategies"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "consolidate_relationships",
                "document_id": state["document_id"],
                "relationships_before": len(state["final_relationships"])
            })
        
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
            
            # Add output metadata
            if run:
                run.add_metadata({
                    "consolidated_relationships": len(state["consolidated_relationships"]),
                    "consolidation_summary": state["consolidation_summary"]
                })
            
            logger.info(f"Relationship consolidation complete: {len(state['consolidated_relationships'])} consolidated relationships, "
                       f"{state['consolidation_summary']}")
            return state
            
        except Exception as e:
            error_msg = f"Error in relationship consolidation: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            # Keep existing final_relationships
            return state
    
    @traceable(name="update_global_graph", tags=["global", "graph_integration"])
    async def _update_global_graph(self, state: GraphRAGState) -> GraphRAGState:
        """Update global graph with processed results from the pipeline"""
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "node": "update_global_graph",
                "document_id": state["document_id"],
                "entities_to_add": len(state["final_entities"]),
                "relationships_to_add": len(state["final_relationships"])
            })
        
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
            
            # Add output metadata
            if run:
                run.add_metadata({
                    "entities_processed": global_results.get('entities_processed', 0),
                    "relationships_processed": global_results.get('relationships_processed', 0),
                    "global_processing_results": global_results
                })
            
            logger.info(f"Global graph update complete for document {state['document_id']}: "
                       f"{global_results.get('entities_processed', 0)} entities, "
                       f"{global_results.get('relationships_processed', 0)} relationships processed")
            
            return state
            
        except Exception as e:
            error_msg = f"Error updating global graph: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            return state
    
    @traceable(
        name="graphrag_pipeline_process_document",
        tags=["pipeline", "document_processing"],
        metadata={"version": "1.0"}
    )
    async def process_document(self, document_id: str, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a document through the GraphRAG pipeline with global graph integration
        
        Args:
            document_id: Document ID
            sections: List of sections to process
            
        Returns:
            Processing results
        """
        # Add metadata to run
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "document_id": document_id,
                "num_sections": len(sections),
                "pipeline_stage": "initialization"
            })
        
        logger.info(f"Starting document processing with global graph integration: {document_id}")
        
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
