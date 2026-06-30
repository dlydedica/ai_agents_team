"""
🧬 Built-in: проверка разрешений (tools) агентов по грейдам согласно ADR-003.

Ожидаемые разрешения по грейдам:
    J (Junior)  → [read, search, edit]
    M (Middle)  → [read, search, edit, execute]
    S (Senior)  → [read, search, edit, execute]
    L (Lead)    → [read, search, edit, execute, web]

Исключения:
    - Read-only роли (compliance): только [read, search]
    - Research роли (rd, talent_scout): имеют web на любом грейде
    - Manual роли (manual_tester, compliance): без execute
    - Market research роли (product, marketing): web на любом грейде

Сканирует .github/agents/members/ и .github/agents/departments/.
"""
from pathlib import Path

# ── Эталонные permissions по грейдам ──────────────────────────────────────
GRADE_MAP: dict[str, str] = {
    "J": "J", "L": "L",
    "S": "S", "M": "M",
    "JUNIOR": "J", "MIDDLE": "M", "SENIOR": "S", "LEAD": "L",
    "JUN": "J", "MID": "M", "SEN": "S",
}

GRADE_PERMISSIONS: dict[str, set[str]] = {
    "J": {"read", "search", "edit"},
    "M": {"read", "search", "edit", "execute"},
    "S": {"read", "search", "edit", "execute"},
    "L": {"read", "search", "edit", "execute", "web"},
}

CORE_TOOLS: set[str] = {"read", "search", "edit"}

# ── Роли-исключения ──────────────────────────────────────────────────────
RESEARCH_ROLES = {"rd", "rnd", "research", "talent_scout", "innovation", "research_engineer"}
MANUAL_ROLES = {"manual", "manual_tester"}
MARKET_ROLES = {"product", "marketing", "content", "growth", "brand"}
READ_ONLY_ROLES = {"compliance", "compliance_officer"}


def _parse_frontmatter(content: str) -> dict:
    """Извлечь YAML frontmatter из .agent.md файла."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}

    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end == -1:
        return {}

    result: dict = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = [
                v.strip().strip('"').strip("'")
                for v in value[1:-1].split(",")
            ]
            result[key] = [v for v in items if v]
        else:
            result[key] = value.strip('"').strip("'")

    return result


def _get_role_key(filepath: Path) -> str:
    """Извлечь role_key из имени файла: alex.product_manager.agent.md → product_manager"""
    stem = filepath.stem
    name_part = stem.replace(".agent", "")
    parts = name_part.split(".")
    return parts[-1].lower() if parts else ""


def _expected_tools(grade: str, role_key: str) -> list[str]:
    """Определить ожидаемый набор tools по грейду и роли."""
    grade_key = GRADE_MAP.get(grade.upper(), "M")
    grade_tools = GRADE_PERMISSIONS.get(grade_key, GRADE_PERMISSIONS["M"])
    tools = set(grade_tools)

    # Read-only override (самый высокий приоритет)
    if any(r in role_key for r in READ_ONLY_ROLES):
        return ["read", "search"]

    # Manual roles: убрать execute
    if any(r in role_key for r in MANUAL_ROLES):
        tools.discard("execute")

    # Research roles: добавить web
    if any(r in role_key for r in RESEARCH_ROLES):
        tools.add("web")

    # Market research roles: добавить web (на всех грейдах)
    if any(r in role_key for r in MARKET_ROLES):
        tools.add("web")

    return sorted(tools)


def check() -> tuple[bool, str]:
    """
    Проверка permissions для всех agent-файлов.

    Returns:
        (True, сообщение) если всё ок
        (False, сообщение об ошибке) если проблемы найдены
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    members_dir = repo_root / ".github" / "agents" / "members"
    departments_dir = repo_root / ".github" / "agents" / "departments"

    errors = []
    checked = 0

    # Сканируем member-файлы
    if members_dir.exists():
        for f in sorted(members_dir.glob("*.agent.md")):
            checked += 1
            result = _validate_agent_file(f)
            if result:
                errors.append(result)

    # Сканируем department head-файлы
    if departments_dir.exists():
        for f in sorted(departments_dir.glob("*.agent.md")):
            checked += 1
            result = _validate_dept_head_file(f)
            if result:
                errors.append(result)

    if errors:
        msg = f"Проверено {checked} файлов. Найдено {len(errors)} ошибок:\n"
        for e in errors[:10]:
            msg += f"  • {e}\n"
        if len(errors) > 10:
            msg += f"  • ... и ещё {len(errors) - 10} ошибок\n"
        return False, msg.strip()

    return True, f"Проверено {checked} файлов. Все permissions корректны."


def _validate_agent_file(filepath: Path) -> str | None:
    """Проверить permissions одного member agent-файла."""
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    fm = _parse_frontmatter(content)

    grade = fm.get("grade", "")
    tools = fm.get("tools", [])
    role_key = _get_role_key(filepath)

    if not grade:
        return f"{filepath.name}: отсутствует grade в frontmatter"

    expected = _expected_tools(grade, role_key)

    if set(tools) != set(expected):
        return (f"{filepath.name}: tools mismatch. "
                f"Имеется: {tools}, ожидается: {expected} (grade={grade}, role={role_key})")

    # Проверяем обязательные поля
    for field in ["alias", "grade", "department"]:
        if field not in fm:
            return f"{filepath.name}: отсутствует поле '{field}' в frontmatter"

    return None


def _validate_dept_head_file(filepath: Path) -> str | None:
    """Проверить, что department head файл имеет корректные tools."""
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    fm = _parse_frontmatter(content)

    # Department heads должны иметь как минимум [read, search, edit]
    tools = set(fm.get("tools", []))
    if not CORE_TOOLS.issubset(tools):
        return f"{filepath.name}: Head должен иметь как минимум {sorted(CORE_TOOLS)}, имеется {sorted(tools)}"

    return None
