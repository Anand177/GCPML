from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from model_service import load_model_from_gcs, run_model
from pydantic import BaseModel, Field
from typing import Any

import logging
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__file__)

class HouseRecord(BaseModel):
    HOUSE_AGE: int
    HOUSE_AREA: float
    TOTAL_ROOMS: int
    TOTAL_BEDROOMS: int
    POPULATION: int
    OWNER_INCOME: int
    ZIP: str

class PredictRequest(BaseModel):
    records: list[HouseRecord] = Field(min_length=1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.artifact = load_model_from_gcs()
    yield

app = FastAPI(title="House Price Estimator", lifespan=lifespan)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status" : "ok"}

@app.post("/predict")
def predict(payload: PredictRequest, request: Request) -> list[dict[str, Any]]:
    artifact = request.app.state.artifact
    records = [r.model_dump() for r in payload.records]
    try:
        return run_model(artifact, records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

if __name__ == "__main__":
   uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)