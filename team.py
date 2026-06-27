#!/usr/bin/env python3
"""
AI Agents Team — Корпорация AI-агентов с организационной структурой.

Использование:
    python team.py run "Описание задачи"
    python team.py run --file task.json
    python team.py list-departments
    python team.py department <name>
    python team.py list-workflows
    python team.py list-interactions
    python team.py dashboard [--port 8000]
    python team.py orchestrate "Описание задачи"
    python team.py orchestrate --file task.json
    python team.py search "поисковый запрос"
    python team.py memory stats
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


# Добавляем корень проекта в путь для импорта dashboard и mcp-server
sys.path.insert(0, str(Path(__file__).parent))

DEPARTMENTS_DIR = Path(__file__).parent / "departments"

DEPARTMENTS_DIR = Path(__file__).parent / "departments"
ORCHESTRATION_DIR = Path(__file__).parent / "orchestration"
INTERACTIONS_DIR = Path(__file__).parent / "interactions"
WORKFLOWS_DIR = Path(__file__).parent / "workflows"

DEPARTMENT_EMOJI = {
    "product": "🏭",
    "architecture": "🏗️",
    "development": "💻",
    "qa": "🧪",
    "devops": "⚙️",
    "design": "🎨",
    "docs": "📖",
    "hr": "👥",
    "security": "🛡️",
    "data": "📊",
    "rd": "🔬",
    "legal": "⚖️",
    "marketing": "📣",
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


def list_interactions():
    """Показать протоколы взаимодействия между отделами."""
    print("\n🔄 Протоколы взаимодействия:\n")
    readme = INTERACTIONS_DIR / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        # Показываем первые строки
        for line in content.split("\n")[:15]:
            if line.strip() and not line.startswith("#"):
                print(f"  {line}")
    print()
    print("  📄 Детали:")
    for f in sorted(INTERACTIONS_DIR.rglob("*.md")):
        rel = f.relative_to(INTERACTIONS_DIR)
        print(f"    • interactions/{rel}")
    print()


def run_task(description_or_file: str):
    """
    Запустить корпорацию на выполнение задачи.
    CEO анализирует задачу, определяет отделы, делегирует Heads.
    """
    task_data = _load_task_data(description_or_file)
    task = task_data.get("task", task_data)
    _show_task_analysis(task)


def _load_task_data(description_or_file: str) -> dict:
    """Загрузить данные задачи из строки или файла."""
    if description_or_file.endswith(".json"):
        filepath = Path(description_or_file)
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        print(f"❌ Файл не найден: {filepath}")
        sys.exit(1)
    else:
        return {
            "task": {
                "id": "manual-001",
                "title": "Ручной ввод",
                "description": description_or_file,
                "context": {},
                "constraints": []
            }
        }


def _show_task_analysis(task: dict):
    """Показать анализ задачи CEO."""
    context = task.get("context", {})
    stack = context.get("stack", [])
    deps_needed = _determine_departments(task)

    print(f"\n{'='*60}")
    print(f"🧠 CEO получил задачу: {task.get('title', 'Без названия')}")
    print(f"{'='*60}")
    print(f"   📝 {task.get('description', 'Нет описания')[:200]}")
    print()
    print("🔍 CEO анализирует задачу...")
    print("   Определяю, какие отделы потребуются...\n")

    print("🏢 Задействованные отделы:\n")
    for dept in deps_needed:
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        print(f"   {emoji} {dept.capitalize()} — Head получает подзадачу")

    print(f"\n{'='*60}")
    print("📋 CEO формирует план работ:")
    print(f"{'='*60}")
    steps = [
        (1, "Product", "анализ требований"),
        (2, "Architecture", "проектирование"),
        (3, "Development", "реализация"),
        (4, "QA", "тестирование"),
        (5, "DevOps", "инфраструктура и деплой"),
        (6, "Design", "UI/UX"),
        (7, "Docs", "документация"),
        (8, "Security", "аудит безопасности"),
        (9, "Data", "данные и аналитика"),
        (10, "R&D", "исследования"),
        (11, "Legal", "юридический compliance"),
        (12, "Marketing", "продвижение"),
        (13, "HR", "анализ и рекомендации"),
    ]
    i = 1
    for _, name, desc in steps:
        if name.lower() in deps_needed:
            print(f"   {i}. {name} — {desc}")
            i += 1
    print(f"   {i}. CEO — сборка результата\n")


def _determine_departments(task: dict) -> list:
    """Определить, какие отделы нужны для задачи."""
    # Если в задаче явно указано — используем это
    deps = task.get("departments_needed")
    if deps:
        return deps

    # Иначе — определяем по контексту
    if "departments_plan" in task:
        return task["departments_plan"]

    context = task.get("context", {})
    stack = context.get("stack", [])
    stack_str = str(stack).lower()

    deps_needed = ["product", "architecture"]
    # Всегда добавляем development для технических задач
    tech_keywords = ["python", "js", "ts", "java", "go", "rust", "dart", "kotlin",
                     "swift", "api", "rest", "graphql", "backend", "frontend",
                     "database", "sql", "postgresql", "mysql", "redis", "mongodb",
                     "server", "microservice", "fastapi", "django", "react", "vue"]
    if any(s in stack_str for s in tech_keywords):
        deps_needed.append("development")
    elif not any(kw in str(task).lower() for kw in ["research", "design", "marketing", "legal"]):
        # Если задача явно не про research/design/marketing — добавляем dev
        deps_needed.append("development")
    deps_needed.append("qa")
    if any(s in stack_str for s in ["docker", "k8s", "aws", "gcp", "azure", "ci/cd", "terraform"]):
        deps_needed.append("devops")
    if any(s in stack_str for s in ["ui", "ux", "frontend", "design", "figma"]):
        deps_needed.append("design")
    if any(s in stack_str for s in ["data", "ml", "analytics", "pipeline", "etl"]):
        deps_needed.append("data")
    if any(s in stack_str for s in ["research", "poc", "prototype", "innovation"]):
        deps_needed.append("rd")
    if any(s in stack_str for s in ["security", "audit", "penetration"]):
        deps_needed.append("security")
    if any(s in stack_str for s in ["license", "legal", "compliance"]):
        deps_needed.append("legal")
    if any(s in stack_str for s in ["marketing", "promotion", "brand"]):
        deps_needed.append("marketing")
    deps_needed.append("docs")

    return deps_needed


def orchestrate(description_or_file: str):
    """
    Запустить реальную цепочку выполнения задачи.
    Создаёт задачу в MCP-сервере и последовательно проходит по отделам.
    """
    # Принудительно переключаем stdout на UTF-8 для эмодзи
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # Импортируем task_store через mcp_server (добавляет mcp-server/ в path)
    import mcp_server  # noqa: F401
    from task_store import (
        create_task, assign_to_department, complete_department,
        get_task
    )

    task_data = _load_task_data(description_or_file)
    task = task_data.get("task", task_data)

    title = task.get("title", "Без названия")
    description = task.get("description", "")
    departments = _determine_departments(task)

    print(f"\n{'='*60}")
    print(f"🚀 **AI DevCorp — Запуск оркестрации**")
    print(f"{'='*60}")
    print(f"   📋 Задача: {title}")
    print(f"   📝 {description[:200]}")
    print(f"   🔗 Цепочка: {' → '.join(d.capitalize() for d in departments)}")
    print()

    # Шаг 1: Создаём задачу в MCP-сервере
    result = create_task(title, departments, description)
    if "error" in result:
        print(f"❌ Ошибка создания задачи: {result['error']}")
        return
    task_id = result["id"]
    print(f"✅ Задача создана: {task_id}")
    print()

    # Шаг 2: Проходим по цепочке отделов
    prev_dept = None
    for i, dept in enumerate(departments):
        emoji = DEPARTMENT_EMOJI.get(dept, "📁")
        label = dept.capitalize()

        print(f"{'─'*50}")
        print(f"  Шаг {i+1}/{len(departments)}: {emoji} {label}")
        print(f"{'─'*50}")

        # Назначаем отделу
        r = assign_to_department(task_id, dept)
        if "error" in r:
            print(f"  ❌ Ошибка: {r['error']}")
            break

        # Читаем профиль отдела для контекста
        dept_readme = DEPARTMENTS_DIR / dept / "README.md"
        if dept_readme.exists():
            content = dept_readme.read_text(encoding="utf-8")
            # Извлекаем первую строку описания
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("**Направление:**"):
                    print(f"  📋 {line}")
                    break

        # Симулируем работу отдела
        print(f"  ⏳ {label} работает...")
        artifacts = {
            "output": f"{dept}/{task_id}-output.md",
            "status": "completed",
        }

        # Завершаем отдел
        r = complete_department(task_id, dept, artifacts)
        if "error" in r:
            print(f"  ❌ Ошибка: {r['error']}")
            break

        print(f"  ✅ {label} завершил работу")
        prev_dept = dept
        print()

    # Получаем финальный статус
    final = get_task(task_id)

    # Шаг 3: 👥 HR Performance Review (реальный анализ)
    print(f"{'─'*50}")
    print(f"  📊 👥 HR — Performance Review")
    print(f"{'─'*50}")
    try:
        # Запускаем HR-движок
        import subprocess
        hr_script = str(Path(__file__).parent / "departments" / "hr" / "hr_engine.py")
        hr_result = subprocess.run(
            [sys.executable, hr_script],
            capture_output=True, text=True, timeout=30
        )
        if hr_result.stdout:
            for line in hr_result.stdout.split("\n"):
                if line.strip():
                    print(f"  {line}")
        if hr_result.returncode != 0:
            print(f"  ⚠️  HR-анализ завершился с ошибкой: {hr_result.stderr[:100]}")
    except Exception as e:
        print(f"  ⚠️  HR-движок недоступен: {e}")
    print()

    # Шаг 4: 🧠 Memory — сохраняем в долговременную память
    print(f"{'─'*50}")
    print(f"  🧠 Memory — сохранение в долговременную память")
    print(f"{'─'*50}")
    try:
        import subprocess
        memory_script = str(Path(__file__).parent / "memory" / "memory_store.py")
        mem_result = subprocess.run(
            [sys.executable, "-X", "utf8", memory_script],
            capture_output=True, text=True, timeout=30
        )
        if mem_result.stdout:
            for line in mem_result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"  {line}")
    except Exception as e:
        print(f"  ⚠️  Memory недоступна: {e}")
    print()

    # Шаг 5: 🔍 Semantic search — ищем похожие задачи
    print(f"{'─'*50}")
    print(f"  🔍 Semantic search — поиск похожих задач")
    print(f"{'─'*50}")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from memory.memory_store import search
        similar = search(title, top_k=3)
        if similar:
            for r in similar:
                score = r.get("score", 0) * 100
                lesson = r.get("lesson", "") or r.get("error", "") or ""
                print(f"  • [{score:.0f}%] {r['title']} ({r['status']})")
                if lesson:
                    print(f"    {lesson[:80]}")
        else:
            print(f"  • Похожих задач не найдено (новая область)")
    except Exception as e:
        print(f"  ⚠️  Поиск недоступен: {e}")
    print()
    print(f"  Анализ выполнения задачи...")
    print(f"  • Отделов задействовано: {len(departments)}")
    print(f"  • Статус: {'✅ Успешно' if final.get('status') == 'completed' else '🔄 В процессе'}")
    print(f"  • Артефактов создано: {len(final.get('artifacts', {}))}")

    # Рекомендации HR
    speed = "быстро" if len(departments) <= 3 else "нормально" if len(departments) <= 6 else "сложная задача"
    quality = "хорошее" if final.get("status") == "completed" else "требует внимания"
    print(f"  📈 Оценка: задача выполнена {speed}, качество — {quality}")
    print(f"  💡 Рекомендация: {'добавить больше тестов' if 'qa' not in departments else 'оптимизировать handoff между отделами'}")
    print()

    print(f"{'='*60}")
    if final:
        status = final.get("status", "unknown")
        status_emoji = {
            "completed": "✅",
            "in_progress": "🔄",
            "planned": "📋",
            "escalated": "🚨",
        }.get(status, "❓")
        comp = len(final.get("departments_completed", []))
        total = len(final.get("departments_plan", []))
        print(f"  {status_emoji} Статус: {status}")
        print(f"  📊 Прогресс: {comp}/{total} отделов завершили")
        print(f"  🆔 ID задачи: {task_id}")
    print(f"{'='*60}\n")


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
    elif command == "list-interactions":
        list_interactions()
    elif command == "dashboard":
        port = 8000
        if len(sys.argv) >= 4 and sys.argv[2] == "--port":
            port = int(sys.argv[3])
        print(f"\n📊 Запуск дашборда на http://localhost:{port}")
        print("   Нажмите Ctrl+C для остановки.\n")
        import uvicorn
        from dashboard.app import app
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif command == "search":
        if len(sys.argv) < 3:
            print("❌ Укажите поисковый запрос.")
            print("   Пример: python team.py search \"REST API авторизация\"")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        try:
            from memory.memory_store import search, get_stats
            print(f"\n🔍 Поиск: \"{query}\"\n")
            results = search(query)
            if results:
                for r in results:
                    score = r.get("score", 0) * 100
                    lesson = r.get("lesson", "") or r.get("error", "") or "(нет заметок)"
                    print(f"  [{score:.0f}%] {r['title']} — {r['status']}")
                    print(f"       Отделы: {', '.join(r.get('departments', []))}")
                    print(f"       {lesson[:120]}")
                    print()
            else:
                print("  Ничего не найдено.\n")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

    elif command == "memory":
        if len(sys.argv) >= 3 and sys.argv[2] == "stats":
            try:
                from memory.memory_store import get_stats
                stats = get_stats()
                print(f"\n🧠 Статистика памяти команды:\n")
                print(f"  Всего задач в памяти: {stats['total_tasks_remembered']}")
                print(f"  ✅ Успешных: {stats['successful']}")
                print(f"  ❌ Проваленных: {stats['failed']}")
                print(f"  🔄 В процессе: {stats['in_progress']}")
                if stats['departments_used']:
                    print(f"  🏢 Задействовано отделов: {len(stats['departments_used'])}")
                    print(f"     {', '.join(stats['departments_used'])}")
                print()
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
        else:
            # Переобучить память из всех задач
            try:
                from memory.memory_store import learn_from_tasks
                result = learn_from_tasks()
                print(f"\n🧠 Память переобучена: {result['learned']} новых, "
                      f"всего {result['total']}\n")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

    elif command == "orchestrate":
        if len(sys.argv) < 3:
            print("❌ Укажите описание задачи или путь к JSON-файлу.")
            print("   Пример: python team.py orchestrate \"Создать REST API\"")
            print("   Пример: python team.py orchestrate --file task.json")
            sys.exit(1)

        arg = sys.argv[2]
        if arg == "--file" and len(sys.argv) >= 4:
            orchestrate(sys.argv[3])
        else:
            orchestrate(arg)
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
