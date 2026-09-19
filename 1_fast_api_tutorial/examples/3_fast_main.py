from fastapi import FastAPI
import pandas as pd
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/hello/{name}")
def hello_path(name: str):
    return {"hello" : f"{name}"}


@app.get("/square/{num}")
def get_square(num: int):
    return {"result" : num * num}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
