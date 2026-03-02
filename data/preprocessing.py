def create_features(df):
    df = df.sort_values(["Location", "Date"])
    df["lag_1"] = df.groupby("Location")["HHS Care Load"].shift(1)
    df["lag_3"] = df.groupby("Location")["HHS Care Load"].shift(3)
    df["rolling_7d"] = df.groupby("Location")["HHS Care Load"].shift(1).rolling(7).mean()
    df = df.dropna()
    return df
