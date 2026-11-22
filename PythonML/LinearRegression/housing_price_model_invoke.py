from google.cloud import storage
from google.oauth2 import service_account

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
MODEL_NAME = "house_pricing_model.joblib"


def get_gcp_credentials() -> service_account.Credentials:
    """ Get GCP Credentials from JSON Key"""
    if not os.path.exists (GCP_SA_KEY):
        raise FileNotFoundError (f" GCP SA Key {GCP_SA_KEY} not found")
    log.info("Authentication Successful")
    return service_account.Credentials.from_service_account_file(GCP_SA_KEY,
            scopes = [GCP_SCOPE])


def load_model_from_gcs(credentials: service_account.Credentials, model_name: str) -> dict[str, any]:
    """Download model from GCS and load"""
    client = storage.Client(credentials= credentials, project= GCP_PROJECT_ID)
    blob_name = f"{GCS_PATH}/{model_name}"
    blob = client.bucket(GCS_BUCKET).blob(blob_name)

    if not blob.exists():
        raise FileNotFoundError(f"Model Artifact not found @ {blob_name}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, os.path.basename(blob_name))
        log.info("Downloaded model to path %s", local_path.__str__)
        blob.download_to_filename(local_path)
        artifact = joblib.load(local_path)

    log.info("Loaded model from %s", blob_name)
    return artifact


def prepare_input_data(records : list[dict[str, any]], numeric_features: list[str], 
                categorical_features: list[str]) -> pd.DataFrame:
    "Validate input and prepare data for Model inferencing"
    df = pd.DataFrame(records)
    expected_cols = numeric_features + categorical_features
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns -> {missing_cols}")
    df = df[expected_cols].copy()
    df["HOUSE_AREA"] = df["HOUSE_AREA"].astype(float)
    df["ZIP"] = df["ZIP"].astype(str)
    return df


def run_model(artifact : dict[str, any], records : list[dict[str, any]]) -> str:
    """Execute Model with inputs"""
    pipeline = artifact.get("pipeline")
    numeric_features = artifact.get("numeric_features")
    categorical_features = artifact.get("categorical_features")
    label = artifact.get("label")

    X_new = prepare_input_data(records, numeric_features, categorical_features)
    predicted_op = pipeline.predict(X_new)

    result = X_new.copy()
    result[f"PREDICTED_{label}"] = predicted_op * 100
    return result.to_json(orient="records", indent=3)


if __name__ == "__main__":
    sample_inputs = [{
        "HOUSE_AGE": 1,
        "HOUSE_AREA": 850.0,
        "TOTAL_ROOMS": 3,
        "TOTAL_BEDROOMS": 1,
        "POPULATION": 87560.0,
        "OWNER_INCOME": 150100,
        "ZIP": "10379"
    },
    {
        "HOUSE_AGE": 12,
        "HOUSE_AREA": 1200.0,
        "TOTAL_ROOMS": 4.0,
        "TOTAL_BEDROOMS": 2.0,
        "POPULATION": 58226,
        "OWNER_INCOME": 100000,
        "ZIP": "10702"
    }]

    credentials = get_gcp_credentials()
    artifacts = load_model_from_gcs(credentials, MODEL_NAME)
    df = run_model(artifacts, sample_inputs)
    print(df)