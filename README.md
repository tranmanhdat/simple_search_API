# Employee Search Directory API

A FastAPI-based microservice for searching an employee directory with PostgreSQL database, comprehensive filtering, pagination, and custom rate limiting. Optimized for large datasets (4M+ records).

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 💾 **PostgreSQL Database** - Production-ready relational database with advanced indexing
- 🔍 **Advanced Search** - Search by name, department, position, location, and status with pagination
- 📊 **Large Dataset Support** - Optimized for 4 million+ records with composite and pattern indexes
- 🛡️ **Custom Rate Limiting** - 30 requests per minute per IP (custom implementation, no external libraries)
- ✅ **Comprehensive Tests** - 19 unit tests with 100% pass rate
- 📝 **OpenAPI Documentation** - Auto-generated interactive API docs (OpenAPI 3.0)
- 🐳 **Docker Support** - Fully containerized application with PostgreSQL container
- ⚡ **Performance Script** - Bulk insert script for populating and testing with millions of records

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
| status | Integer | Employee status: 0 (inactive), 1 (active), 2 (on leave) |

## Installation

### Option 1: Docker with PostgreSQL (Recommended)

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

### Option 2: Local Installation with PostgreSQL

**Prerequisites:**
- Python 3.8 or higher
- PostgreSQL 12+ installed and running
- pip (Python package manager)

**Setup:**

1. Install and configure PostgreSQL:
```bash
# Create database
createdb employees_db

# Or using psql:
psql -U postgres -c "CREATE DATABASE employees_db;"
```

2. Clone the repository:
```bash
git clone https://github.com/tranmanhdat/simple_search_API.git
cd simple_search_API
```

3. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set database connection (optional, defaults to localhost):
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/employees_db"
```

## Running the Application

### Development Server

Start the development server with hot reload:

```bash
# Make sure PostgreSQL is running first
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Production Server

For production, use Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

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

**Local Installation:**
```bash
# Make sure PostgreSQL is running and DATABASE_URL is set
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/employees_db"

# Insert 4 million records (default)
python3 insert_employees.py

# Insert custom number of records
python3 insert_employees.py 1000000

# Custom records and batch size
python3 insert_employees.py 5000000 20000
```

The script includes:
- Progress monitoring with ETA
- Automatic index creation (12 indexes including composite and pattern indexes)
- PostgreSQL-specific optimizations (VACUUM ANALYZE)
- Performance testing of common queries with EXPLAIN ANALYZE
- Database statistics reporting

**Performance Characteristics:**
- Inserts ~50,000-150,000 records/second (depending on hardware)
- Uses PostgreSQL's `execute_values` for batch insertion
- Creates B-tree and text_pattern_ops indexes for optimal search performance
- Includes query performance benchmarks showing sub-millisecond response times

## Rate Limiting

The API implements a **custom rate limiting system** (no external libraries) that tracks requests per IP address:

- **Limit**: 30 requests per minute per IP address
- **Scope**: Applies to all API endpoints
- **Implementation**: In-memory counter that tracks request timestamps
- **Response**: Returns HTTP `429 Too Many Requests` when limit is exceeded

The rate limiter automatically cleans up old request records to prevent memory bloat. This is a simple but effective implementation suitable for moderate traffic volumes.

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

## Database

The application uses SQLite with the database file `employees.db` created automatically on first run. The database is excluded from version control via `.gitignore`.

For testing, a separate `test_employees.db` is created and destroyed for each test run.

## Status Codes

The employee status field uses the following integer codes:

- `0`: Inactive
- `1`: Active
- `2`: On Leave

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid query parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded

## Security Considerations

1. **Rate Limiting**: Prevents API abuse and DoS attacks
2. **Input Validation**: Pydantic schemas validate all input data
3. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
4. **Database**: SQLite file is excluded from version control

## Development

### Adding New Fields

To add new fields to the Employee model:

1. Update `app/database.py` - Add column to `Employee` model
2. Update `app/schemas.py` - Add field to Pydantic schemas
3. Update tests in `tests/test_api.py`
4. Recreate the database or use migrations

### Customizing Rate Limits

The custom rate limiter is configured in `app/main.py`. To change the limit:

```python
# In app/main.py
rate_limiter = RateLimiter(max_requests=30)  # Change to your desired limit
```

## Docker Deployment

### Building the Image

```bash
docker build -t employee-search-api .
```

### Running the Container

```bash
# Run with default settings
docker run -p 8000:8000 employee-search-api

# Run with persistent database
docker run -p 8000:8000 -v $(pwd)/data:/app/data employee-search-api
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## OpenAPI Specification

The API automatically generates an OpenAPI 3.0 specification. Access it in multiple formats:

- **JSON Format**: http://localhost:8000/openapi.json
- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

You can export the OpenAPI specification for use with API clients, documentation generators, or testing tools:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

## Troubleshooting

### Database Locked Error

If you encounter "database is locked" errors, ensure no other process is accessing the database file.

### Import Errors

Make sure you're in the project root directory and the virtual environment is activated.

### Port Already in Use

If port 8000 is in use, specify a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure they pass
5. Submit a pull request

## License

This project is for demonstration purposes only.

## Contact

For questions or support, please open an issue in the GitHub repository.
