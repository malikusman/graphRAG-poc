# SageWrite GraphRAG

[![CI Pipeline](https://github.com/malikusman/graphRAG-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/malikusman/graphRAG-poc/actions/workflows/ci.yml)

A comprehensive Graph-based Retrieval-Augmented Generation system for scientific papers, built with FastAPI, LangGraph, and MongoDB. This system processes documents through an 8-node pipeline to extract entities and relationships, builds a knowledge graph, and provides intelligent search capabilities through multiple retrieval strategies.

## 🎯 What This Application Does

SageWrite GraphRAG is an intelligent document processing and search system that:

1. **Processes Scientific Documents**: Extracts text from PDFs, segments into sections, and generates embeddings
2. **Builds Knowledge Graphs**: Extracts entities (genes, methods, diseases) and relationships using LLM-powered analysis
3. **Enables Smart Search**: Provides semantic search, graph traversal, and hybrid retrieval strategies
4. **Integrates External APIs**: Fetches and processes data from external scientific APIs
5. **Resolves Contradictions**: Detects and resolves conflicting information across documents

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   GraphRAG       │    │   MongoDB       │
│   (API Layer)   │◄──►│   Pipeline       │◄──►│   (Database)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────▼──────┐
                       │   Celery    │
                       │  (Tasks)    │
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │   Redis     │
                       │ (Message    │
                       │  Broker)    │
                       └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (for containerized setup)
- **Poetry** (for Python dependency management)
- **OpenAI API Key** (for LLM processing)

### Using Docker (Recommended)

1. **Clone and setup**
   ```bash
   git clone https://github.com/malikusman/graphRAG-poc.git
   cd graphRAG-poc
   cp env.example .env
   # Edit .env with your OpenAI API key: OPENAI_API_KEY=your_key_here
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

### Local Development Setup

1. **Install Python dependencies**
   ```bash
   poetry install
   ```

2. **Start infrastructure services**
   ```bash
   docker-compose up mongodb redis -d
   ```

3. **Run backend**
   ```bash
   cd app
   poetry run uvicorn main:app --reload
   ```

## 📁 Project Structure

```
sagewrite-app/
├── docker-compose.yml          # Multi-service Docker setup
├── .env                        # Environment variables
├── pyproject.toml              # Python dependencies
│
├── app/                        # Backend Application
│   ├── main.py                 # FastAPI application entry point
│   ├── core/                   # Core configurations
│   │   ├── config.py           # Application settings
│   │   └── database.py         # MongoDB connection
│   ├── models/                 # Data models
│   │   ├── entities.py         # Entity definitions and types
│   │   ├── relationships.py    # Relationship models and types
│   │   └── query_models.py     # Query/response models
│   ├── api/                    # API endpoints
│   │   ├── documents.py        # Document upload/management
│   │   ├── queries.py          # Search endpoints
│   │   └── endpoints/          # Feature-specific endpoints
│   │       └── api_integration.py  # External API integration
│   ├── services/               # Core business logic services
│   │   ├── retrieval_service.py        # Main query orchestration
│   │   ├── query_analysis_service.py   # Query understanding with LLM
│   │   ├── vector_search_service.py    # Semantic similarity search
│   │   ├── graph_traversal_service.py  # Knowledge graph navigation
│   │   ├── embeddings.py               # OpenAI embeddings service
│   │   ├── api_data_adapter.py         # External API data fetching
│   │   ├── entity_canonicalizer.py     # Entity deduplication and merging
│   │   ├── contradiction_detector.py   # Contradiction identification
│   │   ├── relationship_consolidator.py # Relationship merging
│   │   ├── global_graph_manager.py     # Global knowledge graph management
│   │   └── retrieval_strategies/       # Search strategy implementations
│   │       ├── base_strategy.py        # Abstract base class
│   │       ├── vector_first_strategy.py # Semantic search strategy
│   │       ├── graph_first_strategy.py  # Graph traversal strategy
│   │       └── hybrid_strategy.py      # Combined approach
│   ├── pipelines/              # Processing pipelines
│   │   └── graphrag_pipeline.py        # 8-node LangGraph workflow
│   ├── tasks/                  # Background processing tasks
│   │   ├── processing_tasks.py         # Document processing
│   │   └── api_processing_tasks.py     # API data processing
│   ├── prompts/                # LLM prompts for different phases
│   │   ├── map/                        # Entity/relationship extraction
│   │   ├── reduce/                     # Canonicalization and consolidation
│   │   └── orchestrator/               # Query analysis
│   ├── configs/                # Configuration files
│   │   └── schemas/                    # Entity categories and relationship types
│   └── utils/                  # Utility functions
│       ├── math_utils.py               # Noisy-OR calculations
│       └── vector_utils.py             # Vector similarity operations
```

## 🔄 How the GraphRAG Pipeline Works

### 1. Document Processing Pipeline (8-Node LangGraph Workflow)

The core of the system is an 8-node LangGraph pipeline that processes documents through Map-Combine-Reduce phases:

**Map Phase (Nodes 1-2):**
- **Node 1 - Entity Extraction**: Uses LLM to extract entities (genes, methods, diseases) from document sections with canonical names, types, and descriptions
- **Node 2 - Relationship Extraction**: Identifies relationships between entities using controlled vocabulary and calculates relationship strength

**Combine Phase (Nodes 3-4):**
- **Node 3 - Entity Combination**: Merges duplicate entities within documents, combines aliases, and selects best descriptions
- **Node 4 - Relationship Combination**: Consolidates relationships within documents using noisy-OR aggregation and combines provenance

**Reduce Phase (Nodes 5-7):**
- **Node 5 - Entity Canonicalization**: Merges entities across documents using stable identifiers (MeSH, HGNC) and similarity matching
- **Node 6 - Contradiction Detection**: Identifies conflicting relationships and applies resolution strategies
- **Node 7 - Relationship Consolidation**: Merges relationships across documents with evidence aggregation

**Update Phase (Node 8):**
- **Node 8 - Global Graph Update**: Updates the global knowledge graph with canonicalized entities and consolidated relationships

### 2. Query Processing & Retrieval

**Query Analysis**: User queries are analyzed by an LLM to determine intent (factual, exploratory, comparative), complexity, and optimal retrieval strategy.

**Strategy Selection**: The system intelligently chooses between Vector-First (semantic similarity), Graph-First (entity traversal), or Hybrid (combined) strategies based on query characteristics.

**Result Generation**: Retrieved information is synthesized into comprehensive answers with source citations, confidence scores, and graph traversal paths when relevant.

### 3. External API Integration

**Data Fetching**: The system fetches scientific data from external APIs, filters for valid content, and processes through the same GraphRAG pipeline.

**Background Processing**: API data processing runs asynchronously using Celery tasks, allowing for scalable processing of large datasets.

#### Notes → Entity Relationships API

The `/api/v1/notes/entity-relationships` endpoint fetches raw note chunks from the external `document-vectors` API, cleans them with an LLM-powered prompt, and runs the GraphRAG pipeline per `document_id`.

- **Fetch**: Uses `NOTES_API_*` settings to authenticate and page through note chunks.
- **Clean**: Applies the `preprocess/text_chunk_cleaning.json` prompt to discard noisy data before pipeline processing.
- **Process**: Runs the `graphrag_pipeline_notes` workflow on cleaned chunks, returning entities, relationships, and discarded-chunk metadata per document.
- **Configure**: Override the noise threshold via `TEXT_CHUNK_NOISE_THRESHOLD` or the request body.
- **Inspect**: Set `include_discarded_chunks=false` to omit discarded-chunk summaries from the response.

## 🛠️ Technology Stack

### Backend Services
- **FastAPI**: Modern, high-performance web framework for building APIs with automatic OpenAPI documentation
- **LangChain**: Framework for developing LLM-powered applications with chain-based processing and memory management
- **LangGraph**: Graph-based workflow framework for building stateful, multi-actor applications with LLMs
- **Celery**: Distributed task queue system for handling background processing and asynchronous operations
- **MongoDB**: Document-based NoSQL database for storing documents, entities, relationships, and embeddings
- **Redis**: In-memory data store used as message broker for Celery and caching layer for improved performance

### AI/ML Components
- **LLM Providers**: Supports multiple providers via abstraction layer
  - **OpenAI**: GPT-4, GPT-4o-mini (default)
  - **Amazon Bedrock**: Claude models via langchain-aws
  - **Google Vertex AI**: Gemini models via custom wrapper (see [VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md))
- **Embedding Providers**: Supports multiple embedding models
  - **OpenAI**: text-embedding-3-small (default)
  - **Amazon Bedrock**: Titan embeddings
  - **Google Vertex AI**: textembedding-gecko models
- **NumPy**: Numerical computing library for vector similarity calculations and mathematical operations

### Provider Switching
The application uses a provider abstraction layer that allows seamless switching between different LLM and embedding providers. Switch providers by setting environment variables:

```bash
# Use Bedrock for both LLM and embeddings
LLM_PROVIDER=bedrock
EMBEDDING_PROVIDER=bedrock

# Or mix and match (e.g., Bedrock for LLM, OpenAI for embeddings)
LLM_PROVIDER=bedrock
EMBEDDING_PROVIDER=openai

# Use Vertex AI
LLM_PROVIDER=vertexai
EMBEDDING_PROVIDER=vertexai
```

See `env.example` for complete configuration options for each provider.

**Provider Compatibility Notes:**
- **AWS Bedrock**: Uses `langchain-aws` package (v0.2.35+) which internally manages `boto3`. Supports multiple authentication methods (env vars, IAM roles, `~/.aws/credentials`). Model access must be enabled in Bedrock console.
- **Google Vertex AI**: Uses custom wrapper with `google-cloud-aiplatform` SDK. Requires service account JSON key or Application Default Credentials. Models must be enabled in Vertex AI Model Garden for API access.
- Both providers include comprehensive error handling with specific messages for common issues (authentication, model access, region configuration).

## 🎛️ Core Services

### **GraphRAG Pipeline Service**
Implements the core 8-node Map-Combine-Reduce workflow using LangGraph. Extracts entities and relationships from text sections, merges duplicates within documents, canonicalizes across the entire knowledge base, and updates the global graph.

### **Entity Canonicalizer Service**
Deduplicates and merges entities across documents using stable identifiers (MeSH, HGNC, UniProt) and similarity matching. Handles alias merging, description selection, and provenance consolidation for consistent entity representation.

### **Contradiction Detector Service**
Identifies conflicting relationships between the same entity pairs using LLM-powered analysis. Detects contradictions like "X causes Y" vs "X prevents Y" and provides resolution strategies based on evidence strength and context.

### **Relationship Consolidator Service**
Merges relationships across documents using noisy-OR aggregation and evidence counting. Groups relationships by entity pairs and types, calculates consolidated strength scores, and tracks supporting evidence from multiple sources.

### **Global Graph Manager Service**
Manages the global knowledge graph state across all documents with caching and incremental updates. Coordinates entity canonicalization, contradiction resolution, and relationship consolidation to maintain graph consistency.

### **Query Analysis Service**
Uses LLM-powered analysis to understand user queries, extract entities, determine intent (factual, exploratory, comparative, causal, temporal) and complexity, and recommend the optimal retrieval strategy for each specific query.

### **Retrieval Service**
Orchestrates the query processing pipeline by selecting and executing appropriate retrieval strategies. Coordinates between vector search, graph traversal, and hybrid approaches to deliver comprehensive results with confidence scoring.

### **Vector Search Service**
Implements semantic similarity search using OpenAI embeddings and manual cosine similarity calculation. Finds contextually relevant content by comparing query embeddings with document section embeddings stored in MongoDB.

### **Graph Traversal Service**
Navigates the knowledge graph using breadth-first search algorithms with bounded traversal (2-3 hops). Finds paths between entities, scores relationships based on strength and type, and enables multi-hop reasoning for complex queries.

### **API Data Adapter Service**
Integrates with external scientific APIs to fetch and process data. Handles authentication, data transformation, filtering for valid content, and prepares external data for processing through the GraphRAG pipeline.

### **Embeddings Service**
Generates vector embeddings using OpenAI's text-embedding-3-small model. Handles text truncation, batch processing, and embedding dimension management for semantic similarity calculations.

## 🔍 API Endpoints

### Document Management
- `POST /documents/upload` - Upload and process PDF documents through GraphRAG pipeline
- `GET /documents` - List all documents with processing status
- `GET /documents/{id}` - Get document details and processing results
- `DELETE /documents/{id}` - Remove document and associated graph data

### Search & Retrieval
- `POST /search` - Perform GraphRAG queries with intelligent strategy selection
- `GET /entities` - List entities in the knowledge graph with filtering
- `GET /relationships` - List relationships between entities with filtering


## 🧪 Testing

### Run Tests

**Unit Tests:**
```bash
poetry run pytest
```

**Provider Integration Tests:**
```bash
# Test Vertex AI integration
poetry run python test_vertexai_integration.py

# Test AWS Bedrock integration
poetry run python test_bedrock_integration.py
```

**Additional Tests:**
```bash
# Backend tests
cd app
poetry run pytest

# Test GraphRAG pipeline with single section
python test_single_section_db.py
```

## 🚀 Deployment

### Production Setup
1. Configure environment variables in `.env`
2. Set up MongoDB Atlas for production database
3. Configure Redis for message queuing
4. Deploy using Docker Compose or Kubernetes

### Environment Variables
   ```bash
# Required
OPENAI_API_KEY=your_openai_api_key
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# LLM & Embedding Provider Selection
# Default: Both use OpenAI. Set these to switch providers:
LLM_PROVIDER=openai              # Options: "openai", "bedrock", "vertexai"
EMBEDDING_PROVIDER=openai         # Options: "openai", "bedrock", "vertexai"

# AWS Bedrock Configuration (if using Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Google Vertex AI Configuration (if using Vertex AI)
VERTEX_AI_PROJECT_ID=your-google-cloud-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_CREDENTIALS_PATH=/path/to/service-account-key.json
VERTEX_AI_MODEL_ID=gemini-pro
VERTEX_AI_EMBEDDING_MODEL_ID=textembedding-gecko@003

# Optional
EXTERNAL_API_TOKEN=your_api_token
EXTERNAL_API_BASE_URL=https://writing-api.sagewrite.com
EXTERNAL_API_MAX_SECTIONS=5
EXTERNAL_API_MIN_TEXT_LENGTH=50

# Notes ingestion & cleaning
NOTES_API_TOKEN=your_notes_api_token
NOTES_API_BASE_URL=https://writing-api.sagewrite.com
NOTES_API_ENDPOINT=/document-vectors/
NOTES_API_PAGE_SIZE=200
TEXT_CHUNK_NOISE_THRESHOLD=0.7
```

## 📊 Performance & Scalability

- **Vector Search**: Optimized for up to 10,000 documents with sub-second response times using manual cosine similarity
- **Graph Traversal**: Bounded to 2-3 hops to prevent runaway expansions with cycle detection
- **Background Processing**: Asynchronous task processing with Celery for scalable document handling
- **Entity Canonicalization**: Efficient merging using stable identifiers and similarity matching
- **Caching**: Redis-based caching for frequently accessed graph data and query results

## 🔧 Git Workflow

This project follows a professional Git workflow:

- **`main`** - Production-ready code
- **`develop`** - Integration branch for features
- **`feature/*`** - Feature development branches
- **`hotfix/*`** - Emergency fixes

### Quick Start
```bash
# Clone and setup
git clone https://github.com/malikusman/graphRAG-poc.git
cd graphRAG-poc

# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: your feature description"
git push -u origin feature/your-feature-name
```

## 📋 Development Status

### ✅ Completed Features
- **Complete GraphRAG Pipeline**: 8-node LangGraph workflow with entity/relationship extraction
- **Entity Canonicalization**: Stable identifier support with MeSH, HGNC, UniProt integration
- **Contradiction Detection**: LLM-powered conflict identification and resolution
- **Relationship Consolidation**: Noisy-OR aggregation with evidence tracking
- **Intelligent Retrieval System**: Vector-First, Graph-First, and Hybrid strategies
- **External API Integration**: Seamless processing of external scientific data
- **Production-Ready Architecture**: Docker containerization, async processing, error handling
- **Comprehensive API**: RESTful endpoints with OpenAPI documentation

### 🚧 Future Enhancements
- **MongoDB Atlas Vector Search**: Upgrade to native vector search capabilities
- **Advanced Answer Generation**: LLM-powered answer synthesis from retrieved sources
- **Graph Visualization**: Interactive knowledge graph exploration interface
- **Performance Optimization**: Query caching and result pre-computation

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the test files for usage examples