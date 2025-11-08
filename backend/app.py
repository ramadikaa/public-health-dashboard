"""
Main Flask Application
COVID-19 Public Health Dashboard API

Modul 2: Data Standards & Interoperability
Modul 3: Database Management
Modul 4: Clinical Decision Support Systems
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
from utils.rbac import require_permission, get_rbac_info

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# ===== CORS CONFIGURATION =====
# Allow Streamlit and Postman to access API
CORS(app, resources={
    r"/*": {  # Changed from r"/api/*" to r"/*" to cover all endpoints
        "origins": [
            "http://localhost:8501", 
            "http://127.0.0.1:8501",
            "http://localhost:*",
            "http://127.0.0.1:*"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "X-API-Key"],  # Added X-API-Key
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Add CORS headers to all responses (backup for CORS library)
@app.after_request
def after_request(response):
    """Add CORS headers to every response"""
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,X-API-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept,X-API-Key')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        response.headers.add('Access-Control-Max-Age', '3600')
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
        "modules": {
            "M1": "Health Informatics Foundation",
            "M2": "Data Standards & Interoperability (FHIR R4)",
            "M3": "Database Management (MySQL)",
            "M4": "Clinical Decision Support Systems (ML)",
            "M5": "Public Health Informatics",
            "M6": "Consumer Health Informatics (Streamlit)",
            "M7": "Data Analytics & BI (Plotly)"
        },
        "endpoints": {
            "dashboard_metrics": "/api/dashboard/metrics",
            "dashboard_timeseries": "/api/dashboard/timeseries",
            "top_countries": "/api/dashboard/countries/top",
            "country_cases": "/api/cases/country/{country}",
            "who_regions": "/api/cases/who-regions",
            "fhir_observation": "/api/fhir/observation?country={country}&date={date}",
            "fhir_capability": "/api/fhir/capability",
            "predict_mortality": "/api/predictions/mortality (POST)",
            "model_performance": "/api/predictions/model-performance",
            "rbac_info": "/api/security/rbac",
            "rbac_test": "/api/security/test-rbac"
        },
        "system": {
            "health_check": "/health",
            "database_test": "/test-db",
            "ping": "/ping"
        },
        "documentation": "See /api/security/rbac for RBAC demo",
        "author": "ITENAS Health Informatics - IFB-499 (2025)"
    }), 200

# ===== HEALTH CHECK ENDPOINT =====
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": Config.API_TITLE,
        "version": Config.API_VERSION,
        "timestamp": str(pd.Timestamp.now())
    }), 200

# ===== SECURITY ENDPOINTS (RBAC) =====
@app.route('/api/security/rbac', methods=['GET'])
def rbac_info():
    """Get RBAC configuration and demo keys"""
    return jsonify({
        'status': 'success',
        'rbac': get_rbac_info(),
        'message': 'Use X-API-Key header with demo keys for testing RBAC',
        'example': {
            'curl': 'curl -H "X-API-Key: demo_api_key_researcher" http://127.0.0.1:5000/api/security/test-rbac',
            'postman': {
                'method': 'GET',
                'url': 'http://127.0.0.1:5000/api/security/test-rbac',
                'headers': {
                    'X-API-Key': 'demo_api_key_researcher'
                }
            }
        }
    }), 200

@app.route('/api/security/test-rbac', methods=['GET'])
@require_permission('access_api')
def test_rbac():
    """Test RBAC - requires 'access_api' permission"""
    user = request.current_user
    return jsonify({
        'status': 'success',
        'message': 'RBAC test successful! You have proper authorization.',
        'user': {
            'name': user.get('name'),
            'role': user.get('role')
        },
        'access_granted': True,
        'timestamp': str(pd.Timestamp.now())
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
        
        # Test 4: Sample data
        query4 = "SELECT country_region, confirmed, deaths FROM daily_cases ORDER BY confirmed DESC LIMIT 5"
        result4 = DatabaseConnection.execute_query(query4)
        
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
            "sample_data": result4,
            "message": "✅ Database is connected and tables are accessible"
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
            "error_details": error_details if app.debug else "Enable debug mode for details",
            "troubleshooting": {
                "1": "Check if MySQL service is running",
                "2": f"Verify database '{Config.MYSQL_DB}' exists",
                "3": "Confirm MySQL credentials in config.py",
                "4": "Ensure ETL pipeline has been executed",
                "5": "Test connection: mysql -u root -p"
            }
        }), 500

# ===== PING ENDPOINT (FOR STREAMLIT CONNECTION TEST) =====
@app.route('/ping')
def ping():
    """Simple ping endpoint for connection testing"""
    return jsonify({
        "status": "pong",
        "message": "API is alive and responding",
        "timestamp": str(pd.Timestamp.now())
    }), 200

# ===== ERROR HANDLERS =====
@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    return jsonify({
        "error": "Unauthorized",
        "status_code": 401,
        "message": "Authentication required. Please provide valid X-API-Key header.",
        "example": "X-API-Key: demo_api_key_researcher"
    }), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return jsonify({
        "error": "Forbidden",
        "status_code": 403,
        "message": "Access denied. Your role does not have permission for this resource.",
        "rbac_info": "/api/security/rbac"
    }), 403

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status_code": 404,
        "message": f"The requested URL '{request.path}' was not found on this server.",
        "available_endpoints": {
            "dashboard": "/api/dashboard",
            "cases": "/api/cases",
            "fhir": "/api/fhir",
            "predictions": "/api/predictions",
            "security": "/api/security"
        },
        "documentation": "/"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    error_details = traceback.format_exc()
    return jsonify({
        "error": "Internal server error",
        "status_code": 500,
        "message": str(error),
        "details": error_details if app.debug else "Enable debug mode for error details",
        "contact": "Check Flask terminal for detailed logs"
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    error_details = traceback.format_exc()
    
    # Don't log expected errors in production
    if app.debug:
        print("\n" + "="*70)
        print("🔴 UNHANDLED EXCEPTION")
        print("="*70)
        print(error_details)
        print("="*70 + "\n")
    
    return jsonify({
        "error": "Unexpected error occurred",
        "error_type": type(error).__name__,
        "message": str(error),
        "details": error_details if app.debug else "Enable debug mode for error details"
    }), 500

# ===== STARTUP MESSAGE =====
if __name__ == '__main__':
    import pandas as pd  # Import for timestamp
    
    print("\n" + "="*70)
    print(f"🚀 Starting {Config.API_TITLE} v{Config.API_VERSION}")
    print("="*70)
    print(f"📊 API Documentation:   http://127.0.0.1:5000/")
    print(f"❤️  Health Check:        http://127.0.0.1:5000/health")
    print(f"🗄️  Database Test:       http://127.0.0.1:5000/test-db")
    print(f"🏓 Ping Test:           http://127.0.0.1:5000/ping")
    print(f"🔐 RBAC Info:           http://127.0.0.1:5000/api/security/rbac")
    
    print(f"\n📡 Available API Endpoints:")
    print(f"   Dashboard:")
    print(f"   • Metrics:              /api/dashboard/metrics")
    print(f"   • Time Series:          /api/dashboard/timeseries")
    print(f"   • Top Countries:        /api/dashboard/countries/top")
    
    print(f"\n   Cases:")
    print(f"   • Country Data:         /api/cases/country/Indonesia")
    print(f"   • WHO Regions:          /api/cases/who-regions")
    
    print(f"\n   FHIR (Interoperability):")
    print(f"   • Observation:          /api/fhir/observation")
    print(f"   • Capability:           /api/fhir/capability")
    
    print(f"\n   Predictions (ML):")
    print(f"   • Mortality (POST):     /api/predictions/mortality")
    print(f"   • Model Performance:    /api/predictions/model-performance")
    
    print(f"\n   Security (RBAC):")
    print(f"   • RBAC Config:          /api/security/rbac")
    print(f"   • Test RBAC:            /api/security/test-rbac")
    
    print(f"\n🔧 Configuration:")
    print(f"   • Debug Mode:           ON")
    print(f"   • Auto-reload:          ENABLED")
    print(f"   • Threaded:             YES")
    print(f"   • MySQL Database:       {Config.MYSQL_DB}")
    print(f"   • CORS:                 ENABLED (Streamlit + Postman)")
    
    print("\n" + "="*70)
    print("✅ Flask API is ready! Waiting for requests...")
    print("="*70 + "\n")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',      # Listen on all interfaces
        port=5000,
        debug=True,          # Enable debug mode
        use_reloader=True,   # Auto-reload on code changes
        threaded=True        # Handle multiple requests concurrently
    )
