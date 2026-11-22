from google.cloud import storage

import joblib, logging, os, tempfile
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)

GCP_PROJECT_ID = "gcp-project-375309"
GCS_BUCKET = "anand12345"
GCS_PATH = "ML/Models"
MODEL_NAME = "house_pricing_model.joblib"

def load_model_from_gcs(model_name: str = MODEL_NAME) -> dict[str, any]:
    """Load model from GCS and load"""
    client = storage.Client(project= GCP_PROJECT_ID)
    blob_name = f"{GCS_PATH}/{model_name}"
    blob = client.bucket(GCS_BUCKET).blob(blob_name)

    if not blob.exists():
        raise FileNotFoundError(f"Model Artifact not found @ {blob_name}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_path = os.path.join(tmp_dir, os.path.basename(blob_name))
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

    if pipeline is None or numeric_features is None or categorical_features is None or label is None:
        raise ValueError("""Model artifact is missing one of: pipeline, numeric_features, 
                    categorical_features, label""")

    X_new = prepare_input_data(records, numeric_features, categorical_features)
    predicted_op = pipeline.predict(X_new)
    output = [{**rec, "PREDICTED_PRICE": float(p)} for rec, p in zip(records, predicted_op)]
    log.info("Predicted Output %s", output)
    return output

"""    result = X_new.copy()
    result[f"PREDICTED_{label}"] = predicted_op * 100
    return result.to_json(orient="records")
"""
    