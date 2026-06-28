# 🌐 Внешние скилы AI DevCorp

В этой директории подключаются скилы от сторонних разработчиков и community.

## Способы подключения

### 1. Git-репозиторий
```bash
python skills/loader.py install https://github.com/community/awesome-dev-skills.git
```

### 2. Pip-пакет
```bash
python skills/loader.py install community-skills-pack
```

### 3. Симлинк на локальную директорию
```bash
python skills/loader.py install /path/to/my-skills my-custom-skills
```

## Структура внешнего скила

Любой источник должен содержать `.skill.md` файлы:

```
my-skills/
├── README.md
├── python_django.skill.md
├── golang_backend.skill.md
└── ...
```

## Поиск community-скилов

Следите за обновлениями в репозитории проекта — мы планируем:
- [ ] Маркетплейс community-скилов
- [ ] Валидация и рейтинг внешних скилов
- [ ] Автоматические обновления (git pull)
