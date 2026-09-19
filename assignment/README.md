### Project Description: Building a FastAPI Application with Stable Diffusion Image Generation

**Objective**: Develop a FastAPI application from scratch that integrates the Stable Diffusion model, provided by Stability AI for custom image generation. You will create an asynchronous API that accepts unique prompts, processes them using Stable Diffusion, and generates corresponding images.

#### Background:
- Stable Diffusion is a powerful AI model capable of creating detailed images from textual descriptions.
- For now we'll simply integrate their sdk and access the model using their SaaS offering.
- Your task is to understand how to effectively utilize a ml model in a FastAPI context.

#### Resources Provided:
- Access to the `ImageGenerator` API that uses Stable Diffusion.
- A GPT-Service Implementation + API for optional profanity checking.
- An API key for the `ImageGenerator` service.
- Documentation on Stable Diffusion and its prompt-handling capabilities.

#### Key Tasks and Requirements:
1. **Set Up a FastAPI Project**:
   - Initialize a new FastAPI application.
   - Install necessary dependencies, including libraries for interacting with the `ImageGenerator` service.

2. **Custom Prompt Development**:
   - Design a unique prompt structure that users can utilize your own image requirements.

3. **Asynchronous Image Generation Endpoint (`/images`)**:
   - Create an endpoint to accept image generation requests.
   - Implement asynchronous processing using FastAPI's `BackgroundTasks`.
   - Optional: use redis queue

4. **Background Task for Image Generation (`gen_image_task`)**:
   - Code a function that uses the `ImageGenerator` with custom prompts to generate images.
   - Handle image saving and retrieval.

5. **Image Retrieval Endpoint (`/image/{image_id}`)**:
   - Develop an endpoint for users to retrieve their generated images using an image ID.
   - Implement appropriate responses for different image statuses (e.g., processing, ready, not found).


#### Deliverables:
- Complete source code of the FastAPI application.
- A README or documentation detailing the API usage, setup instructions, and any important decisions made during development.

#### Evaluation Criteria:
- Functionality and correctness of the FastAPI application in an async way.
- Effective integration of the Stable Diffusion model.
- Creativity and utility of the custom prompt system.

#### Tips:
- Start with a basic FastAPI setup and gradually integrate the image generation features.


This project is an excellent opportunity to demonstrate your skills in web API development, asynchronous programming, and AI model integration. Good luck!

---

## Implementation

This solution implements an asynchronous FastAPI image-generation API using the provided `ImageGenerator` service and Stability AI.

The application accepts a structured image request, builds a complete generation prompt, creates a unique image ID, and schedules image generation using FastAPI `BackgroundTasks`. The generated image can later be retrieved through the `/image/{image_id}` endpoint.

### Main Features

* FastAPI application with interactive Swagger documentation
* Structured custom prompt system
* Input validation using Pydantic
* Asynchronous image generation using `BackgroundTasks`
* Unique UUID-based image IDs (My take on ID generations)
* Stable Diffusion image generation through the provided `ImageGenerator`
* Generated PNG image storage
* Image status and retrieval endpoint
* Error handling for missing configuration and generation failures
* Optional GPT-based profanity checking (Verified with personal API key)
* Offline automated tests using mocked external services

## Architecture

The image-generation workflow is:

```text
POST /images
     |
     v
Validate ImageRequest
     |
     v
Build structured prompt
     |
     v
Optional profanity check
     |
     v
Generate UUID
     |
     v
Store job as "processing"
     |
     v
FastAPI BackgroundTasks
     |
     v
gen_image_task()
     |
     v
ImageGenerator / Stability AI
     |
     v
Save generated PNG
     |
     v
Update job to "ready"
     |
     v
GET /image/{image_id}
```

Job metadata is stored in memory for this assignment. Generated images are stored in the `generated_images/` directory.

## Custom Prompt System

Instead of accepting only one free-text prompt, the API accepts structured image-generation parameters:

* `subject` - required main subject or scene
* `style` - visual style
* `mood` - intended atmosphere
* `lighting` - lighting conditions
* `composition` - framing or composition
* `details` - optional additional requirements

Only `subject` is required. The remaining fields have useful defaults.

Example:

```json
{
  "subject": "A futuristic Vienna tram crossing a rain-soaked street at night",
  "style": "cinematic cyberpunk illustration",
  "mood": "mysterious and atmospheric",
  "lighting": "neon reflections and soft fog",
  "composition": "wide street-level shot",
  "details": "high detail, wet pavement and realistic perspective"
}
```

The application combines these fields into a single structured prompt before passing it to the provided `ImageGenerator`.

For example:

```text
Subject: A futuristic Vienna tram crossing a rain-soaked street at night.
Style: cinematic cyberpunk illustration.
Mood: mysterious and atmospheric.
Lighting: neon reflections and soft fog.
Composition: wide street-level shot.
Additional details: high detail, wet pavement and realistic perspective.
```

Pydantic validation also trims input strings and rejects missing, too-short, or whitespace-only required values.

## Setup with GitHub Codespaces

The repository contains a dev container configuration using Python 3.11 and `uv`.

Create a Codespace from the repository:

1. Open the repository on GitHub.
2. Select **Code > Codespaces**.
3. Create a Codespace from the `main` branch.
4. Wait for the dev container setup to complete.

The dev container installs the locked environments automatically.

### Required Environment Variable

