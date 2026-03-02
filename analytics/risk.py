import numpy as np

def compute_risk_metrics(df):
    df["Capacity Gap"] = df["Forecasted HHS Care Load"] - df["Forecasted HHS Care Load"].max()
    df["Status"] = np.where(df["Capacity Gap"] > 0, "SHORTAGE", "SURPLUS")
    df["Capacity Breach Probability (%)"] = (df["Capacity Gap"] > 0).mean()*100
    return df
