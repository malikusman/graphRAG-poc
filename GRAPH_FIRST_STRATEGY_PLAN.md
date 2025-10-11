# Graph-First Strategy Implementation Plan

**Date**: October 10, 2025  
**Purpose**: Detailed plan for implementing Graph-First retrieval strategy using entity-relationship knowledge graph

---

## 🎯 **Executive Summary**

### **What is Graph-First Strategy?**

Graph-First Strategy retrieves information by:
1. **Finding entities** mentioned in the query (e.g., "p53", "cancer")
2. **Traversing relationships** in the knowledge graph (e.g., p53 → PREVENTS → cancer)
3. **Following paths** to discover connected information
4. **Ranking paths** by relationship strength and relevance
5. **Retrieving source documents** from the entities/relationships

**Best for**:
- ✅ Relationship queries: "How does X affect Y?"
- ✅ Comparative queries: "What's the difference between X and Y?"
- ✅ Exploratory queries: "What does X interact with?"
- ✅ Causal queries: "Why does X cause Y?"

**Not ideal for**:
- ❌ Simple factual queries: "What is X?" (use Vector-First)
- ❌ Broad topic searches: "Cancer research" (use Vector-First)

---

## 📊 **Current State - What We Have**

### **✅ Knowledge Graph is Ready!**

#### **1. Entities Collection**
```python
Entity Schema:
  entity_name: str                    # "p53", "CRISPR", "cancer"
  entity_type: EntityType             # "protein", "method", "disease"
  entity_category: EntityCategory     # "biological_entities", etc.
  entity_description: str             # "Tumor suppressor protein"
  aliases: List[str]                  # ["TP53", "tumor protein 53"]
  paper_ids: List[str]                # Where this entity appears
  section_ids: List[str]              # Which sections mention it
  frequency: int                      # How often it appears
```

**Available Methods** (from `EntityCollection`):
- ✅ `find_entity_by_name_and_type(name, type)`
- ✅ `find_similar_entities_by_name(name, threshold)`
- ✅ `find_entities_by_type_and_category(type, category)`
- ✅ `get_entity_frequency_stats(name)`

#### **2. Relationships Collection**
```python
Relationship Schema:
  source_entity: str                  # "p53"
  target_entity: str                  # "cancer"
  relationship_type: RelationshipType # "PREVENTS"
  relationship_strength: float        # 0.0 to 1.0 (0.9 = high confidence)
  description: str                    # "p53 prevents cancer by..."
  paper_ids: List[str]                # Evidence papers
  section_ids: List[str]              # Evidence sections
```

**Relationship Types** (38 types available):
- Biological: `REGULATES`, `INHIBITS`, `ACTIVATES`, `BINDS_TO`, `INTERACTS_WITH`
- Causal: `CAUSES`, `PREVENTS`, `PROMOTES`, `INDUCES`, `SUPPRESSES`
- Functional: `USES`, `TREATS`, `TARGETS`, `MEASURES`
- Structural: `PART_OF`, `CONTAINS`, `LOCATED_IN`
- And 20+ more...

**Available Methods** (from `RelationshipCollection`):
- ✅ `get_relationships_by_entity(entity_name)` - All relationships for an entity
- ✅ `find_relationships_between_entities(source, target)` - Direct connections
- ✅ `get_relationships_by_type(relationship_type)` - Filter by type
- ✅ `find_relationship_by_entities_and_type(source, target, type)` - Specific relationship

#### **3. GraphPath Model** (Already Exists!)
```python
class GraphPath(BaseModel):
    path: List[str]                    # ["p53", "apoptosis", "cancer"]
    entities: List[Dict[str, Any]]     # Entity details
    relationships: List[Dict[str, Any]] # Relationship details
    total_strength: float              # Combined path strength
    metadata: Dict[str, Any]           # Additional info
```

---

## 🔄 **Graph-First Strategy - How It Works**

### **Example Query**: "How does p53 prevent cancer?"

#### **Step-by-Step Flow**:

```
Query: "How does p53 prevent cancer?"
    ↓
1. Extract Entities from Query
   - Use QueryAnalysisService results
   - Entities: ["p53", "cancer"]
    ↓
2. Find Entities in Knowledge Graph
   - Search entities collection
   - Match: p53 (protein), cancer (disease)
   - Use aliases: TP53 also matches p53
    ↓
3. Find Relationships Between Entities
   - Query: relationships where source="p53" AND target="cancer"
   - Found: p53 --[PREVENTS]--> cancer (strength: 0.9)
    ↓
4. Traverse to Find Paths
   - Option A: Direct path
     p53 → cancer (1 hop)
   
   - Option B: Multi-hop paths
     p53 → apoptosis → cancer (2 hops)
     p53 → cell cycle → cancer (2 hops)
    ↓
5. Score Each Path
   - Direct path: strength = 0.9
   - Two-hop path: strength = 0.9 × 0.8 = 0.72
   - Three-hop path: strength = 0.9 × 0.8 × 0.7 = 0.504
    ↓
6. Retrieve Source Documents
   - Get paper_ids from relationships
   - Fetch document + section metadata
   - Build QuerySource objects
    ↓
7. Return Results
   - QuerySource[] with relevance scores
   - GraphPath[] showing entity connections
   - Confidence based on path quality
```

