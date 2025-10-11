# LangGraph Pipeline & Services - Complete Analysis

**Date**: October 9, 2025  
**Purpose**: Comprehensive understanding of GraphRAG pipeline nodes and services before implementing Vector-First Strategy

---

## 📊 **System Architecture Overview**

### **High-Level Flow**

```
Document Upload
    ↓
Document Processing (Celery Task)
    ↓
GraphRAG Pipeline (LangGraph)
    ├─ MAP Phase: Extract entities and relationships from each section
    ├─ COMBINE Phase: Merge within document
    ├─ REDUCE Phase: Canonicalize and detect contradictions
    └─ UPDATE Phase: Integrate with global knowledge graph
    ↓
Store in MongoDB (entities, relationships collections)
    ↓
Query/Retrieval System (What we're building)
    └─ Search the knowledge graph
```

---

## 🔄 **LangGraph Pipeline - Detailed Walkthrough**

### **Pipeline Structure** (`app/pipelines/graphrag_pipeline.py`)

The pipeline has **8 nodes** in sequential order:

```python
workflow = StateGraph(GraphRAGState)

# Node definitions
1. map_entities              # Extract entities from text
2. map_relationships         # Extract relationships from text
3. combine_entities          # Merge entities within document
4. combine_relationships     # Merge relationships within document
5. reduce_entities           # Canonicalize across documents
6. reduce_relationships      # Detect contradictions
7. consolidate_relationships # Apply consolidation strategies
8. update_global_graph       # Update global knowledge graph

# Edge flow (sequential)
map_entities → map_relationships → combine_entities → 
combine_relationships → reduce_entities → reduce_relationships → 
consolidate_relationships → update_global_graph → END
```

---

## 📦 **Pipeline State** (`GraphRAGState`)

The state object that flows through all nodes:

```python
class GraphRAGState(TypedDict):
    # Input
    document_id: str
    sections: List[Dict[str, Any]]
    
    # MAP Phase outputs
    temp_entities: List[Dict[str, Any]]        # Raw entities from each section
    temp_relationships: List[Dict[str, Any]]   # Raw relationships from each section
    
    # COMBINE Phase outputs
    doc_entities: List[Dict[str, Any]]         # Merged entities (within doc)
    doc_relationships: List[Dict[str, Any]]    # Merged relationships (within doc)
    
    # REDUCE Phase outputs
    final_entities: List[Dict[str, Any]]       # After canonicalization
    final_relationships: List[Dict[str, Any]]  # After contradiction resolution
    
    # Global graph context
    global_entities: List[Dict[str, Any]]      # Existing global entities
    global_relationships: List[Dict[str, Any]] # Existing global relationships
    
    # Processing results
    entity_merges: List[Dict[str, Any]]        # Entity merge operations
    contradictions: List[Dict[str, Any]]       # Detected contradictions
    contradiction_resolutions: List[Dict[str, Any]]  # Resolution results
    resolution_summary: Dict[str, Any]         # Summary statistics
    consolidated_relationships: List[Dict[str, Any]]  # Consolidation results
    consolidation_summary: Dict[str, Any]      # Consolidation statistics
    global_processing_results: Dict[str, Any]  # Global graph update results
    
    # Error tracking
    errors: List[str]
```

---

## 🎯 **Phase 1: MAP Phase**

### **Purpose**: Extract entities and relationships from raw text sections

---

### **Node 1: `_map_entities`** (Lines 112-149)

**What it does**: Extract entities from each section using LLM

**Process**:
```python
For each section in document:
    1. Send section text + title to LLM with entity extraction prompt
    2. LLM returns entities found in that section
    3. Add metadata: document_id, section_id, provenance
    4. Collect in temp_entities list
```

**Input**:
- `state["sections"]` - List of sections with text content

**LLM Prompt**: `app/prompts/map/entity_extraction.json`
- Asks LLM to identify entities in text
- Returns: entity_name, entity_type, entity_category, description, aliases

