"""Seed multiple tasks to test HR analysis."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "mcp-server"))
from task_store import create_task, assign_to_department, complete_department, escalate

# 5 задач с разными отделами
t1 = create_task("REST API", ["product", "architecture", "development", "qa", "devops", "docs"],
                 "FastAPI CRUD")
for d in ["product", "architecture", "development", "qa", "devops", "docs"]:
    assign_to_department(t1["id"], d)
    complete_department(t1["id"], d)

t2 = create_task("Telegram Bot", ["product", "development", "qa", "docs"],
                 "Бот для заказа")
for d in ["product", "development", "qa", "docs"]:
    assign_to_department(t2["id"], d)
    complete_department(t2["id"], d)

t3 = create_task("Дашборд метрик", ["product", "data", "design", "development", "qa"],
                 "BI dashboard")
for d in ["product", "data", "design", "development", "qa"]:
    assign_to_department(t3["id"], d)
    complete_department(t3["id"], d)

t4 = create_task("Аудит безопасности", ["security", "development", "devops"],
                 "Penetration test")
for d in ["security", "development", "devops"]:
    assign_to_department(t4["id"], d)
    complete_department(t4["id"], d)

# Эскалированная задача
t5 = create_task("Срочный хотфикс", ["development", "qa", "devops"],
                 "P0 — баг в продакшене")
assign_to_department(t5["id"], "development")
escalate(t5["id"], "Критическая уязвимость в авторизации")

print(f"✅ Создано 5 задач для HR-анализа")
