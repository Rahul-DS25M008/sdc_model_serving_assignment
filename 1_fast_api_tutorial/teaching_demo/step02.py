from fastapi import FastAPI, Query

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
