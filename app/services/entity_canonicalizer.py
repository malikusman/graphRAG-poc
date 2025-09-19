import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

from app.core.config import settings
from app.configs.schemas import load_prompt
from app.database.models import EntityCollection
from app.models.entities import Entity, EntityResponse

logger = logging.getLogger(__name__)


class EntityCanonicalizer:
    """Service for canonicalizing entities across documents"""
    
    def __init__(self):
        """Initialize the canonicalizer with LLM and prompts"""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Load canonicalization prompt
        self.prompt_config = load_prompt("entity_canonicalization", "reduce")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        self.parser = JsonOutputParser()
    
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
    
    async def calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity between two entities using LLM"""
        try:
            # Prepare entities for comparison
            entities_list = [
                {
                    "entity_name": entity1.entity_name,
                    "entity_type": entity1.entity_type,
                    "entity_category": entity1.entity_category,
                    "aliases": entity1.aliases,
                    "description": entity1.entity_description
                },
                {
                    "entity_name": entity2.entity_name,
                    "entity_type": entity2.entity_type,
                    "entity_category": entity2.entity_category,
                    "aliases": entity2.aliases,
                    "description": entity2.entity_description
                }
            ]
            
            # Use LLM to analyze similarity
            entity_chain = self.prompt | self.llm | self.parser
            result = await entity_chain.ainvoke({
                "entities_list": json.dumps(entities_list, indent=2)
            })
            
            if "analysis" in result:
                return result["analysis"].get("confidence", 0.0)
            else:
                logger.warning(f"No analysis in LLM result: {result}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating entity similarity: {str(e)}")
            return 0.0
    
    async def merge_entities(self, entities: List[Entity]) -> Optional[Entity]:
        """Merge multiple entities into a canonical entity"""
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
                    "description": entity.entity_description
                })
            
            # Use LLM to determine canonical entity
            entity_chain = self.prompt | self.llm | self.parser
            result = await entity_chain.ainvoke({
                "entities_list": json.dumps(entities_list, indent=2)
            })
            
            if "canonical_entity" in result and result["analysis"]["should_merge"]:
                canonical_data = result["canonical_entity"]
                logger.info(f"Canonical data received: {canonical_data}")
                
                # Create canonical entity
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
    
    async def process_entity_canonicalization(self, new_entities: List[Entity]) -> Dict[str, Any]:
        """Process canonicalization for a list of new entities"""
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
                    # Calculate similarity with each similar entity
                    best_match = None
                    best_similarity = 0.0
                    
                    for similar_entity in similar_entities:
                        similarity = await self.calculate_entity_similarity(entity, similar_entity)
                        if similarity > best_similarity and similarity > 0.8:
                            best_similarity = similarity
                            best_match = similar_entity
                    
                    if best_match:
                        # Merge entities
                        entities_to_merge = [entity, best_match]
                        canonical_entity = await self.merge_entities(entities_to_merge)
                        
                        if canonical_entity:
                            canonicalization_results["canonical_entities"].append(canonical_entity.model_dump())
                            canonicalization_results["merges_performed"] += 1
                            canonicalization_results["merge_operations"].append({
                                "source_entity": entity.entity_name,
                                "target_entity": canonical_entity.entity_name,
                                "similarity": best_similarity
                            })
                            
                            # Mark both entities as processed
                            processed_entity_ids.add(entity.entity_name)
                            processed_entity_ids.add(best_match.entity_name)
                        else:
                            canonicalization_results["canonical_entities"].append(entity.model_dump())
                    else:
                        canonicalization_results["canonical_entities"].append(entity.model_dump())
                else:
                    canonicalization_results["canonical_entities"].append(entity.model_dump())
                
                processed_entity_ids.add(entity.entity_name)
            
            logger.info(f"Canonicalization complete: {canonicalization_results['merges_performed']} merges performed")
            return canonicalization_results
            
        except Exception as e:
            logger.error(f"Error in entity canonicalization: {str(e)}")
            return {
                "entities_processed": 0,
                "merges_performed": 0,
                "canonical_entities": [],
                "merge_operations": [],
                "errors": [str(e)]
            }
