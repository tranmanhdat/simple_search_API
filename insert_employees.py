#!/usr/bin/env python3
"""
Script to populate the employee database with 4 million records.
Includes performance testing and optimization.
"""

import sqlite3
import random
import time
import json
from datetime import datetime

# Sample data for generating realistic employee records
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Gregory", "Debra",
    "Frank", "Rachel", "Alexander", "Catherine", "Patrick", "Carolyn", "Jack", "Janet",
    "Dennis", "Ruth", "Jerry", "Maria", "Tyler", "Heather", "Aaron", "Diane"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez"
]

DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Human Resources", "Finance",
    "Operations", "Customer Support", "Product", "Legal", "IT",
    "Research & Development", "Quality Assurance", "Design", "Data Science", "Security"
]

POSITIONS = [
    "Software Engineer", "Senior Engineer", "Junior Engineer", "Team Lead", "Manager",
    "Director", "VP", "Sales Representative", "Account Manager", "Marketing Specialist",
    "HR Specialist", "Recruiter", "Financial Analyst", "Accountant", "Operations Manager",
    "Support Specialist", "Product Manager", "Legal Counsel", "System Administrator",
    "Data Analyst", "QA Engineer", "UX Designer", "Security Analyst", "DevOps Engineer",
    "Business Analyst", "Project Manager", "Consultant", "Coordinator", "Associate", "Intern"
]

LOCATIONS = [
    "New York", "San Francisco", "Los Angeles", "Chicago", "Boston",
    "Seattle", "Austin", "Denver", "Atlanta", "Miami",
    "Dallas", "Houston", "Phoenix", "Philadelphia", "San Diego",
    "Portland", "Washington DC", "Minneapolis", "Detroit", "Nashville"
]


def generate_employee_data(start_id, count):
    """Generate employee data in batches."""
    employees = []
    for i in range(count):
        employee_id = start_id + i
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Generate contact info as JSON
        contact_info = json.dumps({
            "phone": f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 9999)}@company.com"
        })
        
        department = random.choice(DEPARTMENTS)
        position = random.choice(POSITIONS)
        location = random.choice(LOCATIONS)
        status = random.choice([0, 1, 1, 1, 2])  # More active employees
        
        employees.append((
            employee_id, first_name, last_name, contact_info,
            department, position, location, status
        ))
    
    return employees


