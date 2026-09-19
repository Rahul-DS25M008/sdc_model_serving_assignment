"""Exercise the installed OpenAI SDK using in-memory HTTP responses only."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# OpenAI 3.x uses httpx2; Starlette's TestClient uses the separate httpx package.
import httpx2
from openai import AsyncOpenAI, OpenAI


path = Path(__file__).resolve().parents[1] / "assignment" / "gpt_service.py"
spec = importlib.util.spec_from_file_location("regression_gpt_service", path)
gpt_service = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gpt_service
spec.loader.exec_module(gpt_service)


def completion(content, refusal=None):
    return {
        "id": "chatcmpl-offline",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [{
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": content, "refusal": refusal},
        }],
    }


class GPTServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.reply = completion("Hello Ada")
        self.sync_client = OpenAI(
            api_key="offline-test-key", base_url="https://offline.invalid/v1",
            http_client=httpx2.Client(transport=httpx2.MockTransport(self.respond)),
        )
        self.async_client = AsyncOpenAI(
            api_key="offline-test-key", base_url="https://offline.invalid/v1",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(self.respond)),
        )
        with patch.object(gpt_service, "OpenAI", return_value=self.sync_client), \
                patch.object(gpt_service, "AsyncOpenAI", return_value=self.async_client):
            self.service = gpt_service.GPTService("offline-test-key", "Check for profanity.")

    async def asyncTearDown(self):
        self.sync_client.close()
        await self.async_client.close()

    def respond(self, request):
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.path, "/v1/chat/completions")
        self.requests.append(json.loads(request.content))
        if isinstance(self.reply, str):
            return httpx2.Response(200, headers={"content-type": "text/event-stream"},
                                   content=self.reply)
        return httpx2.Response(200, json=self.reply)

    async def test_sync_completion_and_helper_preserve_message_history(self):
        history = [{"role": "system", "content": "Be concise."}]
        response = self.service.query_gpt(history, "Hello")
        self.assertEqual(response.choices[0].message.content, "Hello Ada")
        self.assertEqual(self.requests[-1]["model"], "gpt-4o")
        self.assertEqual(self.requests[-1]["messages"], history + [{"role": "user", "content": "Hello"}])
        self.assertEqual(history, [{"role": "system", "content": "Be concise."}])
        self.assertEqual(self.service.get_ai_response(history, "Hello"), "Hello Ada")
        self.assertEqual(self.requests[-1]["model"], "gpt-4o-mini")
        self.reply = completion(None, refusal="Cannot answer")
        self.assertEqual(self.service.get_ai_response([], "Hello"), "")

    async def test_async_stream_uses_sdk_sse_parsing(self):
        chunks = []
        for content, finish_reason in (("Hello ", None), ("Ada", None), (None, "stop")):
            chunks.append({
                "id": "chatcmpl-offline", "object": "chat.completion.chunk",
                "created": 0, "model": "gpt-4o",
                "choices": [{"index": 0, "delta": {"content": content},
                             "finish_reason": finish_reason}],
            })
        self.reply = "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks)
        self.reply += "data: [DONE]\n\n"
        history = [{"role": "system", "content": "Be concise."}]
        stream = await self.service.aquery_gpt(history, "Hello")
        async with stream:
            parts = [chunk.choices[0].delta.content or "" async for chunk in stream]
        self.assertEqual("".join(parts), "Hello Ada")
        self.assertTrue(self.requests[-1]["stream"])
        self.assertEqual(self.requests[-1]["model"], "gpt-4o")
        self.assertEqual(self.requests[-1]["messages"], history + [{"role": "user", "content": "Hello"}])
        self.assertEqual(history, [{"role": "system", "content": "Be concise."}])

    async def test_structured_profanity_response_is_parsed_as_pydantic_model(self):
        for flagged in (True, False):
            with self.subTest(flagged=flagged):
                self.reply = completion(json.dumps({"flagged": flagged}))
                self.assertIs(self.service.contains_profanity("Sample input"), flagged)
                request = self.requests[-1]
                self.assertEqual(request["model"], "gpt-4o-mini")
                self.assertEqual(request["messages"], [
                    {"role": "system", "content": "Check for profanity."},
                    {"role": "user", "content": "Sample input"},
                ])
                self.assertEqual(request["response_format"]["type"], "json_schema")
                schema = request["response_format"]["json_schema"]
                self.assertTrue(schema["strict"])
                self.assertEqual(schema["schema"]["properties"]["flagged"]["type"], "boolean")

    async def test_structured_refusal_preserves_existing_unparsed_fallback(self):
        self.reply = completion(None, refusal="Cannot answer")
        with self.assertLogs(level="ERROR") as logs:
            self.assertIs(self.service.contains_profanity("Sample input"), False)
        self.assertIn("Failed to parse profanity response", logs.output[0])


if __name__ == "__main__":
    unittest.main()
