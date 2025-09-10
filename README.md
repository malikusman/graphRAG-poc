# SageWrite GraphRAG

A Graph-based Retrieval-Augmented Generation system for scientific papers, built with FastAPI, React, and MongoDB.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Poetry (for local development)

### Using Docker (Recommended)

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd sagewrite-app
   cp env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
sagewrite-app/
├── docker-compose.yml
├── .env
├── pyproject.toml
├── README.md
│
├── app/                    # Main backend application
│   ├── Dockerfile
│   ├── main.py            # FastAPI app entry point
│   ├── core/              # Core configurations and settings
│   ├── models/            # Pydantic/MongoDB models
│   ├── api/               # FastAPI routes
│   ├── services/          # Business logic services
│   ├── tasks/             # Celery tasks
│   ├── pipelines/         # LangGraph pipelines
│   ├── utils/             # Utility functions
│   ├── prompts/           # LLM prompts
│   ├── configs/           # Configuration files
│   └── tests/             # Test files
│
└── frontend/              # React frontend
    ├── Dockerfile
    ├── package.json
    ├── public/
    └── src/
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: ^0.115.6 - Modern, fast web framework
- **LangChain**: ^0.3.20 - LLM application framework
- **LangGraph**: ^0.3.5 - Graph-based workflows
- **Celery**: ^5.3.4 - Distributed task queue
- **MongoDB**: Latest with Motor for async operations
- **Redis**: Latest for caching and message broker

### Frontend
- **React**: ^18.2.0 - UI library
- **Tailwind CSS**: ^3.3.0 - Utility-first CSS
- **React Query**: ^3.39.0 - Data fetching
- **React Router**: ^6.8.0 - Routing

## 🔧 Development

### Local Development

1. **Install dependencies**
   ```bash
   poetry install
   ```

2. **Start services**
   ```bash
   docker-compose up mongodb redis
   ```

3. **Run backend**
   ```bash
   cd app
   poetry run uvicorn main:app --reload
   ```

4. **Run frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 📋 Development Status

This is a Proof of Concept (POC) implementation.

✅ **Completed:**
- Clean project structure
- Docker containerization
- FastAPI backend with health checks
- React frontend setup
- MongoDB and Redis integration
- Celery task queue setup

🚧 **Next Steps:**
- Document processing pipeline
- Entity and relationship extraction
- GraphRAG implementation
- Vector search integration

## 📝 License

MIT License