---

## 🏗️ **Architecture Design**

### **File Structure**

```
app/services/
  ├─ graph_traversal_service.py       # NEW - Core graph traversal logic
  └─ retrieval_strategies/
      └─ graph_first_strategy.py      # NEW - Graph-First implementation

tests/
  ├─ test_graph_traversal_service.py  # NEW - Traversal tests
  ├─ test_graph_first_strategy.py     # NEW - Strategy tests
  └─ test_graph_retrieval_e2e.py      # NEW - End-to-end with real graph
```

---

## 🔧 **Component 1: Graph Traversal Service**

### **File**: `app/services/graph_traversal_service.py`

**Purpose**: Core engine for traversing the knowledge graph

**Key Methods**:

#### **1. `find_entities_in_query(query, analysis)`**
```python
async def find_entities_in_query(
    query: str,
    analysis: QueryAnalysis
) -> List[EntityMatch]:
    """
    Find entities from the query in the knowledge graph
    
    Process:
    1. Use entities from QueryAnalysis (already extracted)
    2. Search knowledge graph for matches
    3. Handle aliases (e.g., "p53" matches "TP53")
    4. Return matched entities with confidence
    
    Example:
        Query: "How does TP53 prevent cancer?"
        Analysis entities: [
            {name: "TP53", type: "gene"},
            {name: "cancer", type: "disease"}
        ]
        
        Found in graph:
        [
            EntityMatch(
                query_entity="TP53",
                matched_entity=Entity(entity_name="p53", aliases=["TP53", ...]),
                match_type="alias",
                confidence=0.95
            ),
            EntityMatch(
                query_entity="cancer",
                matched_entity=Entity(entity_name="cancer", ...),
                match_type="exact",
                confidence=1.0
            )
        ]
    """
```

#### **2. `traverse_graph(start_entities, max_hops, filters)`**
```python
async def traverse_graph(
    start_entities: List[Entity],
    max_hops: int = 3,
    filters: Dict[str, Any] = None
) -> List[GraphPath]:
    """
    Traverse the knowledge graph from starting entities
    
    Algorithms:
    - BFS (Breadth-First Search): Explore all neighbors before going deeper
    - DFS (Depth-First Search): Explore one path fully before trying others
    
    We'll use BFS for balanced exploration
    
    Process:
    1. Start from each entity
    2. Find all relationships (outgoing and incoming)
    3. Follow relationships to connected entities
    4. Repeat for max_hops levels
    5. Track all paths discovered
    6. Calculate path strength (product of relationship strengths)
    
    Example:
        Start: ["p53"]
        max_hops: 2
        
        Hop 1:
        p53 --[PREVENTS, 0.9]--> cancer
        p53 --[ACTIVATES, 0.85]--> apoptosis
        p53 --[REGULATES, 0.8]--> cell cycle
        
        Hop 2:
        apoptosis --[PREVENTS, 0.8]--> cancer
        cell cycle --[ASSOCIATED_WITH, 0.7]--> cancer
        
        Paths Found:
        [
            Path(["p53", "cancer"], strength=0.9),               # Direct
            Path(["p53", "apoptosis", "cancer"], strength=0.72), # 2-hop
            Path(["p53", "cell cycle", "cancer"], strength=0.56) # 2-hop
        ]
    """
```

#### **3. `find_paths_between_entities(source_entities, target_entities, max_hops)`**
```python
async def find_paths_between_entities(
    source_entities: List[Entity],
    target_entities: List[Entity],
    max_hops: int = 3
) -> List[GraphPath]:
    """
    Find all paths connecting source and target entities
    
    This is the key method for relationship queries like:
    "How does p53 affect cancer?"
    
    Algorithm:
    Bidirectional BFS:
    1. Start BFS from source entities
    2. Start BFS from target entities
    3. Find where they meet in the middle
    4. Construct complete paths
    
    Benefits:
    - Faster than single-direction BFS
    - Finds shortest paths first
    - Efficient for distant entities
    
    Example:
        Sources: [p53]
        Targets: [cancer]
        max_hops: 3
        
        Forward from p53:
        p53 → apoptosis (hop 1)
        
        Backward from cancer:
        cancer ← apoptosis (hop 1)
        
        Meet at: apoptosis
        
        Complete path:
        p53 --[ACTIVATES]--> apoptosis --[PREVENTS]--> cancer
    """
```

