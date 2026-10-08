> **Статус реализации (обновлено 01.10.2026).** Этот документ — исходная концепция;
> исполнение ведётся по техпроекту `ZCODE-HUB-DESIGN.md` (журналы §12–§14), решениям
> `docs/adr/0001-engineering-hub-adoption.md` и ADR-001 о совместимости
> («Совместимость ZCode с Engineering Hub и скиллом adversarial-review.md»).
> Итоговое устройство Hub — `ZCODE-HUB-LAYOUT.md` (as-built, единственный источник истины).
>
> **Выполнено.** Фаза I — фундамент: Level 0 (`~/.zcode/AGENTS.md`), project.yaml
> в 6 из 7 проектов, шаблоны (`templates/`), git init + первые коммиты в 6 репозиториях.
> Фаза II — пилот стандарта: BUBBLES _jupiter, Kutuncev, t-invest-skill (feature-ветки,
> задачи Level 2, Conventional Commits, squash-merge по гейту Level C). Фаза III —
> завершена 01.10: 5 глобальных skills (zcode-doctor, project-onboarding, project-health,
> git-start-task, git-finish-task), первый CI кластера (Kutuncev → GitHub Actions),
> полигон `openrouter_chat`, первый плагин кластера `adversarial-review` (29.09, ADR-001
> вариант B; пилот на реальном проекте валидировал терминал ABORT), сам hub под git и
> push → `Es1688/ZCode-Engineering-Hub` (29.09), онбординг и push stelthVPN (30.09),
> **слой принуждения hub-guard** (01.10, ADR-0002: hook PreToolUse, 18 правил по Level 0,
> все режимы включая yolo; старт — shadow).
>
> **Не сделано.** Push 6 репозиториев без remote (нужен gh CLI либо ручное создание);
> перевод проектов в режим `build` (шаг 8 дорожной карты); переход guard
> shadow → enforce (критерии ADR-0002 п.3); финал протокола adversarial-review на реальном
> проекте (инцидент провайдера OpenRouter — баланс/ключ); Фаза IV (кластерная
> автоматизация). Внешних MCP — 0 (по политике п.4).

ZCode Engineering Hub — единая среда управления разработкой, в которой ZCode является оркестратором проектов, Git — системой контроля изменений, Skills — стандартизированными процессами, MCP — интерфейсами к внешним системам, а Rules/Knowledge — системой инженерных знаний и политики.

То есть не:

ZCode
 ├── Skills
 ├── MCP
 └── Git

а:

                    ┌─────────────────────┐
                    │       ZCode         │
                    │  Engineering Hub    │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
        PROJECTS           KNOWLEDGE          TASKS
             │                 │                 │
             ▼                 ▼                 ▼
          RULES              ADR              Tracker
             │
             ▼
          SKILLS
             │
             ▼
           MCP
      ┌──────┼──────┐
      ▼      ▼      ▼
     Git    CI     DB/API
      │      │      │
      └──────┼──────┘
             ▼
          GitHub/GitLab

И здесь появляется кластерный уровень, которого в исходном плане практически нет.

1. Сначала нужно определить, что такое «кластер»

Это принципиальный момент.

Я бы не делал один огромный проект, куда складываются все репозитории.

Вместо этого:

ZCODE-HUB/
│
├── global/
│   ├── rules/
│   ├── skills/
│   ├── mcp/
│   └── policies/
│
├── projects/
│   ├── openrouter-bot/
│   ├── bubbles/
│   ├── stelthvpn/
│   └── ...
│
├── templates/
│   ├── python/
│   ├── docker/
│   ├── telegram-bot/
│   └── scientific/
│
└── docs/
    ├── architecture/
    ├── git/
    └── operations/

При этом каждый настоящий проект остаётся самостоятельным Git-репозиторием.

Это очень важно.

Например:

PROJECT A
    Git repository
    project rules
    project skills
    project docs

PROJECT B
    Git repository
    project rules
    project docs

PROJECT C
    Git repository
    project rules
    project docs

А ZCode предоставляет общий верхний слой.

2. Нужна трёхуровневая система правил

В исходном плане это есть, но я бы сделал намного строже.

Level 0 — Global

Правила всей инженерной среды.

Например:

GLOBAL
│
├── безопасность
├── работа с секретами
├── Git policy
├── MCP policy
├── правила использования AI
├── запрет опасных операций
└── стиль взаимодействия
Level 1 — Project

Например для BUBBLES:

