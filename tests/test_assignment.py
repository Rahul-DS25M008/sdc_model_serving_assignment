"""Offline tests for the completed image-generation assignment API."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "assignment"

if str(ASSIGNMENT) not in sys.path:
    sys.path.insert(0, str(ASSIGNMENT))

import app as assignment_app

class FakeImageGenerator:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_image(self, prompt):
        return b"fake-png-data"

class FailingImageGenerator:
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_image(self, prompt):
        raise RuntimeError("Simulated Stability failure")

class FlaggingGPTService:
    def __init__(self, api_key, profanity_prompt):
        self.api_key = api_key
        self.profanity_prompt = profanity_prompt

    def contains_profanity(self, prompt):
        return True

class AssignmentAPITests(unittest.TestCase):
    def setUp(self):
        assignment_app.image_jobs.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.original_generated_dir = assignment_app.GENERATED_IMAGES_DIR
        assignment_app.GENERATED_IMAGES_DIR = Path(self.temp_dir.name)
        self.addCleanup(
            setattr,
            assignment_app,
            "GENERATED_IMAGES_DIR",
            self.original_generated_dir
        )
        self.environment = patch.dict(
            os.environ,
            {
                "STABILITY_KEY": "offline-stability-key",
                "OPENAI_API_KEY": "offline-openai-key",
                "ENABLE_PROFANITY_CHECK": "false",
            },
            clear=False,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = self.enterContext(
            TestClient(assignment_app.app)
        )

    def test_image_request_validation(self):
        invalid_requests = [
            {},
            {"subject": "ab"},
            {"subject": "   "},
            {"subject": " a "},
        ]

        for body in invalid_requests:
            with self.subTest(body=body):
                response = self.client.post("/images", json=body)
                self.assertEqual(response.status_code, 422)

    def test_image_generation_and_retrieval(self):
        with patch.object(
            assignment_app,
            "ImageGenerator",
            FakeImageGenerator
        ):
            response = self.client.post(
                "/images",
                json={"subject": "A quiet library"}
            )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["status"], "processing")
        self.assertIn("image_id", body)
        self.assertEqual(
            body["status_url"],
            f"/image/{body['image_id']}"
        )

        image_id = body["image_id"]
        job = assignment_app.image_jobs[image_id]
        # TestClient waits until Starlette background tasks finish.
        self.assertEqual(job["status"], "ready")
        self.assertIn("A quiet library", job["prompt"])
        image_response = self.client.get(
            f"/image/{image_id}"
        )

        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(
            image_response.headers["content-type"],
            "image/png"
        )
        self.assertEqual(
            image_response.content,
            b"fake-png-data"
        )

    def test_unknown_image_returns_404(self):
        response = self.client.get(
            "/image/not-a-real-image-id"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Image ID not found"}
        )

    def test_generation_failure_is_recorded(self):
        with patch.object(
            assignment_app,
            "ImageGenerator",
            FailingImageGenerator
        ):
            response = self.client.post(
                "/images",
                json={"subject": "A broken generator test"}
            )

        self.assertEqual(response.status_code, 202)
        image_id = response.json()["image_id"]
        self.assertEqual(
            assignment_app.image_jobs[image_id]["status"],
            "failed"
        )

        image_response = self.client.get(
            f"/image/{image_id}"
        )

        self.assertEqual(image_response.status_code, 500)
        self.assertIn(
            "Simulated Stability failure",
            image_response.json()["detail"]
        )

    def test_missing_stability_key_returns_503(self):
        with patch.dict(
            os.environ,
            {"STABILITY_KEY": ""},
            clear=False
        ):
            response = self.client.post(
                "/images",
                json={"subject": "A valid image prompt"}
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "detail":
                "Image generation service is not configured"
            }
        )
        self.assertEqual(
            assignment_app.image_jobs,
            {}
        )

    def test_enabled_profanity_check_can_reject_prompt(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_PROFANITY_CHECK": "true",
                "OPENAI_API_KEY": "offline-openai-key",
            },
            clear=False,
        ), patch.object(
            assignment_app,
            "GPTService",
            FlaggingGPTService
        ):
            response = self.client.post(
                "/images",
                json={"subject": "A prompt to be flagged"}
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "detail":
                "Prompt was rejected by the profanity check"
            }
        )
        self.assertEqual(
            assignment_app.image_jobs,
            {}
        )

if __name__ == "__main__":
    unittest.main()