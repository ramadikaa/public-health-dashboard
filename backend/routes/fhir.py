"""
FHIR-Compatible API Routes
Modul 2: Data Standards & Interoperability
"""

from flask import Blueprint, jsonify, request
from utils.db import DatabaseConnection
from datetime import datetime

fhir_bp = Blueprint('fhir', __name__, url_prefix='/api/fhir')

@fhir_bp.route('/observation', methods=['GET'])
def get_observation():
    """
    FHIR Observation endpoint for COVID-19 data
    
    Query params:
        - country: Country name
        - date: YYYY-MM-DD
    """
    try:
        country = request.args.get('country', None)
        date = request.args.get('date', None)
        
        if not country or not date:
            return jsonify({
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "required",
                    "diagnostics": "country and date parameters are required"
                }]
            }), 400
        
        query = """
        SELECT 
            country_region,
            date,
            SUM(confirmed) as confirmed,
            SUM(deaths) as deaths,
            SUM(recovered) as recovered,
            latitude,
            longitude
        FROM daily_cases
        WHERE country_region = %s AND date = %s
        GROUP BY country_region, date, latitude, longitude
        """
        
        result = DatabaseConnection.execute_query(query, (country, date), fetch_one=True)
        
        if not result:
            return jsonify({
                "resourceType": "OperationOutcome",
                "issue": [{
                    "severity": "error",
                    "code": "not-found",
                    "diagnostics": f"No data found for {country} on {date}"
                }]
            }), 404
        
        # FHIR Observation resource format
        fhir_observation = {
            "resourceType": "Observation",
            "id": f"covid-{country.replace(' ', '-')}-{date}",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "94500-6",
                    "display": "SARS-CoV-2 RNA Pnl Respiratory specimen by NAA with probe detection"
                }],
                "text": "COVID-19 Test"
            },
            "subject": {
                "reference": f"Location/{country.replace(' ', '-')}",
                "display": country
            },
            "effectiveDateTime": date,
            "issued": datetime.now().isoformat(),
            "valueQuantity": {
                "value": result['confirmed'],
                "unit": "cases",
                "system": "http://unitsofmeasure.org",
                "code": "{cases}"
            },
            "component": [
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "64518-6",
                            "display": "Deaths"
                        }],
                        "text": "COVID-19 Deaths"
                    },
                    "valueQuantity": {
                        "value": result['deaths'],
                        "unit": "deaths"
                    }
                },
                {
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "82810-3",
                            "display": "Recovered"
                        }],
                        "text": "COVID-19 Recovered"
                    },
                    "valueQuantity": {
                        "value": result['recovered'],
                        "unit": "recovered"
                    }
                }
            ]
        }
        
        return jsonify(fhir_observation), 200
        
    except Exception as e:
        return jsonify({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "error",
                "code": "exception",
                "diagnostics": str(e)
            }]
        }), 500


@fhir_bp.route('/capability', methods=['GET'])
def get_capability_statement():
    """FHIR CapabilityStatement endpoint"""
    capability = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.now().isoformat(),
        "publisher": "ITENAS Health Informatics",
        "kind": "instance",
        "software": {
            "name": "COVID-19 Public Health Dashboard API",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "FHIR-compatible API for COVID-19 surveillance data"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [{
                "type": "Observation",
                "interaction": [
                    {"code": "read"},
                    {"code": "search-type"}
                ],
                "searchParam": [
                    {
                        "name": "country",
                        "type": "string"
                    },
                    {
                        "name": "date",
                        "type": "date"
                    }
                ]
            }]
        }]
    }
    
    return jsonify(capability), 200
