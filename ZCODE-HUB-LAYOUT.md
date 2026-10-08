# ZCode Engineering Hub — окончательный макет (as-built)

**Статус:** действует • **Дата:** 01.10.2026 • **Обслуживает:** кластер `~/work`

Единственный источник истины по устройству Engineering Hub. Консолидирует концепцию
(`ZCode Engineering Hub.md`), техпроект с журналами выполнения (`ZCODE-HUB-DESIGN.md`,
§12–§14), решения ADR-0001, ADR-0002, ADR-001 и фактическое состояние кластера на
01.10.2026. Концепция и техпроект переводятся в статус исторических документов; журналы
выполнения продолжают вестись в техпроекте.

## 1. Цель и принципы

**Цель** (концепция, итоговая формулировка): стандартизированная инженерная среда на базе
ZCode, в которой каждый проект имеет единый описываемый жизненный цикл, git-процесс, правила
AI-агента, набор специализированных skills, контролируемые MCP-интеграции, CI/CD и базу
знаний, а ZCode способен одновременно анализировать состояние и управлять множеством
независимых git-репозиториев.

Принципы:

1. Сначала архитектура процессов, потом инструменты (концепция, п.16).
2. Каждый проект — самостоятельный git-репозиторий; Hub — верхний слой, не монорепозиторий.
3. Git — источник истины; Memory MCP — вспомогательный слой, не раньше Фазы IV.
4. Минимальные права по умолчанию: MCP и подтверждения — по потребности, а не «чем больше,
   тем лучше».
5. Документация в git: версионируется, проверяется, переносима между машинами, не зависит
   от конкретного AI.

## 2. Итоговая архитектура (as-built, 01.10.2026)

```
УРОВЕНЬ 0 — глобальная среда агента            ~/.zcode/   (вне git; управляется установщиками/вручную)
├── AGENTS.md ............... правила Level 0 (28.09): язык, безопасность, git-гейты, стиль
├── skills/ ................. 5 глобальных skills (28–29.09) — §7
├── hooks/guard/ ............ hub-guard (01.10, ADR-0002): guard.py + guard.json (shadow) + guard.jsonl
└── cli/config.json ......... hooks.enabled + регистрация guard (создан install_guard.py, с бэкапом)

ШТАБ-КВАРТИРА HUB — git-репозиторий            ~/work/it/zcode → git@github.com:Es1688/ZCode-Engineering-Hub.git
├── ZCode Engineering Hub.md . концепция (историческая, со статус-шапкой)
├── ZCODE-HUB-DESIGN.md ...... техпроект + журналы Фаз I–III (§12–§14)
├── ZCODE-HUB-LAYOUT.md ...... этот макет (as-built)
├── Совместимость ZCode ….md . ADR-001: плагин adversarial-review (вариант B) + журнал версий
├── docs/adr/
│   ├── 0001-engineering-hub-adoption.md ... принятие Hub (28.09)
│   └── 0002-hooks-enforcement.md .......... hub-guard: правила, фазирование, ограничения (01.10)
├── templates/ ............... эталон: project.yaml, AGENTS-L1, task-context, ADR, gitignore/{python,node}
├── plugins/ ................. маркетплейс dev-it-zcode + плагин adversarial-review (§7)
├── hooks/ ................... исходники hub-guard: guard.py, install_guard.py, test_guard.py (132 теста), README
├── audit/ ................... аудит этапа 0 (28.09, снимок, не изменяется)
├── runner.md, SKILL.md ...... рабочие материалы порта adversarial-review
├── .zcode/{project.yaml,tasks/} ......... манифест zcode-hub + контексты задач
└── adversarial-review-master/ ........... upstream-импорт, собственный git, в hub НЕ входит (.gitignore)

ПРОЕКТЫ — Level 1                              ~/work/<область>/<проект>/   — 9 репозиториев, §11
├── AGENTS.md   README.md   .gitignore
└── .zcode/
    ├── project.yaml ........... манифест v1 (§4)
    └── tasks/ ................. Level 2: контексты задач <ГГГГММДД>-<slug>.md
    (skills/, commands/ — опционально; config.json НЕ создаётся без нужды: авто-подключение MCP)

ВНЕ HUB
├── ~/PROJECTS ................ старый корень (~35 проектов) — только чтение (правило Level 0)
├── it/projects/openrouter_chat  полигон для тестов skills — вне стандарта (решение 28.09)
└── it/kwork/ggsell ........... пустая заготовка, вне git
```

