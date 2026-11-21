from ..config import Config
from google.cloud import bigquery, storage
from google.oauth2 import service_account
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import logging, os
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)

# BQ Configurations
GCP_PROJECT_ID = Config.GCP_PROJECT_ID
GCP_SCOPE = Config.GCP_SCOPE
GCP_SA_KEY = Path(Config.GCP_KEY_PATH) / Config.GCP_KEY_FILE

BQ_TABLE = f"{GCP_PROJECT_ID}.{Config.BQ_DATASET_ID}.{Config.BQ_HOUSING_TABLE}"

GCS_TABLE = Config.GCS_BUCKET


# ML Configurations
NUMERIC_FEATURES = ["HOUSE_AGE", "HOUSE_AREA", "TOTAL_ROOMS", "TOTAL_BEDROOMS", "POPULATION",
                    "OWNER_INCOME"]
CATEGGORICAL_FEATURES = ["ZIP"]
LABEL = "PRICE"

RIDGE_ALPHA = 0.1
TEST_SIZE = 0.3
RANDOM_STATE = 42

TRAINING_QUERY = f"""SELECT HOUSE_AGE, HOUSE_AREA, TOTAL_ROOMS, TOTAL_BEDROOMS, POPULATION,
OWNER_INCOME, ZIP, HOUSE_PRICE / 100 AS PRICE
FROM `{BQ_TABLE}`
"""

def get_gcp_credentials() -> service_account.Credentials:
    """ Get GCP Credentials from JSON Key"""
    if not os.path.exists (GCP_SA_KEY):
        raise FileNotFoundError (f" GCP SA Key {GCP_SA_KEY} not found")
    return service_account.Credentials.from_service_account_file(GCP_SA_KEY,
            scopes = [GCP_SCOPE])


def load_gcs_training_data(credentials : service_account.Credentials) -> pd.DataFrame:
    """Pull Data from GCS for training"""
    log.info(f"Querying {BQ_TABLE}")
    client = bigquery.Client(project = GCP_PROJECT_ID, credentials = credentials)
    df = client.query(TRAINING_QUERY).to_dataframe()
    df["HOUSE_AREA"] = df["HOUSE_AREA"].astype(float)
    df["ZIP"] = df["ZIP"].astype(str)

    log.info(f"Loaded {len(df)} records from {BQ_TABLE} table")
    df = df.dropna(subset=NUMERIC_FEATURES + CATEGGORICAL_FEATURES + [LABEL])
    log.info(f"{len(df)} selected for training")
    return df


def build_pipeline():
    """Define Preprocessing Pipeline"""
    



def main():
    credentials = get_gcp_credentials()
    df = load_gcs_training_data(credentials)

    return