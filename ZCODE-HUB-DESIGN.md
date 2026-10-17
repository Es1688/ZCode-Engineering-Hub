# ZCode Engineering Hub — техпроект (Фазы I–III)

**Статус:** действует — решения §11 зафиксированы, Фазы I–III выполнены (журналы §12–§14) • **Дата:** 28.09.2026, обновлён 29.09.2026
**Входные документы:** концепция (`ZCode Engineering Hub.md`), аудит (`audit/2026-09-28-audit-report.md`)
**Принцип:** сначала архитектура процессов, потом инструменты (концепция, п.16). Ничего из этого
документа не устанавливается до вашего ревью и решений по §11.

---

## 1. Что зафиксировал аудит (основа проектирования)

1. Extension-поверхность ZCode пуста: нет `~/.zcode/AGENTS.md`, нет своих skills/commands, нет
   MCP/hooks, `~/.zcode/cli/config.json` отсутствует → строим с нуля, ничего не ломаем.
2. Нативные места конфигурации подтверждены официальным гайдом (таблица §2).
3. Git-реальность: 2 из 7 проектов в git, у обоих **нет remote** (риск потери данных); 5 проектов
   не версионируются вообще.
4. Режимы исполнения: `plan` / `build` / `yolo` (per-project sticky + per-session); в истории
   57 сессий **yolo — 42%**; явных allow/deny-правил нет (аудит §9).
5. Два корня проектов: `~/work` (новый, 7 проектов) и `~/PROJECTS` (старый, ~35).
6. Эталон Level-1 правил уже существует: `BUBBLES _jupiter/AGENTS.md`.

## 2. Карта «концепция → механизм ZCode»

| Уровень концепции | Механизм ZCode | Место | Статус |
|---|---|---|---|
| Level 0 — Global Rules | user AGENTS.md | `~/.zcode/AGENTS.md` | создать (Приложение А) |
| Level 1 — Project Rules | workspace AGENTS.md | `<repo>/AGENTS.md` | есть у 2 из 7 |
| Level 2 — Task Context | файл задачи + план сессии | `<repo>/.zcode/tasks/<id>.md` (стандарт Hub) | ввести |
| Project Manifest | наш YAML, читаемый skills | `<repo>/.zcode/project.yaml` | ввести (Приложение Б) |
| Global Skills | user skills | `~/.zcode/skills/<имя>/SKILL.md` | ✅ 5 skills (28–29.09, §14) |
| Project Skills | workspace skills | `<repo>/.zcode/skills/` | по потребности |
| Команды | commands | `~/.zcode/commands/*.md`, `<repo>/.zcode/commands/` | ✅ — в составе плагина adversarial-review (29.09, §14) |
| Кастомные subagents | компонент `agents` плагина, адресация `<plugin>:<name>` | `it/zcode/plugins/<плагин>/agents/` | ✅ adversarial-review (29.09); standalone `~/.zcode/agents/` не читается (ADR-001) |
| MCP-политика | config `mcp.servers` | `~/.zcode/cli/config.json`, `<repo>/.zcode/config.json` | не создаём до потребности |
| Подтверждения Level A–D | режимы `plan`/`build`/`yolo` + hooks | UI + `~/.zcode/cli/config.json` | режимы есть; hooks — Фаза III |
| Knowledge Base | docs в git | `<repo>/docs/`, `it/zcode/docs/adr/` | ввести |

Нюансы из гайда, учтённые в проекте:

- User-скоуп **перекрывает** workspace для одноимённых skills/commands/MCP → не называть
  проектные скиллы так же, как глобальные.
- Workspace-MCP **подключается автоматически** при открытии проекта → `<repo>/.zcode/config.json`
  не создаём без явной необходимости; чужие репозитории не открывать без проверки.
