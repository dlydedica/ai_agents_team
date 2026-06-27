"""
🧬 Built-in: критические файлы.
"""
from pathlib import Path


def check() -> tuple[bool, str]:
    """Проверить наличие критических файлов."""
    repo = Path(__file__).resolve().parent.parent.parent
    critical = [
        "team.py",
        "mcp-server/server.py",
        "mcp-server/task_store.py",
        "orchestration/ceo.md",
        "README.md",
        "setup.py",
    ]
    missing = [f for f in critical if not (repo / f).exists()]
    if missing:
        return False, f"Отсутствуют: {', '.join(missing)}"
    return True, f"Все {len(critical)} файлов на месте"
