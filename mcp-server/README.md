# MCP-сервер координации AI Agents Team

Автоматизирует handoff, отслеживание статуса задач и логирование событий между отделами.

## Быстрый старт

```bash
pip install -r requirements.txt
python server.py
```

## Интеграция с VS Code

Добавьте в `.vscode/mcp.json` вашего проекта:

```json
{
  "servers": {
    "ai-agents-coordinator": {
      "type": "stdio",
      "command": "python",
      "args": ["путь/к/ai_agents_team/mcp-server/server.py"],
      "description": "Координатор AI-команды"
    }
  }
}
```

## Доступные инструменты

| Инструмент | Описание |
|-----------|----------|
| `create_task` | Создать новую задачу |
| `assign_to_department` | Назначить задачу отделу |
| `complete_department_task` | Завершить работу отдела |
| `handoff` | Передать задачу следующему отделу |
| `get_task_status` | Получить статус задачи |
| `get_task_timeline` | Получить хронологию задачи |
| `list_active_tasks` | Список активных задач |
| `log_event` | Записать событие в лог задачи |
| `escalate` | Эскалировать проблему |

## Формат задачи

```json
{
  "id": "task-001",
  "title": "Создать REST API",
  "status": "in_progress",
  "current_department": "development",
  "departments_plan": ["product", "architecture", "development", "qa", "devops", "docs"],
  "departments_completed": [],
  "artifacts": {},
  "events": [],
  "created_at": "2024-01-01T12:00:00"
}
```
