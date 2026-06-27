#!/usr/bin/env python3
"""
AI Agents Team — Корпорация AI-агентов с организационной структурой.

Использование:
    python team.py run "Описание задачи"
    python team.py run --file task.json
    python team.py list-departments
    python team.py department <name>
    python team.py list-workflows
"""

import json
import sys
from pathlib import Path


DEPARTMENTS_DIR = Path(__file__).parent / "departments"
ORCHESTRATION_DIR = Path(__file__).parent / "orchestration"
WORKFLOWS_DIR = Path(__file__).parent / "workflows"

DEPARTMENT_EMOJI = {
    "product": "🏭",
    "architecture": "🏗️",
    "development": "💻",
    "qa": "🧪",
    "devops": "⚙️",
    "design": "🎨",
    "docs": "📖",
}


def list_departments():
    """Показать список всех отделов и их сотрудников."""
    print("\n🏢 Отделы корпорации:\n")
    for dept_dir in sorted(DEPARTMENTS_DIR.iterdir()):
        if dept_dir.is_dir():
            emoji = DEPARTMENT_EMOJI.get(dept_dir.name, "📁")
            readme = dept_dir / "README.md"
            print(f"  {emoji} {dept_dir.name.capitalize()}")
            if readme.exists():
                content = readme.read_text(encoding="utf-8")
                # Извлекаем сотрудников
                for line in content.split("\n"):
                    if line.strip().startswith("####") or line.strip().startswith("### 👔"):
                        role = line.replace("####", "").replace("### 👔", "👔").strip()
                        print(f"      {role}")
            print()
    print(f"\n🧠 Руководство: {ORCHESTRATION_DIR.name}/")


def show_department(name: str):
    """Показать подробную информацию об отделе."""
    dept_path = DEPARTMENTS_DIR / name
    if not dept_path.exists():
        print(f"❌ Отдел '{name}' не найден.")
        print(f"   Доступные: {', '.join(d.name for d in DEPARTMENTS_DIR.iterdir() if d.is_dir())}")
        return

    emoji = DEPARTMENT_EMOJI.get(name, "📁")
    readme = dept_path / "README.md"
    if readme.exists():
        print(readme.read_text(encoding="utf-8"))
    else:
        print(f"{emoji} Отдел {name} (описание отсутствует)")


def list_workflows():
    """Показать список доступных workflow."""
    print("\n📋 Доступные workflow:\n")
    for md_file in sorted(WORKFLOWS_DIR.glob("*.md")):
        name = md_file.stem
        print(f"  • {name}")


def run_task(description_or_file: str):
    """
    Запустить корпорацию на выполнение задачи.
    CEO анализирует задачу, определяет отделы, делегирует Heads.
    """
    task_data = {}

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
    print(f"\n{'='*60}")
    print(f"🧠 CEO получил задачу: {task.get('title', 'Без названия')}")
    print(f"{'='*60}")
    print(f"   📝 {task.get('description', 'Нет описания')[:200]}")
    print()

    # CEO анализирует задачу и определяет отделы
    print("🔍 CEO анализирует задачу...")
    print("   Определяю, какие отделы потребуются...\n")

    # Определяем задействованные отделы на основе контекста
    context = task.get("context", {})
    stack = context.get("stack", [])
    deps_needed = ["product", "architecture"]

    if any(s in str(stack).lower() for s in ["python", "js", "ts", "java", "go", "rust", "dart"]):
        deps_needed.append("development")
    deps_needed.append("qa")
    if any(s in str(stack).lower() for s in ["docker", "k8s", "aws", "gcp", "azure", "ci/cd"]):
        deps_needed.append("devops")
    if any(s in str(stack).lower() for s in ["ui", "ux", "frontend", "design"]):
        deps_needed.append("design")
    deps_needed.append("docs")

    print("🏢 Задействованные отделы:\n")
    for dept in deps_needed:
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        print(f"   {emoji} {dept.capitalize()} — Head получает подзадачу")

    print(f"\n{'='*60}")
    print("📋 CEO формирует план работ:")
    print(f"{'='*60}")
    print(f"   1. Product — анализ требований")
    print(f"   2. Architecture — проектирование")
    print(f"   3. Development — реализация")
    print(f"   4. QA — тестирование")
    if "devops" in deps_needed:
        print(f"   5. DevOps — инфраструктура и деплой")
    print(f"   6. Design — UI/UX")
    print(f"   7. Docs — документация")
    print(f"   8. CEO — сборка результата\n")

    print("🚀 Запуск выполнения... (заглушка — полноценная оркестрация будет реализована)")
    print("✅ Задача принята в работу.\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]

    if command == "list-departments":
        list_departments()
    elif command == "department":
        if len(sys.argv) < 3:
            print("❌ Укажите название отдела.")
            print("   Пример: python team.py department development")
            sys.exit(1)
        show_department(sys.argv[2])
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
