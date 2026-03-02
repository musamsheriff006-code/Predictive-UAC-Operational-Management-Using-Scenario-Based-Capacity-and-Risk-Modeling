import xgboost as xgb
import joblib
import os
from config import MODEL_PATH

def train_model(X, y):
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        random_state=42
    )
    model.fit(X, y)

    os.makedirs("models_saved", exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return model

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None
