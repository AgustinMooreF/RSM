# Asset comments

- Since I’m still gaining experience with Python, my decisions in the code are a mix of self-study and assistance from Cursor.
- The same goes for frameworks like LangChain—fortunately, it shares many similarities with Masta IA, which I’ve worked with the most.
- I applied the Singleton pattern in the FastAPI implementation based on my experience with NestJS for performance reasons. It was a great opportunity to learn about concepts like lru_cache, pydantic, and asynccontextmanager to achieve this.
- Apologies in advance if some parts of the repo are a bit messy. I’m very open to learning more about Python best practices, as well as best practices in Generative AI.


# RAG Microservice

A Python-based Retrieval-Augmented Generation (RAG) microservice built with FastAPI, featuring document processing with PDF support, vector search with ChromaDB, and OpenAI integration.

## Features

- 📄 Multi-format document ingestion (text, HTML, markdown, PDF)
- 📤 File upload support for PDFs
- 🔍 Vector search with ChromaDB
- 🧠 OpenAI embeddings integration
- 🐳 Docker containerization
- 🔒 Type safety with Python type hints

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### Setup

1. **Clone and configure**
```bash
git clone <repository-url>
cd RSM
cp env.example .env
```

2. **Set your OpenAI API key in `.env`**
```env
OPENAI_API_KEY=your_openai_api_key_here
```

3. **Run with Docker**
```bash
docker-compose up --build
```

4. **Test the service**
```bash
# Check health
curl http://localhost:8000/api/v1/health

# Ingest a document
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Sample text about AI", "document_type": "text"}'
```

Service available at: **http://localhost:8000**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service information |
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/ingest` | Ingest text/URL documents |
| `POST` | `/api/v1/ingest/file` | Upload PDF files |

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing with Postman

### 1. Health Check
```
GET http://localhost:8000/api/v1/health
```

### 2. Text Document Ingestion
```
POST http://localhost:8000/api/v1/ingest
Content-Type: application/json

{
  "content": "Your document content here",
  "document_type": "text"
}
```

### 3. PDF File Upload
```
POST http://localhost:8000/api/v1/ingest/file
Content-Type: multipart/form-data

Form data:
- file: [your PDF file]
- document_type: "pdf"
```

### Expected Response
```json
{
  "status": "success",
  "message": "Successfully ingested document with 5 chunks",
  "chunks_created": 5,
  "document_info": {
    "type": "text",
    "original_length": 234
  }
}
```

## Local Development

```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your_key_here"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

-	Singleton pattern applied to class instances, improving memory usage and performance by ensuring only one instance of each required class runs at a time.
-	Project structure follows a service–model–controller pattern for better organization and maintainability.
-	Local ChromaDB is used for quick setup and development. For production, changes will be needed to ensure persistence—especially if deploying with technologies like Kubernetes.
- Langfuse is used for observability, as it was the easiest to implement based on my initial and short research.

## How RAG Works

- Supports both files and URLs.
- Accepted file types: .html, .md, .txt, and .pdf.
- Chunk size and overlap are configurable via the .env file (default: 500 and 200, respectively).
- Uses ChromaDB for vector storage.
- The default embedding model is text-embedding-3-small from OpenAI, but this can be changed based on performance needs.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `OPENAI_MODEL` | ❌ | "gpt-4o-mini" | OpenAI model |
| `CHUNK_SIZE` | ❌ | 1000 | Document chunk size |
| `CHUNK_OVERLAP` | ❌ | 200 | Chunk overlap size |

## Project Structure

```
app/
├── api/                    # FastAPI endpoints
│   ├── endpoints/          # Route handlers
│   └── router.py          # Route organization
├── core/                  # Configuration
├── models/                # Pydantic schemas
├── services/              # Business logic
├── utils/                 # Utilities
└── main.py               # FastAPI app
```

## Dependencies

```
fastapi==0.115.14
chromadb==0.4.18
openai>=1.6.1,<2.0.0
pdfplumber==0.10.3
beautifulsoup4==4.12.2
langchain==0.1.0
```

## Troubleshooting

**Missing OpenAI API key:**
```bash
export OPENAI_API_KEY="your_key_here"
```

**Permission errors:**
```bash
chmod 755 ./chroma_db
```

**Module not found:**
```bash
pip install -r requirements.txt
```

---

**Built with FastAPI, ChromaDB, and OpenAI**