## 3. Три уровня правил

| Уровень | Файл | Охват | Статус |
|---|---|---|---|
| 0 Global | `~/.zcode/AGENTS.md` | все сессии всех проектов | установлен 28.09, инжектится (подтверждено живьём) |
| 1 Project | `<repo>/AGENTS.md` | сессии внутри репозитория | во всех репозиториях кластера; эталон — `BUBBLES _jupiter` |
| 2 Task | `<repo>/.zcode/tasks/<id>.md` | одна задача | шаблон `templates/` + пара skills git-start/finish-task |

Контекст сессии = Level 0 + Level 1 + Level 2. Манифест `.zcode/project.yaml` агент обязан
прочитать по правилу Level 0 («в каждом репозитории сначала прочитай AGENTS.md и project.yaml»).

## 4. Project Manifest — `.zcode/project.yaml` (v1)

Соглашение Hub (ZCode нативно файл не читает — обязателен к чтению через правила AGENTS.md).
Обязательные поля: `version`, `name`, `type`, `repository.default_branch`, `quality`, `ai`
(включая `allow_git_push: confirm`). Секреты в манифесте запрещены; файл коммитится.
Покрытие: 9 из 9 репозиториев кластера + сам hub.

## 5. Git-стандарт (центральный протокол)

Модель **github-flow** (один разработчик): `main` всегда стабильный; работа в `feature/<task>`;
слияние — squash; теги `v*` (semver) для проектов, которые релизятся.

Жизненный цикл задачи:

```
ЗАДАЧА → ветка feature/<slug> → контекст Level 2 → реализация → quality-чеки (project.yaml)
       → conventional commit (en) → [гейт C] squash-merge в main → [гейт C] push → CI
```

- Коммиты: Conventional Commits (`feat|fix|docs|refactor|test|chore`), английский.
- `git add` только явными путями, никогда `-A` вслепую; секреты и `.env` не коммитятся.
- Merge в main, push, release — категория Level C: только с явного разрешения пользователя
  (Level 0 + слой принуждения guard, §6).

## 6. Подтверждения: режимы ZCode × Level A–D × hub-guard

| Режим ZCode | Назначение | Уровень действий |
|---|---|---|
| `plan` | аудит, анализ, незнакомые репозитории | A — только чтение |
| `build` | рабочий режим по умолчанию для всех проектов | A — сам; B/C — подтверждение в UI |
| `yolo` | только изолированные одноразовые эксперименты; запрет для проектов с ценными данными | D под политикой |

**Слой принуждения — hub-guard** (ADR-0002, внедрён 01.10): один hook `PreToolUse`
(`~/.zcode/hooks/guard/guard.py`), действует во всех режимах, включая `yolo` (подтверждено
экспериментом). Решения принимаются по инструменту, команде и пути — не по полю `mode` и не
по `riskLevel` (оба ненадёжны, факты ADR-0002). Правила сопоставлены Level 0:

| Level | Действие | Правила |
|---|---|---|
| C | ask (снимается токеном на 10 мин) | G-PUSH, G-MERGE-MAIN, G-RELEASE |
| D | deny | G-PUSH-FORCE, G-ADD-SECRET, G-RM-CRITICAL, G-WRITE-PROTECTED, G-WRITE-REFDATA, G-READ-SSH, G-PIPE-TO-SHELL, G-SYSTEM |
| D | ask | G-GIT-DESTRUCTIVE, G-WRITE-ZCODE, G-SUDO, G-SQL-DESTRUCTIVE |
| B | ask | G-RM-RECURSIVE, G-WRITE-OUTSIDE, G-READ-SECRET |