**Output**:
- `state["temp_entities"]` - Raw entities (duplicates possible, one per section)

**Example**:
```python
# Input section
section = {
    "_id": "sec_123",
    "text": "p53 is a tumor suppressor protein...",
    "title": "abstract"
}

# LLM extracts
temp_entities = [
    {
        "entity_name": "p53",
        "entity_type": "protein",
        "entity_category": "biological_entities",
        "description": "tumor suppressor protein",
        "aliases": ["TP53", "tumor protein 53"],
        "document_id": "doc_123",
        "section_id": "sec_123",
        "provenance": "p53 is a tumor suppressor..."
    }
]
```

---

### **Node 2: `_map_relationships`** (Lines 151-199)

**What it does**: Extract relationships between entities in each section

**Process**:
```python
For each section in document:
    1. Get entities extracted from this section
    2. If < 2 entities, skip (need at least 2 for relationship)
    3. Send section text + entities list to LLM
    4. LLM identifies relationships between entities
    5. Add metadata and collect in temp_relationships
```

**Input**:
- `state["temp_entities"]` - Entities from Node 1
- `state["sections"]` - Section texts

**LLM Prompt**: `app/prompts/map/relationship_extraction.json`
- Asks LLM to find connections between given entities
- Returns: source_entity, target_entity, relationship_type, strength, description

**Output**:
- `state["temp_relationships"]` - Raw relationships (duplicates possible)

**Example**:
```python
# Input
section_entities = [
    {"entity_name": "p53", "entity_type": "protein"},
    {"entity_name": "cancer", "entity_type": "disease"}
]

# LLM extracts
temp_relationships = [
    {
        "source_entity": "p53",
        "target_entity": "cancer",
        "relationship_type": "PREVENTS",
        "relationship_strength": 0.9,
        "description": "p53 prevents cancer by suppressing tumors",
        "document_id": "doc_123",
        "section_id": "sec_123",
        "provenance": "..."
    }
]
```

---

## 🔗 **Phase 2: COMBINE Phase**

### **Purpose**: Merge duplicate entities/relationships within the same document

---

### **Node 3: `_combine_entities`** (Lines 201-241)

**What it does**: Merge duplicate entities found in different sections of same document

**Process**:
```python
1. Group temp_entities by (entity_name, entity_type)
   Example: All "p53" + "protein" entities grouped together
   
2. For each group:
   - Combine all aliases from all occurrences
   - Choose best description (longest/most detailed)
   - Count frequency (number of occurrences)
   - Collect all section_ids where it appeared
   
3. Create merged entity for each group
```

**Algorithm**:
```python
# If p53 appears in 3 sections:
section_1: "p53" with aliases ["TP53"]
section_2: "p53" with aliases ["tumor protein 53"]
section_3: "p53" with aliases ["TP53", "p53 protein"]

# After combine:
merged_entity = {
    "entity_name": "p53",
    "entity_type": "protein",
    "aliases": ["TP53", "tumor protein 53", "p53 protein"],  # Combined & deduplicated
    "frequency": 3,  # Appeared 3 times
    "section_ids": ["sec_1", "sec_2", "sec_3"]
}
```

**Output**:
- `state["doc_entities"]` - Unique entities per document (no duplicates)

---

### **Node 4: `_combine_relationships`** (Lines 243-282)

**What it does**: Merge duplicate relationships using Noisy-OR formula

**Process**:
```python
1. Group temp_relationships by (source_entity, target_entity, relationship_type)
   Example: All "p53 PREVENTS cancer" relationships grouped
   
2. For each group:
   - Calculate combined strength using Noisy-OR formula
   - Combine descriptions
   - Collect all section_ids
   
3. Create merged relationship
```

**Noisy-OR Formula** (from `app/utils/math_utils.py`):
```python
# If relationship appears multiple times with different strengths:
strengths = [0.8, 0.9, 0.7]

# Noisy-OR: P(A or B or C) = 1 - (1-P(A)) * (1-P(B)) * (1-P(C))
combined_strength = 1 - ((1 - 0.8) * (1 - 0.9) * (1 - 0.7))
                  = 1 - (0.2 * 0.1 * 0.3)
                  = 1 - 0.006
                  = 0.994

# Result: Higher confidence when multiple sources agree
```

