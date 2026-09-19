from pathlib import Path
from statistics import fmean
import time
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="FastAPI for Data Scientists")


@app.get("/")
def root():
    return {"message": "Hello, data scientists!"}


@app.get("/square/{number}")
def square(number: int):
    return {"result": number * number}


items = [
    {"id": 0, "name": "item-0"},
    {"id": 1, "name": "item-1"},
    {"id": 2, "name": "item-2"},
    {"id": 3, "name": "item-3"},
]


@app.get("/items")
def list_items(skip: int = Query(0, ge=0), limit: int = Query(3, ge=1, le=10)):
    return items[skip:skip + limit]


class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=1, max_length=100)


class PredictionResponse(BaseModel):
    prediction: float
    model: str


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    # A stand-in for model.predict(...); this is just an arithmetic mean.
    return {"prediction": fmean(request.features), "model": "demo-mean-v1"}


@app.post("/predict-slow", response_model=PredictionResponse)
def slow_predict(request: PredictionRequest):
    # Normal def runs in a thread pool. This request still waits for its result.
    time.sleep(5)
    return predict(request)


# One-process classroom storage: restarting the server loses every job.
# Use one server worker for this demo. This is not a durable job queue.
jobs = {}


def run_prediction_job(job_id: str, request: PredictionRequest):
    jobs[job_id] = {"job_id": job_id, "status": "running"}
    try:
        time.sleep(5)
        result = predict(request)
        jobs[job_id] = {"job_id": job_id, "status": "succeeded", "result": result}
    except Exception:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "error": "Prediction failed. Please try again.",
        }


@app.post("/jobs", status_code=202)
def create_job(request: PredictionRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    job = {"job_id": job_id, "status": "queued"}
    jobs[job_id] = job
    # This sync function runs in a thread pool after the response is sent.
    background_tasks.add_task(run_prediction_job, job_id, request)
    return job


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/sample-image", response_class=FileResponse)
def sample_image():
    image_path = Path(__file__).parent / "assets" / "demo.png"
    return FileResponse(image_path, media_type="image/png")
