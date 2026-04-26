import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:rootpassword@postgres:5432/codeforge")

# Use connection pool
try:
    postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
    if (postgreSQL_pool):
        print("Connection pool created successfully")
except (Exception, psycopg2.DatabaseError) as error:
    print("Error while connecting to PostgreSQL", error)

@contextmanager
def get_db_connection():
    try:
        conn = postgreSQL_pool.getconn()
        yield conn
    finally:
        postgreSQL_pool.putconn(conn)