The Stability API key and OPENAI_API_KEY are configured as a GitHub Codespaces secret and I subsequently removed the .env:

```text
STABILITY_KEY
OPENAI_API_KEY
```

The application checks for this value before accepting image-generation jobs.

### Optional Environment Variables

For GPT-based profanity checking:

```text
OPENAI_API_KEY
ENABLE_PROFANITY_CHECK=true
PROFANITY_PROMPT_FILE=./profanity_prompt.txt
```

Profanity checking is disabled by default:

```text
ENABLE_PROFANITY_CHECK=false
```

This allows the main image-generation API to operate independently of the optional OpenAI service.

API keys should not be committed to the repository.

## Running the Application

From the repository root:

```bash
cd assignment
uv sync --locked
uv run --locked uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

In a Codespace, open the forwarded port 8000.

Interactive API documentation is available at:

```text
/docs
```

For a local environment, this is normally:

```text
http://127.0.0.1:8000/docs
```

## POST `/images`

Creates a new asynchronous image-generation job.

Example request:

```json
{
  "subject": "A small futuristic robot reading a book in a quiet library",
  "style": "detailed concept art",
  "mood": "calm and curious",
  "lighting": "warm ambient lighting",
  "composition": "centered medium shot",
  "details": "bookshelves in the background, clean composition"
}
```

Successful response:

```http
202 Accepted
```

```json
{
  "image_id": "52d799cf-b629-4829-a30e-07ef9dd6df76",
  "status": "processing",
  "status_url": "/image/52d799cf-b629-4829-a30e-07ef9dd6df76"
}
```

The request returns before image generation finishes. The actual generation is executed as a FastAPI background task.

## GET `/image/{image_id}`

Retrieves the status or generated image associated with an image ID.

### Processing

If generation is still running:

```http
202 Accepted
```

```json
{
  "image_id": "52d799cf-b629-4829-a30e-07ef9dd6df76",
  "status": "processing"
}
```

### Ready

When generation succeeds:

```http
200 OK
Content-Type: image/png
```

The generated PNG file is returned directly.

### Unknown ID

```http
404 Not Found
```

```json
{
  "detail": "Image ID not found"
}
```

### Generation Failure

If image generation fails, the job is marked as failed and the retrieval endpoint returns an error response.

```http
500 Internal Server Error
```

## Error Handling

The application handles several failure scenarios:

* invalid request data: `422 Unprocessable Entity`
* missing Stability configuration: `503 Service Unavailable`
* unknown image ID: `404 Not Found`
* failed background image generation: `500 Internal Server Error`
* missing generated image file: `500 Internal Server Error`
* rejected profanity check: `400 Bad Request`
* unavailable optional prompt-validation service: `503 Service Unavailable`

Background-task exceptions are captured and stored in the associated job instead of being allowed to silently terminate the generation process.

## Optional Profanity Checking

The provided `GPTService` can be used to validate the final constructed image prompt before a generation job is submitted.

Enable it with:

```bash
export ENABLE_PROFANITY_CHECK=true
```

When enabled, `OPENAI_API_KEY` must also be configured.

The system prompt used by the profanity classifier is stored in:

```text
profanity_prompt.txt
```

When profanity checking is disabled, the OpenAI API is not required by the image-generation workflow.

## Testing

The assignment contains offline tests that mock the external Stability and OpenAI services.

From the `assignment` directory, run only the assignment tests with:

```bash
uv run --locked python -m unittest discover -s ../tests -p "test_assignment.py" -v
```

Run the complete repository test suite with:

```bash
uv run --locked python -m unittest discover -s ../tests -v
```

The assignment tests verify:

* request validation
* whitespace handling
* asynchronous job creation
* image generation and retrieval
* image storage
* unknown image IDs
* generation failures
* missing Stability configuration
* optional profanity rejection

The mocked tests do not consume Stability AI or OpenAI API requests.

## Design Decisions

### FastAPI `BackgroundTasks`

`BackgroundTasks` was selected because it directly satisfies the assignment requirement and allows the POST endpoint to return before the image-generation task completes.

I felt BackgroundTasks to be already sufficient for this project and hence decided not to add a separate Redis/RQ worker (maybe along with Celery). From my experience, Redis/Celery is only required if we expect many requests arriving upon which we would need a way to store the requests and responses as logs.

### In-Memory Job Storage

Job status is stored in an in-memory dictionary.

This keeps the assignment implementation small and makes the asynchronous workflow easy to understand. A production deployment would normally use persistent storage such as Redis or a database.

### Local Image Storage

Generated images are written to:

```text
assignment/generated_images/
```

This directory is excluded from Git.

A production service could instead use object storage such as S3-compatible storage.

### External Services Are Created Only When Needed

`ImageGenerator` is instantiated inside the background task instead of during module import. This allows the FastAPI application and offline tests to start without immediately requiring a Stability API connection.

The optional GPT profanity service is similarly created only when profanity checking is enabled.

## Limitations

This implementation is designed for the assignment rather than as a distributed production service.

Important limitations include:

* job metadata is lost when the application process restarts
* generated images are stored on the local filesystem
* FastAPI background tasks are tied to the running application process
* there is no authentication or per-user job ownership
* there is no automatic cleanup policy for generated files
* multiple application workers would not share the in-memory job dictionary

For a production deployment, a persistent job store, external worker queue, shared image storage, authentication, and cleanup strategy would be appropriate.
