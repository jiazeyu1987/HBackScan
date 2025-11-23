# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 一定要遵守的规则（非常重要）
不能随意更换端口，如果有被占用的端口，停止占用的进程
尽量多的写日志（存入log文件），方便调试
代码的注释用英文不要用中午呢
不要用虚假数据，不要硬编码
实事求是，不要粉饰太平，有错误即使暴露，有问题及时反馈
不要总结好的，要总结只总结问题

## Project Overview

This is a **Hospital Hierarchy Scanner Microservice** (医院层级扫查微服务) - a FastAPI-based service that manages hierarchical hospital data across four levels: provinces, cities, districts, and hospitals. The system uses Alibaba's DashScope LLM API for intelligent data acquisition and SQLite for data persistence.

## Core Architecture

### Key Components

1. **FastAPI Application** (`main.py`): RESTful API server with comprehensive endpoints
2. **Database Layer** (`db.py`): SQLite database with hierarchical data management
3. **LLM Client** (`llm_client.py`): DashScope API client with multi-level prompt templates
4. **Task Management** (`tasks.py`): Asynchronous task system with progress tracking
5. **Data Models** (`schemas.py`): Pydantic models for request/response validation

### Project Structure

The project follows a dual-directory structure with comprehensive testing infrastructure:

```
HBackScan/
├── code/hospital_scanner/          # Main application code
│   ├── main.py                     # FastAPI application entry
│   ├── db.py                       # Database operations layer
│   ├── llm_client.py               # DashScope LLM integration
│   ├── tasks.py                    # Async task management system
│   ├── schemas.py                  # Pydantic data models
│   ├── start_frontend.py           # Frontend launcher script
│   ├── frontend/                   # Web frontend interface
│   │   └── scanner_test.html       # HTML test interface
│   └── tests/                      # Source-code-level tests
├── tests/                          # Root-level test suite
│   ├── conftest.py                 # Root-level test fixtures
│   ├── helpers.py                  # Test utility functions
│   └── test_*.py                   # Contract, acceptance, integration tests
├── data/                           # Database storage
├── logs/                           # Application logs
├── htmlcov/                        # Coverage reports
├── reports/                        # Test reports and documentation
└── deployment files                # Docker, scripts, etc.
```

### Frontend Interface

The project includes a modern web-based frontend with Chinese localization:

- **HTML Interface**: `code/hospital_scanner/frontend/scanner_test.html`
- **Launcher Script**: `start_frontend.py` - automatically opens browser
- **Features**: Real-time status monitoring, modern UI, result visualization
- **Access**: Run `python start_frontend.py` from the `code/hospital_scanner` directory

### Data Hierarchy
```
Province (省份)
  └── City (城市)
      └── District (区县)
          └── Hospital (医院)
```

## Common Development Commands

### Environment Setup
```bash
# Install dependencies (from project root)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Configure environment variables
cp .env.example .env
# Edit .env file with your DASHSCOPE_API_KEY

# Alternative: Use code/hospital_scanner/.env.example
cp code/hospital_scanner/.env.example code/hospital_scanner/.env
```

### Database Operations
```bash
# Initialize database (from code/hospital_scanner)
cd code/hospital_scanner
python -c "from db import init_db; init_db()"

# Or use the Makefile (from project root)
make db-init
```

### Running the Application

**Development Mode:**
```bash
# Navigate to main application directory
cd code/hospital_scanner

# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Using the start script (from project root)
chmod +x start.sh
./start.sh

# Using Makefile (from project root)
make start

# Launch frontend interface (from code/hospital_scanner)
python start_frontend.py
```

**Docker Mode:**
```bash
# From project root - basic Docker setup
docker-compose up -d

# Production deployment
./deploy.sh
make deploy-prod
```

### Testing Commands

**Run All Tests:**
```bash
make test
pytest tests/ -v
```

**Specific Test Categories:**
```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-smoke         # Quick smoke tests
make test-acceptance    # Full acceptance tests
make test-coverage      # Generate coverage report
```

**Debug Testing:**
```bash
make test-debug         # Verbose output with debugging
pytest tests/ -v -s --capture=no --tb=long
```

### Single Test Execution
```bash
# Run specific test file (from project root)
pytest tests/test_main.py -v

# Run specific test file (from code/hospital_scanner)
pytest code/hospital_scanner/tests/test_main.py -v

# Run specific test function
pytest tests/test_main.py::test_health_check -v

# Run tests with specific markers
pytest tests/ -m "unit" -v
pytest tests/ -m "integration" -v
pytest tests/ -m "not slow" -v
```

## API Architecture

### Core Endpoints

**Data Refresh:**
- `POST /refresh/all` - Full data refresh
- `POST /refresh/province/{province_name}` - Province-specific refresh

**Data Query:**
- `GET /provinces` - List provinces (paginated)
- `GET /cities?province={name}` - Cities by province
- `GET /districts?city={name}` - Districts by city
- `GET /hospitals?district={name}` - Hospitals by district
- `GET /hospitals/search?q={keyword}` - Hospital search

**Task Management:**
- `GET /tasks/{task_id}` - Task status
- `GET /tasks/active` - Active tasks
- `DELETE /tasks/{task_id}` - Cancel task
- `POST /tasks/cleanup` - Clean old tasks

**System:**
- `GET /health` - Health check
- `GET /statistics` - Data statistics
- `GET /docs` - Swagger documentation

### Response Format
All endpoints return standardized responses:
```json
{
  "code": 200,
  "message": "Success message",
  "data": { ... }
}
```