def insert_batch(cursor, employees):
    """Insert a batch of employees efficiently."""
    cursor.executemany(
        """INSERT INTO employees 
           (id, first_name, last_name, contact_info, department, position, location, status) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        employees
    )


def populate_database(total_records=4_000_000, batch_size=10_000):
    """
    Populate the database with the specified number of records.
    
    Args:
        total_records: Total number of employee records to create
        batch_size: Number of records to insert per batch
    """
    print(f"Starting database population: {total_records:,} records")
    print(f"Batch size: {batch_size:,}")
    print("-" * 60)
    
    # Connect to database
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    # Enable performance optimizations
    print("Enabling SQLite performance optimizations...")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            contact_info TEXT NOT NULL,
            department VARCHAR(100) NOT NULL,
            position VARCHAR(100) NOT NULL,
            location VARCHAR(100) NOT NULL,
            status INTEGER NOT NULL
        )
    """)
    
    # Check existing records
    cursor.execute("SELECT COUNT(*) FROM employees")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"Found {existing_count:,} existing records")
        response = input("Delete existing records? (yes/no): ")
        if response.lower() == 'yes':
            print("Deleting existing records...")
            cursor.execute("DELETE FROM employees")
            conn.commit()
            print("Existing records deleted")
        else:
            print("Keeping existing records, will append new ones")
    
    # Start insertion
    start_time = time.time()
    total_inserted = 0
    batches = total_records // batch_size
    
    print(f"\nInserting {total_records:,} records in {batches} batches...")
    
    for batch_num in range(batches):
        batch_start = time.time()
        
        # Generate and insert batch
        start_id = existing_count + (batch_num * batch_size) + 1
        employees = generate_employee_data(start_id, batch_size)
        insert_batch(cursor, employees)
        conn.commit()
        
        total_inserted += batch_size
        batch_time = time.time() - batch_start
        elapsed_time = time.time() - start_time
        records_per_second = total_inserted / elapsed_time if elapsed_time > 0 else 0
        
        # Progress update every 10 batches
        if (batch_num + 1) % 10 == 0 or batch_num == 0:
            progress = (total_inserted / total_records) * 100
            eta_seconds = (total_records - total_inserted) / records_per_second if records_per_second > 0 else 0
            print(f"Progress: {progress:5.1f}% | "
                  f"Inserted: {total_inserted:,}/{total_records:,} | "
                  f"Speed: {records_per_second:,.0f} rec/s | "
                  f"ETA: {eta_seconds:.0f}s")
    
    # Handle remaining records
    remaining = total_records % batch_size
    if remaining > 0:
        start_id = existing_count + (batches * batch_size) + 1
        employees = generate_employee_data(start_id, remaining)
        insert_batch(cursor, employees)
        conn.commit()
        total_inserted += remaining
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("INSERTION COMPLETE")
    print("=" * 60)
    print(f"Total records inserted: {total_inserted:,}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average speed: {total_inserted / total_time:,.0f} records/second")
    print()
    
    # Create indexes for better query performance
    print("Creating indexes for query optimization...")
    index_start = time.time()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_first_name ON employees(first_name)",
        "CREATE INDEX IF NOT EXISTS idx_last_name ON employees(last_name)",
        "CREATE INDEX IF NOT EXISTS idx_status ON employees(status)",
        "CREATE INDEX IF NOT EXISTS idx_department ON employees(department)",
        "CREATE INDEX IF NOT EXISTS idx_position ON employees(position)",
        "CREATE INDEX IF NOT EXISTS idx_location ON employees(location)",
        "CREATE INDEX IF NOT EXISTS idx_status_department ON employees(status, department)",
        "CREATE INDEX IF NOT EXISTS idx_status_location ON employees(status, location)",
        "CREATE INDEX IF NOT EXISTS idx_department_position ON employees(department, position)",
    ]
    
    for idx_sql in indexes:
        cursor.execute(idx_sql)
        conn.commit()
    
    index_time = time.time() - index_start
    print(f"Indexes created in {index_time:.2f} seconds")
    
    # Analyze database for query optimizer
    print("Analyzing database for query optimization...")
    cursor.execute("ANALYZE")
    conn.commit()
    
    # Get final statistics
    cursor.execute("SELECT COUNT(*) FROM employees")
    final_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 1")
    active_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total employees: {final_count:,}")
    print(f"Active employees (status=1): {active_count:,}")
    print(f"Database file: employees.db")
    
    # Get database size
    cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
    db_size = cursor.fetchone()[0]
    print(f"Database size: {db_size / (1024**2):.2f} MB")
    
    conn.close()
    print("\nDatabase population complete!")


def test_query_performance():
    """Test query performance with different filters."""
    print("\n" + "=" * 60)
    print("QUERY PERFORMANCE TESTING")
    print("=" * 60)
    
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    test_queries = [
        ("Count all employees", "SELECT COUNT(*) FROM employees"),
        ("Filter by status", "SELECT COUNT(*) FROM employees WHERE status = 1"),
        ("Filter by department", "SELECT COUNT(*) FROM employees WHERE department = 'Engineering'"),
        ("Filter by status and department", 
         "SELECT COUNT(*) FROM employees WHERE status = 1 AND department = 'Engineering'"),
        ("Search by name (LIKE)", 
         "SELECT COUNT(*) FROM employees WHERE first_name LIKE 'John%'"),
        ("Complex filter", 
         "SELECT COUNT(*) FROM employees WHERE status IN (0, 1) AND department = 'Engineering' AND location = 'New York'"),
        ("Get top 100 results",
         "SELECT * FROM employees WHERE status = 1 LIMIT 100"),
    ]
    
    for test_name, query in test_queries:
        start = time.time()
        cursor.execute(query)
        result = cursor.fetchall()
        elapsed = time.time() - start
        
        if "COUNT" in query:
            count = result[0][0] if result else 0
            print(f"{test_name:40s}: {count:8,} records in {elapsed*1000:6.2f} ms")
        else:
            count = len(result)
            print(f"{test_name:40s}: {count:8,} records in {elapsed*1000:6.2f} ms")
    
    conn.close()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    total_records = 4_000_000
    batch_size = 10_000
    
    if len(sys.argv) > 1:
        total_records = int(sys.argv[1])
    if len(sys.argv) > 2:
        batch_size = int(sys.argv[2])
    
    # Populate database
    populate_database(total_records, batch_size)
    
    # Test query performance
    test_query_performance()
