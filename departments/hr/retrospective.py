"""
🔄 Retrospective Engine — ретроспектива после каждой задачи.

Анализирует: что прошло хорошо, что плохо,
какие checks нужно создать, что улучшить в процессах.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add mcp-server to path
_REPO_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_DIR / "mcp-server"))
sys.path.insert(0, str(_REPO_DIR))  # для импорта memory и checks
from task_store import get_task, get_task_timeline

HR_DIR = _REPO_DIR / "docs" / "hr"
DEPARTMENT_EMOJI = {
    "product": "🏭", "architecture": "🏗️", "development": "💻",
    "qa": "🧪", "devops": "⚙️", "design": "🎨", "docs": "📖",
    "hr": "👥", "security": "🛡️", "data": "📊", "rd": "🔬",
    "legal": "⚖️", "marketing": "📣",
}


def run_retrospective(task_id: str) -> dict:
    """
    Запустить ретроспективу по завершённой задаче.
    Возвращает: что улучшить, какие checks создать, какие изменения в процессах.
    """
    task = get_task(task_id)
    if not task:
        return {"error": f"Задача {task_id} не найдена"}

    timeline = get_task_timeline(task_id) or []
    title = task.get("title", "?")
    status = task.get("status", "?")
    depts = task.get("departments_plan", [])
    completed = task.get("departments_completed", [])
    events = task.get("events", [])

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Анализ
    findings = []
    improvements = []
    new_checks_needed = []
    process_changes = []

    # 1. Были ли эскалации?
    escalations = [e for e in events if e.get("type") == "escalation"]
    if escalations:
        findings.append(f"🔴 {len(escalations)} эскалаций")
        improvements.append("Добавить Quality Gate раньше в цепочке")
        new_checks_needed.append("prevent_escalations")

    # 2. Все ли отделы справились?
    for dept in depts:
        if dept not in completed:
            findings.append(f"🟡 {dept.capitalize()} не завершил работу")
            improvements.append(f"Проверить загрузку отдела {dept}")

    # 3. Сколько handoff'ов было?
    handoffs = [e for e in events if e.get("type") == "handoff"]
    if len(handoffs) > len(depts):
        findings.append(f"🔄 {len(handoffs)} handoff'ов (циклы возврата)")
        improvements.append("Оптимизировать цепочку: меньше возвратов")
        new_checks_needed.append("handoff_loops")

    # 4. Качество Gate
    quality_events = [e for e in events if "quality_gate" in e.get("type", "")]
    if quality_events:
        findings.append(f"🛡️ Quality Gate был пройден не с первого раза")
        improvements.append("Запускать Quality Gate раньше")

    # 5. Длительность (по events)
    if len(events) >= 2:
        try:
            t1 = events[0].get("time", "")
            t2 = events[-1].get("time", "")
            findings.append(f"⏱️ Шагов в задаче: {len(events)} событий")
        except Exception:
            pass

    # Генерация отчёта
    report = f"""# 🔄 Ретроспектива задачи

**Задача:** {title}
**ID:** {task_id}
**Статус:** {status}
**Дата:** {now}

---

## 📊 Что произошло

- **Отделов задействовано:** {len(depts)}
- **Отделов завершило:** {len(completed)}
- **Событий зафиксировано:** {len(events)}

## 🔍 Выводы

"""
    for f in findings:
        report += f"- {f}\n"

    report += f"\n## 💡 Что улучшить\n"
    for imp in improvements:
        report += f"- {imp}\n"

    if new_checks_needed:
        report += f"\n## 🧬 Какие checks создать\n"
        for c in new_checks_needed:
            report += f"- `{c}` — `python team.py learn \"{c}\"`\n"

    if process_changes:
        report += f"\n## 📋 Изменения в процессах\n"
        for p in process_changes:
            report += f"- {p}\n"

    report += f"\n## 📅 События\n"
    for e in events[-10:]:
        report += f"- {e.get('time', '?')[:19]} | {e.get('type', '?')} | {e.get('detail', '')[:80]}\n"

    # Сохраняем
    HR_DIR.mkdir(parents=True, exist_ok=True)
    report_path = HR_DIR / f"retro-{task_id}.md"
    report_path.write_text(report, encoding="utf-8")

    # 🧬 Автоматически создаём checks для найденных проблем
    checks_created = 0
    if new_checks_needed:
        try:
            from checks.registry import learn_from_failure
            for check_name in new_checks_needed:
                learn_from_failure(
                    f"retro-{check_name}",
                    f"python -c \"from checks.registry import run_all_checks; run_all_checks()\""
                )
                checks_created += 1
        except Exception:
            pass

    # 🧠 Сохраняем ретроспективу в долговременную память
    memory_result = None
    try:
        from memory.memory_store import learn_from_tasks
        memory_result = learn_from_tasks()
    except Exception:
        pass

    return {
        "task_id": task_id,
        "findings": len(findings),
        "improvements": improvements,
        "new_checks": new_checks_needed,
        "checks_created": checks_created,
        "memory_saved": memory_result.get("learned", 0) if memory_result else 0,
        "report": str(report_path.relative_to(_REPO_DIR)),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = run_retrospective(sys.argv[1])
        print(f"\n🔄 Ретроспектива: {result['task_id']}")
        print(f"   Выводов: {result['findings']}")
        print(f"   Улучшений: {len(result['improvements'])}")
        print(f"   Checks: {len(result['new_checks'])}")
        print(f"   🧬 Checks создано: {result.get('checks_created', 0)}")
        print(f"   🧠 Записей в память: {result.get('memory_saved', 0)}")
        print(f"   Отчёт: {result['report']}")
    else:
        print("❌ Укажите task_id")
        print("   Пример: python departments/hr/retrospective.py task-a1b2c3")
