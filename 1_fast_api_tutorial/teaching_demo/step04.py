from statistics import fmean
import time

from fastapi import FastAPI, Query
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
