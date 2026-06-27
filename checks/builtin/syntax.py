"""
🧬 Built-in: синтаксис Python.
"""
import ast
from pathlib import Path


def check() -> tuple[bool, str]:
    """Проверить синтаксис всех .py файлов."""
    repo = Path(__file__).resolve().parent.parent.parent
    errors = []
    checked = 0

    for py_file in sorted(repo.rglob("*.py")):
        if "venv" in str(py_file) or "__pycache__" in str(py_file) or "data" in str(py_file):
            continue
        checked += 1
        try:
            ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError as e:
            errors.append(f"{py_file.relative_to(repo)}: {e}")

    if errors:
        return False, f"{len(errors)} синтаксических ошибок:\n" + "\n".join(errors[:3])
    return True, f"{checked} файлов валидны"
