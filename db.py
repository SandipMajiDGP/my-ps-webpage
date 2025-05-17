import mysql.connector
from mysql.connector import pooling

# Define connection pool parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306, 
    'user': 'root',
    'password': 'root123',
    'database': 'password_manager',
    'raise_on_warnings': True
}

# Create the connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="psm_pool",       # Name of the pool
    pool_size=20,               # Max number of connections in the pool (increased from 10)
    **DB_CONFIG                 # Unpack the database configuration
)

def get_connection():
    """Returns a connection from the pool."""
    return connection_pool.get_connection()