#### **4. `score_path(path)`**
```python
def score_path(path: GraphPath) -> float:
    """
    Calculate relevance score for a graph path
    
    Scoring factors:
    1. Path strength (40%):
       - Product of relationship strengths
       - Shorter paths preferred (less decay)
    
    2. Relationship relevance (30%):
       - Certain relationships more meaningful
       - CAUSES, PREVENTS, TREATS > ASSOCIATED_WITH
    
    3. Evidence count (20%):
       - More papers supporting relationships = higher score
       - paper_ids count
    
    4. Path length penalty (10%):
       - 1-hop: 1.0
       - 2-hop: 0.8
       - 3-hop: 0.6
    
    Formula:
    score = (
        0.4 * path_strength +
        0.3 * relationship_relevance +
        0.2 * normalized_evidence_count +
        0.1 * path_length_factor
    )
    
    Example:
        Path: p53 --[PREVENTS, 0.9, 3 papers]--> cancer
        
        Calculation:
        - path_strength: 0.9
        - relationship_relevance: 1.0 (PREVENTS is highly relevant)
        - evidence_count: 3 papers → normalized to 0.75
        - path_length: 1 hop → 1.0
        
        score = 0.4*0.9 + 0.3*1.0 + 0.2*0.75 + 0.1*1.0
              = 0.36 + 0.30 + 0.15 + 0.10
              = 0.91 (excellent!)
    """
```

---

## 🔧 **Component 2: Graph-First Strategy**

### **File**: `app/services/retrieval_strategies/graph_first_strategy.py`

**Purpose**: Orchestrate graph-based retrieval

**Key Methods**:

#### **1. `retrieve(query, analysis, max_results)`**
```python
async def retrieve(
    query: str,
    analysis: QueryAnalysis,
    max_results: int = 10
) -> List[QuerySource]:
    """
    Main retrieval method using graph traversal
    
    Flow:
    1. Extract and find entities from query
    2. Determine query type (single entity vs relationship)
    3. Traverse graph to find relevant paths
    4. Retrieve source documents from paths
    5. Build QuerySource objects
    6. Return results with graph paths
    """
```

**Query Type Detection**:
```python
def _determine_query_type(analysis: QueryAnalysis) -> str:
    """
    Determine what kind of graph query this is
    
    Types:
    1. "single_entity" - One entity, explore its connections
       Example: "What does CRISPR interact with?"
       
    2. "entity_pair" - Two entities, find paths between them
       Example: "How does p53 prevent cancer?"
       
    3. "multi_entity" - Multiple entities, find their relationships
       Example: "How are p53, BRCA1, and cancer related?"
       
    4. "exploration" - No specific entities, explore graph
       Example: "What cancer treatments are there?"
    """
```

#### **2. `_single_entity_exploration(entity, max_hops)`**
```python
async def _single_entity_exploration(
    entity: Entity,
    max_hops: int
) -> Tuple[List[GraphPath], List[QuerySource]]:
    """
    Explore connections from a single entity
    
    Used for queries like:
    - "What does CRISPR target?"
    - "What regulates p53?"
    - "What diseases are associated with BRCA1?"
    
    Process:
    1. Get all relationships for this entity
    2. Traverse outward for max_hops
    3. Score paths by relevance
    4. Retrieve source documents
    
    Example:
        Entity: CRISPR
        max_hops: 2
        
        Discovered paths:
        - CRISPR --[TARGETS]--> genome (strength: 0.9)
        - CRISPR --[USES]--> Cas9 --[BINDS_TO]--> DNA (strength: 0.72)
        - CRISPR --[TREATS]--> genetic diseases (strength: 0.85)
    """
```

#### **3. `_entity_pair_path_finding(source, target, max_hops)`**
```python
async def _entity_pair_path_finding(
    source_entity: Entity,
    target_entity: Entity,
    max_hops: int
) -> Tuple[List[GraphPath], List[QuerySource]]:
    """
    Find all paths connecting two entities
    
    Used for queries like:
    - "How does p53 prevent cancer?"
    - "What's the relationship between CRISPR and gene therapy?"
    
    Algorithm:
    Bidirectional BFS (faster than single-direction)
    
    Example:
        Source: p53
        Target: cancer
        max_hops: 3
        
        Found paths:
        1. p53 --[PREVENTS]--> cancer (direct, strength: 0.9)
        2. p53 --[ACTIVATES]--> apoptosis --[PREVENTS]--> cancer (2-hop, strength: 0.72)
        3. p53 --[REGULATES]--> cell cycle --[ASSOCIATED_WITH]--> cancer (2-hop, strength: 0.64)
    """
```

