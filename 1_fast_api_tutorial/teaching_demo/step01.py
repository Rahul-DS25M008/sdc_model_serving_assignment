from fastapi import FastAPI

app = FastAPI(title="FastAPI for Data Scientists")


@app.get("/")
def root():
    return {"message": "Hello, data scientists!"}
