import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, limiter
from app.database import Base, get_db
import json

# Create test database
TEST_DATABASE_URL = "sqlite:///./test_employees.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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
    """Disable rate limiting for tests."""
    limiter.enabled = False
    yield
    limiter.enabled = True


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
def sample_employee():
    """Sample employee data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "contact_info": json.dumps({"phone": "123-456-7890", "email": "john.doe@example.com"}),
        "department": "Engineering",
        "position": "Software Engineer",
        "location": "New York",
        "status": 1,
    }


@pytest.fixture
def sample_employees():
    """Multiple sample employees for testing search."""
    return [
        {
            "first_name": "Alice",
            "last_name": "Smith",
            "contact_info": json.dumps({"phone": "111-111-1111", "email": "alice@example.com"}),
            "department": "Engineering",
            "position": "Senior Engineer",
            "location": "New York",
            "status": 1,
        },
        {
            "first_name": "Bob",
            "last_name": "Johnson",
            "contact_info": json.dumps({"phone": "222-222-2222", "email": "bob@example.com"}),
            "department": "Sales",
            "position": "Sales Manager",
            "location": "San Francisco",
            "status": 0,
        },
        {
            "first_name": "Charlie",
            "last_name": "Williams",
            "contact_info": json.dumps({"phone": "333-333-3333", "email": "charlie@example.com"}),
            "department": "Engineering",
            "position": "Junior Engineer",
            "location": "New York",
            "status": 2,
        },
        {
            "first_name": "Diana",
            "last_name": "Brown",
            "contact_info": json.dumps({"phone": "444-444-4444", "email": "diana@example.com"}),
            "department": "HR",
            "position": "HR Manager",
            "location": "Chicago",
            "status": 1,
        },
    ]


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


class TestCreateEmployee:
    """Test employee creation."""

    def test_create_employee_success(self, client, sample_employee):
        """Test successful employee creation."""
        response = client.post("/employees/", json=sample_employee)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == sample_employee["first_name"]
        assert data["last_name"] == sample_employee["last_name"]
        assert data["department"] == sample_employee["department"]
        assert data["status"] == sample_employee["status"]
        assert "id" in data

    def test_create_employee_invalid_status(self, client, sample_employee):
        """Test employee creation with invalid status."""
        sample_employee["status"] = 5  # Invalid status
        response = client.post("/employees/", json=sample_employee)
        assert response.status_code == 422  # Validation error

    def test_create_employee_missing_field(self, client, sample_employee):
        """Test employee creation with missing required field."""
        del sample_employee["first_name"]
        response = client.post("/employees/", json=sample_employee)
        assert response.status_code == 422


class TestGetEmployee:
    """Test getting employee by ID."""

    def test_get_employee_success(self, client, sample_employee):
        """Test successful retrieval of employee."""
        # First create an employee
        create_response = client.post("/employees/", json=sample_employee)
        employee_id = create_response.json()["id"]

        # Then retrieve it
        response = client.get(f"/employees/{employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == employee_id
        assert data["first_name"] == sample_employee["first_name"]

    def test_get_employee_not_found(self, client):
        """Test retrieval of non-existent employee."""
        response = client.get("/employees/99999")
        assert response.status_code == 404


class TestUpdateEmployee:
    """Test employee update."""

    def test_update_employee_success(self, client, sample_employee):
        """Test successful employee update."""
        # Create an employee
        create_response = client.post("/employees/", json=sample_employee)
        employee_id = create_response.json()["id"]

        # Update the employee
        update_data = {"position": "Senior Software Engineer", "status": 2}
        response = client.put(f"/employees/{employee_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == update_data["position"]
        assert data["status"] == update_data["status"]
        # Original fields should remain unchanged
        assert data["first_name"] == sample_employee["first_name"]

    def test_update_employee_not_found(self, client):
        """Test update of non-existent employee."""
        update_data = {"position": "Manager"}
        response = client.put("/employees/99999", json=update_data)
        assert response.status_code == 404


class TestDeleteEmployee:
    """Test employee deletion."""

    def test_delete_employee_success(self, client, sample_employee):
        """Test successful employee deletion."""
        # Create an employee
        create_response = client.post("/employees/", json=sample_employee)
        employee_id = create_response.json()["id"]

        # Delete the employee
        response = client.delete(f"/employees/{employee_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/employees/{employee_id}")
        assert get_response.status_code == 404

    def test_delete_employee_not_found(self, client):
        """Test deletion of non-existent employee."""
        response = client.delete("/employees/99999")
        assert response.status_code == 404


class TestSearchEmployees:
    """Test employee search functionality."""

    @pytest.fixture(autouse=True)
    def setup_employees(self, client, sample_employees):
        """Create multiple employees before each test."""
        for employee in sample_employees:
            client.post("/employees/", json=employee)

    def test_search_all_employees(self, client):
        """Test retrieving all employees."""
        response = client.get("/employees/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4  # We created 4 employees

    def test_search_by_status_single(self, client):
        """Test searching by single status."""
        response = client.get("/employees/?status=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Diana have status 1
        for employee in data:
            assert employee["status"] == 1

    def test_search_by_status_multiple(self, client):
        """Test searching by multiple statuses."""
        response = client.get("/employees/?status=0,1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # Alice (1), Bob (0), and Diana (1)
        for employee in data:
            assert employee["status"] in [0, 1]

    def test_search_by_status_all(self, client):
        """Test searching with status=all."""
        response = client.get("/employees/?status=all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_search_by_invalid_status(self, client):
        """Test searching with invalid status."""
        response = client.get("/employees/?status=5")
        assert response.status_code == 400

    def test_search_by_department(self, client):
        """Test searching by department."""
        response = client.get("/employees/?department=Engineering")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Charlie
        for employee in data:
            assert employee["department"] == "Engineering"

    def test_search_by_position(self, client):
        """Test searching by position."""
        response = client.get("/employees/?position=Sales Manager")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Bob"

    def test_search_by_location(self, client):
        """Test searching by location."""
        response = client.get("/employees/?location=New York")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Alice and Charlie

    def test_search_by_name_first(self, client):
        """Test searching by first name."""
        response = client.get("/employees/?name=Alice")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Alice"

    def test_search_by_name_last(self, client):
        """Test searching by last name."""
        response = client.get("/employees/?name=Brown")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_name"] == "Brown"

    def test_search_by_name_partial(self, client):
        """Test searching by partial name match."""
        response = client.get("/employees/?name=illi")  # Matches Williams
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_name"] == "Williams"

    def test_search_combined_filters(self, client):
        """Test searching with multiple filters combined."""
        response = client.get(
            "/employees/?department=Engineering&location=New York&status=1"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Only Alice matches all criteria
        assert data[0]["first_name"] == "Alice"

    def test_search_no_results(self, client):
        """Test search that returns no results."""
        response = client.get("/employees/?department=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def enable_rate_limit(self):
        """Enable rate limiting for specific tests."""
        limiter.enabled = True
        yield
        limiter.enabled = False

    def test_rate_limit_enforcement(self, client, sample_employee, enable_rate_limit):
        """Test that rate limiting is enforced."""
        # Make multiple requests to trigger rate limit
        # Note: This is a basic test. In production, you might want more sophisticated testing
        responses = []
        for _ in range(25):  # Limit is 20/minute for create
            response = client.post("/employees/", json=sample_employee)
            responses.append(response.status_code)

        # At least one request should be rate limited (429)
        assert 429 in responses

    def test_rate_limit_different_endpoints(self, client, enable_rate_limit):
        """Test that different endpoints have independent rate limits."""
        # Health endpoint has 100/minute limit
        for _ in range(10):
            response = client.get("/")
            assert response.status_code == 200
