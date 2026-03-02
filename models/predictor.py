import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error


def forecast_per_location(df, scenario_settings, staff_pct=100, forecast_horizon=14, staff_cost=250):
    """
    Generate HHS Care Load forecasts per location and scenario.

    Args:
        df (pd.DataFrame): Preprocessed data with features.
        scenario_settings (list of dict): List of scenarios with 'arrival_surge' and 'discharge_delay'.
        staff_pct (float): Available staff percentage for capacity calculations.
        forecast_horizon (int): Number of days to forecast.
        staff_cost (float): Cost per staff per day.

    Returns:
        pd.DataFrame: Forecasted HHS Care Load with KPIs, staffing, and capacity metrics.
    """
    forecasts = []

    for scenario in scenario_settings:
        arrival_surge = scenario["arrival_surge"]
        discharge_delay = scenario["discharge_delay"]

        df_scenario = df.copy()
        df_scenario["CBP Intake"] *= (1 + arrival_surge / 100)
        df_scenario["Discharged from HHS"] *= (1 - discharge_delay / 100)

        for loc, group in df_scenario.groupby("Location"):
            df_loc = group.copy()
            features = ["lag_1", "lag_3", "rolling_7d", "CBP Intake", "Transferred to HHS"]
            X = df_loc[features]
            y = df_loc["HHS Care Load"]

            # Train XGBoost model
            model = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05)
            model.fit(X, y)

            # Forecast
            loc_horizon = min(forecast_horizon, len(X))
            X_future = X.tail(loc_horizon)
            forecast = model.predict(X_future)

            forecast_df = df_loc.tail(loc_horizon).copy()
            forecast_df["Forecasted HHS Care Load"] = forecast
            forecast_df["Scenario"] = f"Arrival {arrival_surge}%, Discharge {discharge_delay}%"

            # Capacity & Status
            capacity = df_loc["HHS Care Load"].max() * staff_pct / 100
            forecast_df["Capacity Gap"] = forecast_df["Forecasted HHS Care Load"] - capacity
            forecast_df["Status"] = np.where(forecast_df["Capacity Gap"] > 0, "SHORTAGE", "SURPLUS")

            # Ensure Capacity Breach Probability exists
            forecast_df["Capacity Breach Probability (%)"] = (forecast_df["Capacity Gap"] > 0).mean() * 100

            # Staffing calculations
            forecast_df["Staff Required"] = np.ceil(forecast_df["Forecasted HHS Care Load"] / 10)
            forecast_df["Medical Staff Required"] = np.ceil(forecast_df["Forecasted HHS Care Load"] / 20)
            forecast_df["Caseworkers Required"] = np.ceil(forecast_df["Forecasted HHS Care Load"] / 15)
            forecast_df["Estimated Daily Cost"] = forecast_df["Staff Required"] * staff_cost  # Corrected

            # KPIs
            mae = mean_absolute_error(df_loc["HHS Care Load"].tail(loc_horizon), forecast)
            forecast_accuracy = max(0, 100 - (mae / df_loc["HHS Care Load"].mean() * 100))
            forecast_stability = np.std(forecast) / np.mean(forecast) * 100
            forecast_df["Forecast Accuracy (%)"] = forecast_accuracy
            forecast_df["Forecast Stability Index (%)"] = forecast_stability
            forecast_df["Model Robustness"] = 100 - forecast_stability

            forecasts.append(forecast_df)

    return pd.concat(forecasts, ignore_index=True)