- Hooks требуют `hooks.enabled: true`; событий ровно семь (`SessionStart`, `UserPromptSubmit`,
  `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `Stop`).
- `work/AGENTS.md` подхватится только сессиями, открытыми **в самом `work/`** (поиск AGENTS.md
  идёт вверх до корня проекта; для репозитория корень — сам репозиторий). Поэтому правила
  кластера живут в Level 0, а не в `work/AGENTS.md`.

## 3. Архитектура кластера

```
Уровень 0 — глобально                   ~/.zcode/
├── AGENTS.md                ← правила Level 0 (Приложение А)
├── skills/                  ← глобальные skills (Фаза III)
├── commands/                ← глобальные команды (Фаза III)
└── cli/config.json          ← MCP user-scope + hooks (сознательно не создаём)

Кластер — dataBaseDir                    /home/egor/work/
└── it/zcode/                ← штаб-квартира Hub (не кодовый проект)
    ├── ZCode Engineering Hub.md         концепция
    ├── audit/2026-09-28-audit-report.md аудит ЭТАПА 0
    ├── ZCODE-HUB-DESIGN.md              этот техпроект
    ├── templates/                       .gitignore по типам, project.yaml, ADR
    ├── plugins/                         плагины кластера + marketplace.json (с 29.09, §14)
    └── docs/adr/                        решения кластера (ADR)

Проект — Level 1            /home/egor/work/<область>/<проект>/
├── AGENTS.md                ← правила проекта (эталон: BUBBLES _jupiter)
├── README.md
├── .gitignore
└── .zcode/
    ├── project.yaml         ← манифест (Приложение Б)
    ├── tasks/               ← Level 2: контекст задач
    ├── skills/  commands/   ← опционально
    └── config.json          ← НЕ создавать без нужды (авто-подключение MCP!)
```

`~/PROJECTS` — выводится из эксплуатации (варианты — §11, вопрос 3).

## 4. Project Manifest — `.zcode/project.yaml` (v1)

Назначение: skill или команда читает конфигурацию, а не угадывает правила. ZCode нативно файл
не читает — это соглашение Hub, обязательное к чтению через правила AGENTS.md.

Обязательные поля: `version`, `name`, `type`, `repository.default_branch`, `quality`, `ai`
(включая `allow_git_push: confirm`). Файл коммитится; секреты в нём запрещены. Пример —
Приложение Б.

## 5. Git-стандарт (центральный протокол)

Модель — github-flow (оптимальна для одного разработчика):

- `main` — всегда стабильный; работа в `feature/<task>`; слияние squash; теги `v*` (semver)
  для проектов, которые релизятся.
- Commit-сообщения: Conventional Commits (`feat|fix|docs|refactor|test|chore`), язык — §11.2.
- Перед коммитом — тесты/линтер из `project.yaml`.
- `git push`, merge в main, release — категория Level C: только с явного разрешения
  (закрепляется в Level 0, Приложение А).

Приоритет приведения к стандарту (по аудиту §5):

1. **Remote + первый push для `BUBBLES _jupiter` и `Kutuncev`** — единственный срочный пункт
   всей Фазы: сейчас у единственных версионируемых проектов нет бэкапа.
2. `git init` + базовая структура для 5 проектов: t-invest-skill-main, BUBBLES, ohotskoe,
   ggsell, adversarial-review-master.
3. Выравнивание всех 7 по шаблону: `README.md`, `AGENTS.md`, `.gitignore`,
   `.zcode/project.yaml`, `docs/adr/`. *(Уточнение Фазы II: `docs/adr/` создаётся вместе
   с первым ADR проекта — пустые каталоги не версионируются; репозитории с шаблоном
   `.zcode/*` в .gitignore обязаны явно включать `!.zcode/project.yaml` и
   `!.zcode/tasks/`.)*

## 6. Система подтверждений: режимы ZCode × Level A–D

Факты (аудит §9): режимы `plan`/`build`/`yolo`; per-project sticky + per-session; явных правил
нет; в истории 42% сессий — yolo.

Политика Hub:

| Режим | Когда используется | Соответствие Level A–D |
|---|---|---|
| `plan` | аудит, анализ, незнакомые репозитории | Level A — только чтение |
| `build` | **рабочий режим по умолчанию для всех проектов** | A — сам; B/C — подтверждение в UI |
| `yolo` | только изолированные одноразовые эксперименты; запрет для проектов с ценными/оригинальными данными | Level D под политикой |

Жёсткое внедрение (Фаза III): hooks `PreToolUse` / `PermissionRequest` в
`~/.zcode/cli/config.json` дают формальные правила (запрет push без явного флага, запрет
опасных команд вне workspace). До этого — мягкое внедрение правилами Level 0.

Целевое состояние после Фазы I: все проекты в `build`; оба BUBBLES уже там; остальное сейчас
в `plan` — переключается вами в UI при следующем открытии проекта.

## 7. Skills — стандарт и классы

Формат SKILL.md (концепция п.3): `INPUT → PRECONDITIONS → STEPS → VALIDATION → OUTPUT →
POSTCONDITIONS`. Описания — русский; имена — en-kebab. Классы каталогов: `git/`, `development/`,
`project/`, `release/`, `operations/`, `research/`.

Размещение: глобальные — `~/.zcode/skills/`, проектные — `<repo>/.zcode/skills/`.
Созданы 28–29.09 (Фаза III): `zcode-doctor`, `project-onboarding`, `git-finish-task`,
`git-start-task`, `project-health` — активны в новых сессиях.

Кастомные subagents доставляются **только плагинами** (компонент `agents`, адресация
`<plugin>:<name>`; каталог `~/.zcode/agents/` в discovery не входит — живой тест 29.09,
коррекция F8 в ADR-001). Первый плагин кластера — `adversarial-review` (29.09,
`it/zcode/plugins/`): skill-оркестратор + command + 2 агента-ревьюера (read-only
`[Read, Grep, Glob]` и exec `+Bash`); маркетплейс `it/zcode/plugins/marketplace.json`
(имя `dev-it-zcode`). Правки исходника плагина не hot-reload: bump `version` в манифесте
и каталоге → refresh рынка в UI → Update → новая сессия.

## 8. MCP-политика

- Tier 1 (read-only filesystem/search/docs) — **не подключаем**: у агента есть нативные
  файловые и поисковые инструменты.
- Tier 2 (GitHub/GitLab, browser) — по реальной потребности после Фазы II; ключи через
  переменные окружения, не в config.
- Tier 3 (production DB, deploy, secrets) — запрет до отдельного ADR.
- Текущее состояние: 0 внешних MCP — сохраняется. Workspace-MPC авто-подключается — помним.
- BYOK-модель-провайдер — не MCP и в этот счёт не входит: 29.09 пользователь подключил
  OpenRouter (`openrouter/openai/gpt-5.3-codex`) как модель adversarial-ревьюера (§14).

## 9. База знаний

README → ARCHITECTURE → ADR (`docs/adr/NNNN-<slug>.md`, шаблон в `it/zcode/templates/`) →
RUNBOOK → GIT_STANDARD (§5 этого документа). Memory MCP — не раньше Фазы IV
(`memoryEnabled: false` — и это правильно).

## 10. Дорожная карта Фазы I

| # | Шаг | Кто | Статус (28.09) |
|---|---|---|---|
| 1 | Ревью техпроекта + решения §11 | вы | ✅ решения зафиксированы (§11) |
| 2 | Remote (GitHub) + push 6 репозиториев | я | ⏳ отложено вашим решением: по команде после систематизации |
| 3 | Установка `~/.zcode/AGENTS.md` (Приложение А) | я | ✅ |
| 4 | `git init` + структура проектов | я | ✅ 4 из 5 (ggsell пуст — пропущен) |
| 5 | `project.yaml` | я | ✅ 6 из 7 (ggsell пуст) |
| 6 | AGENTS.md Level 1 | я | ✅ (в adversarial — свой, не менялся) |
| 7 | `templates/` + ADR-0001 «Принятие Engineering Hub» | я | ✅ |
| 8 | Перевод проектов на режим `build` | вы (UI) | ⏳ |

## 11. Решения — зафиксировано 28.09.2026

1. **Платформа git-remote:** GitHub, приватные репозитории. Для шага 2 дорожной карты нужно от
   вас: аккаунт GitHub и аутентификация (`gh auth login` или ssh-ключ); репозитории создаю я.
2. **Язык commit-сообщений:** английский, Conventional Commits. Существующая русская история
   двух репозиториев не переписывается — стандарт действует на новые коммиты.
3. **Судьба `~/PROJECTS`:** остаётся как есть, без изменений. Hub охватывает только `~/work`;
   старый корень защищён правилом Level 0 «вне workspace — только чтение». Перенос отдельных
   проектов — по мере оживления, отдельными решениями.
4. **Обновление 3.11.2 → 3.14.3:** после Фазы I; сразу после обновления — экспресс-перепроверка
   аудита (пути и форматы config могли измениться).

---

## 12. Журнал выполнения Фазы I (28.09.2026)

**Установлено и создано:**

- `~/.zcode/AGENTS.md` — правила Level 0 (Приложение А дословно); действуют в новых сессиях.
- `it/zcode/templates/` — gitignore/python, gitignore/node, project.yaml, AGENTS-L1, ADR.
- `it/zcode/docs/adr/0001-engineering-hub-adoption.md` — принятие Hub + решения §11.
- Новые репозитории (`git init -b main` + первый коммит + AGENTS.md L1 + `.zcode/project.yaml`):
  t-invest-skill (`a6782a2`), BUBBLES (`136a651`), ohotskoe (`55e82ba`),
  adversarial-review (`6285a04`, его собственный AGENTS.md сохранён без изменений).
- Kutuncev: `59968db` (gitignore с исключением для манифеста, планы сессий сняты с учёта)
  + `ba88d3b` (манифест + правила L1); ветка уже `main`, рабочий статус чистый.
- BUBBLES _jupiter: `f29c51e` (планы сессий сняты с учёта) + `2976671` (манифест);
  ветка `main` переведена fast-forward на актуальный комит (была позади на 3, история
  не переписана; ветка `develop` оставлена — удалить после WIP-коммита пользователя);
  незакоммиченный научный WIP (BUBBLES.ipynb, BUBBLES_user.ipynb, docs/) не тронут.

**Аутентификация GitHub:** SSH-ключ `id_ed25519` подтверждён (`Hi Es1688!`); `gh` CLI не
установлен и не нужен — push будет по SSH.

**Отложено (ваше решение 28.09):** push всех 6 репозиториев — по команде. План: создать
приватные репозитории `Es1688/<name>` и запушить `main` каждого.

**Инцидент 28.09 ~21:09 (исправлен ~21:35):** содержимое `~/.zcode` было перенесено в
`work/.zcode`; приложение пересоздало домашний каталог в течение минуты — перенос
штатно не поддерживается, `~/.zcode` зашит как user-scope корень. Служебное восстановлено
копированием (приложение не перезапускалось): `AGENTS.md`, база сессий (sqlite
online-backup: 58 сессий, 10 проектных режимов), `credentials.json` / `config.json`
(права 600), полный `setting.json` (частичный новый сохранён как
`setting.json.fresh-after-move.bak`), история `agents/`+`artifacts/`+`exec/`+`rollout/`,
`known_marketplaces.json`. Копии в `work/.zcode` оставлены как резерв. После перезапуска
приложения и проверки можно удалить только перенесённые туда элементы
(`work/.zcode/{cli,plugin-workspace,AGENTS.md}`); `v2/`, `workspace/`, `plans/` в
`work/.zcode` трогать нельзя — их ведёт приложение (`dataBaseDir=work`). Вывод для Hub:
переносимость достигается `dataBaseDir` + git-репозиториями, а не переносом пользовательского
каталога ZCode.

*Резерв очищен (проверка 28.09 ~22:35):* элементы `work/.zcode/{cli,plugin-workspace,AGENTS.md}`
к этому моменту уже отсутствовали — удалены вне сессии аудита, вручную. В `work/.zcode`
остались только управляемые приложением `v2/` и `workspace/`. Живой `~/.zcode` активен
и пишется (cli/db, exec), `AGENTS.md` Level 0 и `skills/` (Фаза III) на месте.

### Экспресс-перепроверка после обновления 3.14.3 (28.09, поздняя проверка)

- Пакет: `zcode 3.14.3-7762` (dpkg), приложение запущено (14 процессов).
- **Целостность после обновления и инцидента:** все 6 репозиториев на месте (в `_jupiter` —
  только WIP пользователя); `~/.zcode/AGENTS.md` (Level 0) цел; восстановленная база сессий
  отвечает (58 сессий, 10 проектных режимов — совпадает с записью об инциденте);
  `~/.zcode/cli` (плагины, db, rollout) доступен.
- **setting.json:** появились `providerFamilyConnectionSelections`,
  `startPlanRecommendationDismissed`; исчезли устаревшие `instantGrepIndexingEnabled`,
  `optimizeAgentExperience…` ×2, `repoSnapshotIndexingEnabled`; `dataBaseDir: /home/egor/work`
  сохранён.
- **Права:** рабочий `work/.zcode/v2/config.json` после инцидента имел 0664 — возвращено `0600`;
  новый `provider_config.json` создан сразу с `600`.
- **Гайд-плагин 0.3.0** (пришёл с обновлением): все пути и правила конфигурации идентичны
  прежним (`~/.zcode/AGENTS.md`, `~/.zcode/cli/config.json`, `<repo>/.zcode/…`,
  авто-подключение workspace-MCP, те же 7 событий hooks) — карта §2 техпроекта валидна без
  изменений.
- **⚠ Открытый пункт — кастомные провайдеры:** рабочий `work/.zcode/v2/config.json` (7202 байта,
  записан свежим приложением во время инцидента) содержит только builtin-провайдеры; два
  кастомных OpenRouter (gemini-3.8-flash, CODEX) остались только в восстановленной глобальной
  копии `~/.zcode/v2/config.json`; `provider_config.json` — пустой стаб. Проверить в UI
  (настройки моделей): если провайдеров нет — восстановить из глобальной копии.
  **→ Закрыто 29.09:** OpenRouter-провайдер подключён (пользователь, UI); модель
  `openrouter/openai/gpt-5.3-codex` видна хосту и используется плагином adversarial-review.
- **Очистка резерва после инцидента** (`work/.zcode/{cli,plugin-workspace,AGENTS.md}`) — условия
  из записи об инциденте выполнены (перезапуск + проверка); выполняется только по явному
  подтверждению пользователя.

---

## 13. Журнал Фазы II — пилот стандарта (28.09.2026, вечер)

**Докомплектация шаблона (§5.3):**

- README.md создан: BUBBLES (`e526af9`), ohotskoe (`268aca4`), Kutuncev (в пилотном коммите);
  в t-invest, adversarial, _jupiter README уже был.
- `templates/task-context.template.md` — шаблон контекста задач Level 2 (первое применение —
  сразу в пилотных циклах).
- ADR-0001 «Переход на стандарт Engineering Hub» создан в трёх пилотных проектах.

**Пилотные циклы (feature-ветка → контекст Level 2 → conventional commit):**

| Проект | Ветка | Коммит | Примечание |
|---|---|---|---|
| BUBBLES _jupiter | `feature/hub-adoption-docs` | `433eba0` | WIP пользователя не тронут |
| Kutuncev | `feature/hub-adoption-docs` | `779f94c` | `.gitignore`: + `!.zcode/tasks/` |
| t-invest-skill | `feature/hub-adoption-adr` | `55a031d` | чеки недоступны (нет node) |

Merge выполнен 28.09 по подтверждению пользователя (гейт Level C отработал штатно):
squash-merge в main — `_jupiter` `cc591a4`, Kutuncev `fcf223f`, t-invest `499c547`;
feature-ветки удалены. В `_jupiter` ветка `develop` осталась (позади main) — удалить
после WIP-коммита пользователя.

**Находка при merge:** у Kutuncev появился remote `origin → git@github.com:Es1688/CMR.git`
(создан пользователем после аудита; на момент аудита remote не было). `origin/main` стоит
на `70f8164`, локальный main опережает на 3 коммита (`59968db`, `ba88d3b`, `fcf223f`) —
push по команде. Остальные 5 репозиториев без remote.

**Находки Фазы II (правки стандарта приняты):**

1. Шаблон `.zcode/*` в .gitignore глушит `.zcode/tasks/` — зафиксировано правило-исключение
   (см. уточнение в §5.3); комментарии шаблонов gitignore обновлены.
2. **node/npm в системе отсутствуют** → quality-чеки t-invest (`typecheck`/`lint`/`vitest`)
   невыполнимы. Задолженность окружения: установить Node.js (например, через nvm) до первой
   кодовой задачи в t-invest.
3. **Level 0 подтверждён вживую**: `~/.zcode/AGENTS.md` инжектится в сессии (наблюдается
   в текущей сессии после перестройки контекста).
4. Level 1 применяется через правило Level 0 («сначала прочитай AGENTS.md проекта»);
   авто-инъекция при открытии сессии внутри репозитория — проверить пользователю при
   следующем открытии проекта (шаг 8 заодно: режим `build`).

---

## 14. Журнал Фазы III — старт автоматизации (28.09.2026)

**Созданы три глобальных skills в `~/.zcode/skills/`:**

| Skill | Назначение |
|---|---|
| `zcode-doctor` | диагностика соответствия стандарту: 8 проверок PASS/WARN/FAIL + счёт; только читает |
| `project-onboarding` | разбор незнакомого репозитория → `PROJECT_MAP.md` в корне |
| `git-finish-task` | стандартное закрытие задачи; merge в main и push — только по явному «да» |

- Формат — по официальному skill-creator: frontmatter `name`/`description` (триггеры на
  русских фразах пользователя), тело INPUT→PRECONDITIONS→STEPS→VALIDATION→OUTPUT→POSTCONDITIONS.
- Место `~/.zcode/skills/` (а не рекомендуемая skill-creator'ом `.agents/skills/`):
  окружение ZCode-only по аудиту (`~/.agents` и `~/.claude` отсутствуют), решение §2.
- В содержимое заложены правила, проверенные Фазой II: гейты Level C, исключения
  `!.zcode/{project.yaml,tasks/}` для репозиториев с шаблоном `.zcode/*`, задачи Level 2,
  Conventional Commits (en), запрет `git add -A` вслепую.
- **Smoke-тест** чек-листа zcode-doctor на Kutuncev: 8/8 PASS (100%) — каждая проверка
  чек-листа исполнима реальной командой и даёт однозначный вердикт.
- Активация: skills обнаруживаются в **новых сессиях** ZCode (в текущей сессии не загружены).

**Дальше по Фазе III** (по концепции): CI и Project Health — после появления remotes
(push отложен решением пользователя); расширенная git-автоматизация и release-процесс —
по мере реальных задач; MCP — по политике §8 (не подключаем без потребности).

### Push и полигон (28.09, поздний вечер)

- **Push:** Kutuncev запушен в существующий `Es1688/CMR` (`70f8164..fcf223f` — docs-коммиты
  стандарта). Создание остальных 5 репозиториев (bubbles-jupiter, bubbles-original,
  ohotskoe, adversarial-review, t-invest-skill) отложено пользователем: для создания нужен
  gh CLI с входом (сейчас не установлен; SSH-ключ уже есть, но репозитории по SSH не
  создаются) либо ручное создание в вебе. Вернуться по команде.
- **Skills подтверждены пользователем в новой сессии** («добавил новый проект, проверка
  сработала»).
- **Полигон для тестов:** `it/projects/openrouter_chat` (Python-чат с OpenRouter, 49М,
  скопирован из `~/PROJECTS`, копия в старом корне осталась) — решением пользователя
  **НЕ переводится на стандарт** и используется для проверки skills (zcode-doctor на нём
  должен показывать FAIL, project-onboarding — строить карту). Будущим сессиям: не
  онбординговать этот проект без явной задачи. ⚠ В корне лежит `.env` с ключом OpenRouter,
  а .gitignore его не покрывает; репозиторий без коммитов (27 незакрытых файлов) — при
  любом будущем коммите сначала добавить `.env` и `cookies.txt` в .gitignore.

### Фаза III, продолжение (29.09) — Kutuncev как эталонный пример

Решение пользователя: Kutuncev — пример для отработки плана; остальные проекты приводятся
к общему виду после реализации плана.

- **CI (первый в кластере):** `.github/workflows/ci.yml` — push/PR → ubuntu → Node 20 →
  последовательный прогон `tests/*.test.js` (тесты — plain-Node, без зависимостей).
  Локально node отсутствует → CI становится единственным способом прогона тестов
  (закрывает задолженность окружения из Фазы II). `project.yaml` дополнен секцией `ci`.
  Цикл стандарта: ветка `feature/ci-github-actions`, задача
  `.zcode/tasks/20260928-ci-github-actions.md`, коммит `cbfdcad`. **Merge+push выполнены
  29.09 по подтверждению пользователя:** squash в main → `c80d7ee`, ветка удалена,
  push в `Es1688/CMR` (`fcf223f..c80d7ee`), локал и remote совпадают (ahead 0). Первый
  запуск CI проверить во вкладке Actions репозитория; критерий «CI зелёный» в задаче
  закрывается после проверки.
- **Skills +2:** `git-start-task` (начало задачи: feature-ветка + контекст Level 2 по
  шаблону; пара к `git-finish-task`) и `project-health` (сводка кластера:
  ветки/dirty/remote/ahead/последний коммит/маркеры стандарта + блок «Требует внимания»;
  полигоны не онбординговать).
- **Smoke-тест project-health** выявил и устранил 3 дефекта подхода: (1) пути с пробелами
  («BUBBLES _jupiter») ломают наивный цикл по find — нужен null-разделённый обход;
  (2) ahead считался от зашитого `origin/main` вместо upstream текущей ветки —
  feature-ветки с незапушенными коммитами были невидимы; (3) репозитории без коммитов
  не помечались. Все три исправления внесены в SKILL.md; сводка кластера корректна.

### Фаза III, продолжение (29.09) — первый плагин кластера: adversarial-review (вариант B)

Полная история и протокол — ADR-001 («Совместимость ZCode с Engineering Hub и скиллом
adversarial-review», `it/zcode/Совместимость ZCode ….md`, статус Accepted).

**Сделано:**

- **Прогон совместимости** (~25 экспериментов, блоки A–F ADR): подтверждены лимиты Bash
  (default 120 c / max 600 c; сверх max — auto-background с сохранением жизненного цикла),
  Plan-mode запрет записи в `/tmp`, схема приоритетов конфигураций; факты F1–F16, среди них
  коррекция F8 (см. ниже). Блокер варианта A (порт «как есть» с Codex CLI): Codex CLI не
  установлен → **выбран вариант B** — нативный сабагент-ревьюер.
- **Первый плагин кластера:** `it/zcode/plugins/adversarial-review/` — skill-оркестратор
  (хирургический EN-порт протокола, 43 КБ), command-обёртка с `$ARGUMENTS`, 2 кастомных
  агента (`adversarial-review:adversarial-reviewer` — физически read-only
  `[Read, Grep, Glob]`; `…-exec` — `+Bash` для verify-команд, по `sandbox:workspace-write`);
  модель ревьюера — BYOK `openrouter/openai/gpt-5.3-codex` (другое семейство против
  GLM-lead — смысл adversarial-петли). Каталог маркетплейса `it/zcode/plugins/`
  (`marketplace.json`, имя `dev-it-zcode`); установку и настройку BYOK выполнил
  пользователь в UI.
- **Живая валидация** (смоук-репо с заведомыми дефектами, режим `code`, 3 раунда полного
  протокола): ревьюер подтвердил оба заложенных дефекта (high×2) и в последующих раундах
  нашёл новые собственные — окно truncate при записи, symlink-утечка за пределы каталога,
  потеря прав при mkstemp-публикации. Все находки верифицированы lead'ом (в т.ч.
  эмпирическими тестами), исправлены; re-scope с техническим обоснованием; verbatim-вывод
  ревью, снапшоты мутаций до/после, full-history раунды — работают.

**Не завершено (решение владельца — валидация на первом реальном проекте):** финал
протокола (APPROVED / итоговая сводка / cleanup) живьём не наблюдался; не проверены
exec-ревьюер (`sandbox:workspace-write`), режимы `plan`/`code-vs-plan`, >50 файлов,
Plan-mode инлайн-путь, терминальные состояния NOT VERIFIED / ABORT.

**Открытия для стандарта (учтены в §2, §7):**

1. Кастомные subagents регистрируются **только** компонентом `agents` плагина;
   standalone `~/.zcode/agents/` игнорируется (symlink-подход провалился живым тестом).
2. Правки плагина не hot-reload: bump version → refresh рынка → Update → новая сессия.
3. `/tmp` очищается при перезагрузке — временные артефакты скиллов нежизнеспособны
   между сессиями (для adversarial-review это штатно:cleanup и так обязателен).

### Фаза III, продолжение (29.09) — сам hub под git (задача 20260929-hub-under-git)

Последняя неверсионируемая точка кластера устранена: каталог `it/zcode` (концепция,
техпроект, ADR, шаблоны, плагин, аудит) поставлен под git по стандарту, задача
`.zcode/tasks/20260929-hub-under-git.md` (done).

- `main` — бутстрап `418ffd9` (`.gitignore`, `.zcode/project.yaml` name `zcode-hub`,
  `AGENTS.md` L1); ветка `feature/hub-under-git` — импорт 21 источника без правок
  (`b8de175`) + контекст и закрытие задачи.
- `adversarial-review-master/` (upstream-импорт, собственный репозиторий) исключён
  через `.gitignore` — в git hub не входит; скан на секреты перед первым коммитом — чисто.
- Remote создан пользователем вручную: `git@github.com:Es1688/ZCode-Engineering-Hub.git`
  (приватный; второй репозиторий кластера с remote после `Es1688/CMR`). Squash-merge
  и первый push — по подтверждению (Level C).
- Открытым остаётся: push остальных 5 репозиториев (нужен `gh` CLI либо ручное создание).

### Фаза III завершена (01.10) — hub-guard внедрён; окончательный макет

- **Слой принуждения (hooks-политика §6, пункт 3 плана):** эксперимент probe-hook дал
  факты 1–6 (в т.ч. deny работает в yolo; поля `mode`/`riskLevel` ненадёжны) — принято
  ADR-0002 `docs/adr/0002-hooks-enforcement.md`. Реализация `hooks/`: `guard.py`
  (18 правил G-* по Level 0, режимы off/shadow/enforce, `--report`/`--doctor`, fail-open),
  `install_guard.py` (dry-run, бэкап config.json), `test_guard.py` (132 автотеста).
  Внедрено в систему 01.10: установлен в `~/.zcode/hooks/guard`, стартовый режим —
  **shadow**; критерии перехода в enforce — ADR-0002 п.3. Внесено на main отдельными
  коммитами: `6a998b0` (запись ADR-001 о пилоте), `e15741d` (guard + ADR-0002).
- **ADR-001 дополнен 29.09 (поздняя запись):** пилот adversarial-review на реальном проекте
  (WebRTC-блокировка STUN/TURN, 8 файлов) — терминал ABORT провалидирован живьём (честный
  отказ при сбое диспетчеризации, WIP нетронут); причина сбоя — провайдер OpenRouter
  (баланс/ключ/rate-limit), проверяется в UI.
- **Кластер:** stelthVPN онбордингован по стандарту и запушен (`Es1688/stelthVPN`, к 30.09,
  ahead 0) — третий remote кластера; TG-MAX_bridge — bootstrap 29.09; полигон
  openrouter_chat 29.09 импортирован с файлами стандарта (статус полигона по решению
  28.09 сохраняется, не онбординговать). Без remote остались 6 репозиториев
  (5 исходных + TG-MAX_bridge).
- **Окончательный макет:** `ZCODE-HUB-LAYOUT.md` (as-built кластера на 01.10, задача
  `20261001-hub-final-layout`) — единственный источник истины по устройству Hub; концепция
  и техпроект — исторические документы, журналы продолжаются здесь. Фаза III закрыта;
  далее — Фаза IV по потребности и остаточная дорожная карта (макет §13).

### После Фазы III (09.10) — hub-guard: проба субагентов workflow

- **Открытый вопрос №2 ADR-0002 (видимость) закрыт пробой:** прогон
  `dwfrun-64bad652` (динамический workflow, два параллельных субагента, маркеры
  `guard-probe`) — PreToolUse-hook видит вызовы субагентов workflow: 5/5 проб в
  `guard.jsonl` с ожидаемыми правилами (G-READ-SECRET, G-PUSH, G-PIPE-TO-SHELL,
  G-WRITE-OUTSIDE×2; решения ask×4/deny×1, `effective=allow` в shadow), 0
  внутренних ошибок при параллельной работе. SID субагентов атрибутируются
  отдельно от родительской сессии (`ctor_1_1`/`ctor_2_1`) — в `--report` видны
  как отдельные сессии. Не проверено: блокировка в `enforce`, субагенты
  инструмента Agent, `ask` (тест C). ADR-0002 дополнен (вопрос №2 сужен). До
  перевода в enforce остаётся критерий (г) — тест `ask`
  (задача 20261009-guard-subagent-probe).

---

## Приложение А. `~/.zcode/AGENTS.md` (Level 0) — установлен 28.09.2026

Намеренно короткий: инжектится в каждую сессию. Изменения — через ADR.

```markdown
# Global Engineering Rules — Level 0

## Язык
- Общение и документация — на русском; код, идентификаторы, commit-сообщения — на английском.

## Безопасность
- Никогда не выводи и не коммить секреты (API-ключи, токены, пароли, *.key, .env).
  Перед `git add` проверь .gitignore.
- Опасные операции (удаление вне проекта, rm -rf, DROP, изменение ~/.zcode, ~/.ssh,
  системных конфигов) — только после явного подтверждения пользователя.
- Конфиги и логи с ключами (~/.zcode/) не читать и не копировать без прямой задачи.

## Git
- git push, merge в main, release — только с явного разрешения пользователя.
- Коммит-сообщения: Conventional Commits (feat/fix/docs/refactor/test/chore), английский.
- Перед коммитом прогони тесты/линтер, если они есть; правила проекта — в .zcode/project.yaml.

## Проекты
- В каждом репозитории сначала прочитай AGENTS.md проекта (Level 1) и .zcode/project.yaml —
  их правила перекрывают эти.
- Эталонные/оригинальные данные (legacy-исходники, DATASTOR, REPORTS) не изменять.
- Вне текущего workspace (~/PROJECTS, системные каталоги) — только чтение, если явно
  не разрешено иное.

## Стиль работы
- Минимальные изменения в стиле существующего кода; комментарии — только для неочевидных
  ограничений.
- Закончи начатое: проверь результат; о пропущенных шагах и ошибках докладывай честно.
```

## Приложение Б. `.zcode/project.yaml` — пример для BUBBLES _jupiter

```yaml
version: 1
name: bubbles-jupiter
type: scientific-python
description: Порт BUBBLES (Turbo Pascal, 1996) на Python/Jupyter, физика 1:1

language: { name: python, version: "3.12" }
runtime: { env: conda:science, entry: BUBBLES.ipynb }

repository:
  platform: github            # назначается на шаге 2 дорожной карты
  default_branch: main
  strategy: github-flow

quality:
  test: notebook-validation   # ячейки валидации против REPORTS/VOSTOK/174D.DOC, порог 5e-4
  lint: null

validation:
  how: сравнение статистики и гистограмм с эталоном 174D.DOC
  forbidden: изменение физики, порядка вычислений и констант (AGENTS.md Level 1)

ai:
  allow_shell: controlled
  allow_git_push: confirm
  execution_mode: build
```
