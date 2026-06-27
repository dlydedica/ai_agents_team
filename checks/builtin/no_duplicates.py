"""
🧬 Built-in: дублированные блоки кода.
"""
from pathlib import Path


def check() -> tuple[bool, str]:
    """Проверить файлы на дублированные блоки (как в инциденте с dashboard)."""
    repo = Path(__file__).resolve().parent.parent.parent
    issues = []
    checked = 0

    # Шаблоны, которые могут повторяться легально
    SKIP_PATTERNS = {
        '"""', "'''", "if __name__", "import ", "from ", "def test_",
        "def check(", "        ", "    return", "    pass", "    try:",
        "    except", "        if ", "            ", "raise ",
    }

    for py_file in sorted(repo.rglob("*.py")):
        if "venv" in str(py_file) or "__pycache__" in str(py_file) or "learned" in str(py_file):
            continue
        checked += 1
        content = py_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Ищем дубликаты блоков из 5+ строк (не 2, чтобы избежать ложных срабатываний)
        for i in range(len(lines) - 5):
            # Пропускаем блоки, начинающиеся с частых паттернов
            first_line = lines[i].strip()
            if any(first_line.startswith(p) for p in SKIP_PATTERNS):
                continue
            # Пропускаем пустые строки и комментарии
            if not first_line or first_line.startswith("#"):
                continue

            block = "\n".join(lines[i:i+5])
            rest = "\n".join(lines[i+5:])
            if block in rest:
                issues.append(f"{py_file.relative_to(repo)} стр.{i+1}")
                break  # одна проблема на файл

    if issues:
        return False, f"Найдено дубликатов: {len(issues)} — {'; '.join(issues[:5])}"
    return True, f"{checked} файлов без дубликатов"
