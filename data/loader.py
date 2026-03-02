import pandas as pd
import numpy as np
from config import LOCATIONS

def load_data(file_upload=None):
    if file_upload:
        df = pd.read_csv(file_upload, parse_dates=["Date"])
        return df
    else:
        # Generate synthetic demo data
        dates = pd.date_range(end=pd.Timestamp.today(), periods=90)
        df_list = []
        for loc in LOCATIONS:
            df_loc = pd.DataFrame({
                "Date": dates,
                "Location": loc,
                "CBP Intake": np.random.poisson(20, len(dates)),
                "CBP Care Load": np.random.poisson(100, len(dates)),
                "Transferred to HHS": np.random.poisson(15, len(dates)),
                "HHS Care Load": np.random.poisson(120, len(dates)),
                "Discharged from HHS": np.random.poisson(10, len(dates))
            })
            df_list.append(df_loc)
        df = pd.concat(df_list, ignore_index=True)
        return df