BUBBLES
│
├── Python 3.12
├── pytest
├── numpy
├── matplotlib
├── PyInstaller
├── структура проекта
├── научные ограничения
└── правила совместимости с Pascal
Level 2 — Task

Контекст конкретной задачи:

TASK
│
├── issue
├── требования
├── ограничения
├── acceptance criteria
└── изменяемые файлы

И агент должен получать:

GLOBAL
   +
PROJECT
   +
TASK
   =
CURRENT CONTEXT

Это намного надёжнее, чем огромный CLAUDE.md.

3. Skills надо разделить на классы

В исходном плане skills рассматриваются почти как набор команд.

Я бы сделал архитектуру:

skills/
│
├── git/
│   ├── start-task
│   ├── commit
│   ├── review
│   ├── rebase
│   └── finish-task
│
├── development/
│   ├── implement
│   ├── debug
│   ├── refactor
│   └── write-tests
│
├── project/
│   ├── onboarding
│   ├── analyze
│   ├── document
│   └── architecture
│
├── release/
│   ├── release
│   ├── changelog
│   └── hotfix
│
├── operations/
│   ├── deploy
│   ├── rollback
│   └── incident
│
└── research/
    ├── literature
    ├── data-analysis
    └── reproducibility

И главное:

skill не должен просто говорить агенту «сделай X».

Он должен определять:

INPUT
↓
PRECONDITIONS
↓
STEPS
↓
VALIDATION
↓
OUTPUT
↓
POSTCONDITIONS

Например:

git-finish-task

PRECONDITIONS:
- clean working tree
- tests passed
- branch is not main

STEPS:
1. inspect diff
2. run tests
3. run lint
4. create commit
5. push
6. create PR

VALIDATION:
- CI green
- PR created

OUTPUT:
- commit SHA
- PR URL

Это уже инженерный процесс, а не prompt.

4. MCP — не «чем больше, тем лучше»

Вот здесь исходный план я бы изменил сильнее всего.

Не нужно сразу подключать:

Git
GitHub
Jira
Notion
Postgres
Playwright
Sentry
Memory
...

Это создаёт огромную поверхность атаки и непредсказуемость агента.

Нужна MCP-пирамида.

Tier 1 — безопасные
filesystem
git
documentation
read-only search
Tier 2 — рабочие
GitHub/GitLab
issue tracker
CI
browser
Tier 3 — опасные
production DB
deployment
cloud infrastructure
secrets
production APIs

И для каждого MCP:

READ
WRITE
EXECUTE
ADMIN

Например:

MCP	Read	Write	Execute	Admin
Git	✓	✓	✓	—
GitHub	✓	✓	—	—
PostgreSQL	✓	—	—	—
Production	✓	—	—	—
Deploy	✓	✓	✓	—

Причём:

По умолчанию агент должен иметь минимально необходимые права.

5. Самое важное — система подтверждений

Для AI IDE это критично.

Необходимо классифицировать действия.

Level A — безопасные

Агент может делать самостоятельно:

читать файлы
искать код
анализировать Git
запускать тесты
запускать линтер
создавать документацию
Level B — контролируемые
изменение файлов
создание branch
commit
локальные миграции
Level C — подтверждение пользователя
git push
merge
release
deploy
изменение БД
удаление файлов
изменение инфраструктуры
Level D — запрещённые без специального режима
удаление production data
изменение секретов
работа с приватными ключами
опасные shell-команды

Это должно стать частью архитектуры ZCode, а не просто рекомендацией.

6. Git-стандарт нужно сделать центральным протоколом

Здесь исходный план хороший, но я бы пошёл ещё дальше.

Нужно стандартизировать не только:

branch
commit
PR
release

а весь жизненный цикл задачи.

Например:

IDEA
 ↓
ISSUE
 ↓
TASK
 ↓
BRANCH
 ↓
IMPLEMENTATION
 ↓
TEST
 ↓
COMMIT
 ↓
PUSH
 ↓
PR
 ↓
REVIEW
 ↓
MERGE
 ↓
CI
 ↓
RELEASE
 ↓
DEPLOY
 ↓
MONITORING

И ZCode должен понимать эту модель.

7. Git должен стать machine-readable

Например:

project/
├── .git/
├── .github/
│   ├── workflows/
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── .gitattributes
├── .gitignore
├── .editorconfig
│
├── docs/
│   └── GIT_STANDARD.md
│
└── project.yaml

И потенциально:

project:
  name: bubbles
  language: python
  version: "3.12"

