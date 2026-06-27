#!/usr/bin/env python3
"""
AI Agents Team — точка входа для запуска команды AI-агентов.

Использование:
    python team.py run "Описание задачи"
    python team.py run --file task.json
    python team.py list-agents
    python team.py list-workflows
"""

import json
import sys
from pathlib import Path


AGENTS_DIR = Path(__file__).parent / "agents"
WORKFLOWS_DIR = Path(__file__).parent / "workflows"


def list_agents():
    """Показать список доступных агентов."""
    print("\n📋 Доступные агенты:\n")
    for md_file in sorted(AGENTS_DIR.glob("*.md")):
        name = md_file.stem
        print(f"  • {name}")


def list_workflows():
    """Показать список доступных workflow."""
    print("\n📋 Доступные workflow:\n")
    for md_file in sorted(WORKFLOWS_DIR.glob("*.md")):
        name = md_file.stem
        print(f"  • {name}")


def run_task(description_or_file: str):
    """
    Запустить команду на выполнение задачи.
    В текущей версии — загрузка конфигурации, в будущем — оркестрация агентов.
    """
    task_data = {}

    # Проверяем, передан ли путь к JSON-файлу
    if description_or_file.endswith(".json"):
        filepath = Path(description_or_file)
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                task_data = json.load(f)
            print(f"📥 Загружена задача из файла: {filepath}")
        else:
            print(f"❌ Файл не найден: {filepath}")
            sys.exit(1)
    else:
        task_data = {
            "task": {
                "id": "manual-001",
                "title": "Ручной ввод",
                "description": description_or_file,
                "context": {},
                "constraints": []
            }
        }

    task = task_data.get("task", task_data)
    print(f"\n🧠 Задача принята: {task.get('title', 'Без названия')}")
    print(f"   Описание: {task.get('description', 'Нет описания')[:100]}...")
    print(f"\n{'='*50}")
    print("🚀 Оркестратор анализирует задачу...")
    print("   (заглушка — полноценная оркестрация будет реализована позже)")
    print(f"{'='*50}\n")

    print("Команда агентов, которые потребуются:")
    print("  🧠 Orchestrator — координация")
    print("  📐 Architect — проектирование")
    print("  💻 Developer — разработка")
    print("  🔍 Reviewer — ревью")
    print("  📖 Documenter — документация")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]

    if command == "list-agents":
        list_agents()
    elif command == "list-workflows":
        list_workflows()
    elif command == "run":
        if len(sys.argv) < 3:
            print("❌ Укажите описание задачи или путь к JSON-файлу.")
            print("   Пример: python team.py run \"Создать REST API\"")
            print("   Пример: python team.py run --file task.json")
            sys.exit(1)

        arg = sys.argv[2]
        if arg == "--file" and len(sys.argv) >= 4:
            run_task(sys.argv[3])
        else:
            run_task(arg)
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
