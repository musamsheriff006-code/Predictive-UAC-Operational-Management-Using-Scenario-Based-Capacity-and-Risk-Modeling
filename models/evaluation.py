from sklearn.metrics import mean_absolute_error
import numpy as np

def evaluate_model(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    accuracy = max(0, 100 - (mae / np.mean(y_true) * 100))
    stability = np.std(y_pred) / np.mean(y_pred) * 100

    return {
        "mae": mae,
        "accuracy": accuracy,
        "stability": stability,
        "robustness": 100 - stability
    }