#### **4. `_multi_entity_analysis(entities, max_hops)`**
```python
async def _multi_entity_analysis(
    entities: List[Entity],
    max_hops: int
) -> Tuple[List[GraphPath], List[QuerySource]]:
    """
    Analyze relationships among multiple entities
    
    Used for queries like:
    - "How are p53, BRCA1, and cancer related?"
    - "What connects CRISPR, gene therapy, and genetic diseases?"
    
    Process:
    1. Find all pairwise paths between entities
    2. Identify common connections (hubs)
    3. Build a subgraph of related entities
    4. Score by interconnectedness
    
    Example:
        Entities: [p53, BRCA1, cancer]
        
        Paths:
        - p53 --[PREVENTS]--> cancer
        - BRCA1 --[PREVENTS]--> cancer
        - p53 --[INTERACTS_WITH]--> BRCA1
        
        Common hub: cancer (both p53 and BRCA1 prevent it)
    """
```

---

## 📊 **Graph Algorithms**

### **Algorithm 1: Breadth-First Search (BFS)**

**Purpose**: Explore graph level by level

```python
def bfs_traverse(start_entity, max_hops):
    """
    BFS explores all neighbors before going deeper
    
    Process:
    Level 0: [p53]
    Level 1: [cancer, apoptosis, cell cycle]  # All direct neighbors
    Level 2: [DNA repair, cell death, ...]     # Neighbors of level 1
    
    Guarantees:
    - Finds shortest paths first
    - Complete exploration at each level
    - Good for finding direct connections
    """
    
    queue = [(start_entity, [])]  # (entity, path_so_far)
    visited = set()
    paths = []
    
    while queue and len(paths) < max_paths:
        current_entity, current_path = queue.pop(0)
        
        if current_entity in visited:
            continue
        visited.add(current_entity)
        
        # Get relationships for current entity
        relationships = await get_relationships_by_entity(current_entity)
        
        for rel in relationships:
            # Get connected entity
            connected = rel.target if rel.source == current_entity else rel.source
            
            # Build new path
            new_path = current_path + [(current_entity, rel, connected)]
            
            # Add to results
            paths.append(GraphPath.from_path(new_path))
            
            # Continue traversal if under max_hops
            if len(new_path) < max_hops:
                queue.append((connected, new_path))
    
    return paths
```

### **Algorithm 2: Bidirectional BFS**

**Purpose**: Find paths between two specific entities (faster)

```python
def bidirectional_bfs(source, target, max_hops):
    """
    Search from both ends and meet in the middle
    
    Advantage: Much faster for distant entities
    - Single BFS: Explores 10^n nodes for n hops
    - Bidirectional: Explores 2 × 10^(n/2) nodes (much smaller!)
    
    Example:
        source: p53
        target: cancer
        max_hops: 4
        
        Forward from p53:
        Hop 1: [apoptosis, cell cycle]
        Hop 2: [DNA damage, cell death]
        
        Backward from cancer:
        Hop 1: [apoptosis, cell division]
        Hop 2: [DNA damage, tumor growth]
        
        Meet at: apoptosis, DNA damage
        
        Paths constructed:
        - p53 → apoptosis → cancer
        - p53 → cell cycle → DNA damage → cancer
    """
    
    forward_search = {source: []}
    backward_search = {target: []}
    
    for hop in range(max_hops // 2):
        # Expand forward
        forward_search = expand_frontier(forward_search)
        
        # Expand backward
        backward_search = expand_frontier(backward_search)
        
        # Check for intersection
        meeting_points = set(forward_search.keys()) & set(backward_search.keys())
        
        if meeting_points:
            # Construct complete paths
            paths = []
            for meeting in meeting_points:
                forward_path = forward_search[meeting]
                backward_path = backward_search[meeting]
                complete_path = forward_path + [meeting] + reversed(backward_path)
                paths.append(complete_path)
            return paths
    
    return []  # No path found within max_hops
```

---

## 📊 **Data Structures**

### **EntityMatch**
```python
@dataclass
class EntityMatch:
    """
    Represents a match between query entity and knowledge graph entity
    """
    query_entity: str          # "TP53" from query
    matched_entity: Entity     # p53 entity from graph
    match_type: str            # "exact", "alias", "fuzzy"
    confidence: float          # 0.0 to 1.0
    
    # Why matched:
    # "exact": query="p53" matches entity_name="p53"
    # "alias": query="TP53" matches entity.aliases=["TP53"]
    # "fuzzy": query="p 53" fuzzy matches "p53"
```

