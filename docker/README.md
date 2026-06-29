# 🐳 Docker — для справки

Файлы в этой папке — **справочные**. Не являются частью активного рантайма.

- `Dockerfile` — сборка MCP-сервера для production-развёртывания
- `docker-compose.yml` — поднимает MCP + Dashboard

Для запуска дашборда используйте:
```bash
python team.py dashboard
```

Для production-деплоя — скопируйте `docker/` в инфраструктурный проект.
