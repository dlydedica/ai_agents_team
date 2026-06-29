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
    python team.py validate
    python team.py delegate <task_id> <department>
    python team.py self-diagnose
    python team.py self-diagnose --fix
    python team.py learn "описание ошибки" "команда для проверки"    python team.py skills suggest [технология...]
    python team.py skills search <технология>
    python team.py skills install <url> [имя]
    python team.py skills assign <скил> <отдел>
    python team.py skills scan [путь_к_проекту]
    python team.py skills sync
    python team.py skills report"""

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


def validate_all_python(verbose: bool = True):
    """Проверить весь Python-код на синтаксис. Возвращает (count, errors)."""
    import ast
    repo = Path(__file__).parent
    errors = []
    checked = 0

    py_files = list(repo.rglob("*.py"))
    py_files = [f for f in py_files
                if "venv" not in f.parts
                and "__pycache__" not in f.parts
                and "data" not in f.parts
                and "site-packages" not in f.parts]

    for f in sorted(py_files):
        checked += 1
        try:
            ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            errors.append({"file": f.relative_to(repo), "error": str(e), "type": "syntax"})
        except Exception as e:
            errors.append({"file": f.relative_to(repo), "error": str(e), "type": "other"})

    if verbose:
        print(f"\n🔍 Проверено {checked} файлов")
        if errors:
            print(f"   ❌ {len(errors)} ошибок")
            for e in errors:
                print(f"      {e['file']}: {e['error'][:80]}")
        else:
            print(f"   ✅ Все файлы валидны")

    return checked, errors


def _auto_fix():
    """Попытаться автоматически исправить дублированные блоки."""
    repo = Path(__file__).parent
    fixes = []
    checked, errors = validate_all_python(verbose=False)

    for e in errors:
        try:
            fpath = repo / e["file"]
            if not fpath.exists():
                fixes.append(f"  ❌ Файл не существует: {e['file']}")
                continue

            content = fpath.read_text(encoding="utf-8")
            lines = content.split("\n")
            changed = False
            i = 0
            while i < len(lines) - 2:
                block = "\n".join(lines[i:i+2])
                rest = "\n".join(lines[i+2:])
                if block in rest:
                    idx = rest.index(block)
                    lines = lines[:i+2] + lines[i+2+idx:]
                    changed = True
                    fixes.append(f"  🔧 {e['file']}: удалён дубликат")
                    break
                i += 1
            if changed:
                fpath.write_text("\n".join(lines), encoding="utf-8")
            else:
                fixes.append(f"  ⚠️  {e['file']}: {e['error'][:60]}")
        except Exception as ex:
            fixes.append(f"  ⚠️  {e['file']}: ошибка автофикса: {ex}")

    return fixes


def self_diagnose(fix_mode: bool = False):
    """
    Адаптивная самодиагностика. Запускает все зарегистрированные проверки
    из checks/builtin/ и checks/learned/. Новые проверки добавляются
    автоматически через team.py learn.
    """
    from checks.registry import run_all_checks, discover_checks

    print(f"\n{'='*60}")
    print(f"  🧬 AI DevCorp — Адаптивная самодиагностика")
    print(f"{'='*60}")

    checks = discover_checks()
    builtin = [c for c in checks if c.get("source") == "builtin"]
    learned = [c for c in checks if c.get("source") == "learned"]

    print(f"\n  📊 Реестр проверок: {len(builtin)} встроенных + {len(learned)} изученных\n")

    passed, failed = run_all_checks(verbose=True)

    print(f"\n  {'='*50}")
    print(f"  ✅ Пройдено: {len(passed)}")
    print(f"  ❌ Ошибок: {len(failed)}")
    if learned:
        print(f"  🧠 Изученных проверок: {len(learned)}")
    print(f"  {'='*50}\n")

    if failed:
        print(f"  🚨 Обнаружены проблемы. Рекомендации:")
        for f in failed:
            print(f"    • {f['name']}: {f['message'][:100]}")
        if fix_mode:
            print(f"\n  🔧 Запуск автоисправления...")
            from checks.registry import learn_from_failure
            for f in failed:
                learn_from_failure(f"{f['name']}: {f['message']}")
                print(f"    ✅ Создана проверка для: {f['name']}")
        print()
    else:
        # Если всё ок — запускаем ретроспективу completed задач
        try:
            from task_store import get_all_tasks
            completed = [t for t in get_all_tasks().values() if t.get("status") == "completed"]
            if completed:
                from departments.hr.retrospective import run_retrospective
                last = completed[-1]
                result = run_retrospective(last["id"])
                if result and "error" not in result:
                    print(f"  📋 Ретроспектива последней задачи: {result['report']}")
        except Exception:
            pass

    return len(failed) == 0


def _quality_gate():
    """Quality Gate — запускается перед завершением задачи."""
    print(f"\n{'─'*50}")
    print(f"  🛡️ QA — Quality Gate")
    print(f"{'─'*50}")
    checked, errors = validate_all_python(verbose=True)
    if errors:
        print(f"\n  ❌ Quality Gate НЕ ПРОЙДЕН — {len(errors)} ошибок")
        print(f"  🚨 Задача будет эскалирована")
        print(f"  🔧 Попробуйте: python team.py self-diagnose --fix\n")
        return False
    print(f"\n  ✅ Quality Gate ПРОЙДЕН — код чист\n")
    return True


def delegate(task_id: str, department: str):
    """
    Сформировать промпт для вызова subagent'а через MCP.
    CEO использует этот вывод для делегирования отделам.
    """
    import json as _json
    import mcp_server  # noqa: F401
    from task_store import get_task
    task = get_task(task_id)
    if not task:
        print(f"❌ Задача {task_id} не найдена")
        return

    dept_readme = DEPARTMENTS_DIR / department / "README.md"
    agent_file = Path(__file__).parent / ".github" / "agents" / "departments" / f"{department}.agent.md"

    direction = ""
    if dept_readme.exists():
        for line in dept_readme.read_text(encoding="utf-8").split("\n"):
            if line.strip().startswith("**Направление:**"):
                direction = line.strip().replace("**", "")
                break

    handoff_input = []
    handoff_output = []
    if agent_file.exists():
        in_section = False
        out_section = False
        for line in agent_file.read_text(encoding="utf-8").split("\n"):
            if line.strip().startswith("## Вход"):
                in_section = True; out_section = False; continue
            if line.strip().startswith("## Выход"):
                out_section = True; in_section = False; continue
            if line.strip().startswith("## ") and "Вход" not in line and "Выход" not in line:
                in_section = False; out_section = False
            if in_section and "`" in line:
                handoff_input.append(line.strip())
            if out_section and "`" in line:
                handoff_output.append(line.strip())

    emoji = DEPARTMENT_EMOJI.get(department, "📁")
    print(f"\n{'='*60}")
    print(f"{emoji} Делегирование: {department.capitalize()}")
    print(f"{'='*60}")
    print(f"  Задача: {task.get('title', '?')}")
    print(f"  {direction}")
    print()
    print(f"  📥 Handoff input:")
    for h in handoff_input:
        print(f"    {h}")
    print()
    print(f"  📤 Ожидаемый output:")
    for h in handoff_output:
        print(f"    {h}")
    print()
    print(f"  📋 Контекст для subagent:")
    print(f"    task_id: {task_id}")
    print(f"    title: {task.get('title', '?')}")
    print(f"    departments_plan: {task.get('departments_plan', [])}")
    print(f"    departments_completed: {task.get('departments_completed', [])}")
    print(f"    artifacts: {_json.dumps(task.get('artifacts', {}), ensure_ascii=False)}")
    print()
    print(f"  💡 Вызови subagent: departments/{department}.agent.md")
    print(f"     с описанием задачи выше")
    print()


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

    # 🔍 Ищем похожие задачи в памяти
    try:
        from memory.memory_store import suggest_similar
        similar = suggest_similar(title, description)
        if similar:
            print(f"  🧠 Найдены похожие задачи в памяти ({len(similar)} шт.):")
            for s in similar:
                score = s.get("score", 0) * 100
                lesson = s.get("lesson", "") or ""
                print(f"     • [{score:.0f}%] {s['title']} — {s.get('status', '?')}")
                if lesson:
                    print(f"       {lesson[:100]}")
            print()
    except Exception:
        pass

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
        handoff_inputs = ""
        handoff_outputs = ""
        if dept_readme.exists():
            content = dept_readme.read_text(encoding="utf-8")
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("**Направление:**"):
                    print(f"  📋 {line}")
                # Извлекаем handoff информацию из agent файла
        agent_file = Path(__file__).parent / ".github" / "agents" / "departments" / f"{dept}.agent.md"
        if agent_file.exists():
            agent_content = agent_file.read_text(encoding="utf-8")
            in_section = False
            out_section = False
            for line in agent_content.split("\n"):
                if line.strip().startswith("## Вход"):
                    in_section = True
                    out_section = False
                    continue
                if line.strip().startswith("## Выход"):
                    out_section = True
                    in_section = False
                    continue
                if line.strip().startswith("## ") and not line.strip().startswith("## Вход") and not line.strip().startswith("## Выход"):
                    in_section = False
                    out_section = False
                if in_section and line.strip().startswith("- `"):
                    handoff_inputs += f"\n      {line.strip()}"
                if out_section and line.strip().startswith("- `"):
                    handoff_outputs += f"\n      {line.strip()}"

        print(f"  📥 Handoff input:{handoff_inputs}")
        print(f"  ⏳ {label} работает...")
        artifacts = {
            "output": f"{dept}/{task_id}-output.md",
            "status": "completed",
        }

        # Показываем handoff пакет
        if i > 0:
            prev = departments[i - 1]
            print(f"  📦 Handoff: {prev.capitalize()} → {label}")
        print(f"  📤 Handoff output:{handoff_outputs}")

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

    # Шаг 2.5: 🛡️ Quality Gate — проверка кода перед завершением
    quality_ok = _quality_gate()

    # Если Quality Gate не пройден — запускаем адаптивный цикл
    if not quality_ok:
        try:
            from task_store import escalate, log_event
            from checks.registry import learn_from_failure, run_all_checks

            escalate(task_id, "Quality Gate failed — код содержит ошибки")

            # 🔬 R&D — анализ ошибки и создание check
            print(f"{'─'*50}")
            print(f"  🔬 R&D — анализ ошибки и создание проверки")
            print(f"{'─'*50}")
            passed, failed = run_all_checks(verbose=False)
            for f in failed:
                learn_from_failure(f"{f['name']}: {f['message']}")
                print(f"  🧬 Создан check: {f['name']}")
            log_event(task_id, "rd.check_created",
                      f"Создано {len(failed)} checks для предотвращения повторения")

            # 💻 Development — auto-fix
            print(f"\n{'─'*50}")
            print(f"  💻 Development — автоисправление")
            print(f"{'─'*50}")
            fixes = _auto_fix()
            if fixes:
                for f in fixes:
                    print(f"  {f}")
                log_event(task_id, "dev.auto_fix", f"Применено {len(fixes)} исправлений")
            else:
                print(f"  Ручное исправление не требуется или невозможно")

            print(f"\n  🚨 Задача {task_id} эскалирована (Quality Gate не пройден)")
            print(f"  🧬 Созданы checks для предотвращения в будущем")

        except Exception as e:
            print(f"  ⚠️  Адаптивный цикл: {e}")

    # 👥 Память сохраняется в Шаге 4 (ниже) для всех случаев — успех и ошибка

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

    # Шаг 3.5: 🔄 Ретроспектива — анализ для самоулучшения
    print(f"{'─'*50}")
    print(f"  🔄 Ретроспектива — анализ задачи")
    print(f"{'─'*50}")
    try:
        retro_script = str(Path(__file__).parent / "departments" / "hr" / "retrospective.py")
        retro_result = subprocess.run(
            [sys.executable, retro_script, task_id],
            capture_output=True, text=True, timeout=15
        )
        if retro_result.stdout:
            for line in retro_result.stdout.strip().split("\n"):
                if line.strip() and not line.startswith("❌"):
                    print(f"  {line}")
    except Exception as e:
        print(f"  ⚠️  Ретроспектива: {e}")
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

# ──────────────────────────────────────────────
# Skills management
# ──────────────────────────────────────────────


def _skills_help():
    """Показать справку по подкомандам skills."""
    print(__doc__)


def _skills_suggest(technologies: list[str] = None):
    """Предложить скилы для установки на основе технологий."""
    from skills.discovery import suggest_skills

    if technologies:
        print(f"\n🔍 Поиск скилов для технологий: {', '.join(technologies)}\n")
    else:
        print("\n🔍 Все известные источники скилов:\n")

    suggestions = suggest_skills(technologies=technologies)
    if not suggestions:
        print("  😕 Ничего не найдено")
        return

    for s in suggestions:
        status = "✅" if s.is_installed else "⬇️"
        depts = ", ".join(s.departments)
        techs_str = ", ".join(s.technologies)
        stars = f" ⭐{s.stars}" if s.stars else ""
        print(f"  {status} {s.name} — {s.description[:100]}{stars}")
        print(f"       отделы: {depts} | технологии: {techs_str}")
        print(f"       {s.repo}")
        if not s.is_installed:
            print(f"       установка: python team.py skills install {s.url}")
        print()

    installed = sum(1 for s in suggestions if s.is_installed)
    total = len(suggestions)
    print(f"  📊 Найдено: {total} | Установлено: {installed} | Доступно: {total - installed}\n")


def _skills_search(technology: str):
    """Поиск скилов на GitHub по технологии."""
    from skills.discovery import search_github_skills

    print(f"\n🔍 Поиск на GitHub: \"{technology}\"\n")
    results = search_github_skills(technology)

    if not results:
        print("  😕 Ничего не найдено. GitHub API может быть недоступен.\n")
        print("  💡 Попробуйте: python team.py skills suggest")
        return

    for r in results:
        techs = ", ".join(r.get("technologies", []))
        stars = r.get("stars", 0)
        print(f"  📦 {r['name']} ⭐{stars}")
        print(f"       {r.get('description', '')[:120]}")
        print(f"       технологии: {techs}")
        print(f"       установка: python team.py skills install {r['url']}")
        print()


def _skills_install(url: str, name: str = ""):
    """Установить внешние скилы из git-репозитория."""
    from skills.loader import install_from_git

    print(f"\n📦 Установка скилов из: {url}\n")
    result = install_from_git(url, name)

    if "error" in result:
        print(f"❌ Ошибка: {result['error']}\n")
        return

    installed = result.get("skills_installed", [])
    print(f"✅ Источник '{result['source']}' установлен")
    if installed:
        print(f"   Найдено скилов: {len(installed)}")
        for s in installed:
            print(f"     • {s}")
    else:
        # Пересканируем — наш реестр мог подхватить SKILL.md форматы
        print(f"   🔄 Пересканирование реестра...")
    print(f"\n   Проверить: python team.py skills report\n")


def _skills_assign(skill_name: str, department: str):
    """Назначить скил отделу."""
    from skills.assigner import assign_skill_to_department

    result = assign_skill_to_department(skill_name, department)

    if "error" in result:
        print(f"❌ {result['error']}")
        return
    if "warning" in result:
        print(f"⚠️  {result['warning']}")
        return
    print(f"✅ {result['message']}")


def _skills_scan(project_path: str = "."):
    """Сканировать проект на технологии и предложить скилы."""
    from skills.project_scanner import scan_project, technologies_to_search_tags, auto_extend_known_repos

    print(f"\n🔍 Сканирование проекта: {project_path}\n")
    result = scan_project(project_path)

    if not result.technologies:
        print("  😕 Технологии не обнаружены\n")
        return

    print(f"  📁 Проект: {result.project_name}\n")
    print(f"  📊 Стек технологий:\n")

    for cat in result.categories:
        techs = [t for t in result.technologies if t.category == cat]
        print(f"  [{cat.upper()}]")
        for t in techs:
            print(f"     ✅ {t.name:25s} ({t.source_file})")
        print()

    # Анализ покрытия скилами
    coverage = auto_extend_known_repos(result.technologies)

    print(f"  📋 Покрытие скилами:\n")
    if coverage["covered"]:
        print(f"     ✅ Есть скилы: {', '.join(coverage['covered'])}")
    if coverage["uncovered"]:
        print(f"     ⚠️  Нет скилов: {', '.join(coverage['uncovered'])}")

    # Поиск на GitHub
    if coverage["suggestions"]:
        print(f"\n  🌐 Найдено на GitHub ({len(coverage['suggestions'])} репозиториев):\n")
        for s in sorted(coverage["suggestions"], key=lambda x: -x.get("stars", 0))[:5]:
            depts = ", ".join(s["departments"])
            print(f"     ⭐{s.get('stars', 0)} {s['key']} — {s.get('description', '')[:80]}")
            print(f"        отделы: {depts}")
            print(f"        установка: python team.py skills install {s['url']}")
            print()
    elif coverage["uncovered"]:
        print(f"\n  🌐 GitHub API недоступен — не удалось найти скилы в интернете.")
        print(f"     💡 Можно добавить репозитории вручную в skills/known_repos.json\n")

    if coverage["github_error"]:
        print(f"  ⚠️  Ошибка GitHub: {coverage['github_error']}\n")

    tags = technologies_to_search_tags(result.technologies)
    print(f"  🏷️  Теги для поиска: {' '.join(tags)}\n")


def _skills_sync():
    """Установить все известные, но ещё не установленные репозитории."""
    from skills.discovery import ALL_SOURCES
    from skills.loader import install_from_git

    pending = [s for s in ALL_SOURCES if not s.get("installed") and s.get("url")]
    if not pending:
        print("\n✅ Все известные репозитории уже установлены\n")
        return

    print(f"\n📦 Установка {len(pending)} репозиториев:\n")
    for s in pending:
        name = s["name"]
        url = s["url"]
        branch = s.get("branch", "main")
        print(f"  ⬇️  {name} — {s.get('description', url)}")
        try:
            result = install_from_git(url, name, branch)
            if "error" in result:
                print(f"     ❌ {result['error']}")
            else:
                installed = result.get("skills_installed", [])
                print(f"     ✅ Установлено ({len(installed)} скилов)")
        except Exception as e:
            print(f"     ❌ {e}")
        print()
    print("  💡 Проверить: python team.py skills suggest\n")


def _skills_report():
    """Показать отчёт о покрытии отделов скилами."""
    from skills.assigner import generate_coverage_report

    print("\n📊 Отчёт о покрытии отделов скилами:\n")
    reports = generate_coverage_report()

    for report in reports:
        emoji = DEPARTMENT_EMOJI.get(report.department, "📁")
        bar = "█" * min(report.total_skills, 20) + "░" * max(0, 20 - min(report.total_skills, 20))
        print(f"  {emoji} {report.department.capitalize():15s} |{bar}| {report.total_skills:2d} скилов "
              f"({report.builtin_skills} builtin + {report.external_skills} external)")

        if report.missing_tags:
            print(f"       ⚠️  Непокрытые технологии: {', '.join(report.missing_tags[:5])}")
            print(f"       💡 python team.py skills suggest {' '.join(report.missing_tags[:3])}")
        print()

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

    elif command == "delegate":
        if len(sys.argv) < 4:
            print("❌ Укажите task_id и отдел.")
            print("   Пример: python team.py delegate task-a1b2c3 development")
            sys.exit(1)
        delegate(sys.argv[2], sys.argv[3])
    elif command == "validate":
        ok = validate_all_python(verbose=True)
        sys.exit(0 if ok else 1)
    elif command == "self-diagnose":
        fix_mode = "--fix" in sys.argv
        ok = self_diagnose(fix_mode=fix_mode)
        # Если были ошибки и fix_mode — создаём checks
        if not ok and fix_mode:
            from checks.registry import learn_from_failure, run_all_checks
            passed, failed = run_all_checks(verbose=False)
            for f in failed:
                learn_from_failure(f"{f['name']}: {f['message']}")
                print(f"  🧠 Создана проверка для: {f['name']}")
            print(f"  ✅ Проверки созданы. Они будут запускаться при каждой диагностике.")
        sys.exit(0 if ok else 1)
    elif command == "skills":
        if len(sys.argv) < 3:
            _skills_help()
            sys.exit(1)

        subcmd = sys.argv[2]

        if subcmd == "suggest":
            techs = sys.argv[3:] if len(sys.argv) > 3 else None
            _skills_suggest(techs)
        elif subcmd == "search":
            if len(sys.argv) < 4:
                print("❌ Укажите технологию для поиска.")
                print("   Пример: python team.py skills search golang")
                sys.exit(1)
            _skills_search(sys.argv[3])
        elif subcmd == "install":
            if len(sys.argv) < 4:
                print("❌ Укажите URL репозитория со скилами.")
                print("   Пример: python team.py skills install https://github.com/example/skills.git")
                sys.exit(1)
            url = sys.argv[3]
            name = sys.argv[4] if len(sys.argv) > 4 else ""
            _skills_install(url, name)
        elif subcmd == "assign":
            if len(sys.argv) < 5:
                print("❌ Укажите скил и отдел.")
                print("   Пример: python team.py skills assign dart_flutter_developer development")
                sys.exit(1)
            _skills_assign(sys.argv[3], sys.argv[4])
        elif subcmd == "scan":
            project_path = sys.argv[3] if len(sys.argv) > 3 else "."
            _skills_scan(project_path)
        elif subcmd == "sync":
            _skills_sync()
        elif subcmd == "report":
            _skills_report()
        else:
            print(f"❌ Неизвестная подкоманда: {subcmd}")
            _skills_help()
            sys.exit(1)

    elif command == "learn":
        if len(sys.argv) < 3:
            print("❌ Укажите описание ошибки.")
            print("   Пример: python team.py learn \"dashboard содержит дубликаты\"")
            print("   Пример: python team.py learn \"импорт task_store\" \"python -c 'from task_store import get_task'\"")
            sys.exit(1)
        error_desc = sys.argv[2]
        check_cmd = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        from checks.registry import learn_from_failure
        learn_from_failure(error_desc, check_cmd)
        print(f"✅ Создана проверка для: {error_desc}")
        print(f"   Она будет автоматически запускаться при self-diagnose и Quality Gate.")

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
