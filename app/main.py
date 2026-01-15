from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from app.database import get_db, init_db, Employee
from app.schemas import EmployeeResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom rate limiter implementation
class RateLimiter:
    """Simple in-memory rate limiter that tracks requests per IP per minute."""
    
    def __init__(self, max_requests: int = 30):
        self.max_requests = max_requests
        self.requests = defaultdict(list)  # IP -> list of request timestamps
        self.last_cleanup = datetime.now()
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if a request from the given IP is allowed."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean up old requests for this IP
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if timestamp > one_minute_ago
        ]
        
        # Periodically cleanup old IP entries (every 5 minutes)
        if (now - self.last_cleanup).total_seconds() > 300:
            self._cleanup_old_entries()
            self.last_cleanup = now
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True
    
    def _cleanup_old_entries(self):
        """Remove entries for IPs that haven't made requests recently (internal method)."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        ips_to_remove = []
        for ip, timestamps in list(self.requests.items()):
            # Remove old timestamps
            self.requests[ip] = [ts for ts in timestamps if ts > one_minute_ago]
            # Mark for removal if no recent requests
            if not self.requests[ip]:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self.requests[ip]


# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=30)


async def check_rate_limit(request: Request):
    """Dependency to check rate limit for incoming requests."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 30 requests per minute allowed."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    init_db()
    logger.info("Database initialized successfully")
    logger.info("Rate limiter initialized: 30 requests per minute per IP")
    yield
    # Shutdown (if needed)
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Employee Search Directory API",
    description="A FastAPI microservice for searching employee directory",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def root(request: Request, _: None = Depends(check_rate_limit)):
    """Root endpoint for health check."""
    return {
        "message": "Employee Search Directory API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/employees/", response_model=List[EmployeeResponse], tags=["Search"])
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
