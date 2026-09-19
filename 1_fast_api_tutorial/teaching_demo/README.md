# FastAPI practice examples

Run every command below from `1_fast_api_tutorial`. These examples use the tutorial's
`pyproject.toml`, locked dependencies, and environment. It needs no API keys or
external services.

Start the minimal app on port 8011:

```sh
uv run --locked uvicorn main:app --app-dir teaching_demo --reload --port 8011
```

Open [Swagger UI](http://127.0.0.1:8011/docs) and try the root route. You can extend
`teaching_demo/main.py` as you work through the notebook, or explore a complete
checkpoint directly:

```sh
uv run --locked uvicorn step01:app --app-dir teaching_demo --reload --port 8011
uv run --locked uvicorn step02:app --app-dir teaching_demo --reload --port 8011
uv run --locked uvicorn step03:app --app-dir teaching_demo --reload --port 8011
uv run --locked uvicorn step04:app --app-dir teaching_demo --reload --port 8011
uv run --locked uvicorn step05:app --app-dir teaching_demo --reload --port 8011
```

Run one server at a time; stop it with **Ctrl+C** before choosing another checkpoint.

| Checkpoint | Adds |
| --- | --- |
| `step01.py` | Minimal app, root route, and automatic documentation |
| `step02.py` | Typed path parameters and constrained query parameters |
| `step03.py` | Pydantic request and response models for a mean prediction |
| `step04.py` | A slow prediction that keeps the request waiting |
| `step05.py` | Background jobs, status polling, and a local image response |

The final checkpoint stores jobs in one process's memory. Restarting clears the
jobs; use a single server worker. The image is included at `assets/demo.png` and
resolved relative to the Python module, so it works from the tutorial directory.

Try these exercises in Swagger UI while running the matching checkpoint:

1. **Routes and documentation:** In `step01`, call `GET /`. Open
   [the OpenAPI schema](http://127.0.0.1:8011/openapi.json) and find the operation
   for that route.
2. **Input validation:** In `step02`, compare `/square/4` with `/square/banana`.
   Try `/items?skip=1&limit=2`, then an invalid limit such as `0`. Explain which
   function annotations or constraints determine each response.
3. **Request and response models:** In `step03`, send `{"features": [1, 2, 3]}`
   to `POST /predict`. Then try an empty list and a list containing `"banana"`.
   Identify where the request and response models appear in the API docs.
4. **Waiting for work:** In `step04`, send the same valid body to
   `POST /predict-slow`. Observe how long the request takes and compare its result
   with `POST /predict`.
5. **Background work and files:** In `step05`, send the valid body to `POST /jobs`,
   copy the returned `job_id`, and call `GET /jobs/{job_id}` until it finishes.
   Compare the initial response status and timing with the slow prediction.
   Open `/sample-image`, then inspect how its file path is constructed in the code.

Run the automated checks after exploring the examples:

```sh
uv run --locked python teaching_demo/smoke_check.py
```

The check starts and stops its own server on an available local port. It verifies
routes, input validation, OpenAPI, the image, job failures, and the difference
between waiting for a slow prediction and receiving a `202 Accepted` job response.