## Database Schema

### Tables
- `province` - Provincial data
- `city` - City data with foreign key to province
- `district` - District data with foreign key to city
- `hospital` - Hospital data with foreign key to district
- `task` - Task tracking and management

### Key Database Methods
- `upsert_*` methods handle insert/update operations
- Pagination support for all list methods
- Foreign key relationships maintain data integrity
- Search functionality with LIKE queries

## Task Management System

### Task Types
- **Full Refresh**: Complete hierarchy refresh starting from provinces
- **Province Refresh**: Targeted refresh for specific provinces

### Task Status Flow
`PENDING` → `RUNNING` → `SUCCEEDED/FAILED`

### Progress Tracking
- Real-time progress updates (0-100%)
- Current step descriptions
- Error tracking and reporting
- Concurrent task limiting (default: 5)

## LLM Integration

### DashScope Client Features
- Multi-level prompt templates for each hierarchy level
- Automatic retry mechanism with exponential backoff
- Response parsing and validation
- JSON structure enforcement
- Proxy support for corporate environments

### Prompt Hierarchy
- Province level: Returns all provinces
- City level: Cities within specified province
- District level: Districts within specified city
- Hospital level: Hospitals within specified district

## Configuration

### Environment Variables (.env)
```bash
# Required
DASHSCOPE_API_KEY=your-dashscope-api-key-here

# Optional
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DATABASE_PATH=data/hospitals.db
MAX_CONCURRENT_TASKS=5
TASK_CLEANUP_HOURS=24
```

### Docker Configuration
- Development: `docker-compose.yml`
- Health checks and automatic restarts configured
- Volume mounts for data persistence (`./data:/app/data`, `./logs:/app/logs`)

## Development Patterns

### Error Handling
- Global exception handler in `main.py`
- Comprehensive logging throughout the application
- Database transaction rollback on errors
- Graceful degradation for LLM API failures

### Async Patterns
- All database operations are synchronous
- LLM calls and task execution are asynchronous
- Background task processing with progress tracking
- Semaphore-based concurrency control

### Testing Strategy

**Dual Test Structure:**
- **Root-level tests** (`tests/`): Contract tests, acceptance tests, integration tests
- **Source-level tests** (`code/hospital_scanner/tests/`): Unit tests, API integration tests

**Test Types:**
- Unit tests for individual components
- Integration tests for API endpoints
- Acceptance tests for complete workflows
- Contract tests for API consistency
- Performance tests for load testing
- Mock LLM responses for reliable testing
- Database fixtures for consistent test data

**Test Categories (pytest.ini):**
- `unit`: Individual component tests
- `integration`: System integration tests
- `acceptance`: End-to-end workflow tests
- `performance`: Load and stress tests
- `fast`: Quick tests for development
- `slow`: Comprehensive tests that take longer
- `contract`: API contract validation tests
- `database`: Database-dependent tests
- `network`: Tests requiring network access
- `api`: API-related tests
- `llm`: LLM-related tests
- `mock`: Tests using mock data
- `smoke`: Quick validation tests
- `regression`: Regression tests
- `security`: Security tests
- `schema`: Schema validation tests

## Important Files

### Core Application
- `code/hospital_scanner/main.py` - FastAPI application and routing
- `code/hospital_scanner/db.py` - Database operations and management
- `code/hospital_scanner/llm_client.py` - DashScope LLM integration
- `code/hospital_scanner/tasks.py` - Async task management system
- `code/hospital_scanner/schemas.py` - Pydantic data models
- `code/hospital_scanner/start_frontend.py` - Frontend launcher script
- `code/hospital_scanner/frontend/scanner_test.html` - Web-based test interface

### Configuration & Deployment
- `.env.example` - Environment variable template
- `docker-compose.yml` - Development Docker setup
- `Makefile` - Development commands and utilities with colorized output
- `pytest.ini` - Comprehensive pytest configuration with coverage and markers
- `start.sh` - Development server startup script

### Testing
- `tests/` - Root-level test suite (contract, acceptance, integration)
- `code/hospital_scanner/tests/` - Source-level test suite (unit, API integration)
- `tests/conftest.py` - Root-level test fixtures and configuration
- `tests/helpers.py` - Test utility functions
- `requirements-dev.txt` - Comprehensive development dependencies (195 lines)

## Troubleshooting

### Common Issues
1. **API Key Errors**: Verify `DASHSCOPE_API_KEY` is set correctly
2. **Database Issues**: Ensure `data/` directory exists and is writable
3. **Network Issues**: Configure proxy settings if behind corporate firewall
4. **Task Failures**: Check logs for LLM API rate limits or network issues

### Debug Commands
```bash
# Check service health
curl http://localhost:8000/health

# View application logs
docker-compose logs -f
tail -f logs/scanner.log
tail -f logs/ai_debug.log

# Database inspection (from project root)
sqlite3 data/hospitals.db ".tables"
sqlite3 data/hospitals.db "SELECT COUNT(*) FROM hospital;"

# Test frontend interface
cd code/hospital_scanner
python start_frontend.py

# Run specific component tests
pytest code/hospital_scanner/tests/test_llm_client.py -v -s
pytest tests/test_contracts.py -v
```

### Performance Monitoring
- Task progress tracking via API endpoints
- Database query optimization with indexes
- Concurrent task limiting to prevent API rate limiting
- Comprehensive logging for performance analysis
- Frontend real-time status updates and result visualization
- Health check endpoints for monitoring system status