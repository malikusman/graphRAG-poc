"""
Query Analysis Service - Step 1

This service analyzes user queries to understand:
1. What type of question they're asking (intent)
2. How complex the query is
3. What entities and relationships are mentioned
4. Which retrieval strategy would work best

We'll build this incrementally and test each part.
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from app.core.config import settings
from app.core.llm_provider import get_llm
from app.configs.schemas import load_prompt

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """What type of question is the user asking?"""
    FACTUAL = "factual"              # "What is X?"
    EXPLORATORY = "exploratory"      # "Tell me about X"
    COMPARATIVE = "comparative"      # "Compare X and Y"
    CAUSAL = "causal"               # "How does X cause Y?"
    TEMPORAL = "temporal"           # "Recent developments in X"


class QueryComplexity(str, Enum):
    """How complex is this query?"""
    SIMPLE = "simple"               # Single entity, straightforward
    MODERATE = "moderate"           # Multiple entities, some relationships
    COMPLEX = "complex"             # Multiple entities, complex relationships


class RetrievalStrategy(str, Enum):
    """Which retrieval strategy should we use?"""
    VECTOR_FIRST = "vector_first"   # Semantic similarity search
    GRAPH_FIRST = "graph_first"     # Entity-based traversal
    HYBRID = "hybrid"              # Combine both approaches


class EntityInfo(BaseModel):
    """Information about an entity found in the query"""
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (gene, method, disease, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="How confident are we this is an entity")


class QueryAnalysis(BaseModel):
    """Complete analysis of a user query"""
    query: str = Field(..., description="Original query")
    intent: QueryIntent = Field(..., description="What type of question")
    complexity: QueryComplexity = Field(..., description="How complex")
    entities: List[EntityInfo] = Field(default_factory=list, description="Entities found")
    recommended_strategy: RetrievalStrategy = Field(..., description="Best strategy to use")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in analysis")


class QueryAnalysisService:
    """Service to analyze user queries and recommend retrieval strategies"""
    
    def __init__(self):
        """Initialize the query analyzer"""
        # Use LLM provider abstraction to support both OpenAI and Bedrock
        self.llm = get_llm(temperature=0.1)
        
        # Load query analysis prompt from JSON file
        self.prompt_config = load_prompt("query_analysis", "orchestrator")
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_config["system_prompt"]),
            ("user", self.prompt_config["user_prompt"])
        ])
        
        self.parser = JsonOutputParser()
    
    @traceable(name="analyze_query_service", tags=["retrieval", "query_analysis"])
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to understand what they're asking for
        
        Args:
            query: The user's question
            
        Returns:
            QueryAnalysis: Complete analysis of the query
        """
        run = get_current_run_tree()
        if run:
            run.add_metadata({
                "query_length": len(query),
                "query_words": len(query.split())
            })
        
        try:
            logger.info(f"Analyzing query: {query}")
            
            # Create the analysis chain
            analysis_chain = self.analysis_prompt | self.llm | self.parser
            
            # Get analysis from LLM
            result = await analysis_chain.ainvoke({"query": query})
            
            # Convert to our QueryAnalysis model
            analysis = self._convert_to_analysis(query, result)
            
            # Add output metadata
            if run:
                run.add_metadata({
                    "detected_intent": analysis.intent.value,
                    "complexity": analysis.complexity.value,
                    "recommended_strategy": analysis.recommended_strategy.value,
                    "num_entities": len(analysis.entities)
                })
            
            logger.info(f"Analysis complete: intent={analysis.intent}, complexity={analysis.complexity}, "
                       f"strategy={analysis.recommended_strategy}, confidence={analysis.confidence:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            # Return a fallback analysis
            return self._create_fallback_analysis(query)
    
    def _convert_to_analysis(self, query: str, result: Dict[str, Any]) -> QueryAnalysis:
        """Convert LLM result to QueryAnalysis object"""
        try:
            # Convert entities
            entities = []
            for entity_data in result.get("entities", []):
                entities.append(EntityInfo(
                    name=entity_data["name"],
                    type=entity_data["type"],
                    confidence=entity_data["confidence"]
                ))
            
            return QueryAnalysis(
                query=query,
                intent=QueryIntent(result["intent"]),
                complexity=QueryComplexity(result["complexity"]),
                entities=entities,
                recommended_strategy=RetrievalStrategy(result["recommended_strategy"]),
                confidence=result.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error converting analysis result: {str(e)}")
            raise ValueError(f"Invalid analysis result: {str(e)}")
    
    def _create_fallback_analysis(self, query: str) -> QueryAnalysis:
        """Create a simple fallback analysis when LLM fails"""
        logger.warning(f"Creating fallback analysis for: {query}")
        
        return QueryAnalysis(
            query=query,
            intent=QueryIntent.EXPLORATORY,
            complexity=QueryComplexity.MODERATE,
            entities=[],
            recommended_strategy=RetrievalStrategy.HYBRID,
            confidence=0.5
        )
    
    def get_strategy_reasoning(self, analysis: QueryAnalysis) -> str:
        """
        Explain why we chose a particular strategy
        
        Args:
            analysis: The query analysis
            
        Returns:
            str: Explanation of strategy choice
        """
        reasoning_map = {
            QueryIntent.FACTUAL: "Factual questions benefit from precise, direct answers",
            QueryIntent.EXPLORATORY: "Exploratory questions need broad coverage of information",
            QueryIntent.COMPARATIVE: "Comparative questions need structured, related information",
            QueryIntent.CAUSAL: "Causal questions need relationship traversal",
            QueryIntent.TEMPORAL: "Temporal questions need time-aware search"
        }
        
        strategy_reasoning = {
            RetrievalStrategy.VECTOR_FIRST: "Vector search finds semantically similar content",
            RetrievalStrategy.GRAPH_FIRST: "Graph traversal finds related entities and relationships", 
            RetrievalStrategy.HYBRID: "Combines multiple approaches for comprehensive results"
        }
        
        intent_reason = reasoning_map.get(analysis.intent, "General query processing")
        strategy_reason = strategy_reasoning.get(analysis.recommended_strategy, "Best available approach")
        
        return f"Intent: {intent_reason}. Strategy: {strategy_reason}."