**Why Noisy-OR?**
- Represents "independent evidence" aggregation
- Multiple weak evidences → strong combined evidence
- Standard in probabilistic reasoning

**Output**:
- `state["doc_relationships"]` - Unique relationships per document

---

## 🎓 **Phase 3: REDUCE Phase**

### **Purpose**: Integrate document results with global knowledge graph

---

### **Node 5: `_reduce_entities`** (Lines 284-325)

**What it does**: Canonicalize entities across ALL documents using EntityCanonicalizer service

**Process**:
```python
1. Convert doc_entities to Entity objects (Pydantic models)

2. Call EntityCanonicalizer.process_entity_canonicalization(entities)
   This service:
   - Finds similar entities in global database
   - Uses LLM to determine if they're the same (e.g., "p53" == "TP53")
   - Merges entities with confidence scores
   - Tracks stable identifiers (HGNC:11998 for p53)
   
3. Update state with:
   - final_entities: Canonical entity list
   - entity_merges: Record of merge operations
```

**Example**:
```python
# Current document has:
doc_entity = {
    "entity_name": "p53",
    "entity_type": "protein",
    "frequency": 5
}

# Global database has:
global_entity = {
    "entity_name": "TP53",
    "entity_type": "protein",
    "frequency": 10,
    "stable_identifier": "HGNC:11998"
}

# EntityCanonicalizer decides:
merge_result = {
    "should_merge": True,
    "confidence": 0.95,
    "reason": "Both refer to same protein (HGNC:11998)",
    "canonical_name": "TP53"
}

# Result:
final_entity = {
    "entity_name": "TP53",  # Canonical name
    "entity_type": "protein",
    "frequency": 15,  # Combined frequency
    "aliases": ["p53", "tumor protein 53"],
    "stable_identifier": "HGNC:11998"
}
```

**Service Used**: `EntityCanonicalizer` (Lines 76)

---

### **Node 6: `_reduce_relationships`** (Lines 327-406)

**What it does**: Detect and resolve contradictions in relationships using two services

**Process**:
```python
1. Convert doc_relationships to Relationship objects

2. Call ContradictionDetector.process_contradiction_detection_with_resolver()
   This orchestrates:
   
   a) ContradictionDetector:
      - Groups relationships by entity pairs
      - Uses LLM to identify contradictions
      - Example: "p53 ACTIVATES apoptosis" vs "p53 INHIBITS apoptosis"
      
   b) ContradictionResolver:
      - Determines resolution strategy (evidence-based, consensus, context-dependent)
      - Chooses which relationship to keep
      - Provides confidence score

3. Update state with:
   - contradictions: List of detected contradictions
   - contradiction_resolutions: Resolution results
   - resolution_summary: Statistics
   
4. Apply resolutions to final_relationships
```

**Example**:
```python
# Two contradicting relationships:
rel_1 = {
    "source": "p53",
    "target": "cell cycle",
    "type": "ACTIVATES",
    "strength": 0.7,
    "paper_ids": ["paper_1"]
}

rel_2 = {
    "source": "p53",
    "target": "cell cycle",
    "type": "INHIBITS",
    "strength": 0.9,
    "paper_ids": ["paper_2", "paper_3"]
}

# ContradictionDetector finds:
contradiction = {
    "entity_pair": ["p53", "cell cycle"],
    "contradicting_relationships": [rel_1, rel_2],
    "contradiction_type": "opposite_relationships",
    "severity": "high"
}

# ContradictionResolver decides:
resolution = {
    "strategy": "evidence_based",  # More papers support INHIBITS
    "chosen_relationship": rel_2,
    "confidence": 0.85,
    "reason": "2 papers vs 1 paper, higher strength"
}

# Final result:
final_relationship = rel_2  # INHIBITS wins
```

