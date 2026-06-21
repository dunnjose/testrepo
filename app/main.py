"""FastAPI application exposing a task/todo manager."""

import os
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status

from . import __version__
from .models import Status, Task, TaskCreate, TaskUpdate
from .storage import TaskStore

DATA_PATH = Path(os.environ.get("TASKS_DB", "tasks.json"))

app = FastAPI(
    title="Task Manager API",
    version=__version__,
    description="A small REST API for managing todo tasks.",
)

_store = TaskStore(DATA_PATH)


def get_store() -> TaskStore:
    """Dependency hook so tests can swap in an isolated store."""
    return _store


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/tasks", response_model=List[Task])
def list_tasks(
    status: Optional[Status] = Query(None, description="Filter by status"),
    store: TaskStore = Depends(get_store),
) -> List[Task]:
    return store.list(status=status.value if status else None)


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    store: TaskStore = Depends(get_store),
) -> Task:
    return store.create(payload)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, store: TaskStore = Depends(get_store)) -> Task:
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    store: TaskStore = Depends(get_store),
) -> Task:
    task = store.update(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, store: TaskStore = Depends(get_store)) -> None:
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
