"""
ContradictionResolver service for resolving detected contradictions in relationships
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from datetime import datetime

from app.core.config import settings
from app.configs.schemas import load_prompt
from app.models.relationships import Relationship

logger = logging.getLogger(__name__)


class ContradictionResolver:
    """Service for resolving contradictions in relationships using evidence-based strategies"""
    
    def __init__(self):
        """Initialize the resolver with LLM and prompts"""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Load contradiction resolution prompt
        self.prompt_config = load_prompt("contradiction_resolution", "reduce")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        self.parser = JsonOutputParser()
    
    def evaluate_evidence_strength(self, relationship: Dict[str, Any]) -> float:
        """Evaluate the evidence strength of a relationship"""
        try:
            strength = 0.0
            
            # Base strength from relationship strength
            base_strength = relationship.get("relationship_strength", 0.0)
            strength += base_strength * 0.4
            
            # Evidence from description quality
            description = relationship.get("description", "")
            if len(description) > 100:  # Detailed description
                strength += 0.2
            elif len(description) > 50:  # Moderate description
                strength += 0.1
            
            # Evidence from frequency (how many times this relationship appears)
            frequency = relationship.get("frequency", 1)
            if frequency > 5:
                strength += 0.2
            elif frequency > 2:
                strength += 0.1
            
            # Evidence from paper count
            paper_ids = relationship.get("paper_ids", [])
            if len(paper_ids) > 3:
                strength += 0.1
            elif len(paper_ids) > 1:
                strength += 0.05
            
            # Evidence from section count
            section_ids = relationship.get("section_ids", [])
            if len(section_ids) > 5:
                strength += 0.1
            elif len(section_ids) > 2:
                strength += 0.05
            
            return min(strength, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error evaluating evidence strength: {str(e)}")
            return 0.0
    
    def determine_resolution_strategy(self, contradiction: Dict[str, Any]) -> str:
        """Determine the best resolution strategy for a contradiction"""
        try:
            relationships = contradiction.get("relationships", [])
            if len(relationships) < 2:
                return "insufficient_data"
            
            # Evaluate evidence strength for each relationship
            evidence_scores = []
            for rel in relationships:
                score = self.evaluate_evidence_strength(rel)
                evidence_scores.append(score)
            
            # Check for clear evidence winner
            max_score = max(evidence_scores)
            min_score = min(evidence_scores)
            
            if max_score - min_score > 0.3:  # Clear winner
                return "evidence_based"
            elif max_score - min_score > 0.1:  # Moderate difference
                return "consensus_based"
            else:  # Close scores
                return "context_dependent"
                
        except Exception as e:
            logger.error(f"Error determining resolution strategy: {str(e)}")
            return "manual_review"
    
    def resolve_evidence_based(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve contradiction based on evidence strength"""
        try:
            relationships = contradiction.get("relationships", [])
            if len(relationships) < 2:
                return {"resolution": "insufficient_data", "confidence": 0.0}
            
            # Evaluate evidence strength for each relationship
            best_relationship = None
            best_score = 0.0
            
            for rel in relationships:
                score = self.evaluate_evidence_strength(rel)
                if score > best_score:
                    best_score = score
                    best_relationship = rel
            
            if best_relationship:
                return {
                    "resolution": "evidence_based",
                    "chosen_relationship": best_relationship,
                    "confidence": best_score,
                    "reasoning": f"Chosen based on highest evidence strength ({best_score:.2f})",
                    "rejected_relationships": [r for r in relationships if r != best_relationship]
                }
            else:
                return {"resolution": "insufficient_data", "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error in evidence-based resolution: {str(e)}")
            return {"resolution": "error", "confidence": 0.0}
    
    def resolve_consensus_based(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve contradiction based on consensus and frequency"""
        try:
            relationships = contradiction.get("relationships", [])
            if len(relationships) < 2:
                return {"resolution": "insufficient_data", "confidence": 0.0}
            
            # Group relationships by type and direction
            relationship_groups = {}
            for rel in relationships:
                key = (rel.get("source_entity"), rel.get("target_entity"), rel.get("relationship_type"))
                if key not in relationship_groups:
                    relationship_groups[key] = []
                relationship_groups[key].append(rel)
            
            # Find the group with the most relationships
            best_group = None
            best_count = 0
            
            for group, rels in relationship_groups.items():
                if len(rels) > best_count:
                    best_count = len(rels)
                    best_group = rels
            
            if best_group and best_count > 1:
                # Use the relationship with highest evidence strength from the best group
                best_relationship = max(best_group, key=lambda r: self.evaluate_evidence_strength(r))
                confidence = min(0.8, 0.5 + (best_count - 1) * 0.1)
                
                return {
                    "resolution": "consensus_based",
                    "chosen_relationship": best_relationship,
                    "confidence": confidence,
                    "reasoning": f"Chosen based on consensus ({best_count} relationships) and evidence strength",
                    "rejected_relationships": [r for r in relationships if r not in best_group]
                }
            else:
                return {"resolution": "insufficient_data", "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error in consensus-based resolution: {str(e)}")
            return {"resolution": "error", "confidence": 0.0}
    
    async def resolve_context_dependent(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve contradiction based on context analysis"""
        try:
            relationships = contradiction.get("relationships", [])
            if len(relationships) < 2:
                return {"resolution": "insufficient_data", "confidence": 0.0}
            
            # Use LLM to analyze context and make resolution decision
            contradiction_data = {
                "contradiction_type": contradiction.get("contradiction_type", "unknown"),
                "severity": contradiction.get("severity", "medium"),
                "relationships": relationships,
                "context_analysis": contradiction.get("context_analysis", {}),
                "resolution_strategy": contradiction.get("resolution_strategy", "context_dependent")
            }
            
            # Create LLM chain for context analysis
            resolution_chain = self.prompt | self.llm | self.parser
            result = await resolution_chain.ainvoke({
                "contradiction_data": json.dumps(contradiction_data, indent=2)
            })
            
            if "resolution" in result:
                return result
            else:
                logger.warning(f"No resolution in LLM result: {result}")
                return {"resolution": "manual_review", "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"Error in context-dependent resolution: {str(e)}")
            return {"resolution": "error", "confidence": 0.0}
    
    def flag_for_manual_review(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Flag contradiction for manual expert review"""
        try:
            return {
                "resolution": "manual_review",
                "confidence": 0.0,
                "reasoning": "Contradiction requires expert human review due to complexity or insufficient evidence",
                "review_priority": contradiction.get("severity", "medium"),
                "review_notes": f"Contradiction type: {contradiction.get('contradiction_type', 'unknown')}, "
                               f"Severity: {contradiction.get('severity', 'medium')}, "
                               f"Relationships: {len(contradiction.get('relationships', []))}",
                "relationships": contradiction.get("relationships", [])
            }
            
        except Exception as e:
            logger.error(f"Error flagging for manual review: {str(e)}")
            return {"resolution": "error", "confidence": 0.0}
    
    async def resolve_contradiction(self, contradiction: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a single contradiction using appropriate strategy"""
        try:
            logger.info(f"Resolving contradiction: {contradiction.get('contradiction_type', 'unknown')}")
            
            # Determine resolution strategy
            strategy = self.determine_resolution_strategy(contradiction)
            logger.info(f"Resolution strategy: {strategy}")
            
            # Apply appropriate resolution method
            if strategy == "evidence_based":
                result = self.resolve_evidence_based(contradiction)
            elif strategy == "consensus_based":
                result = self.resolve_consensus_based(contradiction)
            elif strategy == "context_dependent":
                result = await self.resolve_context_dependent(contradiction)
            else:
                result = self.flag_for_manual_review(contradiction)
            
            # Add metadata
            result["strategy_used"] = strategy
            result["resolved_at"] = datetime.utcnow().isoformat()
            result["contradiction_id"] = contradiction.get("contradiction_id", "unknown")
            
            logger.info(f"Contradiction resolved with strategy: {strategy}, confidence: {result.get('confidence', 0.0)}")
            return result
            
        except Exception as e:
            logger.error(f"Error resolving contradiction: {str(e)}")
            return {
                "resolution": "error",
                "confidence": 0.0,
                "reasoning": f"Error in resolution: {str(e)}",
                "strategy_used": "error",
                "resolved_at": datetime.utcnow().isoformat()
            }
    
    async def resolve_contradictions(self, contradictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve multiple contradictions"""
        try:
            logger.info(f"Resolving {len(contradictions)} contradictions")
            
            resolution_results = {
                "contradictions_processed": len(contradictions),
                "resolutions": [],
                "summary": {
                    "evidence_based": 0,
                    "consensus_based": 0,
                    "context_dependent": 0,
                    "manual_review": 0,
                    "errors": 0
                },
                "errors": []
            }
            
            for i, contradiction in enumerate(contradictions):
                try:
                    resolution = await self.resolve_contradiction(contradiction)
                    resolution_results["resolutions"].append(resolution)
                    
                    # Update summary
                    strategy = resolution.get("strategy_used", "unknown")
                    if strategy in resolution_results["summary"]:
                        resolution_results["summary"][strategy] += 1
                    else:
                        resolution_results["summary"]["errors"] += 1
                        
                except Exception as e:
                    error_msg = f"Error resolving contradiction {i}: {str(e)}"
                    logger.error(error_msg)
                    resolution_results["errors"].append(error_msg)
                    resolution_results["summary"]["errors"] += 1
            
            logger.info(f"Contradiction resolution complete: {resolution_results['summary']}")
            return resolution_results
            
        except Exception as e:
            logger.error(f"Error in contradiction resolution process: {str(e)}")
            return {
                "contradictions_processed": 0,
                "resolutions": [],
                "summary": {"errors": 1},
                "errors": [str(e)]
            }
