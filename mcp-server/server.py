"""
MCP-сервер координации AI Agents Team.

Предоставляет инструменты для управления задачами,
handoff между отделами и отслеживания прогресса.
"""

import json
import sys
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

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

server = Server("ai-agents-coordinator")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_task",
            description="Создать новую задачу для команды AI-агентов",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Название задачи"},
                    "description": {"type": "string", "description": "Описание задачи"},
                    "departments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список отделов в порядке выполнения",
                    },
                },
                "required": ["title", "departments"],
            },
        ),
        types.Tool(
            name="assign_to_department",
            description="Назначить задачу отделу для выполнения",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                    "department": {"type": "string", "description": "Название отдела"},
                },
                "required": ["task_id", "department"],
            },
        ),
        types.Tool(
            name="complete_department_task",
            description="Отметить, что отдел завершил свою часть работы",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                    "department": {"type": "string", "description": "Название отдела"},
                    "artifacts": {
                        "type": "object",
                        "description": "Артефакты (файлы, ссылки и т.д.)",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["task_id", "department"],
            },
        ),
        types.Tool(
            name="handoff",
            description="Передать задачу от одного отдела другому",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                    "from_department": {"type": "string", "description": "Откуда"},
                    "to_department": {"type": "string", "description": "Куда"},
                    "artifacts": {
                        "type": "object",
                        "description": "Артефакты для передачи",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["task_id", "from_department", "to_department"],
            },
        ),
        types.Tool(
            name="get_task_status",
            description="Получить текущий статус задачи",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="get_task_timeline",
            description="Получить хронологию событий задачи",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="list_active_tasks",
            description="Список активных задач",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="log_event",
            description="Записать событие в лог задачи",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                    "event_type": {"type": "string", "description": "Тип события"},
                    "detail": {"type": "string", "description": "Описание события"},
                },
                "required": ["task_id", "event_type", "detail"],
            },
        ),
        types.Tool(
            name="escalate",
            description="Эскалировать проблему по задаче",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID задачи"},
                    "reason": {"type": "string", "description": "Причина эскалации"},
                },
                "required": ["task_id", "reason"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "create_task":
            result = store_create_task(
                title=arguments["title"],
                departments=arguments["departments"],
                description=arguments.get("description", ""),
            )
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "assign_to_department":
            result = store_assign(arguments["task_id"], arguments["department"])
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "complete_department_task":
            result = store_complete(
                arguments["task_id"],
                arguments["department"],
                arguments.get("artifacts"),
            )
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "handoff":
            result = store_handoff(
                arguments["task_id"],
                arguments["from_department"],
                arguments["to_department"],
                arguments.get("artifacts"),
            )
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "get_task_status":
            result = store_get_task(arguments["task_id"])
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "get_task_timeline":
            result = store_get_timeline(arguments["task_id"])
            if result is None:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            if not result:
                return [types.TextContent(type="text", text="📭 Нет событий")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "list_active_tasks":
            result = store_list_active()
            if not result:
                return [types.TextContent(type="text", text="📭 Нет активных задач")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "log_event":
            result = store_log_event(arguments["task_id"], arguments["event_type"], arguments["detail"])
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text="✅ Событие записано")]

        elif name == "escalate":
            result = store_escalate(arguments["task_id"], arguments["reason"])
            if not result:
                return [types.TextContent(type="text", text="❌ Задача не найдена")]
            return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"❌ Неизвестный инструмент: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Ошибка: {str(e)}")]


@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return []


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-agents-coordinator",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
