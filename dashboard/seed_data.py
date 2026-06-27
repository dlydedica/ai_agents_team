"""Seed test data for dashboard."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server"))
from task_store import create_task, assign_to_department, complete_department, handoff

# 1. REST API для пользователей (в процессе)
t1 = create_task(
    "REST API для пользователей",
    ["product", "architecture", "development", "qa", "devops", "docs"],
    "CRUD + JWT авторизация на FastAPI"
)
assign_to_department(t1["id"], "product")
complete_department(t1["id"], "product", {"spec": "docs/api-spec.yaml"})
handoff(t1["id"], "product", "architecture", {"spec": "docs/api-spec.yaml"})
assign_to_department(t1["id"], "architecture")

# 2. Микросервис сокращения ссылок (разработка)
t2 = create_task(
    "Микросервис сокращения ссылок",
    ["architecture", "development", "qa", "devops"],
    "FastAPI + Redis + PostgreSQL"
)
assign_to_department(t2["id"], "architecture")
complete_department(t2["id"], "architecture", {"arch": "docs/architecture.md"})
handoff(t2["id"], "architecture", "development", {"arch": "docs/architecture.md"})

# 3. Дашборд метрик (запланирована)
t3 = create_task(
    "Дашборд метрик продукта",
    ["product", "design", "development", "qa"],
    "Визуализация ключевых метрик продукта"
)

# 4. Hotfix бага аутентификации (активна)
t4 = create_task(
    "hotfix: баг аутентификации",
    ["development", "qa", "devops"],
    "P0 — не проходит валидация JWT"
)
assign_to_department(t4["id"], "development")

print("✅ Тестовые данные созданы")
