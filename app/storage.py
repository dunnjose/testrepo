"""JSON-backed storage for tasks.

A tiny persistence layer so the API survives restarts without pulling in a
real database. All access goes through a single TaskStore instance.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import Task, TaskCreate, TaskUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TaskStore:
    """In-memory task store with JSON persistence to disk."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else None
        self._lock = threading.Lock()
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1
        self._load()

    # --- persistence ---------------------------------------------------
    def _load(self) -> None:
        if not self._path or not self._path.exists():
            return
        raw = json.loads(self._path.read_text())
        for item in raw.get("tasks", []):
            task = Task(**item)
            self._tasks[task.id] = task
        self._next_id = raw.get("next_id", max(self._tasks, default=0) + 1)

    def _persist(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "next_id": self._next_id,
            "tasks": [json.loads(t.json()) for t in self._tasks.values()],
        }
        self._path.write_text(json.dumps(payload, indent=2))

    # --- operations ----------------------------------------------------
    def list(self, status: Optional[str] = None) -> List[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.id)

    def get(self, task_id: int) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def create(self, data: TaskCreate) -> Task:
        with self._lock:
            now = _now()
            task = Task(
                id=self._next_id,
                created_at=now,
                updated_at=now,
                **data.dict(),
            )
            self._tasks[task.id] = task
            self._next_id += 1
            self._persist()
            return task

    def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            changes = data.dict(exclude_unset=True)
            if changes:
                updated = task.copy(update={**changes, "updated_at": _now()})
                self._tasks[task_id] = updated
                self._persist()
                return updated
            return task

    def delete(self, task_id: int) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self._persist()
                return True
            return False
