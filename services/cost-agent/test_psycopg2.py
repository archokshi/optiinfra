import psycopg2
print("✅ psycopg2 version:", psycopg2.__version__)

# Test connection to PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="optiinfra",
        user="optiinfra",
        password="optiinfra_dev_password"
    )
    print("✅ PostgreSQL connection successful")
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