Полная таблица с обоснованиями — ADR-0002. Режимы guard: `off` / `shadow` / `enforce`;
**текущий — shadow** (пишет would-решения в журнал `guard.jsonl`, не блокирует). Переход
в enforce — по критериям ADR-0002 п.3: ≥7 дней и ≥5 рабочих сессий минимум в двух проектах,
отчёт `guard.py --report` просмотрен целиком, ложные срабатывания исправлены или приняты,
пройден тест `ask`. Level C снимается токеном `~/.zcode/hooks/guard/allow-level-c` (создаёт
только пользователь в своём терминале; Level D токеном не снимается). Отказоустойчивость:
fail-open + контроль `guard.py --doctor`. Пока `ask` не подтверждён тестом, `ask` исполняется
как `deny` (`ask_fallback`).

**Принятое ограничение:** guard — страховка от ошибок модели, не граница безопасности: не
видит содержимое скриптов (`python -c`, `bash x.sh`), команды, собранные через переменные,
и действия вне ZCode.

## 7. Skills и плагины

Формат SKILL.md: `INPUT → PRECONDITIONS → STEPS → VALIDATION → OUTPUT → POSTCONDITIONS`;
имена — en-kebab, описания — русские. Глобальные — `~/.zcode/skills/`, проектные —
`<repo>/.zcode/skills/` (не называть как глобальные: user-scope перекрывает workspace).

**Готовые глобальные (5):**

| Skill | Назначение |
|---|---|
| `zcode-doctor` | соответствие стандарту: 8 проверок PASS/WARN/FAIL + счёт |
| `project-onboarding` | разбор незнакомого репозитория → `PROJECT_MAP.md` |
| `project-health` | сводка кластера: ветки/dirty/remote/ahead/коммиты + «Требует внимания» |
| `git-start-task` | начало задачи: feature-ветка + контекст Level 2 по шаблону |
| `git-finish-task` | закрытие задачи: чеки, итог, squash-merge и push — только по гейтам |

**Плагин `adversarial-review`** (первый плагин кластера, 29.09, ADR-001 вариант B):
adversarial-ревью кода/планов независимым BYOK-ревьюером `openrouter/openai/gpt-5.3-codex`
(другое семейство против GLM-lead). Состав: skill-оркестратор, command-обёртка, 2 агента
(read-only `[Read, Grep, Glob]`; exec `+Bash` по `sandbox:workspace-write`). Валидация: смоук
3 раунда — ревьюер нашёл и заложенные, и собственные новые дефекты; пилот на реальном
проекте 29.09 — терминал ABORT провалидирован живьём (сбой диспетчеризации — на стороне
провайдера OpenRouter: баланс/ключ, проверяется). Непроверенное живьём: exec-ревьюер, режимы
`plan`/`code-vs-plan`, >50 файлов, терминалы APPROVED-финал / NOT VERIFIED. Правки плагина
не hot-reload: bump `version` → refresh рынка → Update → новая сессия. Кастомные subagents
регистрируются только компонентом `agents` плагина (standalone `~/.zcode/agents/`
игнорируется — коррекция F8 в ADR-001).

**План (по потребности):** классы skills `git/`, `development/`, `project/`, `release/`,
`operations/`, `research/` (концепция п.3); проектные skills — в репозиториях по типу проекта
(научные, Telegram, инфраструктура).

## 8. MCP-политика

Текущее состояние: **0 внешних MCP** — сохраняется (политика §8 техпроекта).

- Tier 1 (read-only filesystem/search/docs) — не подключаем: у агента есть нативные инструменты.
- Tier 2 (GitHub/GitLab, browser, CI) — по реальной потребности; ключи через переменные
  окружения, не в config.
- Tier 3 (production DB, deploy, secrets) — запрет до отдельного ADR.
- Workspace-MCP (`<repo>/.zcode/config.json`) авто-подключается при открытии проекта —
  не создаётся без явной необходимости; чужие репозитории не открывать без проверки.
- BYOK-модель-провайдер (OpenRouter для ревьюера) — не MCP и в этот счёт не входит.

## 9. База знаний

Приоритет: README → ADR (`docs/adr/NNNN-<slug>.md`, шаблон в `templates/`) → журналы
(§12–§14 техпроекта hub; таблица версий в ADR-001) → PROJECT_MAP (skill
`project-onboarding`) → RUNBOOK (по потребности). Memory MCP / Knowledge Graph — не раньше
Фазы IV (`memoryEnabled: false` — осознанно).

