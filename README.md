# Data Assistant API

**LLM-Powered Natural Language to SQL Query Generation**

A modern FastAPI application that leverages Large Language Models to convert natural language questions into SQL queries, summarize datasets, and explain complex SQL statements.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Natural Language to SQL** - Ask questions in plain English, get executable SQL
- **Data Summarization** - AI-generated insights and data quality reports
- **Query Explanation** - Understand what any SQL query does
- **Dual LLM Support** - Works with OpenAI API or local Ollama models
- **Pydantic Validation** - Robust request/response validation
- **Auto Documentation** - Interactive Swagger UI and ReDoc

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA ASSISTANT API                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   FastAPI + Pydantic + OpenAI/Ollama LLM                   │
│                                                             │
│   Features:                                                 │
│   • Natural language → SQL query generation                 │
│   • Data quality report summarization                       │
│   • Schema documentation Q&A                                │
│                                                             │
│   Endpoints:                                                │
│   POST /api/query     → "Show me top 10 customers"         │
│   POST /api/summarize → Summarize a dataset                │
│   POST /api/explain   → Explain a SQL query                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd project_data_assistant_api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and add your OpenAI API key (or configure Ollama)
```

### 3. Run the API

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Explore the API

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### POST /api/query
Convert natural language to SQL and execute.

```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me top 10 customers by total orders"}'
```

**Response:**
```json
{
  "success": true,
  "original_question": "Show me top 10 customers by total orders",
  "generated_sql": "SELECT c.name, COUNT(o.id) as order_count...",
  "explanation": "This query joins customers with orders...",
  "results": [...],
  "row_count": 10,
  "execution_time_ms": 12.5
}
```

### POST /api/summarize
Get AI-powered data quality analysis.

```bash
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{"table_name": "customers", "include_sample_data": true}'
```

### POST /api/explain
Understand what a SQL query does.

```bash
curl -X POST "http://localhost:8000/api/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "sql_query": "SELECT * FROM orders WHERE total > 100",
    "detail_level": "beginner"
  }'
```

## Sample Database

The API includes a sample e-commerce database with:

| Table | Description | Rows |
|-------|-------------|------|
| `customers` | Customer information | 15 |
| `products` | Product catalog | 15 |
| `orders` | Order headers | 100 |
| `order_items` | Order line items | ~250 |
| `inventory_logs` | Stock changes | ~80 |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM backend (`openai` or `ollama`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model name | `gpt-3.5-turbo` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama2` |
| `DATABASE_URL` | SQLite database path | `sqlite:///./data/sample.db` |

### Using Ollama (Free, Local)

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama2`
3. Set in `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama2
   ```

## Project Structure

```
project_data_assistant_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py      # Request validation models
│   │   └── responses.py     # Response models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── query.py         # /api/query endpoint
│   │   ├── summarize.py     # /api/summarize endpoint
│   │   ├── explain.py       # /api/explain endpoint
│   │   └── health.py        # Health check endpoints
│   └── services/
│       ├── __init__.py
│       ├── database.py      # SQLite operations
│       ├── llm.py           # LLM provider abstraction
│       └── init_db.py       # Sample data initialization
├── data/                    # SQLite database (auto-created)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

```bash
# Install linting tools
pip install black isort flake8

# Format code
black app/
isort app/
```

## Example Questions to Try

- "Show me top 10 customers by total orders"
- "What are the most popular products?"
- "List all pending orders"
- "Which customers haven't ordered anything?"
- "Show monthly revenue for 2024"
- "Find products with low stock"

## License

MIT License

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [OpenAI](https://openai.com/) - LLM capabilities
- [Ollama](https://ollama.ai/) - Local LLM runtime
