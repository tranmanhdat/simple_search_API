from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
from contextlib import asynccontextmanager
import logging

from app.database import get_db, init_db, Employee
from app.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown (if needed)
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Employee Search Directory API",
    description="A FastAPI microservice for managing and searching employee directory",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/", tags=["Health"])
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint for health check."""
    return {
        "message": "Employee Search Directory API",
        "version": "1.0.0",
        "status": "running",
    }


@app.post(
    "/employees/",
    response_model=EmployeeResponse,
    status_code=201,
    tags=["Employees"],
)
@limiter.limit("20/minute")
async def create_employee(
    request: Request, employee: EmployeeCreate, db: Session = Depends(get_db)
):
    """Create a new employee."""
    db_employee = Employee(**employee.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    logger.info(f"Created employee with ID: {db_employee.id}")
    return db_employee


@app.get("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"])
@limiter.limit("50/minute")
async def get_employee(request: Request, employee_id: int, db: Session = Depends(get_db)):
    """Get a specific employee by ID."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.put("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"])
@limiter.limit("20/minute")
async def update_employee(
    request: Request,
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing employee."""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = employee_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_employee, field, value)

    db.commit()
    db.refresh(db_employee)
    logger.info(f"Updated employee with ID: {employee_id}")
    return db_employee


@app.delete("/employees/{employee_id}", status_code=204, tags=["Employees"])
@limiter.limit("20/minute")
async def delete_employee(request: Request, employee_id: int, db: Session = Depends(get_db)):
    """Delete an employee."""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(db_employee)
    db.commit()
    logger.info(f"Deleted employee with ID: {employee_id}")
    return None


@app.get("/employees/", response_model=List[EmployeeResponse], tags=["Employees"])
@limiter.limit("50/minute")
async def search_employees(
    request: Request,
    name: Optional[str] = Query(None, description="Search by first name or last name"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status: str = Query("all", description="Filter by status: 0, 1, 2, all, or comma-separated like '0,1'"),
    db: Session = Depends(get_db),
):
    """
    Search employees with various filters.
    
    - **name**: Search in first_name and last_name (partial match, case-insensitive)
    - **department**: Exact match for department
    - **position**: Exact match for position
    - **location**: Exact match for location
    - **status**: Filter by status - can be "0", "1", "2", "all", or comma-separated like "0,1" or "0,1,2"
    """
    query = db.query(Employee)

    # Filter by status
    if status.lower() != "all":
        try:
            # Parse status values (support comma-separated)
            status_values = [int(s.strip()) for s in status.split(",")]
            # Validate status values
            for s in status_values:
                if s not in [0, 1, 2]:
                    raise ValueError(f"Invalid status value: {s}")
            query = query.filter(Employee.status.in_(status_values))
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status parameter. Must be 0, 1, 2, all, or comma-separated values. Error: {str(e)}",
            )

    # Filter by name (search in both first_name and last_name)
    if name:
        search_pattern = f"%{name}%"
        query = query.filter(
            (Employee.first_name.ilike(search_pattern))
            | (Employee.last_name.ilike(search_pattern))
        )

    # Filter by other exact match fields
    if department:
        query = query.filter(Employee.department == department)

    if position:
        query = query.filter(Employee.position == position)

    if location:
        query = query.filter(Employee.location == location)

    employees = query.all()
    logger.info(f"Search returned {len(employees)} employees")
    return employees
