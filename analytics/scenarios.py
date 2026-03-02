# For future scenario adjustments
def apply_scenario(df, arrival_surge=0, discharge_delay=0):
    df["CBP Intake"] *= (1 + arrival_surge/100)
    df["Discharged from HHS"] *= (1 - discharge_delay/100)
    return df