### **GraphPath** (Already Exists!)
```python
class GraphPath(BaseModel):
    path: List[str]                # ["p53", "apoptosis", "cancer"]
    entities: List[Dict]           # Full entity details
    relationships: List[Dict]      # Full relationship details
    total_strength: float          # Product of strengths: 0.9 × 0.8 = 0.72
    metadata: Dict                 # Additional info
```

### **PathScore**
```python
@dataclass
class PathScore:
    """
    Scoring information for a graph path
    """
    path: GraphPath
    relevance_score: float         # Overall score (0.0 to 1.0)
    path_strength: float           # Relationship strengths multiplied
    evidence_count: int            # Total papers supporting this path
    hop_count: int                 # Number of hops (1, 2, 3, ...)
    relationship_types: List[str]  # Types of relationships in path
```

---

## 🎯 **Implementation Phases**

### **Phase 1: Graph Traversal Service** (Core Engine)

**Estimated Time**: 3-4 hours

**Tasks**:
1. Create `graph_traversal_service.py`
2. Implement entity matching (`find_entities_in_query`)
3. Implement BFS traversal (`traverse_graph`)
4. Implement bidirectional search (`find_paths_between_entities`)
5. Implement path scoring (`score_path`)
6. Write unit tests (20+ tests)

**Validation**:
```bash
pytest test_graph_traversal_service.py -v
# Expected: All traversal algorithms work correctly
```

---

### **Phase 2: Graph-First Strategy** (Orchestration)

**Estimated Time**: 2-3 hours

**Tasks**:
1. Create `graph_first_strategy.py`
2. Implement `retrieve()` method
3. Implement query type detection
4. Implement single entity exploration
5. Implement entity pair path finding
6. Implement result conversion (paths → QuerySource)
7. Write integration tests (15+ tests)

**Validation**:
```bash
pytest test_graph_first_strategy.py -v
# Expected: Strategy returns relevant sources and graph paths
```

---

### **Phase 3: RetrievalService Integration**

**Estimated Time**: 1 hour

**Tasks**:
1. Update `retrieval_service.py`
2. Add GraphFirstStrategy to strategies dict
3. Update `_generate_answer()` for graph results
4. Handle graph paths in response
5. Write integration tests

**Validation**:
```bash
pytest test_graph_retrieval_integration.py -v
# Expected: End-to-end graph retrieval works
```

---

### **Phase 4: Real Data Testing**

**Estimated Time**: 1-2 hours

**Tasks**:
1. Upload documents with rich entity/relationship data
2. Test relationship queries
3. Test comparative queries
4. Validate graph paths are accurate
5. Check performance

**Validation**:
```bash
python test_graph_real_data_e2e.py
# Expected: Real queries return relevant graph paths
```

---

## 📋 **Example Queries and Expected Behavior**

### **Query 1: Single Entity Exploration**
**Query**: "What does p53 regulate?"

**Process**:
1. Find entity: p53
2. Get all relationships where source="p53"
3. Filter by type: REGULATES, ACTIVATES, INHIBITS
4. Return connected entities

**Expected Results**:
```
Graph Paths:
- p53 --[REGULATES]--> cell cycle (strength: 0.85)
- p53 --[ACTIVATES]--> apoptosis (strength: 0.9)
- p53 --[INHIBITS]--> cell division (strength: 0.8)

Sources:
- Document: "p53 Functions in Cell Cycle Control"
- Document: "p53-Mediated Apoptosis"
- Document: "p53 and Cell Division"
```

### **Query 2: Entity Pair Relationship**
**Query**: "How does CRISPR treat cancer?"

**Process**:
1. Find entities: CRISPR, cancer
2. Find paths between them
3. Score by relevance

**Expected Results**:
```
Graph Paths:
1. CRISPR --[TREATS]--> cancer (direct, strength: 0.85)
2. CRISPR --[MODIFIES]--> immune cells --[TARGET]--> cancer (2-hop, strength: 0.72)
3. CRISPR --[CORRECTS]--> gene mutations --[CAUSE]--> cancer (2-hop, strength: 0.68)

Sources:
- Document: "CRISPR in Cancer Immunotherapy"
- Document: "Gene Correction for Cancer Prevention"
```

### **Query 3: Comparative**
**Query**: "Compare p53 and BRCA1 in cancer prevention"

