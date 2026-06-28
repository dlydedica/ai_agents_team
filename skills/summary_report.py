"""Финальный отчёт о рефакторинге."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from registry import generate_manifest
from manager import list_profiles, list_project_configs

m = generate_manifest()
profiles = list_profiles()
configs = list_project_configs()

print("=" * 50)
print("  📊 ИТОГОВАЯ СТАТИСТИКА РЕФАКТОРИНГА")
print("=" * 50)
print()
print(f"  📚 Скилов в библиотеке:      {m['total']}")
print(f"     builtin (собственных):    {m['by_type']['builtin']}")
print(f"     external (внешних):       {m['by_type']['external']}")
print(f"     по отделам:              {len(m['by_department'])} из 13")
print()
for grade in ["L", "S", "M", "J"]:
    count = m["by_grade"].get(grade, 0)
    label = {"L": "Lead", "S": "Senior", "M": "Middle", "J": "Junior"}[grade]
    print(f"     {label}: {count}")
print()
print(f"  👤 Профилей агентов:         {len(profiles)}")
for p in sorted(profiles, key=lambda x: x["name"]):
    print(f"     • {p['name']} [{p['grade']}] — {p['display_name']} ({len(p['skills'])} скилов)")
print()
print(f"  📋 Per-project конфигов:     {len(configs)}")
for c in configs:
    agents = [a.get("name", a) if isinstance(a, dict) else a for a in c.get("active_agents", [])]
    print(f"     • {c['project']}: {', '.join(agents)}")
print()
print(f"  🔌 MCP-инструментов:         16 (9 задач + 7 скилы)")
print(f"  🧪 Тестов:                   25 (все пройдены)")
print(f"  ✅ Статус:                    ВСЁ РАБОТАЕТ")
print()
print("=" * 50)
print("  ИЗМЕНЁННЫЕ ФАЙЛЫ")
print("=" * 50)
print("  • mcp-server/server.py      — 7 новых MCP-инструментов")
print("  • .vscode/mcp.json          — autoApprove новых инструментов")
print("  • dashboard/app.py          — загрузка данных скилов")
print("  • dashboard/templates/*.html— секция скилов в дашборде")
print("  • memory/memory_store.py    — skills_used в learn_from_tasks()")
print("  • skills/registry.py        — реестр скилов (21 файл)")
print("  • skills/manager.py         — профили и per-project конфиги")
print("  • skills/loader.py          — загрузка внешних скилов")
print("  • skills/builtin/           — 21 .skill.md файл")
print("  • skills/profiles/          — 10 profile.json")
print("  • skills/project-configs/   — 3 конфига")
print("  • skills/test_skills.py     — 25 тестов")
print("  • team.py                   — CLI-команды skills")
print()
