
from fastapi import FastAPI
import uvicorn
import pandas as pd

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


@app.get("/items/")
def read_item(skip: int = 0, limit: int = 10):
    # random df with 100 entries
    # return based on skip and limit
    df = pd.DataFrame({"entries": range(100)})
    return df.iloc[skip:skip+limit].to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
