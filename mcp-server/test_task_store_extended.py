"""Расширенные тесты MCP-сервера (pytest-совместимые)."""
import sys
import os
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Clean data before tests
data_dir = Path(__file__).resolve().parent / "data"
os.makedirs(data_dir, exist_ok=True)
for f in data_dir.glob("*"):
    f.unlink()

from task_store import (
    create_task, assign_to_department, handoff,
    complete_department, get_task, get_task_timeline,
    get_all_tasks, list_active, escalate, log_event
)


class TestTaskStore:
    """Тесты хранилища задач."""

    def setup_method(self):
        """Очищаем перед каждым тестом."""
        for f in data_dir.glob("*"):
            f.unlink()

    def test_create_task(self):
        t = create_task("Test", ["development", "qa"])
        assert "error" not in t
        assert t["title"] == "Test"
        assert t["status"] == "planned"
        assert t["id"].startswith("task-")

    def test_create_task_empty_title(self):
        t = create_task("", ["development"])
        assert "error" in t

    def test_create_task_invalid_dept(self):
        t = create_task("Bad", ["nonexistent"])
        assert "error" in t

    def test_full_cycle(self):
        t = create_task("Cycle", ["development", "qa"])
        assign_to_department(t["id"], "development")
        complete_department(t["id"], "development")
        r = get_task(t["id"])
        assert r["status"] == "in_progress"
        assert r["current_department"] == "qa"
        complete_department(t["id"], "qa")
        r = get_task(t["id"])
        assert r["status"] == "completed"

    def test_handoff_flow(self):
        t = create_task("Handoff", ["architecture", "development"])
        assign_to_department(t["id"], "architecture")
        handoff(t["id"], "architecture", "development")
        r = get_task(t["id"])
        assert r["current_department"] == "development"
        assert "architecture" in r["departments_completed"]

    def test_handoff_invalid_dept(self):
        t = create_task("Bad handoff", ["development"])
        r = handoff(t["id"], "development", "nonexistent")
        assert "error" in r

    def test_complete_unassigned(self):
        t = create_task("Unassigned", ["development", "qa"])
        r = complete_department(t["id"], "development")
        assert "error" in r

    def test_double_complete(self):
        t = create_task("Double", ["development", "qa"])
        assign_to_department(t["id"], "development")
        complete_department(t["id"], "development")
        r = complete_department(t["id"], "development")
        assert "error" in r

    def test_timeline(self):
        t = create_task("Timeline", ["development"])
        assign_to_department(t["id"], "development")
        tl = get_task_timeline(t["id"])
        assert len(tl) >= 2
        assert tl[0]["type"] == "task.created"
        assert tl[1]["type"] == "department.assigned"

    def test_list_active(self):
        create_task("Active1", ["development"])
        create_task("Active2", ["development", "qa"])
        active = list_active()
        assert len(active) == 2

    def test_list_active_after_complete(self):
        t = create_task("Will complete", ["development"])
        assign_to_department(t["id"], "development")
        complete_department(t["id"], "development")
        active = list_active()
        assert all(a["id"] != t["id"] for a in active)

    def test_get_all_tasks(self):
        create_task("T1", ["development"])
        create_task("T2", ["qa"])
        all_t = get_all_tasks()
        assert len(all_t) == 2, f"Expected 2, got {len(all_t)}: {list(all_t.keys())}"

    def test_escalate(self):
        t = create_task("Escalate", ["development"])
        r = escalate(t["id"], "Критический баг")
        assert r["status"] == "escalated"
        tl = get_task_timeline(t["id"])
        assert tl[-1]["type"] == "escalation"

    def test_log_event(self):
        t = create_task("Log", ["development"])
        log_event(t["id"], "custom.event", "Тестовое событие")
        tl = get_task_timeline(t["id"])
        assert tl[-1]["type"] == "custom.event"

    def test_get_nonexistent_task(self):
        assert get_task("task-nonexistent") is None

    def test_assign_nonexistent_task(self):
        r = assign_to_department("task-nonexistent", "development")
        assert "error" in r

    def test_5_department_chain(self):
        depts = ["product", "architecture", "development", "qa", "devops"]
        t = create_task("Long chain", depts)
        for dept in depts:
            assign_to_department(t["id"], dept)
            complete_department(t["id"], dept)
        r = get_task(t["id"])
        assert r["status"] == "completed"
        assert len(r["departments_completed"]) == 5

    def test_task_uuid_uniqueness(self):
        ids = set()
        for _ in range(10):
            t = create_task("Unique", ["development"])
            ids.add(t["id"])
        assert len(ids) == 10

    def test_event_limit(self):
        t = create_task("Many events", ["development"])
        for i in range(150):
            log_event(t["id"], "test.event", f"Event {i}")
        tl = get_task_timeline(t["id"])
        assert len(tl) <= 100  # Ограничение

    def test_artifacts_preserved(self):
        t = create_task("Artifacts", ["development", "qa"])
        assign_to_department(t["id"], "development")
        complete_department(t["id"], "development", {"code": "src/api.py"})
        r = get_task(t["id"])
        assert r["artifacts"]["code"] == "src/api.py"


# === Manual test runner ===
def run_manual():
    """Run all tests and report."""
    test = TestTaskStore()
    tests = [
        name for name in dir(test)
        if name.startswith("test_")
    ]
    passed = 0
    failed = 0
    for name in tests:
        test.setup_method()
        try:
            getattr(test, name)()
            passed += 1
            print(f"  ✅ {name}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
    print(f"\n  ✅ Пройдено: {passed}/{len(tests)}")
    if failed:
        print(f"  ❌ Провалено: {failed}")
    return failed == 0


if __name__ == "__main__":
    run_manual()
