# 📋 Per-Project конфигурация скилов

В этой директории хранятся конфигурации скилов для разных проектов.

## Формат

```json
{
  "project": "название-проекта",
  "description": "Описание проекта",
  "workflow": "default | emergency",

  "active_agents": [
    {"name": "имя_агента", "profile": "имя_профиля"},
    "или_просто_имя_профиля"
  ],

  "skill_overrides": {
    "имя_агента": {
      "add": ["skill_to_add", ...],
      "remove": ["skill_to_remove", ...]
    }
  },

  "external_skills": [
    {"name": "skill_name", "source": "source_name"}
  ],

  "active_skills_only": false
}
```

## CLI

```bash
python team.py skills project <name>          # показать конфиг проекта
python team.py skills projects                # список проектов
python team.py skills active <project>         # активные скилы
python team.py skills assign <agent> --add s1,s2 --project <name>
```