**Services Used**:
- `ContradictionDetector` (Line 77)
- `ContradictionResolver` (Line 78)

---

### **Node 7: `_consolidate_relationships`** (Lines 408-459)

**What it does**: Consolidate similar relationships across documents

**Process**:
```python
1. Convert final_relationships to Relationship objects

2. Call RelationshipConsolidator.consolidate_relationships()
   This service:
   - Groups similar relationships
   - Applies consolidation strategies (Noisy-OR, max, weighted avg)
   - Calculates combined metrics
   
3. Update state with:
   - consolidated_relationships: Consolidated results
   - consolidation_summary: Statistics
   
4. Update final_relationships with consolidated versions
```

**Example**:
```python
# Multiple similar relationships:
rel_group = [
    {
        "source": "CRISPR",
        "target": "genome editing",
        "type": "ENABLES",
        "strength": 0.8,
        "paper_ids": ["p1"]
    },
    {
        "source": "CRISPR",
        "target": "genome editing",
        "type": "ENABLES",
        "strength": 0.9,
        "paper_ids": ["p2"]
    },
    {
        "source": "CRISPR",
        "target": "genome editing",
        "type": "ENABLES",
        "strength": 0.85,
        "paper_ids": ["p3"]
    }
]

# RelationshipConsolidator combines:
consolidated_rel = {
    "source": "CRISPR",
    "target": "genome editing",
    "type": "ENABLES",
    "strength": 0.997,  # Noisy-OR of [0.8, 0.9, 0.85]
    "paper_ids": ["p1", "p2", "p3"],
    "evidence_count": 3,
    "consolidation_method": "noisy_or"
}
```

**Service Used**: `RelationshipConsolidator` (Line 79)

---

### **Node 8: `_update_global_graph`** (Lines 461-529)

**What it does**: Persist processed entities and relationships to global knowledge graph

**Process**:
```python
1. Convert final_entities and final_relationships to proper models

2. Call GlobalGraphManager.process_document_against_global_graph()
   This orchestrates:
   - Load existing global graph state
   - Apply entity canonicalization with global context
   - Apply contradiction detection and resolution
   - Apply relationship consolidation
   - Update MongoDB collections (entities, relationships)
   - Update global state cache

3. Update state with:
   - global_processing_results: Summary of updates
   - Statistics: entities_processed, relationships_processed
```

**Database Operations**:
```python
# Insert or update entities
await EntityCollection.upsert_entity(entity)

# Insert or update relationships
await RelationshipCollection.upsert_relationship(relationship)

# Update global state cache
global_graph_manager._global_entities_cache = updated_entities
global_graph_manager._global_relationships_cache = updated_relationships
```

**Service Used**: `GlobalGraphManager` (Line 80)

---

## 🛠️ **Services Deep Dive**

---

### **Service 1: EntityCanonicalizer**

**File**: `app/services/entity_canonicalizer.py`

**Purpose**: Merge duplicate entities across documents with LLM analysis

**Key Methods**:

#### **`process_entity_canonicalization(entities)`**
```python
async def process_entity_canonicalization(
    entities: List[Entity]
) -> Dict[str, Any]:
    """
    Process entity canonicalization for a list of entities
    
    Steps:
    1. For each entity, find similar entities in database
    2. Use LLM to analyze if they're the same
    3. Merge if confidence > threshold (0.8)
    4. Track merge operations
    5. Return canonical entities
    """
```

#### **`find_similar_entities(entity)`**
```python
async def find_similar_entities(entity: Entity) -> List[EntityResponse]:
    """
    Find entities similar to the given entity
    
    Uses:
    - Database query with name similarity
    - Filters by entity_type and entity_category
    - Returns candidates for LLM analysis
    """
```

