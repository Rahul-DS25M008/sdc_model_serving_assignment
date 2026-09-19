# FastAPI tutorial and assignment

Use Python 3.11 or newer and `uv`. The tutorial and assignment are separate
projects, each with its own `pyproject.toml`, `uv.lock`, and `.venv`.

## Run the tutorial

From the repository root:

```sh
cd 1_fast_api_tutorial
uv sync --locked
uv run --locked uvicorn inclass_fastapi_app:app --reload
```

Open [the interactive API docs](http://127.0.0.1:8000/docs). For example, send
`{"name": "Ada"}` to `POST /class`. Stop the server with Ctrl+C.

To work through the notebook, run `uv run --locked jupyter notebook` from the
same directory and open `fastApi_tutorial.ipynb`.

## Run the assignment

After stopping the tutorial server, run from the repository root:

```sh
cd assignment
uv sync --locked
uv run --locked uvicorn app:app --reload
```

Open [the interactive API docs](http://127.0.0.1:8000/docs) and follow the tasks in
[the assignment README](assignment/README.md). The image-generation endpoints
are intentionally left as exercises.

## Run the checks

From either `1_fast_api_tutorial` or `assignment`, run:

```sh
uv run --locked python -m unittest discover -s ../tests -v
```

## Dev container

Open the repository in its dev container to install both locked environments
automatically. The default Python interpreter is
`1_fast_api_tutorial/.venv/bin/python`; select `assignment/.venv/bin/python` when
working on the assignment.
