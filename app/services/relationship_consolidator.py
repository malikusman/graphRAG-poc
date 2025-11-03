"""
RelationshipConsolidator service for consolidating relationships across documents
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from datetime import datetime

from app.core.config import settings
from app.core.llm_provider import get_llm
from app.configs.schemas import load_prompt
from app.models.relationships import Relationship
from app.utils.math_utils import calculate_noisy_or_strength

logger = logging.getLogger(__name__)


class RelationshipConsolidator:
    """Service for consolidating relationships across documents using enhanced strategies"""
    
    def __init__(self):
        """Initialize the consolidator with LLM and prompts"""
        # Use LLM provider abstraction to support both OpenAI and Bedrock
        self.llm = get_llm(temperature=0.1)
        
        # Load relationship consolidation prompt
        self.prompt_config = load_prompt("relationship_consolidation", "reduce")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        self.parser = JsonOutputParser()
    
    def group_relationships_by_entities_and_type(self, relationships: List[Relationship]) -> Dict[Tuple[str, str, str], List[Relationship]]:
        """Group relationships by (source_entity, target_entity, relationship_type)"""
        groups = {}
        for rel in relationships:
            key = (rel.source_entity, rel.target_entity, rel.relationship_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(rel)
        return groups
    
    def calculate_consolidation_metrics(self, relationships: List[Relationship]) -> Dict[str, Any]:
        """Calculate metrics for relationship consolidation"""
        if not relationships:
            return {}
        
        strengths = [rel.relationship_strength for rel in relationships]
        paper_ids = set()
        section_ids = set()
        years = []
        
        for rel in relationships:
            paper_ids.update(rel.paper_ids)
            section_ids.update(rel.section_ids)
            # Extract year from paper_ids if available (assuming format like "doc_2023_123")
            for paper_id in rel.paper_ids:
                try:
                    year_part = paper_id.split('_')[1] if '_' in paper_id else None
                    if year_part and year_part.isdigit():
                        years.append(int(year_part))
                except (IndexError, ValueError):
                    continue
        
        return {
            "total_relationships": len(relationships),
            "supporting_papers": len(paper_ids),
            "supporting_sections": len(section_ids),
            "average_strength": sum(strengths) / len(strengths),
            "strength_variance": self._calculate_variance(strengths),
            "consensus_ratio": self._calculate_consensus_ratio(strengths),
            "temporal_span_years": max(years) - min(years) if years else 0,
            "earliest_year": min(years) if years else None,
            "latest_year": max(years) if years else None
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _calculate_consensus_ratio(self, strengths: List[float]) -> float:
        """Calculate consensus ratio based on strength similarity"""
        if len(strengths) < 2:
            return 1.0
        
        # Consider relationships with similar strengths as consensus
        avg_strength = sum(strengths) / len(strengths)
        threshold = 0.1  # 10% threshold for consensus
        
        consensus_count = sum(1 for s in strengths if abs(s - avg_strength) <= threshold)
        return consensus_count / len(strengths)
    
    def determine_consolidation_strategy(self, relationships: List[Relationship], metrics: Dict[str, Any]) -> str:
        """Determine the best consolidation strategy based on relationship characteristics"""
        if len(relationships) < 2:
            return "single_relationship"
        
        consensus_ratio = metrics.get("consensus_ratio", 0.0)
        strength_variance = metrics.get("strength_variance", 0.0)
        temporal_span = metrics.get("temporal_span_years", 0)
        
        # High consensus with low variance
        if consensus_ratio > 0.8 and strength_variance < 0.05:
            return "consensus"
        
        # High variance in strengths
        if strength_variance > 0.1:
            return "evidence_based"
        
        # Temporal span suggests evolution of understanding
        if temporal_span > 3:
            return "temporal"
        
        # Different relationship types for same entities
        rel_types = set(rel.relationship_type for rel in relationships)
        if len(rel_types) > 1:
            return "complementary"
        
        # Default to evidence-based
        return "evidence_based"
    
    def consolidate_consensus_relationships(self, relationships: List[Relationship], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate relationships using consensus strategy"""
        try:
            if len(relationships) < 2:
                return self._create_single_relationship_result(relationships[0])
            
            # Use Noisy-OR for strength consolidation
            strengths = [rel.relationship_strength for rel in relationships]
            consolidated_strength = calculate_noisy_or_strength(strengths)
            
            # Combine all paper and section IDs
            all_paper_ids = list(set([pid for rel in relationships for pid in rel.paper_ids]))
            all_section_ids = list(set([sid for rel in relationships for sid in rel.section_ids]))
            
            # Choose the best description (longest/most detailed)
            best_description = max(relationships, key=lambda r: len(r.description or "")).description
            
            # Create consolidated relationship
            consolidated_rel = {
                "source_entity": relationships[0].source_entity,
                "target_entity": relationships[0].target_entity,
                "relationship_type": relationships[0].relationship_type,
                "relationship_strength": consolidated_strength,
                "description": best_description,
                "paper_ids": all_paper_ids,
                "section_ids": all_section_ids,
                "consensus_level": "high" if metrics.get("consensus_ratio", 0) > 0.8 else "medium",
                "confidence": min(0.95, consolidated_strength + 0.1),  # Boost confidence for consensus
                "evidence_count": len(relationships)
            }
            
            return {
                "consolidation_result": {
                    "source_entity": consolidated_rel["source_entity"],
                    "target_entity": consolidated_rel["target_entity"],
                    "consolidated_relationship": consolidated_rel,
                    "consolidation_strategy": "consensus",
                    "consolidation_notes": f"Consolidated {len(relationships)} relationships using consensus strategy with Noisy-OR strength calculation"
                },
                "input_relationships_analysis": [
                    {
                        "relationship_id": f"rel_{i}",
                        "relationship_type": rel.relationship_type,
                        "strength": rel.relationship_strength,
                        "evidence_quality": "high" if rel.relationship_strength > 0.8 else "medium",
                        "contribution_to_consolidation": "primary" if i == 0 else "supporting"
                    }
                    for i, rel in enumerate(relationships)
                ],
                "conflicts_detected": [],
                "evidence_summary": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in consensus consolidation: {str(e)}")
            return {"error": str(e)}
    
    def consolidate_evidence_based_relationships(self, relationships: List[Relationship], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate relationships using evidence-based strategy"""
        try:
            if len(relationships) < 2:
                return self._create_single_relationship_result(relationships[0])
            
            # Sort by evidence strength (relationship_strength + paper count + section count)
            def evidence_score(rel):
                strength_score = rel.relationship_strength * 0.6
                paper_score = min(len(rel.paper_ids) / 5.0, 1.0) * 0.2
                section_score = min(len(rel.section_ids) / 10.0, 1.0) * 0.2
                return strength_score + paper_score + section_score
            
            sorted_relationships = sorted(relationships, key=evidence_score, reverse=True)
            best_relationship = sorted_relationships[0]
            
            # Use Noisy-OR for strength if relationships are similar
            if metrics.get("consensus_ratio", 0) > 0.6:
                strengths = [rel.relationship_strength for rel in relationships]
                consolidated_strength = calculate_noisy_or_strength(strengths)
            else:
                consolidated_strength = best_relationship.relationship_strength
            
            # Combine all paper and section IDs
            all_paper_ids = list(set([pid for rel in relationships for pid in rel.paper_ids]))
            all_section_ids = list(set([sid for rel in relationships for sid in rel.section_ids]))
            
            # Create consolidated relationship
            consolidated_rel = {
                "source_entity": best_relationship.source_entity,
                "target_entity": best_relationship.target_entity,
                "relationship_type": best_relationship.relationship_type,
                "relationship_strength": consolidated_strength,
                "description": best_relationship.description,
                "paper_ids": all_paper_ids,
                "section_ids": all_section_ids,
                "consensus_level": "medium" if metrics.get("consensus_ratio", 0) > 0.6 else "low",
                "confidence": evidence_score(best_relationship),
                "evidence_count": len(relationships)
            }
            
            return {
                "consolidation_result": {
                    "source_entity": consolidated_rel["source_entity"],
                    "target_entity": consolidated_rel["target_entity"],
                    "consolidated_relationship": consolidated_rel,
                    "consolidation_strategy": "evidence_based",
                    "consolidation_notes": f"Chose relationship with highest evidence score, consolidated strength using Noisy-OR"
                },
                "input_relationships_analysis": [
                    {
                        "relationship_id": f"rel_{i}",
                        "relationship_type": rel.relationship_type,
                        "strength": rel.relationship_strength,
                        "evidence_quality": "high" if evidence_score(rel) > 0.8 else "medium",
                        "contribution_to_consolidation": "primary" if i == 0 else "supporting"
                    }
                    for i, rel in enumerate(sorted_relationships)
                ],
                "conflicts_detected": [],
                "evidence_summary": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in evidence-based consolidation: {str(e)}")
            return {"error": str(e)}
    
    def consolidate_temporal_relationships(self, relationships: List[Relationship], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate relationships using temporal strategy"""
        try:
            if len(relationships) < 2:
                return self._create_single_relationship_result(relationships[0])
            
            # Sort by recency (assuming paper_ids contain year information)
            def extract_year(rel):
                for paper_id in rel.paper_ids:
                    try:
                        year_part = paper_id.split('_')[1] if '_' in paper_id else None
                        if year_part and year_part.isdigit():
                            return int(year_part)
                    except (IndexError, ValueError):
                        continue
                return 2020  # Default year if not found
            
            sorted_relationships = sorted(relationships, key=extract_year, reverse=True)
            most_recent = sorted_relationships[0]
            
            # Use Noisy-OR for strength if relationships are similar
            if metrics.get("consensus_ratio", 0) > 0.6:
                strengths = [rel.relationship_strength for rel in relationships]
                consolidated_strength = calculate_noisy_or_strength(strengths)
            else:
                consolidated_strength = most_recent.relationship_strength
            
            # Combine all paper and section IDs
            all_paper_ids = list(set([pid for rel in relationships for pid in rel.paper_ids]))
            all_section_ids = list(set([sid for rel in relationships for sid in rel.section_ids]))
            
            # Create consolidated relationship
            consolidated_rel = {
                "source_entity": most_recent.source_entity,
                "target_entity": most_recent.target_entity,
                "relationship_type": most_recent.relationship_type,
                "relationship_strength": consolidated_strength,
                "description": most_recent.description,
                "paper_ids": all_paper_ids,
                "section_ids": all_section_ids,
                "consensus_level": "medium",
                "confidence": consolidated_strength,
                "evidence_count": len(relationships),
                "temporal_range": {
                    "earliest_year": metrics.get("earliest_year"),
                    "latest_year": metrics.get("latest_year")
                }
            }
            
            return {
                "consolidation_result": {
                    "source_entity": consolidated_rel["source_entity"],
                    "target_entity": consolidated_rel["target_entity"],
                    "consolidated_relationship": consolidated_rel,
                    "consolidation_strategy": "temporal",
                    "consolidation_notes": f"Chose most recent relationship ({extract_year(most_recent)}), consolidated strength using Noisy-OR"
                },
                "input_relationships_analysis": [
                    {
                        "relationship_id": f"rel_{i}",
                        "relationship_type": rel.relationship_type,
                        "strength": rel.relationship_strength,
                        "evidence_quality": "high" if extract_year(rel) >= metrics.get("latest_year", 2020) else "medium",
                        "contribution_to_consolidation": "primary" if i == 0 else "supporting"
                    }
                    for i, rel in enumerate(sorted_relationships)
                ],
                "conflicts_detected": [],
                "evidence_summary": metrics
            }
            
        except Exception as e:
            logger.error(f"Error in temporal consolidation: {str(e)}")
            return {"error": str(e)}
    
    async def consolidate_complementary_relationships(self, relationships: List[Relationship], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate relationships using complementary strategy"""
        try:
            if len(relationships) < 2:
                return self._create_single_relationship_result(relationships[0])
            
            # Use LLM to analyze and consolidate complementary relationships
            relationships_data = []
            for rel in relationships:
                relationships_data.append({
                    "source_entity": rel.source_entity,
                    "target_entity": rel.target_entity,
                    "relationship_type": rel.relationship_type,
                    "relationship_strength": rel.relationship_strength,
                    "description": rel.description,
                    "paper_ids": rel.paper_ids,
                    "section_ids": rel.section_ids
                })
            
            # Prepare context information
            context_info = {
                "publication_years": [metrics.get("earliest_year", 2020), metrics.get("latest_year", 2023)],
                "paper_sources": ["unknown"],  # Could be extracted from paper metadata
                "section_types": ["unknown"],  # Could be extracted from section metadata
                "evidence_quality_metrics": metrics
            }
            
            # Use LLM for complementary consolidation
            consolidation_chain = self.prompt | self.llm | self.parser
            result = await consolidation_chain.ainvoke({
                "relationships_list": json.dumps(relationships_data, indent=2),
                "publication_years": json.dumps(context_info["publication_years"]),
                "paper_sources": json.dumps(context_info["paper_sources"]),
                "section_types": json.dumps(context_info["section_types"]),
                "evidence_quality_metrics": json.dumps(context_info["evidence_quality_metrics"])
            })
            
            if "consolidation_result" in result:
                return result
            else:
                logger.warning(f"No consolidation result in LLM output: {result}")
                # Fallback to evidence-based consolidation
                return self.consolidate_evidence_based_relationships(relationships, metrics)
                
        except Exception as e:
            logger.error(f"Error in complementary consolidation: {str(e)}")
            # Fallback to evidence-based consolidation
            return self.consolidate_evidence_based_relationships(relationships, metrics)
    
    def _create_single_relationship_result(self, relationship: Relationship) -> Dict[str, Any]:
        """Create consolidation result for a single relationship"""
        return {
            "consolidation_result": {
                "source_entity": relationship.source_entity,
                "target_entity": relationship.target_entity,
                "consolidated_relationship": {
                    "source_entity": relationship.source_entity,
                    "target_entity": relationship.target_entity,
                    "relationship_type": relationship.relationship_type,
                    "relationship_strength": relationship.relationship_strength,
                    "description": relationship.description,
                    "paper_ids": relationship.paper_ids,
                    "section_ids": relationship.section_ids,
                    "consensus_level": "high",
                    "confidence": relationship.relationship_strength,
                    "evidence_count": 1
                },
                "consolidation_strategy": "single_relationship",
                "consolidation_notes": "Single relationship, no consolidation needed"
            },
            "input_relationships_analysis": [
                {
                    "relationship_id": "rel_0",
                    "relationship_type": relationship.relationship_type,
                    "strength": relationship.relationship_strength,
                    "evidence_quality": "high" if relationship.relationship_strength > 0.8 else "medium",
                    "contribution_to_consolidation": "primary"
                }
            ],
            "conflicts_detected": [],
            "evidence_summary": {
                "total_relationships": 1,
                "supporting_papers": len(relationship.paper_ids),
                "average_strength": relationship.relationship_strength,
                "strength_variance": 0.0,
                "consensus_ratio": 1.0,
                "temporal_span_years": 0
            }
        }
    
    async def consolidate_relationships(self, relationships: List[Relationship]) -> Dict[str, Any]:
        """Consolidate relationships using appropriate strategy"""
        try:
            logger.info(f"Consolidating {len(relationships)} relationships")
            
            consolidation_results = {
                "relationships_processed": len(relationships),
                "consolidated_relationships": [],
                "consolidation_summary": {
                    "consensus": 0,
                    "evidence_based": 0,
                    "temporal": 0,
                    "complementary": 0,
                    "single_relationship": 0,
                    "errors": 0
                },
                "errors": []
            }
            
            # Group relationships by (source_entity, target_entity, relationship_type)
            relationship_groups = self.group_relationships_by_entities_and_type(relationships)
            
            for group_key, group_relationships in relationship_groups.items():
                try:
                    # Calculate metrics for this group
                    metrics = self.calculate_consolidation_metrics(group_relationships)
                    
                    # Determine consolidation strategy
                    strategy = self.determine_consolidation_strategy(group_relationships, metrics)
                    
                    # Apply appropriate consolidation method
                    if strategy == "consensus":
                        result = self.consolidate_consensus_relationships(group_relationships, metrics)
                    elif strategy == "evidence_based":
                        result = self.consolidate_evidence_based_relationships(group_relationships, metrics)
                    elif strategy == "temporal":
                        result = self.consolidate_temporal_relationships(group_relationships, metrics)
                    elif strategy == "complementary":
                        result = await self.consolidate_complementary_relationships(group_relationships, metrics)
                    else:  # single_relationship
                        result = self._create_single_relationship_result(group_relationships[0])
                    
                    if "error" in result:
                        consolidation_results["errors"].append(result["error"])
                        consolidation_results["consolidation_summary"]["errors"] += 1
                    else:
                        consolidation_results["consolidated_relationships"].append(result)
                        consolidation_results["consolidation_summary"][strategy] += 1
                        
                except Exception as e:
                    error_msg = f"Error consolidating relationship group {group_key}: {str(e)}"
                    logger.error(error_msg)
                    consolidation_results["errors"].append(error_msg)
                    consolidation_results["consolidation_summary"]["errors"] += 1
            
            logger.info(f"Relationship consolidation complete: {consolidation_results['consolidation_summary']}")
            return consolidation_results
            
        except Exception as e:
            logger.error(f"Error in relationship consolidation process: {str(e)}")
            return {
                "relationships_processed": 0,
                "consolidated_relationships": [],
                "consolidation_summary": {"errors": 1},
                "errors": [str(e)]
            }
