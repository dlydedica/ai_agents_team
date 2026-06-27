"""
🧬 Adaptive Check Registry — саморасширяющаяся система проверок.

Любой файл .py в checks/builtin/ или checks/learned/ с функцией check()
автоматически регистрируется и запускается в self-diagnose и Quality Gate.

Если что-то упало — можно создать новый check одной командой:
    python team.py learn "Описание ошибки" "команда для проверки"
"""
import importlib.util
import sys
from pathlib import Path
from typing import Callable

CHECKS_DIR = Path(__file__).resolve().parent
BUILTIN_DIR = CHECKS_DIR / "builtin"
LEARNED_DIR = CHECKS_DIR / "learned"


def discover_checks() -> list[dict]:
    """Найти все файлы с функцией check() в директориях проверок."""
    checks = []

    for directory in [BUILTIN_DIR, LEARNED_DIR]:
        if not directory.exists():
            continue
        for py_file in sorted(directory.glob("*.py")):
            mod_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(mod_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "check") and callable(module.check):
                        checks.append({
                            "name": mod_name,
                            "file": py_file.relative_to(CHECKS_DIR.parent),
                            "func": module.check,
                            "source": "builtin" if directory == BUILTIN_DIR else "learned",
                        })
            except Exception as e:
                checks.append({
                    "name": mod_name,
                    "file": py_file.relative_to(CHECKS_DIR.parent),
                    "func": None,
                    "source": "error",
                    "error": str(e),
                })

    return checks


def run_all_checks(verbose: bool = True) -> tuple[list, list]:
    """Запустить все найденные проверки. Возвращает (passed, failed)."""
    checks = discover_checks()
    passed = []
    failed = []

    if verbose:
        print(f"\n  🧬 Запуск {len(checks)} проверок:\n")

    for check in checks:
        name = check["name"]
        source = check["source"]

        if source == "error":
            failed.append({"name": name, "message": f"Ошибка загрузки: {check.get('error')}"})
            if verbose:
                print(f"  ❌ {name}: ошибка загрузки: {check.get('error')}")
            continue

        if check["func"] is None:
            failed.append({"name": name, "message": "Функция check() не найдена"})
            continue

        try:
            ok, msg = check["func"]()
            if ok:
                passed.append({"name": name, "message": msg})
                if verbose:
                    print(f"  ✅ {name}: {msg}")
            else:
                failed.append({"name": name, "message": msg})
                if verbose:
                    print(f"  ❌ {name}: {msg}")
        except Exception as e:
            failed.append({"name": name, "message": f"Исключение: {e}"})
            if verbose:
                print(f"  ❌ {name}: исключение: {e}")

    return passed, failed


def learn_from_failure(error_desc: str, check_command: str = "") -> bool:
    """
    Создать новый check на основе возникшей ошибки.
    Автоматически регистрируется в системе и будет запускаться при каждой диагностике.

    Пример:
        team.py learn "dashboard/app.py дублированный код" "python -c \"import ast; ast.parse(open('dashboard/app.py').read())\""
    """
    import datetime

    LEARNED_DIR.mkdir(parents=True, exist_ok=True)

    # Генерируем имя файла из описания ошибки
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in error_desc.lower())
    safe_name = safe_name[:50].strip("_") or f"check_{datetime.datetime.now().strftime('%H%M%S')}"

    # Генерируем код проверки
    if check_command:
        check_code = f'''"""
🧬 Автоматически созданная проверка.
Источник: {error_desc}
Команда: {check_command}
"""
import subprocess
import sys


def check() -> tuple[bool, str]:
    """
    Проверка: {error_desc}
    """
    try:
        result = subprocess.run(
            r"""{check_command}""",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, "Проверка пройдена"
        else:
            return False, f"Ошибка: {{result.stderr.strip() or result.stdout.strip()}}"
    except Exception as e:
        return False, f"Исключение: {{e}}"
'''
    else:
        # Проверка на основе grep — ищем паттерн ошибки в файлах
        check_code = f'''"""
🧬 Автоматически созданная проверка.
Источник: {error_desc}
"""
import os
from pathlib import Path


def check() -> tuple[bool, str]:
    """
    Проверка: {error_desc}
    """
    repo = Path(__file__).resolve().parent.parent.parent
    files_checked = 0
    issues = []

    for py_file in repo.rglob("*.py"):
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        files_checked += 1
        content = py_file.read_text(encoding="utf-8", errors="ignore")

        # Проверяем на наличие дублированных блоков (как в прошлом инциденте)
        lines = content.split("\\n")
        for i in range(len(lines) - 2):
            block = "\\n".join(lines[i:i+2])
            rest = "\\n".join(lines[i+2:])
            if block in rest:
                issues.append(f"Дубликат в {{py_file.relative_to(repo)}}: строка {{i+1}}")

    if issues:
        return False, f"Найдено {{len(issues)}} проблем: {{issues[0]}}"
    return True, f"{{files_checked}} файлов проверено"
'''

    filepath = LEARNED_DIR / f"{safe_name}.py"
    filepath.write_text(check_code, encoding="utf-8")

    return True


if __name__ == "__main__":
    # Диагностика
    passed, failed = run_all_checks(verbose=True)
    print(f"\n  ✅ Пройдено: {len(passed)}, ❌ Ошибок: {len(failed)}")
