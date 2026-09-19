import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from image_generator import ImageGenerator

app = FastAPI()

# Function to be run as a background task.
# This is just a placeholder function for demonstration.
# In your application, this could be a function that generates an image.
def write_log(message: str):
    # Example of a time-consuming task: Writing a message to a file.
    # Replace this with the logic of your image generation task.
    with open("log.txt", "a") as file:
        file.write(f"{message}\n")

@app.get("/example")
async def example_endpoint(background_tasks: BackgroundTasks):
    # This endpoint demonstrates how to add a background task.
    # The `write_log` function will be executed after the response is sent.
    # Note: The task runs in the same process but does not block the response.
    background_tasks.add_task(write_log, "Example endpoint was visited")
    return {"message": "This is an example endpoint"}

# TODO: Define your POST /images endpoint for asynchronous image generation
# This endpoint should accept a custom prompt, process it asynchronously,
# and return an image ID for later retrieval.
class ImageRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=500)
    style: str = Field(
        default="digital illustration",
        min_length=2,
        max_length=100
    )
    mood: str = Field(

        default="cinematic",
        min_length=2,
        max_length=100
    )
    lighting: str = Field(
        default="soft natural lighting",
        min_length=2,
        max_length=100
    )
    composition: str = Field(
        default="balanced composition",
        min_length=2,
        max_length=100
    )
    details: Optional[str] = Field(
        default=None,
        max_length=300
    )


# In-memory storage for image generation jobs.
# A persistent database or queue would normally be used in production.

image_jobs: dict[str, dict[str, str | None]] = {}
GENERATED_IMAGES_DIR = Path(__file__).resolve().parent / "generated_images"
GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def build_image_prompt(request: ImageRequest) -> str:
    prompt_parts = [
        f"Subject: {request.subject.strip()}",
        f"Style: {request.style.strip()}",
        f"Mood: {request.mood.strip()}",
        f"Lighting: {request.lighting.strip()}",
        f"Composition: {request.composition.strip()}",
    ]

    if request.details and request.details.strip():
        prompt_parts.append(f"Additional details: {request.details.strip()}")
    return ". ".join(prompt_parts) + "."


@app.post("/images", status_code=status.HTTP_202_ACCEPTED)
async def create_image(
    request: ImageRequest,
    background_tasks: BackgroundTasks
):
    image_id = str(uuid.uuid4())
    image_prompt = build_image_prompt(request)

    image_jobs[image_id] = {
        "status": "processing",
        "prompt": image_prompt,
        "image_path": None,
        "error": None,
    }

    background_tasks.add_task(
        gen_image_task,
        image_id,
        image_prompt
    )

    return {
        "image_id": image_id,
        "status": "processing",
        "status_url": f"/image/{image_id}",
    }

# TODO: Implement the background task function for image generation
# This function will use the ImageGenerator service to generate images
# based on the provided custom prompt and save them.

def gen_image_task(image_id: str, prompt: str):
    try:
        stability_key = os.getenv("STABILITY_KEY")
        if not stability_key:
            raise RuntimeError(
                "STABILITY_KEY environment variable is not configured"
            )
        image_generator = ImageGenerator(stability_key)
        image_binary = image_generator.generate_image(prompt)
        if not image_binary:
            raise RuntimeError(
                "Image generation completed without returning image data"
            )
        image_path = GENERATED_IMAGES_DIR / f"{image_id}.png"
        image_path.write_bytes(image_binary)
        image_jobs[image_id]["image_path"] = str(image_path)
        image_jobs[image_id]["status"] = "ready"
    except Exception as exc:
        image_jobs[image_id]["status"] = "failed"
        image_jobs[image_id]["error"] = str(exc)

# TODO: Create an endpoint for retrieving generated images
# The endpoint should take an image ID and return the corresponding image
# if it's ready, or an appropriate status message otherwise.

@app.get("/image/{image_id}")
async def get_image(image_id: str):
    job = image_jobs.get(image_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image ID not found"
        )
    if job["status"] == "processing":
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "image_id": image_id,
                "status": "processing",
            }
        )
    if job["status"] == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=job["error"] or "Image generation failed"
        )
    image_path = job["image_path"]
    if not image_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generated image path is missing"
        )

    image_file = Path(image_path)
    if not image_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generated image file could not be found"
        )
    
    return FileResponse(
        path=image_file,
        media_type="image/png",
        filename=f"{image_id}.png"
    )

# TODO: Implement error handling for various possible failure scenarios

# OPTIONAL: Implement any necessary profanity checking or validation for the user prompts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