git:
  default_branch: main
  strategy: github-flow
  commit_style: conventional
  merge_strategy: squash

quality:
  tests: pytest
  lint: ruff
  typecheck: mypy

release:
  strategy: semver

Тогда skill может читать конфигурацию, а не угадывать правила проекта.

Это очень сильное улучшение.

8. Нужен Project Manifest

Я считаю это одним из наиболее важных недостающих элементов исходного плана.

Например:

.zcode/
    project.yaml
    rules/
    skills/
    workflows/

project.yaml описывает проект:

name: bubbles
type: scientific-python

language:
  name: python
  version: "3.12"

repository:
  platform: github
  default_branch: main

quality:
  test: pytest
  lint: ruff

build:
  tool: pyinstaller

documentation:
  root: docs/

ai:
  allow_shell: controlled
  allow_git_push: confirm

Теперь ZCode может автоматически определить:

Что это за проект и как с ним работать?

9. Нужно различать Project Skills и Global Skills

Например:

GLOBAL SKILLS

git-start-task
git-review
git-finish-task
create-adr
release

А проект BUBBLES добавляет:

PROJECT SKILLS

compare-with-pascal
run-scientific-validation
generate-bubble-report
build-exe

Получаем:

Global Skills
       +
Project Skills
       +
Task Context
       ↓
ZCode Agent

Это позволяет масштабировать систему на десятки проектов.

10. Нужна база знаний, но я бы не начинал с Memory MCP

Это ещё одна вещь, которую я бы изменил.

Сначала:

README
ARCHITECTURE
ADR
RUNBOOK
GIT_STANDARD
PROJECT_MANIFEST

И только потом:

Memory / Knowledge Graph

Потому что документация в Git:

версионируется;
проверяется;
проходит review;
переносится между компьютерами;
не зависит от конкретного AI;
воспроизводима.

То есть:

Git должен быть источником истины. Memory MCP — вспомогательным слоем.

11. Нужен режим «Onboarding»

Это очень мощная функция для ZCode-кластера.

Открываем неизвестный репозиторий.

ZCode выполняет:

1. определить стек
2. определить структуру
3. определить Git
4. определить CI
5. найти документацию
6. найти тесты
7. найти entry points
8. определить зависимости
9. проверить состояние репозитория
10. построить PROJECT_MAP

Результат:

PROJECT_MAP.md

Например:

BUBBLES

Language: Python 3.12
Build: PyInstaller
Tests: pytest
Entry point: bubbles/app.py

Architecture:
    layer.py
    stratum.py
    reports.py
    plots.py
    ui.py
    app.py

Data:
    DATASTOR/VOS

Legacy:
    Turbo Pascal BUBBLES.EXE

CI:
    GitHub Actions

Current branch:
    feature/report-validation

Для работы с большим количеством проектов это крайне полезно.

12. Нужно сделать Project Health

ZCode должен уметь ответить:

«В каком состоянии мои проекты?»

Например:

ZCODE PROJECT DASHBOARD

BUBBLES
  ✓ Git clean
  ✓ Tests 127/127
  ✓ CI green
  ⚠ 2 outdated dependencies
  ⚠ no release for 48 days

OPENROUTER
  ✓ Git clean
  ✓ CI green
  ✓ Docker build
  ⚠ 1 stale PR

STELTHVPN
  ⚠ uncommitted changes
  ⚠ CI unavailable
  ✓ tests

Это уже действительно кластер управления проектами.

13. И ещё один уровень — Orchestrator

В будущем можно сделать:

ZCode
  │
  ├── Project A agent
  ├── Project B agent
  ├── Project C agent
  └── Research agent

Например:

«Проверь все мои Python-проекты на устаревшие зависимости».

ZCode:

BUBBLES → check
OpenRouter → check
Research → check
Telegram → check

И выдаёт:

4 projects checked

BUBBLES
numpy update available

OpenRouter
asyncpg update available

Telegram
aiogram update available

Research
no changes

А уже затем пользователь выбирает, где создавать задачи.

Это и будет настоящий project cluster.

14. Отдельный слой — Templates

После стандартизации проектов можно сделать:

templates/

python-service/
python-bot/
docker-service/
scientific-python/
telegram-bot/
cli-tool/

Новый проект:

ZCode
   ↓
New Project
   ↓
Select template
   ↓
Git repository
   ↓
Rules
   ↓
Skills
   ↓
CI
   ↓
README
   ↓
Project Manifest

И новый проект сразу соответствует стандарту.

