"""
Загрузчик внешних скилов AI DevCorp.

Поддерживает:
  - Git submodule (клон репозитория сообщества)
  - Pip install (установка пакета со скилами)
  - Симлинк (ручное подключение директории со скилами)
  - Реестр external/registry.json — учёт подключенных внешних скилов
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

SKILLS_DIR = Path(__file__).parent
EXTERNAL_DIR = SKILLS_DIR / "external"
REGISTRY_FILE = EXTERNAL_DIR / "registry.json"


def _ensure_external_dir():
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> dict:
    """Загрузить реестр внешних скилов."""
    _ensure_external_dir()
    if not REGISTRY_FILE.exists():
        registry = {"sources": [], "skills": []}
        REGISTRY_FILE.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return registry

    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"sources": [], "skills": []}


def _save_registry(registry: dict):
    REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def install_from_git(url: str, name: str = "", branch: str = "main") -> dict:
    """Установить внешние скилы из git-репозитория.

    Args:
        url: URL git-репозитория
        name: Локальное имя (по умолчанию — имя из URL)
        branch: Ветка (по умолчанию main)
    """
    _ensure_external_dir()
    if not name:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")

    target_dir = EXTERNAL_DIR / name
    if target_dir.exists():
        return {"error": f"Источник '{name}' уже установлен в {target_dir}"}

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "-b", branch, url, str(target_dir)],
            capture_output=True, text=True, check=True, timeout=120,
        )
    except subprocess.CalledProcessError as e:
        return {"error": f"Git clone failed: {e.stderr[:500]}"}
    except FileNotFoundError:
        return {"error": "Git не найден. Установите git или используйте другой метод."}
    except subprocess.TimeoutExpired:
        return {"error": "Таймаут при git clone"}

    # Сканируем установленные скилы
    installed = _scan_external_skills(target_dir)
    registry = _load_registry()
    registry["sources"].append({
        "name": name,
        "type": "git",
        "url": url,
        "branch": branch,
        "path": str(target_dir.relative_to(SKILLS_DIR)),
    })
    for s in installed:
        if s not in registry["skills"]:
            registry["skills"].append(s)
    _save_registry(registry)

    return {"success": True, "source": name, "skills_installed": installed}


def install_from_pip(package_name: str) -> dict:
    """Установить внешние скилы из pip-пакета.

    Пакет должен содержать навыки в директории .skills/ внутри пакета.
    """
    _ensure_external_dir()

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True, text=True, check=True, timeout=120,
        )
    except subprocess.CalledProcessError as e:
        return {"error": f"pip install failed: {e.stderr[:500]}"}
    except subprocess.TimeoutExpired:
        return {"error": "Таймаут при pip install"}

    # Ищем .skills/ в установленном пакете
    try:
        import importlib
        module = importlib.import_module(package_name.replace("-", "_"))
        pkg_dir = Path(module.__file__).parent
        skills_src = pkg_dir / ".skills"
        if skills_src.exists() and skills_src.is_dir():
            target_dir = EXTERNAL_DIR / package_name
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(skills_src, target_dir)
            installed = _scan_external_skills(target_dir)
        else:
            installed = []
    except Exception:
        installed = []

    registry = _load_registry()
    registry["sources"].append({
        "name": package_name,
        "type": "pip",
        "path": str(EXTERNAL_DIR / package_name),
    })
    for s in installed:
        if s not in registry["skills"]:
            registry["skills"].append(s)
    _save_registry(registry)

    return {"success": True, "source": package_name, "skills_installed": installed}


def install_from_symlink(source_path: str, name: str = "") -> dict:
    """Подключить внешние скилы через симлинк.

    Args:
        source_path: Путь к директории со скилами
        name: Локальное имя (по умолчанию — имя директории)
    """
    _ensure_external_dir()
    src = Path(source_path).resolve()

    if not src.exists() or not src.is_dir():
        return {"error": f"Путь не существует или не является директорией: {source_path}"}

    if not name:
        name = src.name

    target = EXTERNAL_DIR / name
    if target.exists():
        return {"error": f"Симлинк '{name}' уже существует"}

    try:
        target.symlink_to(src, target_is_directory=True)
    except OSError as e:
        return {"error": f"Не удалось создать симлинк: {e}"}

    installed = _scan_external_skills(target)
    registry = _load_registry()
    registry["sources"].append({
        "name": name,
        "type": "symlink",
        "source_path": str(src),
        "path": str(target.relative_to(SKILLS_DIR)),
    })
    for s in installed:
        if s not in registry["skills"]:
            registry["skills"].append(s)
    _save_registry(registry)

    return {"success": True, "source": name, "skills_installed": installed}


def _scan_external_skills(directory: Path) -> list[str]:
    """Сканирует директорию на наличие .skill.md / SKILL.md файлов."""
    skills = []
    seen = set()
    for pattern in ("*.skill.md", "SKILL.md"):
        for f in sorted(directory.rglob(pattern)):
            parent = f.parent
            if parent not in seen:
                seen.add(parent)
                # Берём имя родительской папки как имя скила
                skills.append(parent.name)
    return skills


def list_external_sources() -> list[dict]:
    """Список подключенных внешних источников скилов."""
    registry = _load_registry()
    return registry.get("sources", [])


def uninstall_source(name: str) -> dict:
    """Удалить внешний источник скилов."""
    registry = _load_registry()
    source = None
    for i, s in enumerate(registry.get("sources", [])):
        if s.get("name") == name:
            source = s
            registry["sources"].pop(i)
            break

    if not source:
        return {"error": f"Источник '{name}' не найден"}

    # Удаляем файлы
    source_path = EXTERNAL_DIR / name
    if source_path.exists():
        if source_path.is_symlink() or source_path.is_dir():
            shutil.rmtree(source_path, ignore_errors=True)
        else:
            source_path.unlink(missing_ok=True)

    _save_registry(registry)
    return {"success": True, "removed": name}


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "install":
        url = sys.argv[2] if len(sys.argv) > 2 else ""
        name = sys.argv[3] if len(sys.argv) > 3 else ""
        if url.startswith("http") or url.endswith(".git"):
            result = install_from_git(url, name)
        elif url.startswith("/") or url.startswith("."):
            result = install_from_symlink(url, name)
        else:
            result = install_from_pip(url)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "list":
        sources = list_external_sources()
        print(f"🌐 Внешние источники скилов ({len(sources)}):\n")
        for s in sources:
            print(f"  • {s.get('name', '?')} [{s.get('type', '?')}]")
            print(f"    путь: {s.get('path', '')}")
            print()

    elif cmd == "uninstall":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        result = uninstall_source(name)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print("Команды:")
        print("  install <git_url|pip_pkg|path> [name]  — установить внешние скилы")
        print("  list                                   — список внешних источников")
        print("  uninstall <name>                       — удалить источник")
