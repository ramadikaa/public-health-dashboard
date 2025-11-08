"""
COVID Cases API Routes
Modul 5: Public Health Informatics
"""

from flask import Blueprint, jsonify, request
from utils.db import DatabaseConnection

cases_bp = Blueprint('cases', __name__, url_prefix='/api/cases')

@cases_bp.route('/country/<string:country>', methods=['GET'])
def get_country_cases(country):
    """
    Get COVID-19 cases for a specific country
    
    Query params:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
    """
    try:
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        query = """
        SELECT 
            date,
            country_region,
            SUM(confirmed) as confirmed,
            SUM(deaths) as deaths,
            SUM(recovered) as recovered,
            SUM(active) as active
        FROM daily_cases
        WHERE country_region = %s
        """
        params = [country]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " GROUP BY date, country_region ORDER BY date ASC"
        
        results = DatabaseConnection.execute_query(query, tuple(params), fetch_all=True)
        
        if not results:
            return jsonify({"error": f"No data found for country: {country}"}), 404
        
        cases_data = []
        for row in results:
            data_point = {
                "date": row['date'].strftime('%Y-%m-%d'),
                "country": row['country_region'],
                "confirmed": row['confirmed'],
                "deaths": row['deaths'],
                "recovered": row['recovered'],
                "active": row['active']
            }
            cases_data.append(data_point)
        
        response = {
            "status": "success",
            "country": country,
            "count": len(cases_data),
            "data": cases_data
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@cases_bp.route('/who-regions', methods=['GET'])
def get_who_regions():
    """Get COVID-19 cases grouped by WHO regions"""
    try:
        # Get latest date
        latest_date_query = "SELECT MAX(date) as max_date FROM daily_cases"
        latest_date_result = DatabaseConnection.execute_query(latest_date_query, fetch_one=True)
        latest_date = latest_date_result['max_date']
        
        query = """
        SELECT 
            who_region,
            SUM(confirmed) as total_confirmed,
            SUM(deaths) as total_deaths,
            SUM(recovered) as total_recovered,
            SUM(active) as total_active
        FROM daily_cases
        WHERE date = %s AND who_region != ''
        GROUP BY who_region
        ORDER BY total_confirmed DESC
        """
        
        results = DatabaseConnection.execute_query(query, (latest_date,), fetch_all=True)
        
        regions_data = []
        for row in results:
            region = {
                "region": row['who_region'],
                "confirmed": row['total_confirmed'],
                "deaths": row['total_deaths'],
                "recovered": row['total_recovered'],
                "active": row['total_active']
            }
            regions_data.append(region)
        
        response = {
            "status": "success",
            "date": latest_date.strftime('%Y-%m-%d'),
            "count": len(regions_data),
            "data": regions_data
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
