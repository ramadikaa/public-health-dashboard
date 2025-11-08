"""
Role-Based Access Control (RBAC) Implementation
Module: Security & Governance
"""

from functools import wraps
from flask import request, jsonify

# Define roles and permissions
ROLES = {
    'public': {
        'permissions': ['view_dashboard', 'view_fhir_capability'],
        'description': 'General public viewer'
    },
    'health_official': {
        'permissions': ['view_dashboard', 'view_statistics', 'view_fhir_capability', 'export_data'],
        'description': 'Government health officials'
    },
    'researcher': {
        'permissions': ['view_dashboard', 'view_statistics', 'access_api', 'export_data', 'view_ml_model'],
        'description': 'Healthcare researchers'
    },
    'clinician': {
        'permissions': ['view_dashboard', 'view_statistics', 'access_api', 'view_fhir_data', 'view_ml_model', 'use_cdss'],
        'description': 'Healthcare providers & clinicians'
    },
    'admin': {
        'permissions': ['all'],
        'description': 'System administrators'
    }
}

# Mock user database (in production, use real auth system)
MOCK_USERS = {
    'demo_api_key_public': {'role': 'public', 'name': 'Public User'},
    'demo_api_key_official': {'role': 'health_official', 'name': 'Health Official'},
    'demo_api_key_researcher': {'role': 'researcher', 'name': 'Researcher'},
    'demo_api_key_clinician': {'role': 'clinician', 'name': 'Dr. Clinician'},
    'demo_api_key_admin': {'role': 'admin', 'name': 'System Admin'}
}

def get_user_from_request():
    """Extract user from API key header"""
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        return None
    
    return MOCK_USERS.get(api_key)

def has_permission(user, required_permission):
    """Check if user has required permission"""
    if not user:
        return False
    
    role = user.get('role')
    
    if role not in ROLES:
        return False
    
    permissions = ROLES[role]['permissions']
    
    # Admin has all permissions
    if 'all' in permissions:
        return True
    
    return required_permission in permissions

def require_permission(permission):
    """Decorator to enforce permission checks on API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_user_from_request()
            
            if not user:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required. Please provide X-API-Key header.',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            if not has_permission(user, permission):
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. Permission required: {permission}',
                    'user_role': user.get('role'),
                    'code': 'PERMISSION_DENIED'
                }), 403
            
            # Add user info to request context
            request.current_user = user
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_rbac_info():
    """Get RBAC configuration for documentation"""
    return {
        'roles': ROLES,
        'demo_api_keys': {
            'public': 'demo_api_key_public',
            'health_official': 'demo_api_key_official',
            'researcher': 'demo_api_key_researcher',
            'clinician': 'demo_api_key_clinician',
            'admin': 'demo_api_key_admin'
        },
        'usage_example': {
            'header': 'X-API-Key',
            'value': 'demo_api_key_researcher',
            'curl_example': 'curl -H "X-API-Key: demo_api_key_researcher" http://127.0.0.1:5000/api/predictions/mortality'
        }
    }
