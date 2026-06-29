"""Tests for MCP server tools."""
import sys
import os
import json
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).resolve().parent))
data_dir = Path(__file__).resolve().parent / "data"
os.makedirs(data_dir, exist_ok=True)
for f in data_dir.glob("*"):
    f.unlink()

from task_store import create_task, get_task


class TestServerTools:
    """Integration tests for MCP server tools."""

    def test_create_task_tool(self):
        """Tool: create_task should return valid task."""
        t = create_task("Test", ["development", "qa"])
        assert "error" not in t
        assert t["id"].startswith("task-")
        assert t["status"] == "planned"
        assert t["departments_plan"] == ["development", "qa"]

    def test_assign_tool(self):
        """Tool: assign_to_department should update current_department."""
        from task_store import assign_to_department
        t = create_task("Assign", ["development", "qa"])
        r = assign_to_department(t["id"], "development")
        assert r["current_department"] == "development"
        assert r["status"] == "in_progress"

    def test_complete_tool_auto_advance(self):
        """Tool: complete_department should auto-assign next dept."""
        from task_store import assign_to_department, complete_department
        t = create_task("Auto", ["development", "qa"])
        assign_to_department(t["id"], "development")
        r = complete_department(t["id"], "development")
        assert r["current_department"] == "qa"
        assert "development" in r["departments_completed"]

    def test_handoff_tool(self):
        """Tool: handoff should transfer between depts."""
        from task_store import assign_to_department, handoff
        t = create_task("Handoff", ["architecture", "development"])
        assign_to_department(t["id"], "architecture")
        r = handoff(t["id"], "architecture", "development")
        assert r["current_department"] == "development"
        assert "architecture" in r["departments_completed"]

    def test_status_tool(self):
        """Tool: get_task should return full state."""
        t = create_task("Status", ["development", "qa"])
        r = get_task(t["id"])
        assert r["id"] == t["id"]
        assert r["title"] == "Status"

    def test_timeline_tool(self):
        """Tool: get_task_timeline should return events."""
        from task_store import get_task_timeline, assign_to_department
        t = create_task("Timeline", ["development"])
        assign_to_department(t["id"], "development")
        tl = get_task_timeline(t["id"])
        assert len(tl) >= 2
        assert tl[0]["type"] == "task.created"

    def test_list_active_tool(self):
        """Tool: list_active returns only active tasks."""
        from task_store import list_active, assign_to_department, complete_department
        t1 = create_task("Active1", ["development"])
        t2 = create_task("Active2", ["development"])
        assign_to_department(t1["id"], "development")
        complete_department(t1["id"], "development")
        active = list_active()
        ids = [a["id"] for a in active]
        assert t1["id"] not in ids  # completed
        assert t2["id"] in ids  # planned

    def test_escalate_tool(self):
        """Tool: escalate should change status."""
        from task_store import escalate
        t = create_task("Esc", ["development"])
        r = escalate(t["id"], "Critical bug")
        assert r["status"] == "escalated"

    def test_log_event_tool(self):
        """Tool: log_event should add to timeline."""
        from task_store import log_event, get_task_timeline
        t = create_task("Log", ["development"])
        log_event(t["id"], "custom.event", "Test")
        tl = get_task_timeline(t["id"])
        assert tl[-1]["type"] == "custom.event"

    def test_validation_invalid_dept(self):
        """Tool should reject invalid department."""
        from task_store import create_task
        r = create_task("Bad", ["nonexistent"])
        assert "error" in r

    def test_validation_empty_title(self):
        """Tool should reject empty title."""
        from task_store import create_task
        r = create_task("", ["development"])
        assert "error" in r

    def test_complete_cycle_5_depts(self):
        """Full cycle through 5 departments."""
        from task_store import assign_to_department, complete_department
        depts = ["product", "architecture", "development", "qa", "devops"]
        t = create_task("Full", depts)
        for d in depts:
            assign_to_department(t["id"], d)
            complete_department(t["id"], d)
        r = get_task(t["id"])
        assert r["status"] == "completed"
        assert len(r["departments_completed"]) == 5

    def test_artifacts_preserved(self):
        """Artifacts should survive complete cycle."""
        from task_store import assign_to_department, complete_department
        t = create_task("Art", ["development", "qa"])
        assign_to_department(t["id"], "development")
        complete_department(t["id"], "development", {"code": "src/api.py"})
        r = get_task(t["id"])
        assert r["artifacts"]["code"] == "src/api.py"

    def test_no_cross_task_interference(self):
        """Operations on one task should not affect another."""
        from task_store import assign_to_department
        t1 = create_task("T1", ["development"])
        t2 = create_task("T2", ["qa"])
        assign_to_department(t1["id"], "development")
        r2 = get_task(t2["id"])
        assert r2["current_department"] is None


def run_all():
    test = TestServerTools()
    tests = [n for n in dir(test) if n.startswith("test_")]
    passed = 0
    failed = 0
    for name in tests:
        data_dir = Path(__file__).resolve().parent / "data"
        for f in data_dir.glob("*"):
            f.unlink()
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
    run_all()
