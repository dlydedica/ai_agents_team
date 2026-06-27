# 📡 Протоколы Handoff между отделами

## 1. Product → Architecture

```
Product завершил → передаёт Architecture
```

**Что передаётся:**
- `spec/product_requirements.md` — требования
- `spec/user_stories.md` — user stories
- `spec/acceptance_criteria.md` — критерии приёмки

**Контекст:** бизнес-цели, приоритеты, ограничения
**Feedback:** Architecture может вернуть на уточнение требований

---

## 2. Architecture → Development

```
Architecture завершил → передаёт Development
```

**Что передаётся:**
- `docs/architecture.md` — архитектура
- `docs/api-spec.yaml` — OpenAPI / GraphQL схема
- `docs/adr/` — Architecture Decision Records
- `docs/data-model.md` — модель данных (если нужно)
- `docs/tech-stack.md` — стек технологий и rationale

**Контекст:** стиль кода, гайдлайны
**Feedback:** Developer может запросить уточнение по API

---

## 3. Development → QA

```
Development завершил → передаёт QA
```

**Что передаётся:**
- `src/` — исходный код (ветка / PR)
- `tests/unit/` — unit-тесты (checklist: ✅ проходят)
- `CHANGELOG.md` — что изменилось
- `docs/implementation-notes.md` — заметки по реализации

**Контекст:** какие сценарии требуют особого внимания
**Feedback:** QA возвращает баги с указанием severity (P0/P1/P2)

---

## 4. QA → DevOps

```
QA принял → передаёт DevOps на деплой
```

**Что передаётся:**
- `tests/reports/test-report.md` — отчёт о тестировании
- `tests/reports/coverage.md` — покрытие (требование: >80%)
- `tests/reports/regression.md` — результаты регрессии
- `docs/deployment-checklist.md` — что нужно для деплоя

**Контекст:** окружение (staging / prod), переменные
**Feedback:** DevOps может запросить фиксы если тесты не пройдены

---

## 5. DevOps → Docs + CEO

```
DevOps завершил → передаёт Docs и CEO
```

**Что передаётся:**
- `docs/infrastructure.md` — схема инфраструктуры
- `docs/deployment-guide.md` — инструкция по деплою
- `docs/monitoring.md` — метрики, алерты
- Статус деплоя (IP, URL, healthcheck)

**Контекст:** доступы, окружение

---

## 6. QA → Security

```
QA → параллельно Security (если требуется)
```

**Что передаётся:** тот же код, что и в QA
**Контекст:** уровень чувствительности данных

---

## 7. Любой отдел → CEO (по завершению)

```
Каждый Head → CEO
```

**Что передаётся:**
- Статус (done / blocked / needs_review)
- Артефакты
- Потраченное время
- Риски / проблемы
- Рекомендации
