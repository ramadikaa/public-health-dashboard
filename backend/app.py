"""
Main Flask Application
COVID-19 Public Health Dashboard API

Modul 2: Data Standards & Interoperability
Modul 3: Database Management
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
import traceback

# Import routes
from routes.dashboard import dashboard_bp
from routes.cases import cases_bp
from routes.fhir import fhir_bp
from routes.predictions import predictions_bp

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# ===== COMPREHENSIVE CORS CONFIGURATION =====
# Allow Streamlit to access API from different origin
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:8501", 
            "http://127.0.0.1:8501",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response, 200

# ===== REGISTER BLUEPRINTS =====
app.register_blueprint(dashboard_bp)
app.register_blueprint(cases_bp)
app.register_blueprint(fhir_bp)
app.register_blueprint(predictions_bp)

# ===== ROOT ENDPOINTS =====
@app.route('/')
def index():
    """API root endpoint with service information"""
    return jsonify({
        "service": Config.API_TITLE,
        "version": Config.API_VERSION,
        "description": Config.API_DESCRIPTION,
        "status": "running",
        "endpoints": {
            "dashboard_metrics": "/api/dashboard/metrics",
            "dashboard_timeseries": "/api/dashboard/timeseries",
            "top_countries": "/api/dashboard/countries/top",
            "country_cases": "/api/cases/country/{country}",
            "who_regions": "/api/cases/who-regions",
            "fhir_observation": "/api/fhir/observation?country={country}&date={date}",
            "fhir_capability": "/api/fhir/capability",
            "predict_mortality": "/api/predictions/mortality",
            "model_performance": "/api/predictions/model-performance"
        },
        "documentation": "https://github.com/your-repo",
        "health_check": "/health",
        "database_test": "/test-db"
    }), 200

# ===== HEALTH CHECK ENDPOINT =====
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": Config.API_TITLE,
        "version": Config.API_VERSION
    }), 200

# ===== DATABASE CONNECTION TEST ENDPOINT =====
@app.route('/test-db')
def test_db():
    """Test database connection and data availability"""
    try:
        from utils.db import DatabaseConnection
        
        # Test 1: Check daily_cases table
        query1 = "SELECT COUNT(*) as count FROM daily_cases"
        result1 = DatabaseConnection.execute_query(query1, fetch_one=True)
        
        # Test 2: Check dashboard_metrics table
        query2 = "SELECT COUNT(*) as count FROM dashboard_metrics"
        result2 = DatabaseConnection.execute_query(query2, fetch_one=True)
        
        # Test 3: Get latest date
        query3 = "SELECT MAX(date) as latest_date FROM daily_cases"
        result3 = DatabaseConnection.execute_query(query3, fetch_one=True)
        
        return jsonify({
            "status": "success",
            "database": "connected",
            "mysql_host": Config.MYSQL_HOST,
            "database_name": Config.MYSQL_DB,
            "tables": {
                "daily_cases": {
                    "status": "ok",
                    "row_count": result1['count']
                },
                "dashboard_metrics": {
                    "status": "ok",
                    "row_count": result2['count']
                }
            },
            "latest_data_date": str(result3['latest_date']) if result3['latest_date'] else None,
            "message": "Database is connected and tables are accessible"
        }), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({
            "status": "error",
            "database": "connection_failed",
            "mysql_host": Config.MYSQL_HOST,
            "database_name": Config.MYSQL_DB,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "error_details": error_details,
            "troubleshooting": {
                "1": "Check if MySQL service is running",
                "2": f"Verify database '{Config.MYSQL_DB}' exists",
                "3": "Confirm MySQL credentials in config.py",
                "4": "Ensure ETL pipeline has been executed"
            }
        }), 500

# ===== PING ENDPOINT (FOR STREAMLIT CONNECTION TEST) =====
@app.route('/ping')
def ping():
    """Simple ping endpoint for connection testing"""
    return jsonify({"status": "pong"}), 200

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status_code": 404,
        "message": f"The requested URL '{request.url}' was not found on this server.",
        "available_endpoints": "/api/dashboard, /api/cases, /api/fhir"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_details = traceback.format_exc()
    return jsonify({
        "error": "Internal server error",
        "status_code": 500,
        "message": str(error),
        "details": error_details if app.debug else "Enable debug mode for error details"
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    error_details = traceback.format_exc()
    return jsonify({
        "error": "Unexpected error occurred",
        "error_type": type(error).__name__,
        "message": str(error),
        "details": error_details if app.debug else "Enable debug mode for error details"
    }), 500

# ===== STARTUP MESSAGE =====
if __name__ == '__main__':
    print("\n" + "="*70)
    print(f"🚀 Starting {Config.API_TITLE} v{Config.API_VERSION}")
    print("="*70)
    print(f"📊 API Documentation: http://localhost:5000/")
    print(f"❤️  Health Check:      http://localhost:5000/health")
    print(f"🗄️  Database Test:     http://localhost:5000/test-db")
    print(f"🏓 Ping Test:         http://localhost:5000/ping")
    print(f"\n📡 Available API Endpoints:")
    print(f"   - Dashboard Metrics:    http://localhost:5000/api/dashboard/metrics")
    print(f"   - Time Series:          http://localhost:5000/api/dashboard/timeseries")
    print(f"   - Top Countries:        http://localhost:5000/api/dashboard/countries/top")
    print(f"   - Country Cases:        http://localhost:5000/api/cases/country/Indonesia")
    print(f"   - WHO Regions:          http://localhost:5000/api/cases/who-regions")
    print(f"   - FHIR Observation:     http://localhost:5000/api/fhir/observation")
    print(f"   - FHIR Capability:      http://localhost:5000/api/fhir/capability")
    print("\n🔧 Debug Mode: ON")
    print("="*70 + "\n")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        debug=True,
        use_reloader=True,  # Auto-reload on code changes
        threaded=True       # Handle multiple requests concurrently
    )
