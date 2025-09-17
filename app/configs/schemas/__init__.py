"""
Configuration schemas for GraphRAG system
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path

# Get the directory of this file
SCHEMAS_DIR = Path(__file__).parent

def load_entity_categories() -> List[str]:
    """Load entity categories from JSON file"""
    with open(SCHEMAS_DIR / "entity_categories.json", "r") as f:
        return json.load(f)

def load_relationship_types() -> List[str]:
    """Load relationship types from JSON file"""
    with open(SCHEMAS_DIR / "relationship_types.json", "r") as f:
        return json.load(f)

def load_prompt(prompt_type: str, phase: str = "map") -> Dict[str, Any]:
    """
    Load prompt configuration from JSON file
    
    Args:
        prompt_type: Type of prompt (entity_extraction, relationship_extraction)
        phase: Phase of pipeline (map, combine, reduce)
        
    Returns:
        Prompt configuration dictionary
    """
    prompt_file = SCHEMAS_DIR.parent.parent / "prompts" / phase / f"{prompt_type}.json"
    
    with open(prompt_file, "r") as f:
        return json.load(f)

# Export commonly used configurations
ENTITY_CATEGORIES = load_entity_categories()
RELATIONSHIP_TYPES = load_relationship_types()

