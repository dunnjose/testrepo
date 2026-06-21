"""End-to-end tests for the task manager API."""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Point the app at an isolated DB file per test, then reload the module
    # so the module-level store binds to that path.
    monkeypatch.setenv("TASKS_DB", str(tmp_path / "tasks.json"))
    import app.main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_and_get(client):
    resp = client.post("/tasks", json={"title": "Write tests"})
    assert resp.status_code == 201
    task = resp.json()
    assert task["id"] == 1
    assert task["title"] == "Write tests"
    assert task["status"] == "todo"

    got = client.get(f"/tasks/{task['id']}")
    assert got.status_code == 200
    assert got.json()["title"] == "Write tests"


def test_list_and_filter(client):
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B", "status": "done"})

    all_tasks = client.get("/tasks").json()
    assert len(all_tasks) == 2

    done = client.get("/tasks", params={"status": "done"}).json()
    assert len(done) == 1
    assert done[0]["title"] == "B"


def test_update(client):
    created = client.post("/tasks", json={"title": "Draft"}).json()
    resp = client.patch(
        f"/tasks/{created['id']}", json={"status": "in_progress"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["title"] == "Draft"


def test_delete(client):
    created = client.post("/tasks", json={"title": "Temp"}).json()
    assert client.delete(f"/tasks/{created['id']}").status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_missing_task_404(client):
    assert client.get("/tasks/999").status_code == 404
    assert client.patch("/tasks/999", json={"title": "x"}).status_code == 404
    assert client.delete("/tasks/999").status_code == 404


def test_validation_rejects_empty_title(client):
    assert client.post("/tasks", json={"title": ""}).status_code == 422


def test_persistence_across_reload(client, tmp_path, monkeypatch):
    client.post("/tasks", json={"title": "Persist me"})
    # Reload the app pointing at the same DB file the fixture configured.
    import app.main as main

    importlib.reload(main)
    reloaded = TestClient(main.app)
    tasks = reloaded.get("/tasks").json()
    assert any(t["title"] == "Persist me" for t in tasks)
