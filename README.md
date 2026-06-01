# AuraEcho Distributed Backend Services

This repository contains the decoupled microservices backend architecture powering the AuraEcho analytical core. It utilizes a dual-layer strategy separating high-throughput system orchestration from compute-intensive artificial intelligence processing.

## Architecture Overview

- /ai-engine : Python FastAPI AI Processing Engine
- /auraecho-api-gateway : Node.js and Express Security & Aggregation Layer

### 1. API Gateway Layer
* Technology: Node.js, Express, TypeScript, PostgreSQL Client (pg)
* Role: Acts as the primary system ingress and database entry ledger. It handles incoming requests, enforces rate limits, logs operation metadata, and aggregates microservice calls.
* Security: Implements IP rate limiting via express-rate-limit to prevent infrastructure exhaustion.

### 2. AI Processing Engine
* Technology: Python, FastAPI, Groq SDK, Pinecone Client
* Role: Executes Natural Language Understanding (NLU) tasks, coordinates structured LLM orchestration, generates vector embeddings, and executes spatial semantic searches.
* Observability: Integrated with LangSmith for real-time traceability, evaluating prompt structures, token volumes, and execution latency.

## Data Layer Integrations

* Relational Storage: Neon serverless PostgreSQL for robust, transactional application records.
* Vector Database: Pinecone for managing contextual mathematical vector metrics for memory queries.

## Local Infrastructure Configuration

### API Gateway Setup (Node.js)

1. Navigate to the gateway directory:
   cd auraecho-api-gateway

2. Install dependencies:
   npm install

3. Configure environment variables (.env):
   DATABASE_URL="your_neon_postgresql_connection_string"

4. Start the server:
   npx ts-node src/server.ts
   (Listens on Port 5000)

### AI Processing Engine Setup (Python)

1. Navigate to the engine directory:
   cd ai-engine

2. Initialize and activate a virtual environment (.venv)

3. Install requirements:
   pip install -r requirements.txt

4. Configure environment variables (.env):
   GROQ_API_KEY="your_groq_api_credential"
   PINECONE_API_KEY="your_pinecone_vector_db_credential"
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY="your_langsmith_credential"
   LANGCHAIN_PROJECT="AuraEcho-Local-Dev"

5. Start the service:
   uvicorn main:app --reload
   (Listens on Port 8000)