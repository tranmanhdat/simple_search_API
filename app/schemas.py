from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    contact_info: str = Field(..., min_length=1)  # JSON string: {"phone": "...", "email": "..."}
    department: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=100)
    status: int = Field(..., ge=0, le=2)  # Must be 0, 1, or 2


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_info: Optional[str] = Field(None, min_length=1)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[int] = Field(None, ge=0, le=2)


class EmployeeResponse(EmployeeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SearchParams(BaseModel):
    name: Optional[str] = None  # Search in first_name and last_name
    department: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "all"  # "0", "1", "2", "all", or comma-separated like "0,1"
