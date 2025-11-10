import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import re

from app.core.config import settings
from app.core.llm_provider import get_llm
from app.configs.schemas import load_prompt
from app.database.models import EntityCollection
from app.models.entities import Entity, EntityResponse

logger = logging.getLogger(__name__)


class EntityCanonicalizer:
    """Enhanced service for canonicalizing entities across documents with stable identifier support"""
    
    def __init__(self):
        """Initialize the canonicalizer with LLM and prompts"""
        # Use LLM provider abstraction to support both OpenAI and Bedrock
        self.llm = get_llm(temperature=0.1)
        
        # Load enhanced canonicalization prompt
        self.prompt_config = load_prompt("entity_canonicalization", "reduce")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        self.parser = JsonOutputParser()
        
        # Stable identifier patterns
        self.stable_id_patterns = {
            "MeSH": r"MESH:D\d{9}",
            "HGNC": r"HGNC:\d+",
            "UniProt": r"UNIPROT:[A-Z0-9]+",
            "GO": r"GO:\d{7}",
            "ChEBI": r"CHEBI:\d+",
            "KEGG": r"KEGG:[A-Z0-9]+"
        }
    
    def extract_stable_identifiers(self, text: str) -> List[str]:
        """Extract stable identifiers from text using regex patterns"""
        identifiers = []
        for id_type, pattern in self.stable_id_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            identifiers.extend(matches)
        return identifiers
    
    def find_stable_identifiers_in_entity(self, entity: Entity) -> List[str]:
        """Find stable identifiers in entity description and aliases"""
        identifiers = []
        
        # Check description
        if entity.entity_description:
            identifiers.extend(self.extract_stable_identifiers(entity.entity_description))
        
        # Check aliases
        for alias in entity.aliases:
            identifiers.extend(self.extract_stable_identifiers(alias))
        
        # Check entity name
        identifiers.extend(self.extract_stable_identifiers(entity.entity_name))
        
        return list(set(identifiers))  # Remove duplicates
    
    async def find_similar_entities(self, entity: Entity) -> List[EntityResponse]:
        """Find entities similar to the given entity"""
        try:
            # Use database method to find similar entities
            similar_entities = await EntityCollection.find_similar_entities_by_name(
                entity.entity_name, 
                threshold=0.8
            )
            
            # Filter by entity type and category for better matches
            filtered_entities = []
            for similar_entity in similar_entities:
                if (similar_entity.entity_type == entity.entity_type and 
                    similar_entity.entity_category == entity.entity_category):
                    filtered_entities.append(similar_entity)
            
            logger.info(f"Found {len(filtered_entities)} similar entities for {entity.entity_name}")
            return filtered_entities
            
        except Exception as e:
            logger.error(f"Error finding similar entities: {str(e)}")
            return []
    
    async def calculate_entity_similarity_with_context(
        self, 
        entity: Entity, 
        existing_entities: List[Entity] = None
    ) -> Dict[str, Any]:
        """
        Calculate similarity between entities using enhanced LLM analysis
        
        Args:
            entity: The primary entity to analyze
            existing_entities: List of entities to compare against (typically similar entities found in database)
            
        Returns:
            Dict containing similarity analysis results with confidence scores and reasoning
        """
        try:
            # Validation: Ensure we have entities to compare against
            if not existing_entities:
                logger.warning(f"No existing entities provided for comparison with {entity.entity_name}")
                return {
                    "analysis": {
                        "should_merge": False,
                        "confidence": 0.0,
                        "reasoning": "No entities provided for comparison",
                        "evidence_types": [],
                        "stable_identifiers_found": []
                    },
                    "canonical_entity": None,
                    "merge_operations": []
                }
            
            # Prepare entities for comparison
            entities_list = [{
                "entity_name": entity.entity_name,
                "entity_type": entity.entity_type,
                "entity_category": entity.entity_category,
                "aliases": entity.aliases,
                "description": entity.entity_description,
                "stable_identifiers": self.find_stable_identifiers_in_entity(entity)
            }]
            
            # Add existing entities for context
            existing_entities_list = []
            if existing_entities:
                for existing_entity in existing_entities:
                    existing_entities_list.append({
                        "entity_name": existing_entity.entity_name,
                        "entity_type": existing_entity.entity_type,
                        "entity_category": existing_entity.entity_category,
                        "aliases": existing_entity.aliases,
                        "description": existing_entity.entity_description,
                        "stable_identifiers": self.find_stable_identifiers_in_entity(existing_entity)
                    })
            
            # Use enhanced LLM to analyze similarity
            entity_chain = self.prompt | self.llm | self.parser
            result = await entity_chain.ainvoke({
                "entities_list": json.dumps(entities_list, indent=2),
                "existing_entities_list": json.dumps(existing_entities_list, indent=2)
            })
            
            if "analysis" in result:
                return result
            else:
                logger.warning(f"No analysis in LLM result: {result}")
                return {
                    "analysis": {
                        "should_merge": False,
                        "confidence": 0.0,
                        "reasoning": "No analysis available",
                        "evidence_types": [],
                        "stable_identifiers_found": []
                    },
                    "canonical_entity": None,
                    "merge_operations": []
                }
                
        except Exception as e:
            logger.error(f"Error calculating entity similarity: {str(e)}")
            return {
                "analysis": {
                    "should_merge": False,
                    "confidence": 0.0,
                    "reasoning": f"Error in analysis: {str(e)}",
                    "evidence_types": [],
                    "stable_identifiers_found": []
                },
                "canonical_entity": None,
                "merge_operations": []
            }
    
    # Backward compatibility method
    async def calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity between two entities using LLM (backward compatibility)"""
        try:
            result = await self.calculate_entity_similarity_with_context(entity1, [entity2])
            return result["analysis"].get("confidence", 0.0)
        except Exception as e:
            logger.error(f"Error calculating entity similarity: {str(e)}")
            return 0.0
    
    async def merge_entities_with_enhanced_analysis(
        self, 
        entities: List[Entity], 
        existing_entities: List[Entity] = None
    ) -> Optional[Entity]:
        """Merge multiple entities into a canonical entity using enhanced analysis"""
        try:
            if len(entities) < 2:
                return entities[0] if entities else None
            
            # Prepare entities for LLM analysis
            entities_list = []
            for entity in entities:
                entities_list.append({
                    "entity_name": entity.entity_name,
                    "entity_type": entity.entity_type,
                    "entity_category": entity.entity_category,
                    "aliases": entity.aliases,
                    "description": entity.entity_description,
                    "stable_identifiers": self.find_stable_identifiers_in_entity(entity)
                })
            
            # Add existing entities for context
            existing_entities_list = []
            if existing_entities:
                for existing_entity in existing_entities:
                    existing_entities_list.append({
                        "entity_name": existing_entity.entity_name,
                        "entity_type": existing_entity.entity_type,
                        "entity_category": existing_entity.entity_category,
                        "aliases": existing_entity.aliases,
                        "description": existing_entity.entity_description,
                        "stable_identifiers": self.find_stable_identifiers_in_entity(existing_entity)
                    })
            
            # Use enhanced LLM to determine canonical entity
            entity_chain = self.prompt | self.llm | self.parser
            result = await entity_chain.ainvoke({
                "entities_list": json.dumps(entities_list, indent=2),
                "existing_entities_list": json.dumps(existing_entities_list, indent=2)
            })
            
            if "canonical_entity" in result and result["analysis"]["should_merge"]:
                canonical_data = result["canonical_entity"]
                logger.info(f"Canonical data received: {canonical_data}")
                
                # Create canonical entity with enhanced fields
                canonical_entity = Entity(
                    entity_name=canonical_data["entity_name"],
                    entity_type=canonical_data["entity_type"],
                    entity_category=canonical_data["entity_category"],
                    aliases=canonical_data["aliases"],
                    entity_description=canonical_data.get("description"),
                    frequency=sum(entity.frequency for entity in entities),
                    paper_ids=list(set([pid for entity in entities for pid in entity.paper_ids])),
                    section_ids=list(set([sid for entity in entities for sid in entity.section_ids]))
                )
                
                logger.info(f"Created canonical entity: {canonical_entity.entity_name}")
                return canonical_entity
            else:
                logger.info("LLM determined entities should not be merged")
                return None
                
        except Exception as e:
            logger.error(f"Error merging entities: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    # Backward compatibility method
    async def merge_entities(self, entities: List[Entity]) -> Optional[Entity]:
        """Merge multiple entities into a canonical entity (backward compatibility)"""
        return await self.merge_entities_with_enhanced_analysis(entities, None)
    
    async def canonicalize_entity_name(self, entity_name: str) -> str:
        """Canonicalize entity name using standard rules"""
        try:
            # Basic canonicalization rules
            canonical_name = entity_name.strip()
            
            # Handle common scientific naming conventions
            if canonical_name.lower().startswith("the "):
                canonical_name = canonical_name[4:]
            
            # Handle common abbreviations
            abbreviations = {
                "crispr": "CRISPR",
                "cas9": "Cas9",
                "tp53": "TP53",
                "p53": "TP53",
                "covid-19": "COVID-19",
                "sars-cov-2": "SARS-CoV-2"
            }
            
            for abbr, canonical in abbreviations.items():
                if canonical_name.lower() == abbr:
                    canonical_name = canonical
                    break
            
            return canonical_name
            
        except Exception as e:
            logger.error(f"Error canonicalizing entity name: {str(e)}")
            return entity_name
    
    async def process_entity_canonicalization_with_context(
        self, 
        new_entities: List[Entity], 
        existing_entities: List[Entity] = None
    ) -> Dict[str, Any]:
        """Process canonicalization for a list of new entities with context from existing entities"""
        try:
            canonicalization_results = {
                "entities_processed": len(new_entities),
                "merges_performed": 0,
                "canonical_entities": [],
                "merge_operations": [],
                "errors": []
            }
            
            processed_entity_ids = set()
            
            for entity in new_entities:
                if entity.entity_name in processed_entity_ids:
                    continue
                
                # Find similar entities
                similar_entities = await self.find_similar_entities(entity)
                
                if similar_entities:
                    # Calculate similarity with each similar entity using enhanced analysis
                    best_match = None
                    best_similarity = 0.0
                    best_analysis = None
                    
                    for similar_entity in similar_entities:
                        analysis_result = await self.calculate_entity_similarity_with_context(
                            entity, 
                            [similar_entity]  # Pass the specific similar entity to compare with
                        )
                        
                        if "analysis" in analysis_result:
                            confidence = analysis_result["analysis"].get("confidence", 0.0)
                            logger.info(f"Similarity analysis for {entity.entity_name} vs {similar_entity.entity_name}: confidence={confidence}, best_similarity={best_similarity}")
                            if confidence > best_similarity and confidence > 0.8:
                                best_similarity = confidence
                                best_match = similar_entity
                                best_analysis = analysis_result
                                logger.info(f"New best match: {best_match.entity_name} with confidence {best_similarity}")
                        else:
                            logger.warning(f"No analysis in result for {entity.entity_name} vs {similar_entity.entity_name}")
                    
                    logger.info(f"Final check for {entity.entity_name}: best_match={best_match.entity_name if best_match else None}, best_analysis={'Present' if best_analysis else None}, best_similarity={best_similarity}")
                    
                    if best_match and best_analysis:
                        logger.info(f"Attempting merge for {entity.entity_name} with {best_match.entity_name}")
                        # Merge entities using enhanced analysis
                        entities_to_merge = [entity, best_match]
                        canonical_entity = await self.merge_entities_with_enhanced_analysis(
                            entities_to_merge, 
                            existing_entities
                        )
                        
                        if canonical_entity:
                            logger.info(f"Merge successful for {entity.entity_name} -> {canonical_entity.entity_name}")
                            canonicalization_results["canonical_entities"].append(canonical_entity.model_dump())
                            canonicalization_results["merges_performed"] += 1
                            
                            # Enhanced merge operation with evidence
                            merge_operation = {
                                "source_entity": entity.entity_name,
                                "target_entity": canonical_entity.entity_name,
                                "similarity": best_similarity,
                                "confidence": best_analysis["analysis"].get("confidence", 0.0),
                                "reasoning": best_analysis["analysis"].get("reasoning", ""),
                                "evidence_types": best_analysis["analysis"].get("evidence_types", []),
                                "stable_identifiers_found": best_analysis["analysis"].get("stable_identifiers_found", [])
                            }
                            canonicalization_results["merge_operations"].append(merge_operation)
                            
                            # Mark both entities as processed
                            processed_entity_ids.add(entity.entity_name)
                            processed_entity_ids.add(best_match.entity_name)
                        else:
                            logger.warning(f"Merge failed for {entity.entity_name} - canonical_entity is None")
                            canonicalization_results["canonical_entities"].append(entity.model_dump())
                    else:
                        logger.info(f"No merge for {entity.entity_name} - best_match or best_analysis is None")
                        canonicalization_results["canonical_entities"].append(entity.model_dump())
                else:
                    canonicalization_results["canonical_entities"].append(entity.model_dump())
                
                processed_entity_ids.add(entity.entity_name)
            
            logger.info(f"Enhanced canonicalization complete: {canonicalization_results['merges_performed']} merges performed")
            return canonicalization_results
            
        except Exception as e:
            logger.error(f"Error in enhanced entity canonicalization: {str(e)}")
            return {
                "entities_processed": 0,
                "merges_performed": 0,
                "canonical_entities": [],
                "merge_operations": [],
                "errors": [str(e)]
            }
    
    # Backward compatibility method
    async def process_entity_canonicalization(self, new_entities: List[Entity]) -> Dict[str, Any]:
        """Process canonicalization for a list of new entities (backward compatibility)"""
        return await self.process_entity_canonicalization_with_context(new_entities, None)
