import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json

from app.core.config import settings
from app.configs.schemas import load_prompt
from app.database.models import RelationshipCollection
from app.models.relationships import Relationship, RelationshipResponse

logger = logging.getLogger(__name__)


class ContradictionDetector:
    """Service for detecting contradictions in relationships"""
    
    def __init__(self):
        """Initialize the contradiction detector with LLM and prompts"""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Load contradiction detection prompt
        self.prompt_config = load_prompt("contradiction_detection", "reduce")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        self.parser = JsonOutputParser()
    
    async def detect_relationship_contradictions(self, relationships: List[Relationship]) -> List[Dict[str, Any]]:
        """Detect contradictions in relationships using LLM"""
        try:
            if len(relationships) < 2:
                return []
            
            # Group relationships by entity pairs
            entity_pairs = {}
            for rel in relationships:
                key = tuple(sorted([rel.source_entity, rel.target_entity]))
                if key not in entity_pairs:
                    entity_pairs[key] = []
                entity_pairs[key].append(rel)
            
            contradictions = []
            
            # Analyze each entity pair for contradictions
            for entity_pair, pair_relationships in entity_pairs.items():
                if len(pair_relationships) < 2:
                    continue
                
                # Prepare relationships for LLM analysis
                relationships_list = []
                for rel in pair_relationships:
                    relationships_list.append({
                        "relationship_id": str(rel.id) if hasattr(rel, 'id') else "unknown",
                        "source_entity": rel.source_entity,
                        "target_entity": rel.target_entity,
                        "relationship_type": rel.relationship_type,
                        "description": rel.description,
                        "relationship_strength": rel.relationship_strength,
                        "paper_ids": rel.paper_ids
                    })
                
                # Use LLM to detect contradictions
                relationship_chain = self.prompt | self.llm | self.parser
                result = await relationship_chain.ainvoke({
                    "relationships_list": json.dumps(relationships_list, indent=2)
                })
                
                if "contradictions" in result and result["contradictions_found"]:
                    for contradiction in result["contradictions"]:
                        contradiction["entity_pair"] = entity_pair
                        contradictions.append(contradiction)
            
            logger.info(f"Detected {len(contradictions)} contradictions")
            return contradictions
            
        except Exception as e:
            logger.error(f"Error detecting relationship contradictions: {str(e)}")
            return []
    
    async def analyze_evidence_strength(self, relationship: Relationship) -> float:
        """Analyze the strength of evidence for a relationship"""
        try:
            # Calculate evidence strength based on multiple factors
            evidence_strength = 0.0
            
            # Factor 1: Relationship strength (0.0 - 1.0)
            evidence_strength += relationship.relationship_strength * 0.4
            
            # Factor 2: Number of supporting papers (normalized)
            paper_count = len(relationship.paper_ids)
            paper_strength = min(paper_count / 5.0, 1.0)  # Normalize to max 5 papers
            evidence_strength += paper_strength * 0.3
            
            # Factor 3: Number of supporting sections (normalized)
            section_count = len(relationship.section_ids)
            section_strength = min(section_count / 10.0, 1.0)  # Normalize to max 10 sections
            evidence_strength += section_strength * 0.2
            
            # Factor 4: Description quality (length and detail)
            description_length = len(relationship.description)
            description_strength = min(description_length / 200.0, 1.0)  # Normalize to max 200 chars
            evidence_strength += description_strength * 0.1
            
            # Ensure strength is between 0.0 and 1.0
            evidence_strength = max(0.0, min(1.0, evidence_strength))
            
            return evidence_strength
            
        except Exception as e:
            logger.error(f"Error analyzing evidence strength: {str(e)}")
            return 0.0
    
    async def resolve_contradictions(self, contradictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve contradictions by choosing the relationship with stronger evidence"""
        try:
            resolutions = []
            
            for contradiction in contradictions:
                resolution = {
                    "contradiction_id": contradiction.get("contradiction_id", "unknown"),
                    "entity_pair": contradiction.get("entity_pair", []),
                    "resolution_type": "evidence_based",
                    "resolved_relationship": None,
                    "rejected_relationships": [],
                    "resolution_reason": ""
                }
                
                # Get the contradicting relationships
                contradicting_relationships = contradiction.get("contradicting_relationships", [])
                
                if len(contradicting_relationships) >= 2:
                    # Analyze evidence strength for each relationship
                    relationship_strengths = []
                    for rel_data in contradicting_relationships:
                        # Create a Relationship object for analysis
                        rel = Relationship(
                            source_entity=rel_data["source_entity"],
                            target_entity=rel_data["target_entity"],
                            relationship_type=rel_data["relationship_type"],
                            relationship_strength=rel_data["evidence_strength"],
                            description=rel_data["description"],
                            paper_ids=rel_data["paper_ids"],
                            section_ids=[]  # Not available in contradiction data
                        )
                        
                        evidence_strength = await self.analyze_evidence_strength(rel)
                        relationship_strengths.append({
                            "relationship": rel_data,
                            "evidence_strength": evidence_strength
                        })
                    
                    # Sort by evidence strength (descending)
                    relationship_strengths.sort(key=lambda x: x["evidence_strength"], reverse=True)
                    
                    # Choose the relationship with strongest evidence
                    strongest = relationship_strengths[0]
                    rejected = relationship_strengths[1:]
                    
                    resolution["resolved_relationship"] = strongest["relationship"]
                    resolution["rejected_relationships"] = [r["relationship"] for r in rejected]
                    resolution["resolution_reason"] = f"Chosen based on evidence strength: {strongest['evidence_strength']:.2f}"
                    
                    # If evidence strengths are very close, mark as unresolved
                    if len(relationship_strengths) > 1:
                        strength_diff = strongest["evidence_strength"] - relationship_strengths[1]["evidence_strength"]
                        if strength_diff < 0.1:  # Less than 10% difference
                            resolution["resolution_type"] = "unresolved"
                            resolution["resolution_reason"] = "Evidence strengths too close to resolve automatically"
                
                resolutions.append(resolution)
            
            logger.info(f"Resolved {len(resolutions)} contradictions")
            return resolutions
            
        except Exception as e:
            logger.error(f"Error resolving contradictions: {str(e)}")
            return []
    
    async def process_contradiction_detection(self, new_relationships: List[Relationship]) -> Dict[str, Any]:
        """Process contradiction detection for a list of new relationships"""
        try:
            detection_results = {
                "relationships_analyzed": len(new_relationships),
                "contradictions_found": 0,
                "contradictions": [],
                "resolutions": [],
                "errors": []
            }
            
            # Detect contradictions
            contradictions = await self.detect_relationship_contradictions(new_relationships)
            detection_results["contradictions"] = contradictions
            detection_results["contradictions_found"] = len(contradictions)
            
            # Resolve contradictions
            if contradictions:
                resolutions = await self.resolve_contradictions(contradictions)
                detection_results["resolutions"] = resolutions
            
            logger.info(f"Contradiction detection complete: {len(contradictions)} contradictions found")
            return detection_results
            
        except Exception as e:
            logger.error(f"Error in contradiction detection: {str(e)}")
            return {
                "relationships_analyzed": 0,
                "contradictions_found": 0,
                "contradictions": [],
                "resolutions": [],
                "errors": [str(e)]
            }
