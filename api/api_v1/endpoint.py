from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
sys.path.append("..")
from database.database import get_db, Employee
from database.schemas import EmployeeResponse
from rate_limit_custom.rate_limit import RateLimiter, check_rate_limit

router = APIRouter()

@router.get("/", tags=["Health"])
async def root(request: Request, _: None = Depends(check_rate_limit)):
    """Root endpoint for health check."""
    return {
        "message": "Employee Search Directory API",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/employees/", response_model=List[EmployeeResponse], tags=["Search"])
async def search_employees(
    request: Request,
    name: Optional[str] = Query(None, description="Search by first name or last name"),
    department: Optional[str] = Query(None, description="Filter by department"),
    position: Optional[str] = Query(None, description="Filter by position"),
    location: Optional[str] = Query(None, description="Filter by location"),
    status: str = Query("all", description="Filter by status: 0, 1, 2, all, or comma-separated like '0,1'"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit),
):
    """
    Search employees with various filters.
    
    - **name**: Search in first_name and last_name (partial match, case-insensitive)
    - **department**: Exact match for department
    - **position**: Exact match for position
    - **location**: Exact match for location
    - **status**: Filter by status - can be "0", "1", "2", "all", or comma-separated like "0,1" or "0,1,2"
    - **limit**: Maximum number of results (default: 100, max: 1000)
    - **offset**: Skip this many results (for pagination)
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

    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    employees = query.all()
    logger.info(f"Search returned {len(employees)} employees")
    return employees