#### **`calculate_entity_similarity_with_context(entity, existing_entities)`**
```python
async def calculate_entity_similarity_with_context(
    entity: Entity,
    existing_entities: List[Entity]
) -> Dict[str, Any]:
    """
    Use LLM to determine if entities are the same
    
    LLM analyzes:
    - Name similarity (p53 vs TP53)
    - Type and category match
    - Description overlap
    - Stable identifiers (HGNC, UniProt)
    - Aliases
    
    Returns:
    {
        "should_merge": bool,
        "confidence": float,
        "canonical_name": str,
        "reason": str
    }
    """
```

**LLM Prompt**: `app/prompts/reduce/entity_canonicalization.json`

**Example Flow**:
```python
# Input entity
entity = Entity(entity_name="p53", entity_type="protein")

# Find similar
similar = await canonicalizer.find_similar_entities(entity)
# Returns: [EntityResponse(entity_name="TP53", ...)]

# Analyze with LLM
analysis = await canonicalizer.calculate_entity_similarity_with_context(
    entity, similar
)
# Returns: {"should_merge": True, "confidence": 0.95, "canonical_name": "TP53"}

# Merge if confidence > 0.8
if analysis["should_merge"] and analysis["confidence"] > 0.8:
    merged_entity = merge(entity, similar[0])
```

---

### **Service 2: ContradictionDetector**

**File**: `app/services/contradiction_detector.py`

**Purpose**: Identify contradictions in relationships using LLM

**Key Methods**:

#### **`detect_relationship_contradictions_with_context(relationships, context)`**
```python
async def detect_relationship_contradictions_with_context(
    relationships: List[Relationship],
    context_info: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Detect contradictions in relationships
    
    Steps:
    1. Group relationships by entity pairs
    2. For each pair with multiple relationships, use LLM to check for contradictions
    3. Return list of detected contradictions
    """
```

**LLM Analysis**:
```python
# LLM prompt includes:
- All relationships for an entity pair
- Context information (paper sources, publication years, section types)
- Request to identify contradictions

# LLM returns:
{
    "has_contradiction": bool,
    "contradicting_relationships": List[str],  # IDs of contradicting relationships
    "contradiction_type": str,  # "opposite_relationships", "conflicting_strengths", etc.
    "severity": str,  # "high", "medium", "low"
    "explanation": str
}
```

**LLM Prompt**: `app/prompts/reduce/contradiction_detection.json`

---

### **Service 3: ContradictionResolver**

**File**: `app/services/contradiction_resolver.py`

**Purpose**: Resolve detected contradictions using various strategies

**Key Methods**:

#### **`determine_resolution_strategy(contradiction)`**
```python
def determine_resolution_strategy(contradiction: Dict[str, Any]) -> str:
    """
    Determine which strategy to use for resolving contradiction
    
    Strategies:
    1. "evidence_based" - Choose relationship with more evidence (paper count)
    2. "consensus_based" - Choose relationship with higher strength/confidence
    3. "context_dependent" - Use LLM to analyze context and decide
    4. "flag_for_manual_review" - Too complex, needs human review
    
    Selection logic:
    - If severity == "high" → context_dependent or manual_review
    - If clear evidence difference → evidence_based
    - If similar evidence but different strengths → consensus_based
    """
```

#### **`resolve_evidence_based(contradiction)`**
```python
async def resolve_evidence_based(contradiction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve by choosing relationship with more evidence
    
    Evidence metrics:
    - Number of papers (paper_ids count)
    - Relationship frequency
    - Section diversity
    
    Returns chosen relationship + confidence score
    """
```

#### **`resolve_context_dependent(contradiction)`**
```python
async def resolve_context_dependent(contradiction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use LLM to analyze context and resolve
    
    LLM considers:
    - Paper sources and reliability
    - Publication years (newer may be better)
    - Section types (methods vs introduction)
    - Biological/scientific context
    
    Returns LLM-chosen relationship + reasoning
    """
```

**LLM Prompt**: `app/prompts/reduce/contradiction_resolution.json`

---

### **Service 4: RelationshipConsolidator**

**File**: `app/services/relationship_consolidator.py`

