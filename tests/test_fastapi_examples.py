"""Offline HTTP regression checks shared by the tutorial and assignment projects."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "1_fast_api_tutorial"


def load_app(path):
    """Load numeric example filenames without starting their uvicorn servers."""
    name = "regression_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TutorialTests(unittest.TestCase):
    def setUp(self):
        self.old_cwd = Path.cwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(os.chdir, self.old_cwd)

    def client(self, filename):
        module = load_app(TUTORIAL / filename)
        client = self.enterContext(TestClient(module.app))
        return module, client

    def test_every_example_serves_swagger_and_openapi(self):
        paths = sorted((TUTORIAL / "examples").glob("*.py"))
        paths.append(TUTORIAL / "inclass_fastapi_app.py")
        for path in paths:
            with self.subTest(example=path.name), TestClient(load_app(path).app) as client:
                docs = client.get("/docs")
                self.assertEqual(docs.status_code, 200)
                self.assertIn("swagger-ui", docs.text)
                schema = client.get("/openapi.json")
                self.assertEqual(schema.status_code, 200)
                self.assertTrue(schema.json()["paths"])

    def test_greeting_examples(self):
        for filename in ("1_plain_fast.py", "2_plain_fast_main.py", "plain_fast_main.py",
                         "3_fast_main.py", "4_fast_main.py"):
            with self.subTest(example=filename):
                _, client = self.client("examples/" + filename)
                self.assertEqual(client.get("/").json(), {"Hello": "World"})

    def test_typed_path_and_query_parameters(self):
        for filename in ("3_fast_main.py", "4_fast_main.py"):
            with self.subTest(example=filename):
                _, client = self.client("examples/" + filename)
                self.assertEqual(client.get("/hello/Ada").json(), {"hello": "Ada"})
                self.assertEqual(client.get("/square/7").json(), {"result": 49})
                self.assertEqual(client.get("/square/banana").status_code, 422)
        _, client = self.client("examples/4_fast_main.py")
        self.assertEqual(client.get("/items/?skip=2&limit=2").json(),
                         [{"entries": 2}, {"entries": 3}])
        self.assertEqual(client.get("/items/?skip=100").json(), [])
        self.assertEqual(client.get("/items/?skip=banana").status_code, 422)
        self.assertEqual(client.get("/items/?limit=banana").status_code, 422)

    def test_dataframe_items_roundtrip_nullable_fields_and_filtering(self):
        _, client = self.client("examples/5_fast_main.py")
        items = [
            {"name": "full", "description": "All fields", "price": 1.5, "tax": 0.2},
            {"name": "minimal", "description": None, "price": 2.5, "tax": None},
            {"name": "explicit-null", "description": None, "price": 3.5, "tax": None},
        ]
        for item in items:
            # Exercise both omitted optional fields and explicit JSON null values.
            body = {"name": "minimal", "price": 2.5} if item["name"] == "minimal" else item
            response = client.post("/items/", json=body)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"item": item})
        response = client.get("/items/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), items)
        for item in items:
            with self.subTest(item=item["name"]):
                response = client.get("/items/" + item["name"])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), item)
                self.assertEqual(client.get("/items/", params={"name": item["name"]}).json(),
                                 [item])
        self.assertEqual(client.get("/items/?name=missing").json(), [])
        missing = client.get("/items/missing")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json(), {"detail": "Item not found"})

    def test_invalid_items_are_rejected_without_mutating_storage(self):
        _, client = self.client("examples/5_fast_main.py")
        for body in ({}, {"name": "invalid", "price": "hello"},
                     {"name": "invalid", "price": 2.5, "tax": "hello"}):
            with self.subTest(body=body):
                self.assertEqual(client.post("/items/", json=body).status_code, 422)
        self.assertEqual(client.get("/items/").json(), [])

    def test_background_log_is_written_and_invalid_input_does_not_run_task(self):
        _, client = self.client("examples/6_fast_main.py")
        self.assertEqual(client.post("/item", json={}).status_code, 422)
        self.assertFalse(Path("log.txt").exists())
        response = client.post("/item", json={"prompt": "A tutorial image"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Image generation has started."})
        # TestClient waits for Starlette background tasks before returning.
        self.assertEqual(Path("log.txt").read_text(), "A tutorial image\n")

    def test_inclass_routes_validate_input_and_execute_background_tasks(self):
        module, client = self.client("inclass_fastapi_app.py")
        for path, expected in (
            ("/", {"message": "hello class"}),
            ("/hello/Ada", {"message": "hello Ada"}),
            ("/square/3", {"result": 9}),
            ("/item?prompt=Ada", {"message": "hello Ada"}),
        ):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), expected)
        self.assertEqual(client.get("/square/banana").status_code, 422)
        self.assertEqual(client.get("/item").status_code, 422)
        response = client.post("/class", json={"name": "Ada"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "hello Ada"})
        for body in ({}, {"name": None}, {"name": 123}):
            with self.subTest(body=body):
                self.assertEqual(client.post("/class", json=body).status_code, 422)
        with patch.object(module, "say_hello") as say_hello:
            self.assertEqual(client.post("/item", json={}).status_code, 422)
            say_hello.assert_not_called()
            response = client.post("/item", json={"prompt": "Ada"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": "Grüß Di Ada"})
            say_hello.assert_called_once_with("Ada")
        self.assertEqual(client.get("/example").status_code, 200)
        self.assertEqual(Path("log.txt").read_text(), "Example endpoint was visited\n")

    def test_assignment_starter_import_docs_and_background_endpoint(self):
        # Import the actual image_generator package too; no service is instantiated.
        with patch.object(sys, "path", [str(ROOT / "assignment"), *sys.path]):
            module = load_app(ROOT / "assignment" / "app.py")
        with TestClient(module.app) as client:
            self.assertEqual(client.get("/docs").status_code, 200)
            schema = client.get("/openapi.json")
            self.assertEqual(schema.status_code, 200)
            self.assertIn("/example", schema.json()["paths"])
            response = client.get("/example")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": "This is an example endpoint"})
            self.assertEqual(Path("log.txt").read_text(), "Example endpoint was visited\n")


if __name__ == "__main__":
    unittest.main()
