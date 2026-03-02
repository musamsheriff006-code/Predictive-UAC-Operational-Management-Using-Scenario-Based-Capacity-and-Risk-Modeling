REQUIRED_COLUMNS = [
    "Date",
    "Location",
    "CBP Intake",
    "Transferred to HHS",
    "HHS Care Load",
    "Discharged from HHS"
]

def validate_schema(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
