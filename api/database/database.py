from sqlalchemy import create_engine, Column, Integer, String, Index, Text, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
import os

# PostgreSQL connection URL
# Format: postgresql://username:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/employees_db"
)

# Create engine with connection pooling optimizations for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Number of connections to maintain
    max_overflow=10,           # Additional connections when pool is exhausted
    pool_pre_ping=True,        # Verify connections before using them
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    contact_info = Column(Text, nullable=False)  # JSON string for phone, email, etc.
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(Integer, nullable=False)  # 0, 1, or 2

    # Composite indexes for common search patterns - PostgreSQL performs better with these
    __table_args__ = (
        # Primary key index on id is automatic
        # Single-column indexes for individual filters
        Index('idx_first_name', 'first_name'),
        Index('idx_last_name', 'last_name'),
        Index('idx_status', 'status'),
        Index('idx_department', 'department'),
        Index('idx_position', 'position'),
        Index('idx_location', 'location'),
        # Composite indexes for frequently combined filters
        Index('idx_status_department', 'status', 'department'),
        Index('idx_status_location', 'status', 'location'),
        Index('idx_status_department_location', 'status', 'department', 'location'),
        Index('idx_department_position', 'department', 'position'),
        # B-tree indexes for text search patterns (PostgreSQL)
        # text_pattern_ops for LIKE 'prefix%' queries
        Index('idx_first_name_pattern', 'first_name', postgresql_ops={'first_name': 'text_pattern_ops'}),
        Index('idx_last_name_pattern', 'last_name', postgresql_ops={'last_name': 'text_pattern_ops'}),
    )


def init_db():
    """Initialize the database by creating all tables and optimizations."""
    Base.metadata.create_all(bind=engine)
    
    # PostgreSQL-specific optimizations
    with engine.connect() as conn:
        # Analyze tables for query optimizer statistics
        conn.execute(text("ANALYZE employees"))
        conn.commit()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

