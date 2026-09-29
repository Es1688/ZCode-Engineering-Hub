# ADR-0001: Принятие ZCode Engineering Hub (Фаза I)

- Статус: accepted
- Дата: 2026-09-28

## Контекст
Аудит ЭТАПА 0 (`it/zcode/audit/2026-09-28-audit-report.md`) показал: extension-поверхность
ZCode пуста (нет AGENTS.md/skills/MCP/hooks); git есть только у 2 из 7 проектов, remote —
ни у одного; режимы исполнения `plan/build/yolo` используются без политики (42% сессий — yolo);
проекты разнесены по двум корням (`~/work`, `~/PROJECTS`).

## Решение
Принять техпроект `ZCODE-HUB-DESIGN.md` и внедрить Фазу I:

- Level 0: глобальные правила `~/.zcode/AGENTS.md`.
- Level 1: `AGENTS.md` + `.zcode/project.yaml` в каждом проекте `~/work`.
- Git-стандарт: github-flow, Conventional Commits (английский), `main` по умолчанию.
- Шаблоны и ADR кластера — в `it/zcode/templates/` и `it/zcode/docs/adr/`.

Зафиксированные решения пользователя (28.09.2026):

1. Remote — GitHub, приватные репозитории; push выполняется после систематизации git.
2. Commit-сообщения — английский, Conventional Commits.
3. `~/PROJECTS` остаётся как есть, вне Hub; правило «вне workspace — только чтение».
4. Обновление ZCode 3.11.2 → 3.14.3 — после Фазы I.

## Последствия
- Новые проекты создаются только в `~/work` по шаблонам Hub.
- Проектные skills/commands не именуются как глобальные (user-скоуп перекрывает workspace).
- `<repo>/.zcode/config.json` не создаётся без отдельного ADR (workspace-MCP
  подключается автоматически).
- Пустые каталоги-заготовки (например, `it/kwork/ggsell`) не инициализируются, пока
  не появится содержимое.
