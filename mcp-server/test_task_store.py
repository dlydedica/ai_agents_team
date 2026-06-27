"""Test the MCP server task_store fixes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from task_store import (
    create_task, assign_to_department, handoff,
    complete_department, get_task, get_task_timeline, get_all_tasks
)

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")

print("🔬 Тестирование MCP-сервера\n")

# 1. Создание задачи
t = create_task("Test task", ["development", "qa"])
check("Create task", "error" not in t, str(t))
check("  UUID ID format", t["id"].startswith("task-"), t["id"])

# 2. Невалидный отдел
t2 = create_task("Bad dept", ["nonexistent"])
check("Reject invalid dept", "error" in t2, t2.get("error", ""))

# 3. Пустое название
t3 = create_task("", ["development"])
check("Reject empty title", "error" in t3, t3.get("error", ""))

# 4. Assign не из плана
r = assign_to_department(t["id"], "marketing")
check("Reject assign to dept not in plan", isinstance(r, dict) and "error" in r, str(r))

# 5. Полный цикл: assign → complete → handoff
assign_to_department(t["id"], "development")
complete_department(t["id"], "development")
r = handoff(t["id"], "development", "qa")
check("Handoff dev → qa", isinstance(r, dict) and "error" not in r, str(r))

# 6. Complete не назначенным
r = complete_department(t["id"], "development")
check("Reject complete already done", isinstance(r, dict) and "error" in r, str(r))

# 7. Новый цикл: assign → handoff напрямую
t4 = create_task("Handoff flow", ["architecture", "development", "qa"])
assign_to_department(t4["id"], "architecture")
r = handoff(t4["id"], "architecture", "development")
check("Handoff transfers between depts", isinstance(r, dict) and r.get("current_department") == "development", str(r))

# 8. Timeline
timeline = get_task_timeline(t["id"])
check("Timeline exists", timeline is not None)
check("Timeline has events", len(timeline) > 0, f"{len(timeline)} events")

# 9. get_all_tasks
all_t = get_all_tasks()
check("get_all_tasks returns dict", isinstance(all_t, dict))
check("Has our task", t["id"] in all_t)

# 10. Завершение задачи через последовательные assign+complete
t5 = create_task("Full cycle", ["development", "qa"])
assign_to_department(t5["id"], "development")
complete_department(t5["id"], "development")  # auto-advances to qa
complete_department(t5["id"], "qa")  # completes the task
final_task = get_task(t5["id"])
check("Task auto-completes after last dept", final_task["status"] == "completed")

print(f"\n{'='*40}")
print(f"  ✅ Пройдено: {passed}")
print(f"  ❌ Провалено: {failed}")
print(f"{'='*40}")
