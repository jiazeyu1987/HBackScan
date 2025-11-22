# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
│   ├── main.py                     # FastAPI application entry (39KB)
│   ├── db.py                       # Database operations layer (32KB)
│   ├── llm_client.py               # DashScope LLM integration (14KB)
│   ├── tasks.py                    # Async task management system (25KB)
│   ├── schemas.py                  # Pydantic data models (11KB)
│   ├── start_frontend.py           # Frontend launcher script
│   ├── frontend/                   # Web frontend interface
│   │   └── scanner_test.html       # HTML test interface (47KB)
│   └── tests/                      # Source-code-level tests
├── tests/                          # Root-level test suite
│   ├── conftest.py                 # Root-level test fixtures (19KB)
│   ├── helpers.py                  # Test utility functions
│   └── test_*.py                   # Contract, acceptance, integration tests
├── config/                         # Configuration files (Redis, etc.)
├── data/                           # Database storage
├── logs/                           # Application logs
├── docs/                           # Comprehensive documentation
├── examples/                       # Usage examples
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
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Configure environment variables
cp .env.example .env
# Edit .env file with your DASHSCOPE_API_KEY
```

### Database Operations
```bash
# Initialize database
python -c "from db import init_db; init_db()"

# Or use the Makefile
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

# From code/hospital_scanner - full service stack
cd code/hospital_scanner
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

### Code Quality
```bash
make lint               # Run linting
make format             # Format code with black/isort
make type-check         # Run mypy type checking
make clean              # Clean generated files
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
DASHSCOPE_API_KEY=your-api-key-here

# Optional
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DB_PATH=data/hospitals.db
MAX_CONCURRENT_TASKS=5
```

### Docker Configuration
- Development: `docker-compose.yml`
- Production: `docker-compose.prod.yml`
- Health checks and automatic restarts configured
- Volume mounts for data persistence

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
- `docker-compose.prod.yml` - Production Docker setup
- `Dockerfile` - Container image definition
- `Makefile` - Development commands and utilities with colorized output
- `pytest.ini` - Comprehensive pytest configuration with coverage and markers

### Testing
- `tests/` - Root-level test suite (contract, acceptance, integration)
- `code/hospital_scanner/tests/` - Source-level test suite (unit, API integration)
- `tests/conftest.py` - Root-level test fixtures and configuration (19KB)
- `tests/helpers.py` - Test utility functions
- `requirements-dev.txt` - Comprehensive development dependencies (195 lines)

### Scripts
- `start.sh` - Development server startup
- `deploy.sh` - Production deployment automation
- `install.sh` - System service installation
- `backup.sh` - Database backup utilities

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

# Database inspection
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

## Testing Infrastructure

The project has a sophisticated testing setup with extensive configuration:

### Test Configuration (pytest.ini)
- Comprehensive marker system for test categorization
- Coverage reporting with HTML and XML output
- Configurable log levels and output formats
- Performance tracking with duration reporting
- Branch coverage analysis with 80% minimum threshold

### Test Dependencies (requirements-dev.txt)
- **Core Testing**: pytest, pytest-cov, pytest-xdist, pytest-asyncio
- **Performance Testing**: locust, memory-profiler, psutil
- **Code Quality**: black, isort, flake8, mypy, bandit
- **Mocking**: factory-boy, faker, responses
- **Documentation**: sphinx, mkdocs
- **Security**: semgrep, OWASP ZAP

### Coverage Configuration
- HTML reports in `htmlcov/` directory
- XML reports for CI/CD integration
- LCOV format for advanced coverage analysis
- Exclusion patterns for non-production code
- Branch coverage with precision reporting