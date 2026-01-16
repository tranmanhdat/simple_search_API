import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, rate_limiter
from app.database import Base, get_db, Employee
import json
import os

# Create test database (use SQLite for tests for simplicity, but can use PostgreSQL too)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_employees.db")

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL test database
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Disable rate limiting during tests except for rate limiting tests
@pytest.fixture(autouse=True)
def disable_rate_limit():
    """Disable rate limiting for tests by setting a very high limit."""
    # Store original value from the rate_limiter in app.main
    original = rate_limiter.max_requests
    rate_limiter.max_requests = 999999
    rate_limiter.requests.clear()
    yield
    rate_limiter.max_requests = original
    rate_limiter.requests.clear()


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def populate_test_data(test_db):
    """Populate test database with sample employees."""
    db = TestingSessionLocal()
    
    employees = [
        Employee(
            first_name="Alice",
            last_name="Smith",
            contact_info=json.dumps({"phone": "111-111-1111", "email": "alice@example.com"}),
            department="Engineering",
            position="Senior Engineer",
            location="New York",
            status=1,
        ),
        Employee(
            first_name="Bob",
            last_name="Johnson",
            contact_info=json.dumps({"phone": "222-222-2222", "email": "bob@example.com"}),
            department="Sales",
            position="Sales Manager",
            location="San Francisco",
            status=0,
        ),
        Employee(
            first_name="Charlie",
            last_name="Williams",
            contact_info=json.dumps({"phone": "333-333-3333", "email": "charlie@example.com"}),
            department="Engineering",
            position="Junior Engineer",
            location="New York",
            status=2,
        ),
        Employee(
            first_name="Diana",
            last_name="Brown",
            contact_info=json.dumps({"phone": "444-444-4444", "email": "diana@example.com"}),
            department="HR",
            position="HR Manager",
            location="Chicago",
            status=1,
        ),
    ]
    
    for emp in employees:
        db.add(emp)
    db.commit()
    db.close()


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"


class TestSearchEmployees:
    """Test employee search functionality."""

    def test_search_all_employees(self, client, populate_test_data):
        """Test retrieving all employees."""
        response = client.get("/employees/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # We created 4 employees

    def test_search_by_status_single(self, client, populate_test_data):
        """Test searching by single status."""
        response = client.get("/employees/?status=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Diana have status 1
        for employee in data:
            assert employee["status"] == 1

    def test_search_by_status_multiple(self, client, populate_test_data):
        """Test searching by multiple statuses."""
        response = client.get("/employees/?status=0,1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Alice (1), Bob (0), and Diana (1)
        for employee in data:
            assert employee["status"] in [0, 1]

    def test_search_by_status_all(self, client, populate_test_data):
        """Test searching with status=all."""
        response = client.get("/employees/?status=all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_search_by_invalid_status(self, client, populate_test_data):
        """Test searching with invalid status."""
        response = client.get("/employees/?status=5")
        assert response.status_code == 400

    def test_search_by_department(self, client, populate_test_data):
        """Test searching by department."""
        response = client.get("/employees/?department=Engineering")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Charlie
        for employee in data:
            assert employee["department"] == "Engineering"

    def test_search_by_position(self, client, populate_test_data):
        """Test searching by position."""
        response = client.get("/employees/?position=Sales Manager")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Bob"

    def test_search_by_location(self, client, populate_test_data):
        """Test searching by location."""
        response = client.get("/employees/?location=New York")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Charlie

    def test_search_by_name_first(self, client, populate_test_data):
        """Test searching by first name."""
        response = client.get("/employees/?name=Alice")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Alice"

    def test_search_by_name_last(self, client, populate_test_data):
        """Test searching by last name."""
        response = client.get("/employees/?name=Brown")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_name"] == "Brown"

    def test_search_by_name_partial(self, client, populate_test_data):
        """Test searching by partial name match."""
        response = client.get("/employees/?name=illi")  # Matches Williams
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_name"] == "Williams"

    def test_search_combined_filters(self, client, populate_test_data):
        """Test searching with multiple filters combined."""
        response = client.get(
            "/employees/?department=Engineering&location=New York&status=1"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only Alice matches all criteria
        assert data[0]["first_name"] == "Alice"

    def test_search_no_results(self, client, populate_test_data):
        """Test search that returns no results."""
        response = client.get("/employees/?department=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_pagination_limit(self, client, populate_test_data):
        """Test pagination with limit parameter."""
        response = client.get("/employees/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_pagination_offset(self, client, populate_test_data):
        """Test pagination with offset parameter."""
        # Get all employees first
        all_response = client.get("/employees/?limit=100")
        all_data = all_response.json()
        
        # Get with offset
        offset_response = client.get("/employees/?offset=2&limit=100")
        offset_data = offset_response.json()
        
        assert len(offset_data) == len(all_data) - 2

    def test_pagination_limit_max(self, client, populate_test_data):
        """Test that limit cannot exceed maximum."""
        response = client.get("/employees/?limit=2000")
        assert response.status_code == 422  # Validation error


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def enable_rate_limit(self):
        """Enable rate limiting for specific tests."""
        rate_limiter.max_requests = 30
        rate_limiter.requests.clear()
        yield
        rate_limiter.max_requests = 999999
        rate_limiter.requests.clear()

    def test_rate_limit_enforcement(self, client, enable_rate_limit):
        """Test that rate limiting is enforced."""
        # Make multiple requests to trigger rate limit (limit is 30/minute)
        responses = []
        for _ in range(35):
            response = client.get("/employees/")
            responses.append(response.status_code)

        # At least one request should be rate limited (429)
        assert 429 in responses
        # Count successful and rate-limited responses
        successful = responses.count(200)
        rate_limited = responses.count(429)
        assert successful == 30  # First 30 should succeed
        assert rate_limited == 5  # Last 5 should be rate limited

    def test_rate_limit_applies_to_all_endpoints(self, client, enable_rate_limit):
        """Test that rate limiting applies to all endpoints."""
        responses = []
        for i in range(35):
            if i % 2 == 0:
                response = client.get("/")
            else:
                response = client.get("/employees/")
            responses.append(response.status_code)
        
        # Should have some rate limited responses
        assert 429 in responses
