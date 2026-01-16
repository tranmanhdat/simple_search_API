import psycopg2

def count_total_entries():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            'postgresql://postgres:postgres@localhost:5432/employees_db'
        )
        
        # Create a cursor object
        cur = conn.cursor()
        
        # Execute query to count total entries
        cur.execute("SELECT COUNT(*) FROM employees")
        
        # Fetch the result
        total_entries = cur.fetchone()[0]
        
        print(f"Total entries: {total_entries}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        return total_entries
        
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")

if __name__ == "__main__":
    count_total_entries()