**Process**:
1. Find entities: p53, BRCA1, cancer
2. Find paths from both to cancer
3. Compare relationship types and strengths

**Expected Results**:
```
Graph Paths for p53:
- p53 --[PREVENTS]--> cancer (strength: 0.9)
- p53 --[SUPPRESSES]--> tumor growth (strength: 0.85)

Graph Paths for BRCA1:
- BRCA1 --[PREVENTS]--> cancer (strength: 0.88)
- BRCA1 --[REPAIRS]--> DNA damage --[PREVENTS]--> cancer (strength: 0.75)

Comparison:
- Both prevent cancer (similar mechanism)
- p53 through apoptosis pathway
- BRCA1 through DNA repair pathway
```

---

## 🧮 **Graph Metrics and Scoring**

### **Path Strength Calculation**

**Simple Path** (1 hop):
```
p53 --[PREVENTS, 0.9]--> cancer

strength = 0.9
```

**Two-Hop Path**:
```
p53 --[ACTIVATES, 0.9]--> apoptosis --[PREVENTS, 0.8]--> cancer

strength = 0.9 × 0.8 = 0.72
```

**Three-Hop Path**:
```
p53 --[REGULATES, 0.85]--> cell cycle --[AFFECTS, 0.75]--> cell division --[CAUSES, 0.7]--> cancer

strength = 0.85 × 0.75 × 0.7 = 0.446
```

**Path Decay**: Each hop reduces strength (multiplicative)

### **Relationship Type Weighting**

Different relationship types have different relevance for queries:

```python
RELATIONSHIP_WEIGHTS = {
    # High relevance (1.0)
    "CAUSES": 1.0,
    "PREVENTS": 1.0,
    "TREATS": 1.0,
    "TARGETS": 1.0,
    
    # Medium-high relevance (0.9)
    "REGULATES": 0.9,
    "ACTIVATES": 0.9,
    "INHIBITS": 0.9,
    "INDUCES": 0.9,
    
    # Medium relevance (0.8)
    "INTERACTS_WITH": 0.8,
    "BINDS_TO": 0.8,
    "ASSOCIATED_WITH": 0.7,
    
    # Lower relevance (0.6)
    "PART_OF": 0.6,
    "LOCATED_IN": 0.6,
    "CONTAINS": 0.6,
    
    # Default
    "OTHER": 0.5
}

# Usage in scoring:
rel_type = "PREVENTS"
relevance = RELATIONSHIP_WEIGHTS[rel_type]  # 1.0
```

---

## 🔍 **Query Entity Extraction**

### **Challenge**: Entities in Query vs Entities in Graph

**Query**: "How does TP53 prevent cancer?"

**Extracted Entities** (from QueryAnalysisService):
- TP53 (gene)
- cancer (disease)

**Matching in Graph**:
```python
# Search for "TP53" in graph
results = await find_entities(query="TP53")

# Option 1: Exact match
entity = find_one(entity_name="TP53")  # May not exist

# Option 2: Alias match
entity = find_one(entity_name="p53", aliases__contains="TP53")  # ✅ Found!

# Option 3: Fuzzy match
entities = find_similar(entity_name="TP53", threshold=0.8)  # p53, TP53, etc.
```

**Entity Matching Strategies**:
1. **Exact name match**: `entity_name == query_entity`
2. **Alias match**: `query_entity in entity.aliases`
3. **Fuzzy match**: Use text similarity or LLM
4. **Type-based filtering**: Only match compatible types

---

## 🎨 **Path Visualization Example**

### **Query**: "How does p53 prevent cancer?"

**Graph Structure**:
```
                    ┌─────────────┐
                    │    p53      │
                    │  (protein)  │
                    └─────┬───────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
       [ACTIVATES]   [REGULATES]  [PREVENTS]
          0.9           0.85          0.9
            │             │             │
            ▼             ▼             ▼
      ┌──────────┐  ┌───────────┐  ┌────────┐
      │apoptosis │  │cell cycle │  │ cancer │
      │(process) │  │ (process) │  │(disease)│
      └────┬─────┘  └─────┬─────┘  └────────┘
           │              │
      [PREVENTS]    [ASSOCIATED_WITH]
          0.8            0.75
           │              │
           └──────┬───────┘
                  ▼
            ┌────────────┐
            │   cancer   │
            │  (disease) │
            └────────────┘
```

**Paths Found**:
1. **Direct Path**: p53 → cancer (1 hop)
   - Strength: 0.9
   - Relationship: PREVENTS
   - Evidence: 3 papers

2. **Via Apoptosis**: p53 → apoptosis → cancer (2 hops)
   - Strength: 0.9 × 0.8 = 0.72
   - Relationships: ACTIVATES, PREVENTS
   - Evidence: 2 + 2 papers

