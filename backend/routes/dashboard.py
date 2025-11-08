"""
Dashboard API Routes
Modul 5: Public Health Informatics
Modul 7: Data Analytics & BI
"""

from flask import Blueprint, jsonify, request
from utils.db import DatabaseConnection
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/metrics', methods=['GET'])
def get_dashboard_metrics():
    """
    Get global dashboard metrics (KPIs)
    
    Returns:
        JSON with latest COVID-19 global statistics
    """
    try:
        # Get date parameter (default: latest)
        date_param = request.args.get('date', None)
        
        if date_param:
            query = """
            SELECT 
                date,
                total_confirmed,
                total_deaths,
                total_recovered,
                total_active,
                daily_new_cases,
                daily_new_deaths,
                global_mortality_rate,
                global_recovery_rate
            FROM dashboard_metrics
            WHERE date = %s
            """
            result = DatabaseConnection.execute_query(query, (date_param,), fetch_one=True)
        else:
            # Get latest date
            query = """
            SELECT 
                date,
                total_confirmed,
                total_deaths,
                total_recovered,
                total_active,
                daily_new_cases,
                daily_new_deaths,
                global_mortality_rate,
                global_recovery_rate
            FROM dashboard_metrics
            ORDER BY date DESC
            LIMIT 1
            """
            result = DatabaseConnection.execute_query(query, fetch_one=True)
        
        if not result:
            return jsonify({"error": "No data found"}), 404
        
        # Format response
        response = {
            "status": "success",
            "data": {
                "date": result['date'].strftime('%Y-%m-%d'),
                "metrics": {
                    "confirmed": {
                        "total": result['total_confirmed'],
                        "new_cases": result['daily_new_cases'] if result['daily_new_cases'] else 0
                    },
                    "deaths": {
                        "total": result['total_deaths'],
                        "new_deaths": result['daily_new_deaths'] if result['daily_new_deaths'] else 0
                    },
                    "recovered": {
                        "total": result['total_recovered']
                    },
                    "active": {
                        "total": result['total_active']
                    },
                    "rates": {
                        "mortality_rate": float(result['global_mortality_rate']),
                        "recovery_rate": float(result['global_recovery_rate'])
                    }
                }
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route('/timeseries', methods=['GET'])
def get_timeseries():
    """
    Get time series data for charts
    
    Query params:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - metric: confirmed|deaths|recovered|active (default: all)
    """
    try:
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        metric = request.args.get('metric', 'all')
        
        # Build query
        query = """
        SELECT 
            date,
            total_confirmed,
            total_deaths,
            total_recovered,
            total_active
        FROM dashboard_metrics
        WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date ASC"
        
        results = DatabaseConnection.execute_query(query, tuple(params), fetch_all=True)
        
        if not results:
            return jsonify({"error": "No data found"}), 404
        
        # Format response
        timeseries_data = []
        for row in results:
            data_point = {
                "date": row['date'].strftime('%Y-%m-%d'),
                "confirmed": row['total_confirmed'],
                "deaths": row['total_deaths'],
                "recovered": row['total_recovered'],
                "active": row['total_active']
            }
            timeseries_data.append(data_point)
        
        response = {
            "status": "success",
            "count": len(timeseries_data),
            "data": timeseries_data
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@dashboard_bp.route('/countries/top', methods=['GET'])
def get_top_countries():
    """
    Get top countries by confirmed cases
    
    Query params:
        - limit: number of countries (default: 20)
        - metric: confirmed|deaths|recovered (default: confirmed)
    """
    try:
        limit = int(request.args.get('limit', 20))
        metric = request.args.get('metric', 'confirmed')
        
        # Get latest date
        latest_date_query = "SELECT MAX(date) as max_date FROM daily_cases"
        latest_date_result = DatabaseConnection.execute_query(latest_date_query, fetch_one=True)
        latest_date = latest_date_result['max_date']
        
        # Column mapping
        metric_column_map = {
            'confirmed': 'confirmed',
            'deaths': 'deaths',
            'recovered': 'recovered',
            'active': 'active'
        }
        
        column = metric_column_map.get(metric, 'confirmed')
        
        query = f"""
        SELECT 
            country_region,
            SUM({column}) as total_{column},
            SUM(confirmed) as total_confirmed,
            SUM(deaths) as total_deaths,
            SUM(recovered) as total_recovered,
            SUM(active) as total_active
        FROM daily_cases
        WHERE date = %s
        GROUP BY country_region
        ORDER BY total_{column} DESC
        LIMIT %s
        """
        
        results = DatabaseConnection.execute_query(query, (latest_date, limit), fetch_all=True)
        
        countries_data = []
        for row in results:
            country = {
                "country": row['country_region'],
                "confirmed": row['total_confirmed'],
                "deaths": row['total_deaths'],
                "recovered": row['total_recovered'],
                "active": row['total_active'],
                "mortality_rate": round((row['total_deaths'] / row['total_confirmed'] * 100), 2) if row['total_confirmed'] > 0 else 0
            }
            countries_data.append(country)
        
        response = {
            "status": "success",
            "date": latest_date.strftime('%Y-%m-%d'),
            "count": len(countries_data),
            "data": countries_data
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
