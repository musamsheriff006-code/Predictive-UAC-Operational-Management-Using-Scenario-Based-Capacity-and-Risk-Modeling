import numpy as np

def compute_staffing(df):
    df["Staff Required"] = np.ceil(df["Forecasted HHS Care Load"]/10)
    df["Medical Staff Required"] = np.ceil(df["Forecasted HHS Care Load"]/20)
    df["Caseworkers Required"] = np.ceil(df["Forecasted HHS Care Load"]/15)
    return df
