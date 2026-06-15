# Task Manager API

A small REST API for managing todo tasks, built with [FastAPI](https://fastapi.tiangolo.com/).
Tasks are persisted to a JSON file so they survive restarts — no database required.

## Features

- Full CRUD for tasks (`title`, `description`, `status`)
- Status lifecycle: `todo` → `in_progress` → `done`
- Filter tasks by status
- Input validation via Pydantic
- Interactive API docs at `/docs`
- Test suite with `pytest`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs for interactive documentation.

By default tasks are stored in `tasks.json`. Override with the `TASKS_DB`
environment variable:

```bash
TASKS_DB=/tmp/mytasks.json uvicorn app.main:app
```

## API

| Method | Path           | Description                          |
| ------ | -------------- | ------------------------------------ |
| GET    | `/health`      | Health check                         |
| GET    | `/tasks`       | List tasks (optional `?status=`)     |
| POST   | `/tasks`       | Create a task                        |
| GET    | `/tasks/{id}`  | Get a task by id                     |
| PATCH  | `/tasks/{id}`  | Partially update a task              |
| DELETE | `/tasks/{id}`  | Delete a task                        |

### Example

```bash
curl -X POST localhost:8000/tasks \
  -H 'content-type: application/json' \
  -d '{"title": "Buy milk", "description": "2%"}'

curl localhost:8000/tasks
curl -X PATCH localhost:8000/tasks/1 -d '{"status": "done"}' \
  -H 'content-type: application/json'
```

## Tests

```bash
pip install pytest httpx
pytest -q
```
