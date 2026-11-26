from config import Config
from google.cloud import bigquery, storage
from google.oauth2 import service_account

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import logging, os
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)


GCP_PROJECT_ID = Config.GCP_PROJECT_ID
GCP_SCOPE = Config.GCP_SCOPE
GCP_SA_KEY = Config.GCP_SA_KEY

BQ_DATASET_ID = Config.BQ_DATASET_ID
BQ_TABLE_ID = Config.BQ_AUS_WEATHER_TABLE_ID


BQ_QUERY = f"""SELECT Date, Location, WindGustDir, WindDir9am, WindDir3pm, RainToday, RainTomorrow, 
MinTemp, MaxTemp, Rainfall, Evaporation, Sunshine, WindGustSpeed, WindSpeed9am, WindSpeed3pm, 
Humidity9am, Humidity3pm, Pressure9am, Pressure3pm, Temp9am, Temp3pm
FROM `{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}`"""

CATEGORICAL_FEATURES = ["Location", "WindGustDir", "WindDir9am", "WindDir3pm", "RainToday"]
NUMERICAL_FEATURES = ["MinTemp", "MaxTemp", "Rainfall", "Evaporation", "Sunshine", "WindGustSpeed", 
                      "WindSpeed9am", "WindSpeed3pm", "Humidity9am", "Humidity3pm", "Pressure9am", 
                      "Pressure3pm", "Temp9am", "Temp3pm"]


def get_gcp_credentials() -> service_account.Credentials:
    if not os.path.exists(GCP_SA_KEY):
        raise FileNotFoundError(f"GCP Key not found in path {GCP_SA_KEY}")
    log.info("Authentication Successful")
    return service_account.Credentials.from_service_account_file(GCP_SA_KEY, 
            scopes = [GCP_SCOPE])


def load_data_from_bq(credentials: service_account.Credentials) -> pd.DataFrame:
    """Load Training/ Test data from BQ"""
    log.info("Loading training/ test data from Big Query")
    client = bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)
    df: pd.DataFrame = client.query(BQ_QUERY).to_dataframe()
    log.info("%d records loaded from %s table", len(df), BQ_TABLE_ID)
    return df


def process_date_feature(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Convert Date column to cyclical """
    log.info("Converting Dates to cyclical representations")
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month
    df["DayOfYear"] = df["Date"].dt.day_of_year
    df["Month_Sine"] = np.sin(2 * np.pi * df["Month"]/12)
    df["Month_Cos"] = np.cos(2 * np.pi * df["Month"]/12)

    days_in_year = np.where(df["Date"].dt.is_leap_year, 366, 365)
    day_of_year = df["Date"].dt.day_of_year
    df["DayOfYear_Sine"] = np.sin( 2 * np.pi * day_of_year/days_in_year)
    df["DayOfYear_Cos"] = np.cos(2 * np.pi * day_of_year/ days_in_year)
    df.info()
    date_feature_list : list[str] = ["Month_Sine", "Month_Cos", "DayOfYear_Sine", "DayOfYear_Cos"]
    return df, date_feature_list


def build_preprocessor(date_feature_list : list[str]) -> ColumnTransformer:
    """Cleansing Data"""
    numeric_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ])
    categorical_pipe = Pipeline(steps = [
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    return ColumnTransformer(transformers = [
        ("num", numeric_pipe, NUMERICAL_FEATURES + date_feature_list),
        ("cat", categorical_pipe, CATEGORICAL_FEATURES)
    ], remainder= "drop")



def main():
    """"""
    credentials: service_account.Credentials = get_gcp_credentials()
    df: pd.DataFrame = load_data_from_bq(credentials)
    df, date_feature_list = process_date_feature(df)

    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + date_feature_list
    X = df[feature_cols]
    print(X)



if __name__ == "__main__":
    main()