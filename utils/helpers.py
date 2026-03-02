def format_dates(df, col="Date"):
    df[col] = pd.to_datetime(df[col])
    return df
