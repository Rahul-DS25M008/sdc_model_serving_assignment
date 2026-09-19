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