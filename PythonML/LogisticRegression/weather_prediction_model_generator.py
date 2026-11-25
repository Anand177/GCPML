from config import Config
from google.cloud import bigquery, storage
from google.oauth2 import service_account

import logging, math, os
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)


GCP_PROJECT_ID = Config.GCP_PROJECT_ID
GCP_SCOPE = Config.GCP_SCOPE
GCP_SA_KEY = Config.GCP_SA_KEY

BQ_DATASET_ID = Config.BQ_DATASET_ID
BQ_TABLE_ID = Config .BQ_AUS_WEATHER_TABLE_ID


BQ_QUERY = f"""SELECT Date, Location, WindGustDir, WindDir9am, WindDir3pm, RainToday, RainTomorrow, 
MinTemp, MaxTemp, Rainfall, Evaporation, Sunshine, WindGustSpeed, WindSpeed9am, WindSpeed3pm, 
Humidity9am, Humidity3pm, Pressure9am, Pressure3pm, Temp9am, Temp3pm
FROM `{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}`"""

CATEGORICAL_FEATURES = ["Location", "WindGustDir", "WindDir9am", "WindDir3pm", "RainToday"]
NUMERICAL_FEATURES = ["MinTemp", "MaxTemp", "Rainfall", "Evaporation", "Sunshine", "WindGustSpeed", 
                      "WindSpeed9am", "WindSpeed3pm", "Humidity9am", "Humidity3pm", "Pressure9am", 
                      "Pressure3pm", "Cloud9am", "Cloud3pm", "Temp9am", "Temp3pm"]


def get_gcp_credentials() -> service_account.Credentials:
    if not os.path.exists(GCP_SA_KEY):
        raise FileNotFoundError(f"GCP Key not found in path {GCP_SA_KEY}")
    log.info("Authentication Successful")
    return service_account.Credentials.from_service_account_file(GCP_SA_KEY, 
            scopes = [GCP_SCOPE])


def load_data_from_bq(credentials: service_account.Credentials) -> pd.DataFrame:
    """Load Training/ Test data from BQ"""
    client = bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)
    df = client.query(BQ_QUERY).to_dataframe()
    return df


def process_date_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Date column to cyclical """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month
    df["DayOfYear"] = df["Date"].dt.day_of_year
    df["Month_Sine"] = math.sin(2 * math.pi * df["Month"]/12)
    df["Month_Cos"] = math.cos(2 * math.pi * df["Month"]/12)

    days_in_year = df["Date"].dt.is_leap_year({True: 366, False: 365})
    day_of_year = df["Date"].dt.day_of_year
    df["DayOfYear_Sine"] = math.sin( 2 * math.pi * day_of_year/days_in_year)
    df["DayOfYear_Cos"] = math.cos(2 * math.pi * day_of_year/ days_in_year)
    df.info()
    return df


def build_preprocessor():
    """Cleansing Data"""



def main():
    """"""
    credentials: service_account.Credentials = get_gcp_credentials()
    df: pd.DataFrame = load_data_from_bq(credentials)
    process_date_feature(df)



if __name__ == "__main__":
    main()