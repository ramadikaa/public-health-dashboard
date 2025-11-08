"""
Database Configuration
Modul 2: Data Standards & Interoperability
"""

import os

class Config:
    # MySQL Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'ifteruts'
    MYSQL_PORT = 3306
    
    # API Configuration
    API_TITLE = "COVID-19 Health Informatics API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "FHIR-compatible REST API for COVID-19 Public Health Dashboard"
    
    # CORS Configuration (allow Streamlit to access API)
    CORS_ORIGINS = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    # Pagination
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
