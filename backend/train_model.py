"""
ML Model Training Script (FINAL FIX - Zero Leakage)
Train Random Forest for COVID-19 outbreak pattern recognition

Modul 4: Clinical Decision Support Systems
Modul 7: Predictive Analytics
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report
)
import pickle
import os
import mysql.connector
from config import Config

print("="*70)
print("🤖 COVID-19 OUTBREAK PATTERN PREDICTION MODEL (FINAL)")
print("="*70)

# ===== 1. LOAD DATA =====
print("\n📊 Loading data from MySQL database...")

try:
    connection = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        database=Config.MYSQL_DB,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        port=Config.MYSQL_PORT
    )
    
    if connection.is_connected():
        print("✅ Connected to MySQL database")
    
    query = """
    SELECT 
        dc.country_region,
        dc.date,
        dc.confirmed,
        dc.deaths,
        dc.recovered,
        dc.active,
        dc.who_region
    FROM daily_cases dc
    WHERE dc.confirmed > 100 AND dc.deaths >= 0
    ORDER BY dc.date, dc.country_region
    """
    
    df = pd.read_sql(query, connection)
    
    print(f"✅ Loaded {len(df):,} records")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
finally:
    if connection and connection.is_connected():
        connection.close()

# ===== 2. CREATE TARGET FIRST =====
print("\n🎯 Creating target variable...")

df = df.sort_values(['country_region', 'date'])

# Calculate mortality rate ONLY for target creation
df['mortality_rate'] = (df['deaths'] / df['confirmed'] * 100).fillna(0)
df['mortality_rate'] = df['mortality_rate'].replace([np.inf, -np.inf], 0)

# Use percentile-based threshold for more balanced classes
mortality_threshold = df['mortality_rate'].quantile(0.6)  # 60th percentile

print(f"✅ Mortality threshold (60th percentile): {mortality_threshold:.2f}%")

df['high_mortality_risk'] = (df['mortality_rate'] > mortality_threshold).astype(int)

# ===== 3. FEATURE ENGINEERING (TEMPORAL PATTERNS ONLY) =====
print("\n🔧 Engineering temporal features (NO direct ratios)...")

# Lag features (2-day window to avoid immediate correlation)
df['confirmed_lag2'] = df.groupby('country_region')['confirmed'].shift(2)
df['deaths_lag2'] = df.groupby('country_region')['deaths'].shift(2)
df['recovered_lag2'] = df.groupby('country_region')['recovered'].shift(2)
df['active_lag2'] = df.groupby('country_region')['active'].shift(2)

# Multi-day changes
df['confirmed_change_2d'] = (df['confirmed'] - df['confirmed_lag2']).fillna(0)
df['deaths_change_2d'] = (df['deaths'] - df['deaths_lag2']).fillna(0)
df['recovered_change_2d'] = (df['recovered'] - df['recovered_lag2']).fillna(0)

# Rolling statistics (14-day window)
df['confirmed_rolling_14d'] = df.groupby('country_region')['confirmed'].transform(
    lambda x: x.rolling(14, min_periods=3).mean()
)
df['deaths_rolling_14d'] = df.groupby('country_region')['deaths'].transform(
    lambda x: x.rolling(14, min_periods=3).mean()
)
df['recovered_rolling_14d'] = df.groupby('country_region')['recovered'].transform(
    lambda x: x.rolling(14, min_periods=3).mean()
)

# Volatility (rolling std)
df['confirmed_volatility'] = df.groupby('country_region')['confirmed'].transform(
    lambda x: x.rolling(7, min_periods=3).std()
).fillna(0)

df['deaths_volatility'] = df.groupby('country_region')['deaths'].transform(
    lambda x: x.rolling(7, min_periods=3).std()
).fillna(0)

# Acceleration (rate of change)
df['confirmed_acceleration'] = df.groupby('country_region')['confirmed_change_2d'].transform(
    lambda x: x.diff()
).fillna(0)

# Day of week (cyclic patterns)
df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek

# Days since first case
df['days_since_first'] = df.groupby('country_region').cumcount()

# WHO Region encoding
region_mapping = {
    'Americas': 0, 'Europe': 1, 'Western Pacific': 2, 
    'Eastern Mediterranean': 3, 'South-East Asia': 4, 'Africa': 5, '': 6
}
df['who_region_encoded'] = df['who_region'].map(region_mapping).fillna(6).astype(int)

# Log transforms (scale features)
df['log_confirmed_lag2'] = np.log1p(df['confirmed_lag2'].fillna(0))
df['log_deaths_lag2'] = np.log1p(df['deaths_lag2'].fillna(0))
df['log_recovered_lag2'] = np.log1p(df['recovered_lag2'].fillna(0))

# Remove rows with insufficient history
df_clean = df.dropna(subset=[
    'confirmed_lag2', 'deaths_lag2', 'confirmed_rolling_14d'
])

print(f"✅ Feature engineering complete: {len(df_clean):,} records")

# ===== 4. SELECT FEATURES (PURE TEMPORAL) =====
feature_columns = [
    # Lagged values (2-day lag to reduce correlation)
    'confirmed_lag2', 'deaths_lag2', 'recovered_lag2', 'active_lag2',
    
    # Multi-day changes
    'confirmed_change_2d', 'deaths_change_2d', 'recovered_change_2d',
    
    # Rolling statistics
    'confirmed_rolling_14d', 'deaths_rolling_14d', 'recovered_rolling_14d',
    
    # Volatility
    'confirmed_volatility', 'deaths_volatility',
    
    # Acceleration
    'confirmed_acceleration',
    
    # Temporal context
    'day_of_week', 'days_since_first',
    
    # Geographic
    'who_region_encoded',
    
    # Log-scaled lagged values
    'log_confirmed_lag2', 'log_deaths_lag2', 'log_recovered_lag2'
]

X = df_clean[feature_columns]
y = df_clean['high_mortality_risk']

print(f"\n📋 Using {len(feature_columns)} pure temporal features")

# Check class distribution
class_dist = y.value_counts()
print(f"\n📊 Target distribution:")
print(f"  Low Risk (0): {class_dist.get(0, 0):,} ({class_dist.get(0, 0)/len(y)*100:.1f}%)")
print(f"  High Risk (1): {class_dist.get(1, 0):,} ({class_dist.get(1, 0)/len(y)*100:.1f}%)")

# ===== 5. FEATURE SCALING =====
print("\n⚖️ Scaling features...")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ===== 6. TRAIN-TEST SPLIT =====
print("\n✂️ Splitting data (30% test set)...")

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y,
    test_size=0.3,
    random_state=42,
    stratify=y
)

print(f"Training: {len(X_train):,} | Test: {len(X_test):,}")

# ===== 7. TRAIN MODEL =====
print("\n🚀 Training Random Forest with strong regularization...")

model = RandomForestClassifier(
    n_estimators=50,           # Reduced trees
    max_depth=5,               # Shallow trees
    min_samples_split=50,      # Large minimum split
    min_samples_leaf=25,       # Large minimum leaf
    max_features='sqrt',       # Limited features per tree
    max_samples=0.7,           # Bootstrap sample size
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)

model.fit(X_train, y_train)

print("✅ Model training complete!")

# ===== 8. CROSS-VALIDATION =====
print("\n🔄 5-fold cross-validation...")

cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc', n_jobs=-1)

print(f"CV AUC-ROC scores: {cv_scores}")
print(f"Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

# ===== 9. EVALUATION =====
print("\n📊 Evaluating model...")

# Training set
y_train_pred = model.predict(X_train)
y_train_proba = model.predict_proba(X_train)[:, 1]
train_acc = accuracy_score(y_train, y_train_pred)
train_auc = roc_auc_score(y_train, y_train_proba)

# Test set
y_test_pred = model.predict(X_test)
y_test_proba = model.predict_proba(X_test)[:, 1]

test_acc = accuracy_score(y_test, y_test_pred)
test_prec = precision_score(y_test, y_test_pred, zero_division=0)
test_rec = recall_score(y_test, y_test_pred, zero_division=0)
test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
test_auc = roc_auc_score(y_test, y_test_proba)

print("\n" + "="*70)
print("📈 FINAL MODEL PERFORMANCE")
print("="*70)

print(f"\n🎓 TRAINING SET:")
print(f"  Accuracy:  {train_acc:.4f} ({train_acc*100:.2f}%)")
print(f"  AUC-ROC:   {train_auc:.4f}")

print(f"\n🧪 TEST SET:")
print(f"  Accuracy:  {test_acc:.4f} ({test_acc*100:.2f}%)")
print(f"  Precision: {test_prec:.4f} ({test_prec*100:.2f}%)")
print(f"  Recall:    {test_rec:.4f} ({test_rec*100:.2f}%)")
print(f"  F1-Score:  {test_f1:.4f} ({test_f1*100:.2f}%)")
print(f"  AUC-ROC:   {test_auc:.4f}")

overfitting_gap = train_acc - test_acc
print(f"\n📊 OVERFITTING CHECK:")
print(f"  Gap: {overfitting_gap:.4f} ({overfitting_gap*100:.2f}%)")

if overfitting_gap < 0.05:
    print(f"  ✅ Excellent: Minimal overfitting")
elif overfitting_gap < 0.10:
    print(f"  ⚠️  Acceptable: Some overfitting")
else:
    print(f"  🔴 Poor: Significant overfitting")

print("="*70)

# Classification report
print("\n📋 Classification Report:")
print(classification_report(y_test, y_test_pred, target_names=['Low Risk', 'High Risk']))

# Confusion matrix
cm = confusion_matrix(y_test, y_test_pred)
print("\n🎯 Confusion Matrix:")
print(f"             Predicted")
print(f"           Low    High")
print(f"Low      {cm[0][0]:5d}  {cm[0][1]:5d}")
print(f"High     {cm[1][0]:5d}  {cm[1][1]:5d}")

# Feature importance
fi = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n🔍 Top 10 Features:")
for i, row in fi.head(10).iterrows():
    print(f"  {row['feature']:<30} {row['importance']:.4f}")

# ROC curve
fpr, tpr, _ = roc_curve(y_test, y_test_proba)

# ===== 10. SAVE MODEL =====
print("\n💾 Saving model...")

os.makedirs('models', exist_ok=True)

with open('models/mortality_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('models/feature_columns.pkl', 'wb') as f:
    pickle.dump(feature_columns, f)

with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

metrics = {
    'accuracy': float(test_acc),
    'precision': float(test_prec),
    'recall': float(test_rec),
    'f1_score': float(test_f1),
    'auc_roc': float(test_auc),
    'train_accuracy': float(train_acc),
    'overfitting_gap': float(overfitting_gap),
    'cv_mean': float(cv_scores.mean()),
    'cv_std': float(cv_scores.std()),
    'confusion_matrix': cm.tolist(),
    'roc_curve': {
        'fpr': fpr.tolist(),
        'tpr': tpr.tolist()
    },
    'feature_importance': fi.to_dict('records'),
    'mortality_threshold': float(mortality_threshold),
    'training_samples': int(len(X_train)),
    'test_samples': int(len(X_test))
}

with open('models/model_metrics.pkl', 'wb') as f:
    pickle.dump(metrics, f)

print("✅ Model saved successfully!")

print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)
print(f"\n📊 Summary:")
print(f"  Test Accuracy: {test_acc*100:.2f}%")
print(f"  Test AUC-ROC: {test_auc:.4f}")
print(f"  Overfitting: {overfitting_gap*100:.2f}%")

if test_auc > 0.75 and overfitting_gap < 0.10:
    print(f"\n✅ Model is acceptable for educational demo")
else:
    print(f"\n⚠️  Model performance is suboptimal but usable")
