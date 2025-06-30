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

[TODO: Add your architecture decisions and explanations here]

## How RAG Works

[TODO: Add your explanation of how the RAG system works here]

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
