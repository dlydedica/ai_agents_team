"""
MCP-сервер координации AI Agents Team.

Поддерживает два транспорта:
  - stdio (по умолчанию): для запуска через подпроцесс
  - http (streamable-http): для запуска как HTTP-сервер (как Figma/GitHub MCP)

Использование:
  # STDIO (по умолчанию)
  python server.py

  # HTTP (Streamable HTTP)
  python server.py --transport http

  # HTTP на другом порту
  python server.py --transport http --port 9000
"""

import argparse
import json
import sys

# Принудительная UTF-8 кодировка для stdout/stderr (особенно важно на Windows)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from mcp.server.fastmcp import FastMCP

from task_store import (
    create_task as store_create_task,
    assign_to_department as store_assign,
    complete_department as store_complete,
    handoff as store_handoff,
    get_task as store_get_task,
    get_task_timeline as store_get_timeline,
    list_active as store_list_active,
    log_event as store_log_event,
    escalate as store_escalate,
)

# Подключаем систему обучения и памяти
from memory.memory_store import learn_from_tasks, suggest_similar

# Создаём FastMCP-сервер
mcp = FastMCP(
    name="ai-agents-coordinator",
    instructions="Координатор команды AI-агентов. Управляет задачами, handoff между отделами и отслеживанием прогресса.",
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/mcp",
)


# ──────────────────────────────────────────────
# Инструменты
# ──────────────────────────────────────────────


@mcp.tool(
    name="create_task",
    description="Создать новую задачу для команды AI-агентов",
)
def create_task(title: str, departments: list[str], description: str = "") -> str:
    """Создать новую задачу.

    Args:
        title: Название задачи
        departments: Список отделов в порядке выполнения
        description: Описание задачи (опционально)
    """
    result = store_create_task(title=title, departments=departments, description=description)

    # 🔍 Ищем похожие задачи в памяти — CEO сможет использовать их план
    if "error" not in result:
        try:
            similar = suggest_similar(title, description)
            if similar:
                result["similar_tasks"] = similar
                result["_note"] = (
                    "🧠 Найдены похожие задачи в памяти — "
                    "используйте их departments_plan как основу"
                )
            else:
                result["similar_tasks"] = []
        except Exception:
            result["similar_tasks"] = []

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="assign_to_department",
    description="Назначить задачу отделу для выполнения",
)
def assign_to_department(task_id: str, department: str) -> str:
    """Назначить задачу отделу.

    Args:
        task_id: ID задачи
        department: Название отдела
    """
    result = store_assign(task_id, department)
    if not result:
        return '{"error": "❌ Задача не найдена"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="complete_department_task",
    description="Отметить, что отдел завершил свою часть работы",
)
def complete_department_task(task_id: str, department: str, artifacts: dict = None) -> str:
    """Завершить работу отдела над задачей.

    Args:
        task_id: ID задачи
        department: Название отдела
        artifacts: Артефакты (файлы, ссылки и т.д.)
    """
    result = store_complete(task_id, department, artifacts)
    if not result:
        return '{"error": "❌ Задача не найдена"}'

    # 🧠 Если задача полностью завершена — извлекаем знания в долговременную память
    if "error" not in result and result.get("status") == "completed":
        try:
            learn_result = learn_from_tasks()
            result["_memory"] = (
                f"🧠 Извлечено знаний: {learn_result.get('learned', 0)} новых, "
                f"всего {learn_result.get('total', 0)}"
            )
        except Exception:
            result["_memory"] = "⚠️ Ошибка записи в память"

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="handoff",
    description="Передать задачу от одного отдела другому",
)
def handoff(task_id: str, from_department: str, to_department: str, artifacts: dict = None) -> str:
    """Передать задачу между отделами.

    Args:
        task_id: ID задачи
        from_department: Откуда
        to_department: Куда
        artifacts: Артефакты для передачи
    """
    result = store_handoff(task_id, from_department, to_department, artifacts)
    if not result:
        return '{"error": "❌ Задача не найдена"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="get_task_status",
    description="Получить текущий статус задачи",
)
def get_task_status(task_id: str) -> str:
    """Получить статус задачи.

    Args:
        task_id: ID задачи
    """
    result = store_get_task(task_id)
    if not result:
        return '{"error": "❌ Задача не найдена"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="get_task_timeline",
    description="Получить хронологию событий задачи",
)
def get_task_timeline(task_id: str) -> str:
    """Получить хронологию задачи.

    Args:
        task_id: ID задачи
    """
    result = store_get_timeline(task_id)
    if result is None:
        return '{"error": "❌ Задача не найдена"}'
    if not result:
        return '{"message": "📭 Нет событий"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="list_active_tasks",
    description="Список активных задач",
)
def list_active_tasks() -> str:
    """Получить список активных задач."""
    result = store_list_active()
    if not result:
        return '{"message": "📭 Нет активных задач"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="log_event",
    description="Записать событие в лог задачи",
)
def log_event(task_id: str, event_type: str, detail: str) -> str:
    """Записать событие.

    Args:
        task_id: ID задачи
        event_type: Тип события
        detail: Описание события
    """
    result = store_log_event(task_id, event_type, detail)
    if not result:
        return '{"error": "❌ Задача не найдена"}'
    return '{"status": "✅ Событие записано"}'


@mcp.tool(
    name="escalate",
    description="Эскалировать проблему по задаче",
)
def escalate(task_id: str, reason: str) -> str:
    """Эскалировать проблему.

    Args:
        task_id: ID задачи
        reason: Причина эскалации
    """
    result = store_escalate(task_id, reason)
    if not result:
        return '{"error": "❌ Задача не найдена"}'
    return json.dumps(result, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="MCP-сервер координации AI Agents Team")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Транспорт: stdio (по умолчанию) или http (Streamable HTTP)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Порт для HTTP-транспорта (по умолчанию: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        # Обновляем порт, если передан через CLI
        mcp.settings.port = args.port
        print(f"🚀 Запуск MCP-сервера в режиме HTTP (Streamable HTTP)")
        print(f"   Эндпоинт: http://0.0.0.0:{args.port}/mcp")
        print(f"   Подключение в VS Code:")
        print(f'     "type": "http",')
        print(f'     "url": "http://localhost:{args.port}/mcp"')
        print()
        mcp.run(transport="streamable-http")
    else:
        print("🚀 Запуск MCP-сервера в режиме STDIO", file=sys.stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