**Purpose**: Consolidate similar relationships across documents

**Key Methods**:

#### **`consolidate_relationships(relationships)`**
```python
async def consolidate_relationships(
    relationships: List[Relationship]
) -> Dict[str, Any]:
    """
    Consolidate similar relationships
    
    Steps:
    1. Group similar relationships (same source, target, type)
    2. Calculate combined metrics:
       - Strength: Noisy-OR aggregation
       - Frequency: Sum of occurrences
       - Evidence: Combined paper_ids and section_ids
    3. Choose consolidation strategy based on relationship type
    4. Return consolidated relationships
    """
```

**Consolidation Strategies**:
```python
# Strategy 1: Noisy-OR (default)
strengths = [0.7, 0.8, 0.9]
consolidated_strength = 1 - ((1 - 0.7) * (1 - 0.8) * (1 - 0.9))
# Result: 0.994

# Strategy 2: Maximum
consolidated_strength = max([0.7, 0.8, 0.9])
# Result: 0.9

# Strategy 3: Weighted Average
weights = [paper_count1, paper_count2, paper_count3]
consolidated_strength = weighted_avg(strengths, weights)

# Strategy 4: Confidence-Weighted
# Weight by relationship_strength (higher strength = more weight)
```

---

### **Service 5: GlobalGraphManager**

**File**: `app/services/global_graph_manager.py`

**Purpose**: Manage global knowledge graph state and orchestrate updates

**Key Methods**:

#### **`load_global_graph_state(force_refresh)`**
```python
async def load_global_graph_state(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Load global graph state from MongoDB
    
    Uses caching:
    - Cache TTL: 5 minutes
    - Force refresh: Reload from database
    
    Returns:
    {
        "global_entities": List[Entity],
        "global_relationships": List[Relationship],
        "entity_count": int,
        "relationship_count": int
    }
    """
```

#### **`process_document_against_global_graph(document_id, entities, relationships)`**
```python
async def process_document_against_global_graph(
    document_id: str,
    entities: List[Entity],
    relationships: List[Relationship]
) -> Dict[str, Any]:
    """
    Process document against global graph
    
    Orchestrates:
    1. Load global graph state
    2. Call EntityCanonicalizer with global context
    3. Call ContradictionDetector
    4. Call ContradictionResolver
    5. Call RelationshipConsolidator
    6. Update MongoDB collections
    7. Update cache
    
    Returns processing statistics
    """
```

**This service is the main orchestrator** - it calls all other services and manages the global state.

---

### **Service 6: EmbeddingsService**

**File**: `app/services/embeddings.py`

**Purpose**: Generate vector embeddings using OpenAI

**Key Methods**:

#### **`generate_embedding(text)`**
```python
def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for text
    
    Model: text-embedding-3-small (1536 dimensions)
    
    Process:
    1. Truncate if too long (8191 tokens)
    2. Call OpenAI API
    3. Return embedding vector
    
    Returns: [0.123, -0.456, 0.789, ..., 0.321]  # 1536 floats
    """
```

#### **`generate_section_embedding(section_text, section_title)`**
```python
def generate_section_embedding(
    section_text: str,
    section_title: str = ""
) -> Optional[List[float]]:
    """
    Generate embedding for section with title context
    
    Combines title + text for better semantic representation
    
    Example:
    title = "Methods"
    text = "We used CRISPR to edit genes..."
    combined = "Methods: We used CRISPR to edit genes..."
    
    Returns embedding of combined text
    """
```

**This service is critical for vector search** - it generates the embeddings we'll use for semantic similarity.

---

### **Service 7: QueryAnalysisService**

**File**: `app/services/query_analysis_service.py`

**Purpose**: Analyze user queries to recommend retrieval strategy

**Key Methods**:

