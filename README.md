# Interview Coach API

A production-ready service that conducts adaptive interviews by ingesting CV/JD + role/industry/company, running an intelligent interview loop, and generating comprehensive evaluation reports.

## Features

- **Adaptive Interview Loop**: Uses LangGraph state machine for intelligent question flow
- **AI-Powered Evaluation**: Rule-based + LLM-as-judge scoring with detailed rubrics
- **Document Processing**: CV/JD ingestion with PDF/text extraction and normalization
- **Vector Search**: pgvector integration for semantic document retrieval
- **Real-time Processing**: Redis + RQ for asynchronous job processing
- **Production Ready**: JWT auth, rate limiting, CORS, Sentry hooks, OpenTelemetry

## Quick Start

### Prerequisites
- Docker & Docker Compose
- MongoDB Atlas account (or local MongoDB)
- Make (optional, for convenience commands)

### Development Setup

1. **Clone and setup**:
```bash
git clone <your-repo>
cd interview-coach-api
```

2. **Configure environment**:
```bash
# Update .env with your MongoDB Atlas URI
MONGO_URI=mongodb+srv://your-user:your-password@cluster.mongodb.net/ai-interview?retryWrites=true&w=majority
```

3. **Start the stack**:
```bash
docker-compose up -d
```

4. **Initialize MongoDB**:
```bash
docker-compose exec api python -m scripts.init_mongo
```

5. **Access services**:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json
- Health: http://localhost:8000/healthz

### Example Usage

#### 1. Create a Session
```bash
curl -X POST "http://localhost:8080/v1/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "role": "Senior Backend Engineer",
    "industry": "Technology",
    "company": "TechCorp Inc"
  }'
```

#### 2. Upload CV/JD (if needed)
```bash
# Upload CV
curl -X POST "http://localhost:8080/v1/uploads/cv" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/cv.pdf"

# Upload JD
curl -X POST "http://localhost:8080/v1/uploads/jd" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/jd.pdf"
```

#### 3. Get Next Question
```bash
curl -X GET "http://localhost:8080/v1/sessions/{session_id}/next-question" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. Submit Answer
```bash
curl -X POST "http://localhost:8080/v1/sessions/{session_id}/answer" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "question_uuid",
    "text": "My answer text here"
  }'
```

#### 5. Get Session Report
```bash
curl -X GET "http://localhost:8080/v1/sessions/{session_id}/report" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Redis + RQ    │    │  MongoDB Atlas  │
│   (Port 8000)   │◄──►│   (Port 6379)   │◄──►│   (Cloud)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  LangGraph      │    │  Background     │    │  Beanie ODM     │
│  Interview      │    │  Workers        │    │  Vector Search  │
│  State Machine  │    │  (Scoring)      │    │  Collections    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
interview-coach-api/
├── apps/
│   ├── api/                 # FastAPI application
│   │   ├── app.py          # Main app entry point
│   │   ├── routers/        # API route handlers
│   │   └── deps/           # Dependencies (auth, etc.)
│   └── worker/             # Background job workers
│       ├── jobs.py         # RQ job definitions
│       └── queue.py        # Queue management
├── core/                   # Core business logic
│   ├── config.py          # Configuration management
│   ├── db.py              # Database connection
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   └── prompts/           # LLM prompt templates
├── ingest/                 # Document processing
│   ├── extract.py         # PDF/text extraction
│   └── normalize.py       # CV/JD normalization
├── rag/                    # Retrieval Augmented Generation
│   ├── embed.py           # Embedding generation
│   └── store_pgvector.py  # Vector storage
├── interview/              # Interview logic
│   ├── graph.py           # LangGraph state machine
│   ├── question.py        # Question generation
│   ├── followup.py        # Follow-up logic
│   └── evaluate/          # Evaluation system
│       ├── rules.py       # Rule-based scoring
│       └── judge.py       # LLM-as-judge
├── infra/docker/           # Docker configurations
├── alembic/                # Database migrations
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── docker-compose.yml      # Development stack
├── Makefile                # Development commands
└── requirements.txt        # Python dependencies
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
MONGO_URI=mongodb+srv://your-user:your-password@cluster.mongodb.net/ai-interview?retryWrites=true&w=majority
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Settings
API_V1_STR=/v1
PROJECT_NAME=Interview Coach API
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# LLM Settings
GROQ_API_KEY=your-groq-api-key
LLM_MODEL=llama-3.1-8b-instant

# Embeddings
EMBEDDINGS_MODEL=local  # or 'openai', 'cohere', etc.
```

## Development

### Running Tests
```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=apps --cov=core --cov=interview

# Run specific test file
docker-compose exec api pytest tests/test_api.py -v
```

### Database Operations
```bash
# Initialize MongoDB indexes and collections
docker-compose exec api python -m scripts.init_mongo

# Run data migration from PostgreSQL (if needed)
docker-compose exec api python -m scripts.migrate_to_mongo
```

### Code Quality
```bash
# Format code
docker-compose exec api black .
docker-compose exec api isort .

# Lint code
docker-compose exec api flake8 .
docker-compose exec api mypy .

# Run all quality checks
make quality
```

## API Endpoints

### Authentication
- `POST /v1/auth/login` - Login and get JWT token
- `POST /v1/auth/register` - Register new user

### Sessions
- `POST /v1/sessions` - Create new interview session
- `GET /v1/sessions/{id}` - Get session details
- `GET /v1/sessions/{id}/next-question` - Get next question
- `POST /v1/sessions/{id}/answer` - Submit answer
- `GET /v1/sessions/{id}/report` - Get session report
- `GET /v1/sessions/{id}/stream` - Stream session updates (SSE)

### Uploads
- `POST /v1/uploads/cv` - Upload CV document
- `POST /v1/uploads/jd` - Upload job description

### Health
- `GET /healthz` - Health check endpoint

## Production Deployment

### Docker Production Build
```bash
docker build -f infra/docker/Dockerfile.api -t interview-coach-api:latest .
```

### Environment Setup
- Set production environment variables
- Configure external PostgreSQL and Redis
- Set up proper SSL/TLS certificates
- Configure reverse proxy (nginx/traefik)
- Set up monitoring and alerting

### Scaling
- Scale API instances horizontally
- Use Redis Cluster for high availability
- Implement database connection pooling
- Set up load balancing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