## 10. CI

Эталон — Kutuncev (первый CI кластера, 29.09): `.github/workflows/ci.yml`, триггеры
push/PR → ubuntu → Node 20 → последовательный прогон `tests/*.test.js` (plain-Node, без
зависимостей). Node.js локально отсутствует → CI — единственный способ прогона тестов
Kutuncev/t-invest (закрывает задолженность окружения Фазы II). Открыто: проверить первый
запуск во вкладке Actions.

## 11. Реестр проектов кластера (01.10.2026)

| Проект | Путь | Remote (GitHub, private) | Состояние |
|---|---|---|---|
| zcode-hub | `it/zcode` | `Es1688/ZCode-Engineering-Hub` | запушен 29.09; guard и ADR приланджены на main 01.10 |
| Kutuncev | `it/kwork/Kutuncev` | `Es1688/CMR` | эталон стандарта; первый CI; ahead 0 |
| stelthVPN | `it/projects/stelthVPN` | `Es1688/stelthVPN` | онбординг по стандарту завершён к 30.09; ahead 0 |
| TG-MAX_bridge | `it/projects/TG-MAX_bridge` | — | bootstrap 29.09, рабочее дерево чистое |
| t-invest-skill | `it/projects/t-invest-skill-main` | — | стандарт; локальные чеки блокирует отсутствие Node.js |
| openrouter_chat | `it/projects/openrouter_chat` | — | полигон (решение 28.09, не онбординговать); 29.09 импортирован с файлами стандарта |
| BUBBLES | `science/projects/BUBBLES` | — | стандарт |
| BUBBLES _jupiter | `science/projects/BUBBLES _jupiter` | — | WIP пользователя (4 файла не трогать); ветка develop — удалить после WIP-коммита |
| ohotskoe | `science/projects/ohotskoe` | — | стандарт |
| adversarial-review-master | `it/zcode/adversarial-review-master` | — | upstream-импорт, собственный git, вне репозитория hub |
| ggsell | `it/kwork/ggsell` | — | пустая заготовка, вне git |

## 12. Статус фаз

| Фаза | Содержание | Статус |
|---|---|---|
| I — Foundation | Level 0, манифесты, шаблоны, git init, безопасность | ✅ 28.09 |
| II — Standardization | пилот на 3 проектах: ветки, задачи L2, коммиты, squash-merge | ✅ 28.09 |
| III — Automation | skills, CI, push, плагин adversarial-review, hub-guard | ✅ 28.09–01.10 |
| IV — Cluster | registry, генерация проектов из шаблонов, orchestrator, memory | ⬜ не начата |

Фаза IV фактически закрыта частично: `project-health` выполняет роль dashboard кластера,
`templates/` готовы к генерации новых проектов.

## 13. Остаточная дорожная карта

1. **guard: shadow → enforce** — критерии ADR-0002 п.3 (7 дней / 5 сессий / отчёт просмотрен /
   тест `ask`); после перехода — поправка Level 0 о запрете обхода отказов (ADR-0002, откр. вопрос 5).
2. **push 6 репозиториев без remote** (5 исходных + TG-MAX_bridge): gh CLI либо ручное создание.
3. **режим `build`** для всех проектов — переключение в UI (шаг 8 дорожной карты Фазы I).
4. **adversarial-review**: разобраться с провайдером OpenRouter (баланс/ключ в UI) → финал
   протокола на первом реальном проекте; непроверенное — §7.
5. **CI Kutuncev** — проверить первый запуск (вкладка Actions).
6. **Node.js** — установить локально (quality-чеки t-invest).
7. **BUBBLES _jupiter** — WIP-коммит пользователя, затем удалить ветку develop.
8. **Фаза IV** — по реальной потребности: формальный Project Registry, генерация проектов
   из шаблонов, orchestrator (концепция п.13), Memory MCP.

---

*Макет поддерживается актуальным: изменения устройства Hub — только через задачу
(`git-start-task` → правка → `git-finish-task`) с записью в журнал техпроекта.*
