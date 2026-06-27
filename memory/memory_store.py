"""
🧠 Memory Store — persistent knowledge base for AI DevCorp.

Stores task summaries, decisions, outcomes, and lessons learned.
Supports semantic search via TF-IDF + cosine similarity.
"""
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add mcp-server for task access
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-server"))
from task_store import get_all_tasks

STORAGE_DIR = Path(__file__).resolve().parent / "data"
MEMORY_FILE = STORAGE_DIR / "knowledge.json"
VOCAB_FILE = STORAGE_DIR / "vocabulary.json"
IDF_FILE = STORAGE_DIR / "idf.json"


# ========== TF-IDF Implementation (pure Python) ==========

def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text."""
    text = text.lower()
    # Remove punctuation, split on whitespace
    tokens = re.findall(r'\b[a-zа-яё0-9]+\b', text, re.UNICODE)
    # Stop words (basic Russian + English)
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'это', 'из', 'к',
        'the', 'a', 'an', 'in', 'on', 'for', 'to', 'of', 'is', 'are',
        'was', 'with', 'as', 'at', 'or', 'but', 'not', 'be', 'has',
    }
    return [t for t in tokens if t not in stop_words and len(t) > 1]


def _compute_tf(tokens: list[str]) -> dict:
    """Compute term frequency."""
    counter = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counter.items()}


def _compute_idf(documents: list[list[str]]) -> dict:
    """Compute inverse document frequency."""
    n = len(documents)
    df = Counter()
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1
    return {term: math.log(n / (1 + count)) + 1 for term, count in df.items()}


def _cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Compute cosine similarity between two TF-IDF vectors."""
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0
    dot = sum(vec1[t] * vec2[t] for t in common)
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ========== Knowledge Store ==========

def _ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    for f in [MEMORY_FILE, VOCAB_FILE, IDF_FILE]:
        if not f.exists():
            f.write_text("{}" if f.suffix == ".json" else "[]", encoding="utf-8")


def _load_json(path: Path) -> dict | list:
    _ensure_storage()
    try:
        data = path.read_text(encoding="utf-8")
        return json.loads(data) if data.strip() else ({} if "vocab" not in path.name else {})
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_json(path: Path, data: dict | list):
    _ensure_storage()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def learn_from_tasks(tasks: dict = None) -> dict:
    """
    Извлечь знания из выполненных задач и сохранить в память.

    Сохраняет:
    - Какие отделы работали вместе
    - Что получилось / не получилось
    - Какие технологии использовались
    - Рекомендации на будущее
    """
    if tasks is None:
        tasks = get_all_tasks()

    _ensure_storage()
    knowledge = _load_json(MEMORY_FILE)
    if not isinstance(knowledge, dict):
        knowledge = {}

    now = datetime.now(timezone.utc).isoformat()
    learned_count = 0

    for task_id, task in tasks.items():
        # Пропускаем уже изученные
        if task_id in knowledge:
            continue

        title = task.get("title", "")
        description = task.get("description", "")
        depts = task.get("departments_plan", [])
        completed = task.get("departments_completed", [])
        artifacts = task.get("artifacts", {})
        status = task.get("status", "")
        events = task.get("events", [])

        # Извлекаем решения (events типа handoff, escalation)
        decisions = [
            e.get("detail", "") for e in events
            if e.get("type") in ("handoff", "escalation", "department.completed")
        ]

        # Извлекаем технологии из контекста и артефактов
        tech_keywords = _tokenize(f"{title} {description} {' '.join(artifacts.values())}")

        memory_entry = {
            "task_id": task_id,
            "title": title,
            "description": description[:200],
            "departments": depts,
            "departments_completed": completed,
            "status": status,
            "artifacts": list(artifacts.keys()),
            "decisions": decisions[:5],
            "tech_tokens": tech_keywords[:20],
            "learned_at": now,
            "outcome": "success" if status == "completed" else (
                "failed" if status == "escalated" else "in_progress"
            ),
        }

        # Если задача завершена успешно — извлекаем уроки
        if status == "completed" and depts:
            memory_entry["lesson"] = (
                f"✅ {title}: задействовано {len(depts)} отделов "
                f"({', '.join(depts)}), "
                f"создано {len(artifacts)} артефактов"
            )

        # Если эскалирована — запоминаем ошибку
        if status == "escalated":
            error_events = [e.get("detail", "") for e in events if e.get("type") == "escalation"]
            memory_entry["error"] = error_events[0] if error_events else "Неизвестная ошибка"

        knowledge[task_id] = memory_entry
        learned_count += 1

    _save_json(MEMORY_FILE, knowledge)

    # Перестраиваем TF-IDF индекс
    _rebuild_index(knowledge)

    return {"learned": learned_count, "total": len(knowledge)}


