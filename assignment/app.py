import os
from fastapi import FastAPI, BackgroundTasks
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

# TODO: Implement the background task function for image generation
# This function will use the ImageGenerator service to generate images
# based on the provided custom prompt and save them.

# TODO: Create an endpoint for retrieving generated images
# The endpoint should take an image ID and return the corresponding image
# if it's ready, or an appropriate status message otherwise.

# TODO: Implement error handling for various possible failure scenarios

# OPTIONAL: Implement any necessary profanity checking or validation for the user prompts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
