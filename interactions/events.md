# 📡 Событийная модель взаимодействия

Отделы реагируют на события, а не только на прямые команды CEO.

## Типы событий

| Событие | Источник | Подписчики | Действие |
|---------|----------|------------|----------|
| `task.assigned` | CEO | Head | Начать работу |
| `task.completed` | Head | CEO | Забрать результат |
| `task.blocked` | Head | CEO, связанные Heads | Разблокировка |
| `artifact.ready` | Отдел | Следующий отдел | Забрать артефакт |
| `review.needed` | Любой | QA, Security | Провести ревью |
| `bug.found` | QA | Development | Исправить |
| `security.issue` | Security | Development | Исправить |
| `decision.needed` | Любой Head | CEO, Совет отделов | Принять решение |
| `deployment.done` | DevOps | Все | Обновить окружение |
| `milestone.reached` | CEO | Все Heads | Синхронизация |
| `quality_gate.failed` | QA | R&D, Development, HR | Адаптивный цикл |
| `check.created` | R&D | QA, CEO | Новый check в реестре |
| `auto_fix.applied` | Development | QA, CEO | Код исправлен автоматически |
| `incident.recorded` | HR | CEO | Инцидент сохранён в memory |

## Flow на событиях

```
CEO: task.assigned(development) ──► Tech Lead начинает
Development: artifact.ready(api) ──► QA забирает
QA: bug.found(api/auth) ──────────► Development исправляет
QA: task.completed ───────────────► CEO проверяет
CEO: decision.needed(data-model) ─► Совет отделов
```

## Взаимодействие через события

1. **Head** публикует событие (например, `artifact.ready`)
2. **Подписчики** получают уведомление
3. **Получатель** забирает артефакт и начинает работу
4. Если получатель не отвечает — CEO эскалирует
