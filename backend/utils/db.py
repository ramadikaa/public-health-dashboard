"""
Database Connection Utilities
Modul 3: Database Management
"""

import mysql.connector
from mysql.connector import Error
from config import Config
from contextlib import contextmanager

class DatabaseConnection:
    """Database connection manager"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """Context manager for database connections"""
        connection = None
        try:
            connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                database=Config.MYSQL_DB,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                port=Config.MYSQL_PORT
            )
            yield connection
        except Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=True):
        """Execute a query and return results"""
        with DatabaseConnection.get_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            cursor.close()
            return result
