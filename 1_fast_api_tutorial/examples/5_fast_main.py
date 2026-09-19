
from fastapi import FastAPI, HTTPException
import uvicorn
import pandas as pd
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = FastAPI()
## static list to store items
df = pd.DataFrame(columns=["name", "description", "price", "tax"])



## endpoint to add items to the df
@app.post("/items/")
async def create_item(item: Item):
    df.loc[len(df)] = pd.Series(item.model_dump())
    return {"item": item}


##also add an endpoint to get all items and search by name
@app.get("/items/")
def get_items(name: str=None):
    if name:
        return df[df["name"] == name].to_dict(orient="records")
    return df.to_dict(orient="records")


## get items with path params, search by name
@app.get("/items/{name}")
def get_item(name: str):
    filtered_df = df[df["name"] == name]
    if not filtered_df.empty:
        # Convert the first matched row to a dictionary
        return filtered_df.iloc[0].to_dict()
    else:
        raise HTTPException(status_code=404, detail="Item not found")


## python main entry point

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