def _rebuild_index(knowledge: dict):
    """Build TF-IDF index from stored knowledge."""
    documents = []
    doc_ids = []

    for task_id, entry in knowledge.items():
        text = f"{entry.get('title', '')} {entry.get('description', '')} {' '.join(entry.get('departments', []))}"
        tokens = _tokenize(text)
        if tokens:
            documents.append(tokens)
            doc_ids.append(task_id)

    if not documents:
        return

    tfidf_vectors = {}
    idf = _compute_idf(documents)

    for i, doc_id in enumerate(doc_ids):
        tf = _compute_tf(documents[i])
        tfidf_vectors[doc_id] = {
            term: tf.get(term, 0) * idf.get(term, 1)
            for term in set(documents[i])
        }

    _save_json(VOCAB_FILE, {"doc_ids": doc_ids})
    _save_json(IDF_FILE, idf)


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Семантический поиск по памяти команды.

    Args:
        query: поисковый запрос (например, "REST API авторизация")
        top_k: сколько результатов вернуть

    Returns:
        Список найденных задач с оценкой релевантности
    """
    knowledge = _load_json(MEMORY_FILE)
    if not isinstance(knowledge, dict) or not knowledge:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    # Загружаем IDF
    idf = _load_json(IDF_FILE)
    if not isinstance(idf, dict):
        idf = {}

    query_tf = _compute_tf(query_tokens)
    query_vec = {term: query_tf.get(term, 0) * idf.get(term, 1) for term in query_tokens}

    # Загружаем vocabulary
    vocab = _load_json(VOCAB_FILE)
    doc_ids = vocab.get("doc_ids", []) if isinstance(vocab, dict) else []

    results = []
    for doc_id in doc_ids:
        if doc_id not in knowledge:
            continue

        entry = knowledge[doc_id]
        doc_text = f"{entry.get('title', '')} {entry.get('description', '')} {' '.join(entry.get('departments', []))}"
        doc_tokens = _tokenize(doc_text)
        if not doc_tokens:
            continue

        doc_tf = _compute_tf(doc_tokens)
        doc_vec = {term: doc_tf.get(term, 0) * idf.get(term, 1) for term in doc_tokens}

        score = _cosine_similarity(query_vec, doc_vec)
        if score > 0.01:
            results.append({
                "task_id": doc_id,
                "title": entry.get("title", ""),
                "status": entry.get("status", ""),
                "departments": entry.get("departments", []),
                "outcome": entry.get("outcome", ""),
                "lesson": entry.get("lesson", ""),
                "error": entry.get("error", ""),
                "score": round(score, 3),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def get_stats() -> dict:
    """Статистика памяти команды."""
    knowledge = _load_json(MEMORY_FILE)
    if not isinstance(knowledge, dict):
        knowledge = {}

    entries = list(knowledge.values())
    return {
        "total_tasks_remembered": len(entries),
        "successful": sum(1 for e in entries if e.get("outcome") == "success"),
        "failed": sum(1 for e in entries if e.get("outcome") == "failed"),
        "in_progress": sum(1 for e in entries if e.get("outcome") == "in_progress"),
        "departments_used": list(set(
            d for e in entries for d in e.get("departments", [])
        )),
    }


def suggest_similar(title: str, description: str = "") -> list[dict]:
    """
    Автоматически найти похожие задачи в памяти.
    Используется CEO для планирования: если есть похожая задача —
    можно взять её план за основу.
    """
    query = f"{title} {description}"
    return search(query, top_k=3)


if __name__ == "__main__":
    result = learn_from_tasks()
    print(f"\n🧠 Memory: изучено {result['learned']} новых задач")
    print(f"   Всего в памяти: {result['total']}\n")
    stats = get_stats()
    print(f"📊 Статистика: {stats['successful']} успешных, {stats['failed']} проваленных")

    # Пример поиска
    print("\n🔍 Пример поиска 'REST API':")
    for r in search("REST API", top_k=3):
        print(f"   [{r['score']}] {r['title']}")
