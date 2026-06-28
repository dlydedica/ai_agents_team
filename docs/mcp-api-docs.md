# 🤖 MCP-сервер AI DevCorp — API документация

MCP-сервер реализует протокол **Model Context Protocol** для координации AI-команды.

## Подключение

### VS Code (рекомендуется)

Добавьте в `mcp.json` вашего проекта:

### Режим HTTP (рекомендуется)

```json
{
  "servers": {
    "ai-agents-coordinator": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "description": "🧠 Координатор AI-команды"
    }
  }
}
```

> **Важно:** Сервер должен быть запущен: `python ai_agents_team/mcp-server/server.py --transport http`

### Режим STDIO (автозапуск)

```json
{
  "servers": {
    "ai-agents-coordinator": {
      "type": "stdio",
      "command": "python",
      "args": ["${workspaceFolder}/ai_agents_team/mcp-server/server.py"],
      "description": "Координатор AI-команды"
    }
  }
}
```

### Из кода Python

```python
import sys
from pathlib import Path
sys.path.insert(0, "путь/к/ai_agents_team/mcp-server")
from task_store import create_task, get_task

task = create_task("Моя задача", ["development", "qa"])
print(f"Создана задача: {task['id']}")
```

### CLI

```bash
python -X utf8 team.py orchestrate "Описание задачи"
```

---

## Инструменты MCP

### 1. `create_task`

Создать новую задачу для команды AI-агентов.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:------------:|----------|
| `title` | string | ✅ | Название задачи |
| `description` | string | ❌ | Описание (до 500 символов) |
| `departments` | string[] | ✅ | Отделы в порядке выполнения |

**Допустимые отделы:** `product`, `architecture`, `development`, `qa`, `devops`, `design`, `docs`, `hr`, `security`, `data`, `rd`, `legal`, `marketing`

**Пример:**

```json
{
  "title": "REST API для пользователей",
  "description": "CRUD + JWT авторизация",
  "departments": ["product", "architecture", "development", "qa", "devops", "docs"]
}
```

**Ответ:**

```json
{
  "id": "task-a1b2c3d4",
  "title": "REST API для пользователей",
  "status": "planned",
  "current_department": null,
  "departments_plan": ["product", "architecture", "development", "qa", "devops", "docs"],
  "departments_completed": [],
  "events": [{"type": "task.created", ...}]
}
```

---

### 2. `assign_to_department`

Назначить задачу отделу для выполнения.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |
| `department` | string | ✅ |

**Ошибки:**
- `Задача {id} не найдена` — неверный task_id
- `Отдел {name} не в плане задачи` — отдел не в цепочке
- `Неизвестный отдел: {name}` — невалидное имя

---

### 3. `complete_department_task`

Отметить, что отдел завершил свою часть работы.

**Параметры:**

| Параметр | Тип | Обязательный | Описание |
|----------|-----|:------------:|----------|
| `task_id` | string | ✅ | ID задачи |
| `department` | string | ✅ | Название отдела |
| `artifacts` | object | ❌ | Артефакты (ключ-значение) |

**Автоматика:** после завершения отдела назначается следующий из плана. Если все отделы завершены — задача переходит в `completed`.

---

### 4. `handoff`

Передать задачу от одного отдела другому.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |
| `from_department` | string | ✅ |
| `to_department` | string | ✅ |
| `artifacts` | object | ❌ |

**Отличие от complete:** handoff одновременно завершает `from_department` и назначает `to_department` за один вызов.

---

### 5. `get_task_status`

Получить текущий статус задачи.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |

**Ответ:** полный объект задачи со всеми полями.

---

### 6. `get_task_timeline`

Получить хронологию событий задачи.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |

**Ответ:** массив событий с полями `time`, `type`, `detail`.

---

### 7. `list_active_tasks`

Список активных задач (planned + in_progress).

**Параметры:** нет

---

### 8. `log_event`

Записать произвольное событие в лог задачи.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |
| `event_type` | string | ✅ |
| `detail` | string | ✅ |

**Лимит:** хранится последних 100 событий на задачу.

---

### 9. `escalate`

Эскалировать проблему по задаче.

**Параметры:**

| Параметр | Тип | Обязательный |
|----------|-----|:------------:|
| `task_id` | string | ✅ |
| `reason` | string | ✅ |

**Эффект:** статус задачи меняется на `escalated`.

---

## Формат задачи

```json
{
  "id": "task-a1b2c3d4",
  "title": "REST API",
  "description": "CRUD + JWT",
  "status": "in_progress",
  "current_department": "development",
  "departments_plan": ["product", "architecture", "development", "qa"],
  "departments_completed": ["product", "architecture"],
  "artifacts": {
    "spec": "docs/spec.md",
    "arch": "docs/architecture.md"
  },
  "events": [
    {"time": "2026-06-28T12:00:00", "type": "task.created", "detail": "REST API"},
    {"time": "2026-06-28T12:01:00", "type": "handoff", "detail": "Handoff: architecture → development"}
  ]
}
```

### Статусы задач

| Статус | Описание |
|--------|----------|
| `planned` | Создана, ещё не начата |
| `in_progress` | В работе, назначен отдел |
| `completed` | Все отделы завершили |
| `escalated` | Эскалирована CEO |

---

## Примеры использования

### Полный цикл через Python

```python
from task_store import create_task, assign_to_department, complete_department

# 1. Создать
t = create_task("API", ["architecture", "development", "qa", "devops"])

# 2. Architecture проектирует
assign_to_department(t["id"], "architecture")
complete_department(t["id"], "architecture", {"arch": "docs/arch.md"})
#   → автоматически назначен development

# 3. Development реализует
complete_department(t["id"], "development", {"code": "src/"})
#   → автоматически назначен qa

# 4. QA тестирует
complete_department(t["id"], "qa", {"report": "tests/report.md"})
#   → автоматически назначен devops

# 5. DevOps деплоит
complete_department(t["id"], "devops", {"url": "https://example.com"})
#   → задача completed
```

### Поиск через memory

```python
from memory.memory_store import search, learn_from_tasks

# Обучить из существующих задач
learn_from_tasks()

# Найти похожие
results = search("REST API авторизация")
for r in results:
    print(f"[{r['score']}] {r['title']} — {r['departments']}")
```

---

## Диагностика

```bash
# Запустить тесты
cd mcp-server && python test_task_store.py
python test_task_store_extended.py

# Запустить дашборд
python -X utf8 team.py dashboard

# Статистика памяти
python -X utf8 team.py memory stats

# Поиск
python -X utf8 team.py search "REST API"
```
