
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from fastapi.requests import Request
from pydantic import BaseModel
import uvicorn


class ImageRequest(BaseModel):
    prompt: str


app = FastAPI()

# Function to be run as a background task.
# This is just a placeholder function for demonstration.
# In your application, this could be a function that generates an image.
def write_log(message: str):
    # Example of a time-consuming task: Writing a message to a file.
    # Replace this with the logic of your image generation task.
    with open("log.txt", "a") as file:
        file.write(f"{message}\n")


@app.post("/item")
async def root(image_request: ImageRequest, background_tasks: BackgroundTasks):
    prompt = image_request.prompt
    background_tasks.add_task(write_log, prompt)
    return {"message": "Image generation has started."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