#### **`analyze_query(query)`**
```python
async def analyze_query(query: str) -> QueryAnalysis:
    """
    Analyze user query
    
    LLM determines:
    - Intent: FACTUAL, EXPLORATORY, COMPARATIVE, CAUSAL
    - Complexity: SIMPLE, MODERATE, COMPLEX
    - Entities: List of entities mentioned in query
    - Recommended Strategy: VECTOR_FIRST, GRAPH_FIRST, HYBRID
    - Confidence: 0.0 to 1.0
    
    Example:
    Query: "What is p53?"
    Returns:
    {
        "intent": "FACTUAL",
        "complexity": "SIMPLE",
        "entities": [{"name": "p53", "type": "protein", "confidence": 0.9}],
        "recommended_strategy": "VECTOR_FIRST",
        "confidence": 0.85
    }
    """
```

**LLM Prompt**: `app/prompts/orchestrator/query_analysis.json`

**This service is our entry point** - it's what the RetrievalService calls first.

---

## 🔄 **How Services Interact**

### **During Document Processing** (GraphRAG Pipeline)

```
Document Upload
    ↓
[MAP PHASE]
_map_entities → LLM extracts entities
_map_relationships → LLM extracts relationships
    ↓
[COMBINE PHASE]
_combine_entities → Simple deduplication (no service)
_combine_relationships → Noisy-OR calculation (math_utils)
    ↓
[REDUCE PHASE]
_reduce_entities → EntityCanonicalizer
    ├─ Finds similar entities in database
    ├─ LLM analyzes similarity
    └─ Merges if confidence > 0.8

_reduce_relationships → ContradictionDetector + ContradictionResolver
    ├─ Detector: LLM identifies contradictions
    └─ Resolver: Chooses resolution strategy

_consolidate_relationships → RelationshipConsolidator
    └─ Applies Noisy-OR or other strategies
    ↓
[UPDATE PHASE]
_update_global_graph → GlobalGraphManager
    ├─ Orchestrates all services with global context
    ├─ EntityCanonicalizer (with global entities)
    ├─ ContradictionDetector + Resolver
    ├─ RelationshipConsolidator
    └─ Updates MongoDB collections
```

### **During Query/Retrieval** (What we're building)

```
User Query
    ↓
QueryAnalysisService
    ├─ LLM analyzes query
    └─ Recommends strategy
    ↓
RetrievalService
    ├─ Selects strategy based on recommendation
    │
    ├─ [VECTOR_FIRST Strategy] ← We're implementing this
    │   ├─ EmbeddingsService: Generate query embedding
    │   ├─ VectorSearchService: Find similar sections
    │   └─ Return QuerySource objects
    │
    ├─ [GRAPH_FIRST Strategy] ← Future
    │   ├─ Extract entities from query
    │   ├─ Find entities in MongoDB
    │   ├─ Traverse relationships
    │   └─ Return QuerySource + GraphPath objects
    │
    └─ [HYBRID Strategy] ← Future
        ├─ Run both vector + graph
        ├─ Combine results
        └─ Rank with fusion algorithm
    ↓
Return QueryResponse
```

---

## 📊 **Data Flow Summary**

### **Storage Flow** (Document → Database)

```
Raw Text
    ↓ (MAP)
temp_entities, temp_relationships
    ↓ (COMBINE)
doc_entities, doc_relationships
    ↓ (REDUCE)
final_entities, final_relationships
    ↓ (UPDATE)
MongoDB (entities, relationships collections)
```

### **Retrieval Flow** (Query → Results)

```
User Query
    ↓ (ANALYZE)
QueryAnalysis (intent, complexity, strategy)
    ↓ (RETRIEVE)
Strategy-specific search
    ├─ Vector: Search embeddings in sections collection
    ├─ Graph: Traverse entities/relationships collections
    └─ Hybrid: Combine both
    ↓ (ENRICH)
Fetch document metadata
    ↓ (RETURN)
QueryResponse (answer, sources, graph_paths)
```

---

## 🎯 **Key Insights for Vector-First Implementation**

### **1. Embeddings Are Already Generated**
- ✅ `EmbeddingsService` exists and works
- ✅ Embeddings stored in `sections` collection
- ✅ Field: `embedding` (1536-dimensional vector)
- ✅ Model: `text-embedding-3-small`

