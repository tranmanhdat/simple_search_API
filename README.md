# Employee Search Directory API (DEMO purpose only)

A FastAPI-based microservice for searching an employee directory with PostgreSQL database, comprehensive filtering, pagination, and custom rate limiting. Optimized for large datasets (4M+ records).

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL Database** - Production-ready relational database with advanced indexing
- **Advanced Search** - Search by name, department, position, location, and status with pagination
- **Large Dataset Support** - Optimized for 4 million+ records with composite and pattern indexes
- **Custom Rate Limiting** - 30 requests per minute per IP (custom implementation, no external libraries)
- **Comprehensive Tests** - 19 unit tests with 100% pass rate
- **OpenAPI Documentation** - Auto-generated interactive API docs (OpenAPI 3.0)
- **Docker Support** - Fully containerized application with PostgreSQL container
- **Performance Script** - Bulk insert script for populating and testing with millions of records

## Table Schema

The `employees` table includes the following columns:

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key (auto-increment) |
| first_name | String | Employee's first name |
| last_name | String | Employee's last name |
| contact_info | String | Contact information (JSON string with phone, email, etc.) |
| department | String | Department name |
| position | String | Job position/title |
| location | String | Work location |
| status | Integer | Employee status: 0 (Active), 1 (Not started), 2 (Terminated) |

## Installation

### Docker with PostgreSQL

**Prerequisites:**
- Docker
- Docker Compose

**Quick Start:**

```bash
# Clone the repository
git clone https://github.com/tranmanhdat/simple_search_API.git
cd simple_search_API

# Build and run with Docker Compose (includes PostgreSQL)
docker-compose up --build

# The services will start:
# - PostgreSQL database on port 5432
# - API service on port 8000
```

The API will be available at `http://localhost:8000`
PostgreSQL will be available at `localhost:5432` (credentials: postgres/postgres)

## API Documentation

Once the server is running, you can access:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

```http
GET /
```

Returns API status and version information.

**Rate Limit:** 30 requests/minute (shared across all endpoints)

### Search Employees

```http
GET /employees/
```

Search and filter employees with multiple parameters and pagination support.

**Query Parameters:**

- `name` (optional): Search in first_name and last_name (partial match, case-insensitive)
- `department` (optional): Filter by exact department name
- `position` (optional): Filter by exact position
- `location` (optional): Filter by exact location
- `status` (optional, default="all"): Filter by status
  - Single value: `0`, `1`, or `2`
  - Multiple values: `0,1` or `0,1,2`
  - All statuses: `all`
- `limit` (optional, default=100, max=1000): Maximum number of results to return
- `offset` (optional, default=0): Number of results to skip (for pagination)

**Examples:**

```bash
# Get all active employees (status 1), first 100 results
GET /employees/?status=1

# Get employees with status 0 or 1, with pagination
GET /employees/?status=0,1&limit=50&offset=100

# Search by name
GET /employees/?name=John

# Filter by department with limit
GET /employees/?department=Engineering&limit=200

# Combined filters
GET /employees/?department=Engineering&location=New York&status=1

# Search by name in Engineering department with active status
GET /employees/?name=Smith&department=Engineering&status=1

# Pagination example - get next page
GET /employees/?limit=100&offset=100
```

**Rate Limit:** 30 requests/minute (shared across all endpoints)

## Populating the Database

A high-performance bulk insert script is provided to populate the PostgreSQL database with millions of records for testing.

### Running the Insert Script

**With Docker Compose:**
```bash
# Ensure containers are running
docker-compose up -d

# Run the script inside the API container
docker-compose exec api python3 insert_employees.py

# Or with custom parameters
docker-compose exec api python3 insert_employees.py 1000000 10000
```


## Rate Limiting

The API implements a **custom rate limiting system** (no external libraries) that tracks requests per IP address:

- **Limit**: 30 requests per minute per IP address
- **Scope**: Applies to all API endpoints
- **Implementation**: In-memory counter that tracks request timestamps
- **Response**: Returns HTTP `429 Too Many Requests` when limit is exceeded

The rate limiter automatically cleans up old request records to prevent memory bloat. This is a simple but effective implementation suitable for moderate traffic volumes.
The custom rate limiter is configured in `app/main.py`. To change the limit:

```python
# In app/main.py
rate_limiter = RateLimiter(max_requests=30)  # Change to your desired limit
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

This generates a coverage report in `htmlcov/index.html`.

### Run Specific Test Class

```bash
pytest tests/test_api.py::TestSearchEmployees
```

### Run with Verbose Output

```bash
pytest -v
```

## Project Structure

```
simple_search_API/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and endpoints
│   ├── database.py       # Database models and configuration
│   └── schemas.py        # Pydantic schemas for request/response
├── tests/
│   ├── __init__.py
│   └── test_api.py       # Comprehensive unit tests
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore           # Git ignore patterns
```

## License

This project is for demonstration purposes only.