3. **Via Cell Cycle**: p53 → cell cycle → cancer (2 hops)
   - Strength: 0.85 × 0.75 = 0.64
   - Relationships: REGULATES, ASSOCIATED_WITH
   - Evidence: 2 + 1 papers

**Ranking**: Path 1 > Path 2 > Path 3 (by strength)

---

## 🔄 **Integration with QuerySource**

### **Challenge**: Graph paths vs Document sources

Graph-First Strategy returns both:
1. **GraphPath objects**: Show entity connections
2. **QuerySource objects**: Actual document sections

**Conversion Process**:
```python
# From path:
path = GraphPath(
    path=["p53", "apoptosis", "cancer"],
    relationships=[
        {"source": "p53", "target": "apoptosis", "type": "ACTIVATES", 
         "section_ids": ["sec_123", "sec_456"]}
    ]
)

# Extract section_ids from relationships
section_ids = ["sec_123", "sec_456"]

# Fetch sections
sections = await fetch_sections(section_ids)

# Convert to QuerySources
sources = [
    QuerySource(
        document_id=section["document_id"],
        document_title="p53 and Apoptosis",
        section_id="sec_123",
        section_type="results",
        content=section["text"],
        relevance_score=0.72,  # From path strength
        metadata={
            "graph_path": ["p53", "apoptosis", "cancer"],
            "relationship_type": "ACTIVATES",
            "evidence_type": "graph_traversal"
        }
    )
]
```

---

## ⚡ **Performance Considerations**

### **Graph Size Impact**

| Entities | Relationships | BFS (1 hop) | BFS (2 hops) | BFS (3 hops) |
|----------|---------------|-------------|--------------|--------------|
| 100 | 500 | ~10ms | ~50ms | ~200ms |
| 1,000 | 5,000 | ~20ms | ~100ms | ~500ms |
| 10,000 | 50,000 | ~50ms | ~300ms | ~2s |

**Optimizations**:
1. **Limit traversal**: max_hops = 3 (beyond that, paths are usually not meaningful)
2. **Prune low-strength paths**: Don't follow relationships < 0.5 strength
3. **Cache frequently traversed entities**: Redis caching
4. **Index optimization**: Ensure compound indexes on source+target

---

## 🎓 **Key Concepts**

### **1. Graph Traversal**
```
Starting from an entity, follow relationships to discover connected entities

Like following a map:
- Start at city A (p53)
- Follow roads (relationships) to city B (apoptosis)
- Continue to city C (cancer)
- Record the path: A → B → C
```

### **2. Path Strength**
```
Confidence in a path based on relationship strengths

Strong path:
p53 --[0.9]--> apoptosis --[0.9]--> cancer
strength = 0.9 × 0.9 = 0.81 (high confidence)

Weak path:
p53 --[0.6]--> X --[0.5]--> Y --[0.4]--> cancer
strength = 0.6 × 0.5 × 0.4 = 0.12 (low confidence)
```

### **3. Bidirectional Search**
```
Search from both ends to find paths faster

Instead of:
p53 → ? → ? → ? → cancer (explore 100s of paths)

Do:
p53 → ? (forward)    AND    cancer ← ? (backward)
Meet in middle = faster!
```

---

## 📊 **Success Criteria**

### **Functional Requirements**
- ✅ Find entities in query with 90%+ accuracy
- ✅ Traverse graph up to 3 hops
- ✅ Return valid GraphPath objects
- ✅ Convert paths to QuerySource objects
- ✅ Score paths meaningfully
- ✅ Handle queries with 1, 2, or 3+ entities

### **Performance Requirements**
- ✅ Entity lookup: < 100ms
- ✅ Graph traversal (3 hops): < 2s for 1000 entities
- ✅ Full query processing: < 5s total
- ✅ Memory usage: < 500MB

### **Quality Requirements**
- ✅ Paths are semantically meaningful
- ✅ Shortest/strongest paths ranked highest
- ✅ Evidence count tracked
- ✅ Source documents are relevant

---

## 🔄 **Comparison: Vector-First vs Graph-First**

### **Vector-First Strategy** (What we built)
```
Query: "What is CRISPR?"

Process:
1. Generate query embedding
2. Find similar document sections
3. Rank by cosine similarity
4. Return top documents

Result:
- Documents semantically similar to query
- Based on text content similarity
- No understanding of entity relationships
- Fast, simple, effective for factual queries
```

