from .stability_api import StabilityApiGenerator


class ImageGenerator:
    negative_prompt = ("photo, painting, cartoon, realistic, portrait, face, colored, 3d, naked, realism, real, hair, "
                       "closeup, closeup shot, lowres, text, error, cropped, worst quality, low quality, "
                       "jpeg artifacts,"
                       "ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn "
                       "hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, "
                       "bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, "
                       "missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, "
                       "long neck, username, watermark, signature")

    image_prompt_template = "{user_input} comical sketch on paper technical details, highly detailed, high resolution"

    def __init__(self, api_key):
        self.stability_api = StabilityApiGenerator(api_key)

    def generate_image(self, text: str):
        image_prompt = self.image_prompt_template.format(user_input=text)
        return self.stability_api.generate_image(image_prompt, self.negative_prompt)
