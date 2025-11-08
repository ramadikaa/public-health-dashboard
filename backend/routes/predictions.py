"""
Predictions API Routes
ML-based mortality risk prediction endpoints

Modul 4: Clinical Decision Support Systems
Modul 7: Predictive Analytics
"""

from flask import Blueprint, jsonify, request
from utils.ml_model import get_predictor
import traceback

predictions_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

@predictions_bp.route('/mortality', methods=['POST'])
def predict_mortality():
    """
    Predict COVID-19 mortality risk using ML model
    
    Request body (JSON):
    {
        "confirmed": 1000,
        "deaths": 50,
        "recovered": 700,
        "active": 250,
        "confirmed_lag1": 900 (optional),
        "deaths_lag1": 45 (optional),
        "who_region_encoded": 1 (optional)
    }
    
    Returns:
        JSON with prediction results
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Validate required fields
        required_fields = ['confirmed', 'deaths']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Get predictor
        predictor = get_predictor()
        
        # Make prediction
        prediction_result = predictor.predict(data)
        
        # Format response
        response = {
            "status": "success",
            "prediction": prediction_result,
            "input_data": {
                "confirmed": data.get('confirmed'),
                "deaths": data.get('deaths'),
                "recovered": data.get('recovered', 0),
                "active": data.get('active', data.get('confirmed', 0) - data.get('deaths', 0) - data.get('recovered', 0))
            },
            "model_info": {
                "type": "Random Forest Classifier",
                "features_count": len(predictor.feature_columns),
                "training_accuracy": predictor.metrics.get('accuracy', 0)
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": error_details if request.args.get('debug') else None
        }), 500


@predictions_bp.route('/model-performance', methods=['GET'])
def get_model_performance():
    """
    Get ML model performance metrics
    
    Returns:
        JSON with metrics including ROC curve data
    """
    try:
        predictor = get_predictor()
        metrics = predictor.get_metrics()
        
        # Format ROC curve data (sample every 10th point for performance)
        roc_data = metrics.get('roc_curve', {})
        fpr = roc_data.get('fpr', [])
        tpr = roc_data.get('tpr', [])
        
        # Sample points if too many
        if len(fpr) > 100:
            step = len(fpr) // 100
            fpr = fpr[::step]
            tpr = tpr[::step]
        
        response = {
            "status": "success",
            "metrics": {
                "accuracy": round(metrics.get('accuracy', 0), 4),
                "precision": round(metrics.get('precision', 0), 4),
                "recall": round(metrics.get('recall', 0), 4),
                "f1_score": round(metrics.get('f1_score', 0), 4),
                "auc_roc": round(metrics.get('auc_roc', 0), 4)
            },
            "roc_curve": {
                "fpr": fpr,
                "tpr": tpr,
                "auc": round(metrics.get('auc_roc', 0), 4)
            },
            "confusion_matrix": {
                "true_negative": int(metrics['confusion_matrix'][0][0]),
                "false_positive": int(metrics['confusion_matrix'][0][1]),
                "false_negative": int(metrics['confusion_matrix'][1][0]),
                "true_positive": int(metrics['confusion_matrix'][1][1])
            },
            "feature_importance": metrics.get('feature_importance', [])[:10],  # Top 10
            "training_info": {
                "training_samples": metrics.get('training_samples', 0),
                "test_samples": metrics.get('test_samples', 0),
                "mortality_threshold": round(metrics.get('mortality_threshold', 0), 2)
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@predictions_bp.route('/feature-importance', methods=['GET'])
def get_feature_importance():
    """Get feature importance from trained model"""
    try:
        predictor = get_predictor()
        metrics = predictor.get_metrics()
        
        feature_importance = metrics.get('feature_importance', [])
        
        return jsonify({
            "status": "success",
            "feature_importance": feature_importance
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
