import warnings
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation


class StabilityApiGenerator:
    def __init__(self, api_key: str):
        # Set up our connection to the API.
        self.stability_api = client.StabilityInference(
            host='grpc.stability.ai:443',  # Host reference.
            key=api_key,  # API Key reference.
            verbose=True,  # Print debug messages.
            engine="stable-diffusion-xl-1024-v1-0"  # Set the engine to use for generation.
        )

    def __stability_request(self, prompt, negative_prompt):
        prompt = [
            generation.Prompt(
                text=prompt, parameters=generation.PromptParameters(weight=1)), # pyright: ignore[reportCallIssue]
            generation.Prompt(
                text=negative_prompt, # pyright: ignore[reportCallIssue]
                parameters=generation.PromptParameters(weight=-1)) # pyright: ignore[reportCallIssue]
        ]
        return self.stability_api.generate(
            prompt=prompt,
            steps=30,
            cfg_scale=8.0,
            width=1024,
            height=1024,
            samples=1,
            sampler=generation.SAMPLER_K_DPMPP_2M)


    # Generate image and return raw bytes.
    # in order to return it via FastAPI, you need to use
    # image_binary = image_generator.generate_image("A fantasy landscape, trending on artstation")
    # return Response(content=image_binary, media_type="image/png")
    def generate_image(self, prompt, negative_prompt):
        answers = self.__stability_request(prompt, negative_prompt)

        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    return artifact.binary
