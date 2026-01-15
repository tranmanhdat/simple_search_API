# Employee Search Directory API

A FastAPI-based microservice for managing and searching an employee directory with SQLite database, comprehensive filtering, and custom rate limiting.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 💾 **SQLite Database** - Lightweight, serverless database
- 🔍 **Advanced Search** - Search by name, department, position, location, and status
- 🛡️ **Custom Rate Limiting** - 30 requests per minute per IP (custom implementation, no external libraries)
- ✅ **Comprehensive Tests** - 25 unit tests with 100% pass rate
- 📝 **OpenAPI Documentation** - Auto-generated interactive API docs (OpenAPI 3.0)
- 🐳 **Docker Support** - Fully containerized application

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

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker
- Docker Compose

**Quick Start:**

```bash
# Clone the repository
git clone https://github.com/tranmanhdat/simple_search_API.git
cd simple_search_API

# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t employee-search-api .
docker run -p 8000:8000 employee-search-api
```

The API will be available at `http://localhost:8000`

### Option 2: Local Installation

**Prerequisites:**
- Python 3.8 or higher
- pip (Python package manager)

**Setup:**

1. Clone the repository:
```bash
git clone https://github.com/tranmanhdat/simple_search_API.git
cd simple_search_API
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Development Server

Start the development server with hot reload:

```bash
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
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```http
GET /
```

Returns API status and version information.

### Create Employee

```http
POST /employees/
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "contact_info": "{\"phone\": \"123-456-7890\", \"email\": \"john.doe@example.com\"}",
  "department": "Engineering",
  "position": "Software Engineer",
  "location": "New York",
  "status": 1
}
```

**Rate Limit:** 30 requests/minute (shared across all endpoints)

### Get Employee

```http
GET /employees/{employee_id}
```

Retrieve a specific employee by ID.

**Rate Limit:** 30 requests/minute (shared across all endpoints)

### Update Employee

```http
PUT /employees/{employee_id}
```

Update an existing employee. All fields are optional.

**Request Body:**
```json
{
  "position": "Senior Software Engineer",
  "status": 2
}
```

**Rate Limit:** 30 requests/minute (shared across all endpoints)

### Delete Employee

```http
DELETE /employees/{employee_id}
```

Delete an employee by ID.

**Rate Limit:** 30 requests/minute (shared across all endpoints)

### Search Employees

```http
GET /employees/
```

Search and filter employees with multiple parameters.

**Query Parameters:**

- `name` (optional): Search in first_name and last_name (partial match, case-insensitive)
- `department` (optional): Filter by exact department name
- `position` (optional): Filter by exact position
- `location` (optional): Filter by exact location
- `status` (optional, default="all"): Filter by status
  - Single value: `0`, `1`, or `2`
  - Multiple values: `0,1` or `0,1,2`
  - All statuses: `all`

**Examples:**

```bash
# Get all active employees (status 1)
GET /employees/?status=1

# Get employees with status 0 or 1
GET /employees/?status=0,1

# Search by name
GET /employees/?name=John

# Filter by department
GET /employees/?department=Engineering

# Combined filters
GET /employees/?department=Engineering&location=New York&status=1

# Search by name in Engineering department with active status
GET /employees/?name=Smith&department=Engineering&status=1
```

**Rate Limit:** 30 requests/minute (shared across all endpoints)

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