### **2. We Have All Collections Ready**
- ✅ `sections` - Contains text + embeddings
- ✅ `documents` - Contains metadata (title, DOI, year)
- ✅ `entities` - Knowledge graph entities
- ✅ `relationships` - Knowledge graph relationships

### **3. RetrievalService Structure**
- ✅ Already has database connections
- ✅ Already uses QueryAnalysisService
- ❌ Currently returns mock data
- 🎯 **Our task**: Replace mock with real vector search

### **4. Integration Points**
```python
# RetrievalService.process_query() currently does:
analysis = await self.query_analyzer.analyze_query(query)  # ✅ Working

# We need to add:
if analysis.recommended_strategy == RetrievalStrategy.VECTOR_FIRST:
    vector_strategy = VectorFirstStrategy(self.db)
    sources = await vector_strategy.retrieve(query, analysis, max_results)
    # sources will be real QuerySource objects from database
```

### **5. What We'll Build**
```
app/utils/vector_utils.py
    ├─ cosine_similarity()           # Math function
    ├─ batch_cosine_similarity()     # Vectorized version
    └─ normalize_vector()            # Helper

app/services/vector_search_service.py
    ├─ search()                      # Main entry point
    ├─ _generate_query_embedding()   # Use EmbeddingsService
    ├─ _fetch_candidate_embeddings() # Query MongoDB
    ├─ _calculate_similarities()     # Use vector_utils
    └─ _rank_and_filter()            # Sort and return top N

app/services/retrieval_strategies/vector_first_strategy.py
    ├─ retrieve()                    # Main orchestration
    ├─ _perform_vector_search()      # Call VectorSearchService
    ├─ _enrich_results()             # Fetch document metadata
    └─ _calculate_confidence()       # Estimate confidence

app/services/retrieval_service.py (UPDATE)
    └─ process_query()               # Add strategy selection logic
```

### **6. No Conflicts**
- ✅ Vector search is **separate** from GraphRAG pipeline
- ✅ Pipeline builds the knowledge graph (entities, relationships)
- ✅ Retrieval uses the stored data (sections with embeddings)
- ✅ They work together but don't interfere

---

## ✅ **Summary**

### **GraphRAG Pipeline Purpose**
**Builds the knowledge graph** from documents:
- Extract entities and relationships (MAP)
- Merge within document (COMBINE)
- Canonicalize across documents (REDUCE)
- Store in global graph (UPDATE)

### **Retrieval System Purpose** (What we're building)
**Searches the knowledge graph** to answer queries:
- Analyze query intent (QueryAnalysisService)
- Choose search strategy (Vector/Graph/Hybrid)
- Execute search against stored data
- Return relevant results

### **Services We'll Use**
1. ✅ **EmbeddingsService** - Generate query embeddings (already exists)
2. ✅ **QueryAnalysisService** - Understand query (already exists)
3. 🆕 **VectorSearchService** - Search by similarity (we'll build)
4. 🆕 **VectorFirstStrategy** - Orchestrate vector retrieval (we'll build)
5. ✅ **RetrievalService** - Main entry point (update existing)

### **Services We WON'T Use (Yet)**
- EntityCanonicalizer - Only for document processing
- ContradictionDetector - Only for document processing
- ContradictionResolver - Only for document processing
- RelationshipConsolidator - Only for document processing
- GlobalGraphManager - Only for document processing

(We'll use entities/relationships collections later for Graph-First Strategy)

---

## 🚀 **Ready to Implement**

Now that we understand:
- ✅ Complete GraphRAG pipeline flow
- ✅ All 8 nodes and their purposes
- ✅ All 7 services and how they work
- ✅ Data flow from document to database
- ✅ How retrieval fits into the system
- ✅ What we need to build
- ✅ What already exists

**We're ready to start implementing Vector-First Strategy!**

The system is well-structured, services are modular, and we have a clear path forward. 🎯



