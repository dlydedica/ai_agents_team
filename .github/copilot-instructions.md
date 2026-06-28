# Инструкции для GitHub Copilot

## AI DevCorp — Корпорация AI-агентов

В проекте подключена команда AI-агентов из `ai_agents_team/`.

Для постановки задачи команде:
1. Откройте Copilot Chat
2. Выберите агента **🧠 CEO — Оркестратор AI-команды**
3. Опишите задачу — Оркестратор проанализирует и распределит работу

Структура команды: `ai_agents_team/departments/` (13 отделов)
Процессы: `ai_agents_team/workflows/`
Бренд: `ai_agents_team/docs/BRANDING.md`

## MCP-сервер координации

MCP-сервер запускается автоматически при использовании Copilot Chat (транспорт `stdio`).

Для явного запуска в **HTTP-режиме** (Docker/production):
```bash
cd ai_agents_team
python mcp-server/server.py --transport http
```
Сервер будет доступен на `http://localhost:8000/mcp`.
Конфигурация подключения: `mcp.json` → `ai-agents-coordinator`
