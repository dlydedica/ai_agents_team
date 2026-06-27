"""
🧬 Built-in: соответствие агентов отделам.
"""
from pathlib import Path


def check() -> tuple[bool, str]:
    """Проверить, что каждый отдел имеет агента."""
    repo = Path(__file__).resolve().parent.parent.parent
    depts = [d for d in (repo / "departments").iterdir() if d.is_dir()]
    agent_dir = repo / ".github" / "agents" / "departments"
    agents = list(agent_dir.glob("*.agent.md")) if agent_dir.exists() else []

    if len(depts) != len(agents):
        return False, f"{len(agents)} агентов, {len(depts)} отделов (должно быть равно)"
    return True, f"{len(agents)} агентов = {len(depts)} отделов"
