from datetime import datetime, timezone
from google.cloud import bigquery, storage
from google.oauth2 import service_account
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import joblib, logging, os, tempfile
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)

# GCP Configurations
GCP_PROJECT_ID = "gcp-project-375309"
GCP_SCOPE = "https://www.googleapis.com/auth/cloud-platform"
GCP_SA_KEY = "C:\\Learning\\AI\\Key\\gcp-project-375309-e4a68a2d2055.json"

BQ_DATASET_ID = "ml"
BQ_HOUSING_TABLE_ID = "housing_detail_raw"
BQ_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_HOUSING_TABLE_ID}"

GCS_BUCKET = "anand12345"
GCS_PATH = "ML/Models"

# ML Configurations
NUMERIC_FEATURES = ["HOUSE_AGE", "HOUSE_AREA", "TOTAL_ROOMS", "TOTAL_BEDROOMS", "POPULATION",
                    "OWNER_INCOME"]
CATEGORICAL_FEATURES = ["ZIP"]
LABEL = "PRICE"

RIDGE_ALPHA = 0.1
TEST_SIZE = 0.3
RANDOM_STATE = 42

MODEL_NAME = "house_pricing"

TRAINING_QUERY = f"""SELECT HOUSE_AGE, HOUSE_AREA, TOTAL_ROOMS, TOTAL_BEDROOMS, POPULATION,
OWNER_INCOME, ZIP, HOUSE_PRICE / 100 AS PRICE
FROM `{BQ_TABLE}`
"""

def get_gcp_credentials() -> service_account.Credentials:
    """ Get GCP Credentials from JSON Key"""
    if not os.path.exists (GCP_SA_KEY):
        raise FileNotFoundError (f" GCP SA Key {GCP_SA_KEY} not found")
    log.info("Authentication Successful")
    return service_account.Credentials.from_service_account_file(GCP_SA_KEY,
            scopes = [GCP_SCOPE])


def load_gcs_training_data(credentials : service_account.Credentials) -> pd.DataFrame:
    """Pull Data from GCS for training"""
    log.info("Querying %s", BQ_TABLE)
    client = bigquery.Client(project = GCP_PROJECT_ID, credentials = credentials)
    df = client.query(TRAINING_QUERY).to_dataframe()
    df["HOUSE_AREA"] = df["HOUSE_AREA"].astype(float)
    df["ZIP"] = df["ZIP"].astype(str)

    log.info("Loaded %d records from %s table", len(df), BQ_TABLE)
    df = df.dropna(subset=NUMERIC_FEATURES + CATEGORICAL_FEATURES + [LABEL])
    log.info("%d selected for training", len(df))
    return df


def build_pipeline() -> Pipeline:
    """Define Preprocessing Pipeline"""
    preprocessor = ColumnTransformer(
        transformers=[ ("num", StandardScaler(), NUMERIC_FEATURES),
                      ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES) ]
    )
    return Pipeline(steps=[("preprocess", preprocessor),
                           ("model", Ridge(alpha=RIDGE_ALPHA)) ]
    )


def train_and_evaluate(df: pd.DataFrame):
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES ]
    y = df[LABEL]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TEST_SIZE, 
            random_state=RANDOM_STATE)
    log.info("Train Rows: %d | Test Rows: %d", len(X_train), len(X_test))

    pipeline = build_pipeline()
    pipeline.fit(X = X_train, y = y_train)
    preds = pipeline.predict(X=X_test)
    metrics = {
        "mean_absolute_error" : float(mean_absolute_error(y_test, preds)),
        "root_mean_squared_error" : float(mean_squared_error(y_test, preds) ** 0.5 ),
        "r2" : float(r2_score(y_test, preds)),
        "train_rows" : int(len(X_train)),
        "test_rows" : int(len(X_test))
    }
    log.info("Model Successfully Created")
    log.info("Test Metrics: %s", metrics)
    return pipeline, metrics


def upload_model_to_gcs(pipeline: Pipeline, metrics: dict, 
                        credentials: service_account.Credentials) -> str:
    """Serialize pileine and load to GCS"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_name = f"{MODEL_NAME}_model.joblib"
    blob_name = f"{GCS_PATH}/{model_name}"
    artifact = {
        "pipeline" : pipeline,
        "numeric_features" : NUMERIC_FEATURES,
        "categorical_features" : CATEGORICAL_FEATURES,
        "label" : LABEL,
        "source_table" : BQ_TABLE,
        "metrics" : metrics,
        "trained_at_utc" : timestamp
    }
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, model_name)
        joblib.dump(artifact, local_path)

        client = storage.Client(project = GCP_PROJECT_ID, credentials = credentials)
        blob = client.bucket(GCS_BUCKET).blob(blob_name=blob_name)
        blob.upload_from_filename(local_path, if_generation_match=None)

    log.info("Model Successfully uploaded to %s", blob_name)
    return blob_name


if __name__ == "__main__":
    credentials = get_gcp_credentials()
    df = load_gcs_training_data(credentials)
    pipeline, metrics = train_and_evaluate(df)
    upload_model_to_gcs(pipeline, metrics, credentials)