15. Я бы добавил «ZCode Doctor»

Очень полезный системный skill.

Запуск:

/zcode-doctor

Проверяет:

✓ project manifest
✓ rules
✓ skills
✓ git
✓ hooks
✓ CI
✓ secrets
✓ documentation
✓ tests
✓ dependencies
✓ repository state

И выдаёт:

ZCode Project Compliance

Git ................ PASS
Rules .............. PASS
Skills ............. PASS
CI ................. PASS
Documentation ...... WARNING
Secrets ............ PASS
Tests .............. PASS

Score: 92/100

Так можно постепенно стандартизировать все репозитории.

16. Что я считаю главным недостатком исходного плана

Он начинается примерно с:

«Давайте создадим rules → skills → MCP → Git».

Я бы изменил порядок.

Правильнее:

                    ┌──────────────────┐
                    │  ENGINEERING     │
                    │     POLICY       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ PROJECT MODEL    │
                    │ Manifest/State   │
                    └────────┬─────────┘
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
           RULES           GIT            KNOWLEDGE
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                          SKILLS
                             │
                             ▼
                           MCP
                             │
                             ▼
                          ZCODE
                             │
                             ▼
                       ORCHESTRATOR

То есть сначала архитектура процессов, потом инструменты.

Предлагаю разбить проект на 4 большие фазы
Фаза I — ZCode Foundation

Цель:

Сделать единый фундамент.

Создаём:

Global Rules
Project Manifest
Git Standard
Security Policy
Skill Standard
MCP Policy
Documentation Standard

MCP пока минимально.

Фаза II — Project Standardization

Берём 2–3 реальных проекта и переводим их на стандарт.

Например:

BUBBLES
OpenRouter
StelthVPN

Это позволит проверить, что архитектура действительно универсальна.

Фаза III — Automation

Добавляем:

Skills
Git automation
CI
Project Doctor
Onboarding
Project Health
Release automation

И только после этого расширяем MCP.

Фаза IV — Cluster

Создаём:

ZCode Hub
│
├── Project Registry
├── Project Health
├── Shared Skills
├── Shared Rules
├── MCP Registry
├── Templates
├── Knowledge Base
└── Automation

И тогда появляется возможность управлять десятками репозиториев единообразно.

Особенно важно для твоего случая

С учётом того, что у тебя есть разные типы проектов — Python/Telegram, инфраструктурные проекты, научные проекты, BUBBLES, Docker/VPS — я бы не пытался сделать один универсальный профиль разработки.

Нужна модель:

                    ZCODE
                      │
             GLOBAL ENGINEERING
                   POLICY
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   SOFTWARE       SCIENCE       INFRASTRUCTURE
        │             │             │
        ▼             ▼             ▼
   Python/etc.    BUBBLES/etc.    Docker/VPS

Общие правила остаются общими, а специализированные skills/rules подключаются по типу проекта.

Это позволит одновременно работать, например, с BUBBLES и серверным проектом, не заставляя научный проект жить по правилам backend-сервиса.

Итоговая концепция

Я бы сформулировал цель проекта так:

Создать стандартизированную инженерную среду на базе ZCode, в которой каждый проект имеет единый описываемый жизненный цикл, Git-процесс, правила AI-агента, набор специализированных skills, контролируемые MCP-интеграции, CI/CD и базу знаний, а ZCode способен одновременно анализировать состояние и управлять множеством независимых Git-репозиториев.

И конечная архитектура:

                         ZCODE
                    ENGINEERING HUB
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
     RULES                SKILLS               MCP
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    PROJECT REGISTRY
                            │
       ┌────────────┬───────┼───────┬────────────┐
       ▼            ▼       ▼       ▼            ▼
   BUBBLES      OPENROUTER  VPN   TELEGRAM    SCIENCE
       │            │       │       │            │
       └────────────┴───────┼───────┴────────────┘
                            │
                         GIT
                            │
                    GitHub / GitLab
                            │
                       CI / CD
                            │
                    Deploy / Monitor

Я бы не начинал сейчас с написания отдельных skills или установки MCP. Сначала стоит сделать технический проект ZCode Engineering Hub: определить архитектуру каталогов, уровни правил, формат project.yaml, Git-протокол, модель permissions для MCP, структуру skills и жизненный цикл задачи. После этого уже по нему последовательно конфигурировать сам ZCode.

Это даст нам не набор разрозненных настроек, а реально масштабируемую систему, которую потом можно переносить на каждый новый репозиторий.
