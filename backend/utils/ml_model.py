"""
ML Model Utility Functions
Load and use trained model for predictions

Modul 4: Clinical Decision Support Systems
"""

import pickle
import numpy as np
import os

class MortalityPredictor:
    """Wrapper class for mortality prediction model"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.metrics = None
        self.load_model()
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            model_path = 'models/mortality_model.pkl'
            features_path = 'models/feature_columns.pkl'
            metrics_path = 'models/model_metrics.pkl'
            scaler_path = 'models/scaler.pkl'
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(features_path, 'rb') as f:
                self.feature_columns = pickle.load(f)
            
            with open(metrics_path, 'rb') as f:
                self.metrics = pickle.load(f)
            
            # Load scaler if exists
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            print("✅ ML Model loaded successfully")
            print(f"   Expected features: {len(self.feature_columns)}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def prepare_features(self, data):
        """
        Prepare features for prediction (UPDATED to match training)
        
        Features (19 total):
        1-4: confirmed_lag2, deaths_lag2, recovered_lag2, active_lag2
        5-7: confirmed_change_2d, deaths_change_2d, recovered_change_2d
        8-10: confirmed_rolling_14d, deaths_rolling_14d, recovered_rolling_14d
        11-12: confirmed_volatility, deaths_volatility
        13: confirmed_acceleration
        14-15: day_of_week, days_since_first
        16: who_region_encoded
        17-19: log_confirmed_lag2, log_deaths_lag2, log_recovered_lag2
        """
        
        # Get input values
        confirmed = data.get('confirmed', 0)
        deaths = data.get('deaths', 0)
        recovered = data.get('recovered', 0)
        active = data.get('active', confirmed - deaths - recovered)
        
        # Lag values (2-day)
        confirmed_lag2 = data.get('confirmed_lag2', confirmed * 0.92)
        deaths_lag2 = data.get('deaths_lag2', deaths * 0.92)
        recovered_lag2 = data.get('recovered_lag2', recovered * 0.92)
        active_lag2 = data.get('active_lag2', active * 0.92)
        
        # 2-day changes
        confirmed_change_2d = confirmed - confirmed_lag2
        deaths_change_2d = deaths - deaths_lag2
        recovered_change_2d = recovered - recovered_lag2
        
        # Rolling averages (14-day)
        confirmed_rolling_14d = data.get('confirmed_rolling_14d', confirmed)
        deaths_rolling_14d = data.get('deaths_rolling_14d', deaths)
        recovered_rolling_14d = data.get('recovered_rolling_14d', recovered)
        
        # Volatility (std of changes)
        confirmed_volatility = data.get('confirmed_volatility', abs(confirmed_change_2d) * 0.5)
        deaths_volatility = data.get('deaths_volatility', abs(deaths_change_2d) * 0.5)
        
        # Acceleration (rate of change of change)
        confirmed_acceleration = data.get('confirmed_acceleration', confirmed_change_2d * 0.1)
        
        # Temporal features
        day_of_week = data.get('day_of_week', 3)  # Default Wednesday
        days_since_first = data.get('days_since_first', 30)
        
        # WHO region
        who_region_encoded = data.get('who_region_encoded', 0)
        
        # Log transforms
        log_confirmed_lag2 = np.log1p(confirmed_lag2)
        log_deaths_lag2 = np.log1p(deaths_lag2)
        log_recovered_lag2 = np.log1p(recovered_lag2)
        
        # Create feature vector (MUST match training order)
        features = np.array([[
            confirmed_lag2,              # 1
            deaths_lag2,                 # 2
            recovered_lag2,              # 3
            active_lag2,                 # 4
            confirmed_change_2d,         # 5
            deaths_change_2d,            # 6
            recovered_change_2d,         # 7
            confirmed_rolling_14d,       # 8
            deaths_rolling_14d,          # 9
            recovered_rolling_14d,       # 10
            confirmed_volatility,        # 11
            deaths_volatility,           # 12
            confirmed_acceleration,      # 13
            day_of_week,                 # 14
            days_since_first,            # 15
            who_region_encoded,          # 16
            log_confirmed_lag2,          # 17
            log_deaths_lag2,             # 18
            log_recovered_lag2           # 19
        ]])
        
        # Apply scaling if scaler exists
        if self.scaler is not None:
            features = self.scaler.transform(features)
        
        return features
    
    def predict(self, data):
        """
        Make mortality risk prediction
        
        Args:
            data (dict): Input data
        
        Returns:
            dict: Prediction results
        """
        try:
            # Prepare features
            features = self.prepare_features(data)
            
            # Get prediction
            prediction = self.model.predict(features)[0]
            prediction_proba = self.model.predict_proba(features)[0]
            
            risk_score = prediction_proba[1]  # Probability of high risk
            
            # Classify risk level
            if risk_score > 0.7:
                risk_level = "HIGH"
                risk_color = "red"
                recommendation = "⚠️ High mortality risk detected. Enhanced surveillance and resource allocation recommended. Implement aggressive public health interventions."
            elif risk_score > 0.4:
                risk_level = "MEDIUM"
                risk_color = "orange"
                recommendation = "⚠️ Moderate mortality risk. Continue monitoring outbreak patterns closely. Prepare contingency plans and ensure healthcare capacity."
            else:
                risk_level = "LOW"
                risk_color = "green"
                recommendation = "✅ Low mortality risk. Maintain standard surveillance protocols. Continue preventive measures and public health education."
            
            # Calculate mortality rate from input
            mortality_rate = (data.get('deaths', 0) / data.get('confirmed', 1) * 100) if data.get('confirmed', 0) > 0 else 0
            
            return {
                'prediction': int(prediction),
                'risk_score': float(risk_score),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'confidence': float(max(prediction_proba)),
                'recommendation': recommendation,
                'mortality_rate': float(mortality_rate)
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            raise
    
    def get_metrics(self):
        """Get model performance metrics"""
        return self.metrics

# Global predictor instance
predictor = None

def get_predictor():
    """Get or create predictor instance"""
    global predictor
    if predictor is None:
        predictor = MortalityPredictor()
    return predictor
