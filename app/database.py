from sqlalchemy import create_engine, Column, Integer, String, Index
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./employees.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    # Performance optimizations for SQLite
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    contact_info = Column(String, nullable=False)  # JSON string for phone, email, etc.
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    status = Column(Integer, nullable=False)  # 0, 1, or 2

    # Composite indexes for common search patterns
    __table_args__ = (
        Index('idx_status_department', 'status', 'department'),
        Index('idx_status_location', 'status', 'location'),
        Index('idx_department_position', 'department', 'position'),
        Index('idx_first_name', 'first_name'),
        Index('idx_last_name', 'last_name'),
        Index('idx_status', 'status'),
        Index('idx_department', 'department'),
        Index('idx_position', 'position'),
        Index('idx_location', 'location'),
    )


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    
    # Enable SQLite performance optimizations
    with engine.connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.commit()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