### **Graph-First Strategy** (What we'll build)
```
Query: "How does CRISPR affect gene expression?"

Process:
1. Find entities: CRISPR, gene expression
2. Traverse relationships between them
3. Discover paths: CRISPR → DNA → gene expression
4. Rank by path strength
5. Return documents from path

Result:
- Documents about entity relationships
- Based on knowledge graph connections
- Understands how concepts relate
- Best for relationship/causal queries
```

### **When to Use Each**

| Query Type | Best Strategy | Why |
|------------|---------------|-----|
| "What is X?" | Vector-First | Semantic similarity to topic |
| "How does X work?" | Vector-First | General explanation |
| "How does X affect Y?" | **Graph-First** | Entity relationship |
| "What regulates X?" | **Graph-First** | Relationship discovery |
| "Compare X and Y" | **Graph-First** | Relationship comparison |
| "X applications" | Vector-First | Broad topic search |
| "Why does X cause Y?" | **Graph-First** | Causal relationship |

---

## 🎯 **Implementation Plan Summary**

### **Phase 1: Graph Traversal Service** (3-4 hours)
Files:
- `app/services/graph_traversal_service.py` (400+ lines)
- `test_graph_traversal_service.py` (300+ lines)

Core features:
- Entity matching (exact, alias, fuzzy)
- BFS traversal
- Bidirectional search
- Path scoring

---

### **Phase 2: Graph-First Strategy** (2-3 hours)
Files:
- `app/services/retrieval_strategies/graph_first_strategy.py` (350+ lines)
- `test_graph_first_strategy.py` (250+ lines)

Core features:
- Query type detection
- Single entity exploration
- Entity pair path finding
- Result conversion

---

### **Phase 3: Integration** (1 hour)
Files:
- `app/services/retrieval_service.py` (update)
- `test_graph_retrieval_integration.py` (200+ lines)

Core features:
- Add GraphFirstStrategy to strategies dict
- Update answer generation for graph results
- Handle GraphPath in responses

---

### **Phase 4: Real Data Testing** (1-2 hours)
Files:
- `test_graph_real_data_e2e.py` (400+ lines)

Tests:
- Relationship queries
- Comparative queries
- Multi-hop traversal
- Performance validation

---

## 🚀 **Total Effort Estimate**

**Time**: 7-10 hours  
**Code**: ~1,500 lines (production + tests)  
**Tests**: 35-40 new tests

---

## ✅ **Benefits of Graph-First**

1. **Semantic Understanding** ✅
   - Understands entity relationships
   - Discovers non-obvious connections
   - Explains causality

2. **Explainability** ✅
   - Shows HOW entities are connected
   - Provides evidence (paper_ids)
   - Traces reasoning path

3. **Discovery** ✅
   - Find indirect connections
   - Discover related concepts
   - Explore knowledge graph

4. **Precision** ✅
   - Specific to query entities
   - Relationship-aware
   - Context-preserved

---

## 🎓 **Key Differences from Vector Search**

| Aspect | Vector-First | Graph-First |
|--------|--------------|-------------|
| **Input** | Query text | Query entities |
| **Process** | Embedding similarity | Graph traversal |
| **Output** | Similar documents | Entity paths + documents |
| **Best for** | Factual queries | Relationship queries |
| **Speed** | Fast (~3s) | Medium (~4-6s) |
| **Explainability** | Score only | Full path shown |
| **Discovery** | Similar content | Connected concepts |

---

## 📋 **Preparation Checklist**

Before we start implementing:

✅ **Database Ready**:
- [x] Entities collection with indexes
- [x] Relationships collection with indexes
- [x] EntityCollection helper methods available
- [x] RelationshipCollection helper methods available

✅ **Models Ready**:
- [x] Entity model defined
- [x] Relationship model defined
- [x] GraphPath model defined
- [x] QuerySource model defined

✅ **Infrastructure Ready**:
- [x] BaseRetrievalStrategy abstract class
- [x] RetrievalService integration point
- [x] Database connection established

✅ **Testing Framework Ready**:
- [x] pytest configured
- [x] Async testing working
- [x] Mocking patterns established

---

## 🚀 **Ready to Start!**

Everything we need is in place. The knowledge graph is built, tested, and validated through the GraphRAG pipeline.

**Recommended Approach** (Incremental, with explanations):

1. **Session 1**: Graph Traversal Service
   - Build entity matching
   - Implement BFS
   - Test thoroughly
   
2. **Session 2**: Graph-First Strategy
   - Build orchestration
   - Implement query types
   - Integration tests
   
3. **Session 3**: Integration & Testing
   - Connect to RetrievalService
   - Test with real data
   - Validate results

Each session will be explained step-by-step, just like we did with Vector-First! 🎓

---

**Ready to start with Phase 1: Graph Traversal Service?**



