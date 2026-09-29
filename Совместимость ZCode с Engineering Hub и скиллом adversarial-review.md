# ADR-001: Совместимость ZCode с Engineering Hub и скиллом adversarial-review

- **Статус:** Accepted (вариант B реализован и живьём провалидирован 2026-09-29: плагин-доставка, BYOK-ревьюер, 2 раунда протокола; см. журнал)
- **Дата:** 2026-09-29
- **Область:** архитектура хаба, порт скилла `adversarial-review` (SKILL.md + runner.md)
- **Владелец решения:** ________
- **Проверенная версия ZCode:** 3.14.3-7762 (desktop, нативный Linux)

---

## 1. Контекст

Нужно встроить в ZCode (Agentic Development Environment от Z.ai) архитектуру Engineering Hub и скилл `adversarial-review`, написанный для Claude Code. Скилл использует: Agent tool + subagent, `codex exec` через Bash, `/tmp`, bwrap, `sha256sum`, определение Plan Mode по системному сообщению Claude Code, поиск `runner.md` в `~/.claude/...`.

## 2. Что подтверждено документацией ZCode

Источник: zcode.z.ai/en/docs (Skill, Plugin, Subagents, Hooks, Safety Confirmation, FAQ), версия ~3.14.

| # | Факт | Влияние |
|---|------|---------|
| F1 | Скиллы: `~/.zcode/skills/<name>/SKILL.md` (глобально), `<workspace>/.zcode/skills/<name>/SKILL.md` (проект) | Раскладка хаба |
| F2 | В плагине скиллы только в плоской раскладке `skills/<name>/SKILL.md`; вложенные группирующие папки не видны агенту | Категории кодировать в имени: `git-review` |
| F3 | Обязательные поля frontmatter: `name`, `description`; `description` ≤ 1024 симв. (иначе скилл отбрасывается); тело > 100 КБ обрезается; лишние поля игнорируются | `user_invocable` безвреден |
| F4 | Метаданные всех включённых скиллов делят один бюджет контекста; при переполнении остаются только имена | Держать включёнными только нужные скиллы |
| F5 | Вызов: `$skill-name` или `/`; команды (`commands/*.md`) поддерживают `$ARGUMENTS`, `skills:` | Тонкий command-файл для аргументов |
| F6 | Импорт скиллов из Claude Code / Codex CLI / Windsurf и др. (symlink или copy, global или project) | Быстрый первый тест |
| F7 | Плагин = skills + commands + agents + hooks + `.mcp.json`; маркетплейс из GitHub / git URL / локальной папки; версия обновления берётся из `marketplace.json` | Хаб = маркетплейс плагинов |
| F8 | Subagents: Agent tool; встроенные `general-purpose` (все инструменты) и `Explore` (read-only); кастомные — `~/.zcode/agents/*.md` или `agents/` в плагине; поля `model`, `thoughtLevel`, `tools`, `disallowedTools`, `maxTurns`, `injectAgentsMd`, `mcpServers` | Runner = кастомный subagent. **Коррекция 2026-09-29 (живой тест):** standalone `~/.zcode/agents/` в discovery НЕ входит; агенты регистрируются только как компонент `agents` плагина (эталон — `documents:visual-judge`), адресация — `<plugin>:<name>` |
| F9 | Кастомный список `tools` исчерпывающий: MCP-инструменты и вызов скиллов в subagent недоступны; subagent не может порождать subagent'ов | Runner: только `Bash, Read, Write, Grep, Glob` |
| F10 | Режимы: Ask before changes (по умолчанию), Edit automatically, Plan, Full access; решения Allow / Always allow / Reject / Always reject | Уровни A–D реализовать hooks'ами |
| F11 | Обычные вопросы агента автопродолжаются через 5 мин без ответа; запросы разрешений и утверждение плана ждут всегда | Гейт «структурных исправлений» через permission, а не вопрос |
| F12 | Hooks (7 событий); `PreToolUse` может allow/ask/deny (deny приоритетнее); hook получает `cwd`, `tool_name`, `tool_input` | Политика через hooks |
| F13 | **Project-level hooks не выполняются**; работают user-level (`~/.zcode/cli/config.json`, `hooks.enabled: true`) и hooks плагинов | Политику доставлять плагином |
| F14 | Плагинные процессы получают `ZCODE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_ROOT`; `SessionStart`-hook может добавить контекст (`additionalContext`) | Обход для путей к runner |
| F15 | Локальные skills / MCP / plugins не переносятся в SSH/WSL-workspace автоматически (кнопки Sync) | Учесть, если работа в WSL |
| F16 | Встроенный скилл `$zcode-configuration-guide` описывает расположение и приоритеты конфигураций (skills, commands, MCP, hooks, plugins, AGENTS.md) | Использовать для E12 |

## 3. Статус «не проверено» (обновлено 2026-09-29)

Закрыто этим прогоном:
- **Bash-лимиты** — проверены экспериментально (E4, E5): default timeout 120 000 мс, max 600 000 мс (из схемы инструмента); при явном timeout < max команда живёт в foreground до конца; при достижении max-таймаута вызов переводится в background (лог-файл + уведомление по завершении), а не убивается. Сторонний отчёт о «жёстком 5-минутном пороге с потерей жизненного цикла» (issue #194, CLI 3.11.x) для desktop 3.14.3 **не воспроизведён**.
- **Схема AGENTS.md** — закрыто через `$zcode-configuration-guide` (E21). `.zcode/rules/` не существует как концепция (в гайде отсутствует, каталога нет).
- **Memory, Wiki, Goal Mode, Automations, Idle-time Task, Task & File Management** — прочитаны, см. блок F.
- **Codebase Indexing** — функции с таким именем в доках 3.14 нет (ближайшее — Wiki, см. E24).

Осталось непроверенным:
- Живой импорт скилла, вызов с аргументами, бюджет метаданных (E1–E3) — UI-шаги (Settings → Import + Refresh).
- Поведение в Ask-before-changes (E10), Plan-mode запись (E14-часть), автопродолжение вопросов (E15) — интерактивные режимы.
- Кастомный runner-subagent (E12) — **закрыт 2026-09-29 (плагин)**: маркетплейс `dev-it-zcode` добавлен пользователем через UI, плагин установлен; живой dispatch `adversarial-review:adversarial-reviewer` в новой сессии успешен, BYOK-ревьюер (`openrouter/openai/gpt-5.3-codex`) вернул валидные ревью (2 раунда). Symlink-подход (`~/.zcode/agents/`) не работает — см. коррекцию F8.
- Качество ревью моделью-lead (E23) — **закрыто 2026-09-29 (смоук)**: ревьюер нашёл оба заложенных дефекта (high×2: проглоченные исключения → UnboundLocalError/чужие данные; delete-before-rename → потеря результата), prose на русском при англ. машинных литералах; lead верифицировал находки глубже ревьюера, применил фиксы, прогнал собственный эмпирический смоук-тест и вскрыл дополнительный дефект за рамками находок (ре-обработка `.processed`), честно раскрыв его ревьюеру в раунде 2. Раунд 2: новая валидная находка (окно truncate при записи); раунд 3: ещё две новые (symlink-утечка high — вне заложенных дефектов; потеря mode при mkstemp-публикации medium); max-severity high×3 — lead корректно классифицировал как сходимость (находки новые, не зацикливание). Финал цикла (APPROVED / Step 8 / Step 9) не наблюдался — по решению владельца валидация продолжится на первом реальном проекте.
- Плагин-механика (E16–E20) — **E16/E17 закрыты 2026-09-29**: локальный маркетплейс добавлен через UI (локальная папка `it/zcode/plugins`), плагин установлен из Personal; плоская раскладка `skills/adversarial-review/SKILL.md` видна, agents зарегистрированы, скилл вызван по аргументу `code`. E18–E20 (hook-политика) — не требуется для варианта B, отдельная задача. Политика доставки — только плагином (F13), что теперь единственный путь и для агентов.
- Живой MCP deny-тест (E22-практика); тиры read/write/execute в доках не описаны — проектировать через явный список инструментов и `disallowedTools`.
- **Установка Codex CLI ≥ 0.132.0 — единственный блокер варианта A** (E6: `codex` не найден, `~/.codex` отсутствует).

## 4. Эксперименты

Прогон 2026-09-29, ZCode 3.14.3-7762, desktop, нативный Ubuntu 24.04 (kernel 7.0.0-31-generic). Вердикт: ✅ ожидание подтверждено / ⚠ подтверждено частично / ❌ не подтверждено / — не проводился (причина).

### Блок A. Скилл как есть

| ID | Что проверить | Как | Ожидание | Факт | Вердикт |
|----|---------------|-----|----------|------|---------|
| E1 | Импорт без правок | Settings → Skills → Import (режим Copy, Project) → Refresh; посмотреть диагностику | Скилл виден; `description` ≤ 1024, тело ≤ 100 КБ | UI-импорт не проводился. Диагностика исходника (`adversarial-review-master/SKILL.md`, байт-в-байт равен копии в корне воркспейса): frontmatter корректный; `description` = 134 симв ≤ 1024; тело = 70 556 байт (≈69 КБ) ≤ 100 КБ; `references/runner.md` на месте. В ZCode скилл пока не установлен: в `~/.zcode/skills/` только 5 хабовских (git-finish-task, git-start-task, project-health, project-onboarding, zcode-doctor); в списке скиллов текущей сессии отсутствует | ⚠ (лимиты пройдены; сам импорт — за пользователем) |
| E2 | Вызов и аргументы | `$adversarial-review plan high sandbox:read-only` | Агент разбирает `plan/high/sandbox:` из текста | — (не проводился: скилл не импортирован; UI Import + Refresh) | — |
| E3 | Метаданные в бюджете | Включить весь набор скиллов, спросить «какие скиллы доступны» | Описание `adversarial-review` не теряется | — (не проводился: UI) | — |

### Блок B. Окружение и Bash

| ID | Что проверить | Как | Ожидание | Факт | Вердикт |
|----|---------------|-----|----------|------|---------|
| E4 | Длинная команда | Через агента: `sleep 400 && echo ok` с `timeout: 620000` | Выполняется в foreground до конца, вывод `ok`, код 0 | `sleep 400` с `timeout: 480000` (схема инструмента ограничивает max 600 000): foreground до конца, вывод `ok`, `exit=0`, ровно 400 с по таймстампам. Авто-ухода в background нет, пока timeout не достигнут | ✅ |
| E5 | Длинная команда > 10 мин | `sleep 660` | Завершается по таймауту, код 124 или ошибка, без «потери» задачи | `sleep 660` с `timeout: 600000` (max): вызов **сразу** вернулся как background-задача (task-ID + лог-файл; по завершении — уведомление). Команда доработала все 660 с (лог: 1790681892→1790682552), `exit=0` — не убита, не 124. Контроль: `sleep 5` с тем же `timeout: 600000` в background **не** уходит → срабатывание зависит от фактического достижения max-таймаута, а не от значения параметра. Lifecycle сохранён (лог + уведомление) | ⚠ (ожидание «124/ошибка» не подтвердилось; поведение мягче: auto-background с сохранением жизненного цикла) |
| E6 | Codex CLI | `codex --version` (≥ 0.132.0); `echo "say ok" \| codex exec --json -m <model> -s read-only -C <repo> -` | Первая строка JSONL содержит `thread_id` (UUID) | Codex CLI не установлен: `command -v codex` → NOT_FOUND, `~/.codex/sessions` отсутствует. Тест проводиться не мог | ❌ (блокер варианта A; нужна установка Codex CLI ≥ 0.132.0) |
| E7 | Окружение | `echo $PATH`, `which codex rg bwrap sha256sum`; `ls ~/.codex/sessions` | Все утилиты найдены | `bwrap`=/usr/bin/bwrap ✅, `sha256sum`=/usr/bin/sha256sum ✅, `rg`=/opt/ZCode/resources/tools/ripgrep/rg ✅ (поставляется вместе с ZCode), `codex` ❌, `node` ❌ (не в PATH). `~/.codex/sessions` нет (Codex никогда не запускался) | ⚠ (всё, кроме codex) |
| E8 | bwrap preflight | `bwrap --dev-bind / / --unshare-net /bin/echo ok` | Печатает `ok` (Linux/WSL). Иначе план: `sandbox:inherit` | Печатает `ok`, `exit=0` | ✅ |
| E9 | ОС | Указать: Windows / WSL / Linux / macOS; где запущен ZCode и где лежит репозиторий | Совпадает с тем, где доступны bwrap и `/tmp` | Нативный Ubuntu 24.04, kernel 7.0.0-31-generic x86_64 (`/proc/version` без признаков WSL/Microsoft). ZCode (deb 3.14.3-7762, /opt/ZCode) и репозиторий на одной машине; `/tmp` и bwrap доступны | ✅ |
| E10 | Права на команды | Запустить E6 в режиме Ask before changes | Показывается запрос; после «Always allow» повторно без запроса | — (не проводился: нужен интерактивный режим Ask before changes; в текущей автоматической сессии Bash-команды выполнялись без запроса разрешений) | — |

### Блок C. Subagent и режимы

| ID | Что проверить | Как | Ожидание | Факт | Вердикт |
|----|---------------|-----|----------|------|---------|
| E11 | Параметры Agent tool | Попросить агента запустить subagent с `subagent_type` и `model` | Понять, принимается ли `model` в вызове или только из файла агента | Схема Agent tool в 3.14.3: только `subagent_type`, `prompt`, `description`, `run_in_background`. Параметра `model` в вызове **нет** → модель задаётся только определением агента (файлом). (`subagent_model` существует лишь в dynamic-workflows — отдельный механизм) | ✅ (вопрос закрыт: model только из файла агента) |
| E12 | Кастомный runner | Создать `agents/codex-review-runner.md` (`tools: Bash, Read, Write, Grep, Glob`, `model: <id>`, `maxTurns: 30`); вызвать через `@` | Записывает файл результата, Bash-запросы разрешений доходят до пользователя | — (не выполнен: запись в `~/.zcode/agents/` по глобальным правилам требует явного подтверждения пользователя; каталог не существует. Альтернатива — `agents/` в плагине, но установка плагина — UI-шаг. Готов выполнить по подтверждению) | — |
| E13 | Foreground / background | Запустить runner дважды, оба раза убедиться, что главный агент ждёт результат | Ждёт (нужен foreground) | Синхронный вызов Agent tool (general-purpose, внутри `sleep 15`) заблокировал главный агент до возврата результата (duration 24 c). Foreground по умолчанию подтверждён; `run_in_background: true` — опция для ухода в фон | ✅ |
| E14 | Plan mode и temp | В режиме Plan записать файл в `/tmp` и в `<workspace>/.zcode/tmp/` | Понять, что блокируется | Вне Plan mode обе записи прошли (`/tmp` — ок, `<workspace>/.zcode/tmp/` — ок; тестовые файлы удалены). Plan-режим не проверялся — переключение режима за пользователем. Попутно: встроенный general-purpose subagent имеет доступ и к MCP-инструментам (в его списке есть `mcp__*`) — уточнение к F9 | ⚠ (половина вопроса закрыта) |
| E15 | Автопродолжение вопросов | Дать агенту вопрос-гейт, не отвечать > 5 мин | Ожидаем «Unanswered, auto-continued»; проверить, отключается ли в Settings → General | — (не проводился: требует неотвеченного взаимодействия с пользователем > 5 мин) | — |

### Блок D. Плагины, hooks, правила

| ID | Что проверить | Как | Ожидание | Факт | Вердикт |
|----|---------------|-----|----------|------|---------|
| E16 | Плоская раскладка | Плагин с `skills/git-review/SKILL.md` и, для негативного теста, `skills/git/review/SKILL.md` | Плоский виден, вложенный нет | — (не проводился: установка плагина — UI-шаг) | — |
| E17 | Локальный маркетплейс | Create → Add marketplace (папка) → Install | Компоненты появляются в Skills / Subagents / Hooks | — (не проводился: UI) | — |
| E18 | Hook-политика | Плагин с `PreToolUse` (matcher `Bash`): `git push` → ask, `danger-full-access` → deny | Срабатывает; deny приоритетнее allow | — (не проводился: UI/установка; по докам deny-правила и hard tool limits не обходятся hook-allow) | — |
| E19 | Hook читает project.yaml | Hook читает `<cwd>/.zcode/project.yaml` и принимает решение | Работает; `hooks.enabled: true` в user-конфиге | — (не проводился; напоминание F13: project-level hooks не выполняются, только плагин/user) | — |
| E20 | Путь к runner | `SessionStart` hook возвращает `additionalContext` с `ZCODE_PLUGIN_ROOT`; агент читает `references/runner.md` | Путь известен агенту | — (не проводился: UI) | — |
| E21 | AGENTS.md | `$zcode-configuration-guide`: где global/workspace AGENTS.md, порядок приоритета, `injectAgentsMd` | Записать схему приоритета | Из `$zcode-configuration-guide` (v0.3.0): user = `~/.zcode/AGENTS.md`, workspace = `<repo>/AGENTS.md` (поиск от cwd вверх до корня проекта). Инъекция: сначала user, затем workspace — workspace может сужать/перекрывать user-дефолты. Discovery скиллов/команд: explicit roots → `~/.zcode/skills|commands` → `~/.agents/skills` → workspace `.zcode/skills` (каждый уровень вверх по дереву) → `.agents/skills` → плагины; при совпадении имён побеждает первый по порядку (user приоритетнее workspace, плагины — ниже всех). `.zcode/rules/` не существует (в гайде отсутствует, каталога нет) | ✅ |
| E22 | MCP-ограничения | Подключить тестовый MCP; настроить deny на один инструмент (permission rule или PreToolUse `mcp__server__tool`) | Понять, как реализовать наши тиры | ⚠ по документации, без живого теста. Конфиги: user `~/.zcode/cli/config.json` → `mcp.servers`, workspace `<repo>/.zcode/config.json` → `mcp.servers`, fallback `*.agents/mcp.json` (ключ `mcpServers`; внутри scope `.zcode` приоритетнее, слияния нет). Workspace читается первым, но при конфликте имён побеждает user. Все scope (user/workspace/plugin/env/CLI) **авто-подключаются**. Построчные тумблеры серверов (`enable: false`). В `tools` сабагентов можно явно перечислять `mcp__<server>__<tool>` (wildcards `mcp__server__*` молча игнорируются), есть `disallowedTools`. Тиры read/write/execute в доках не описаны; `PermissionRequest`-hook умеет allow/deny/update permission rules; explicit deny, Plan-mode write bans, hard tool limits не обходятся hook-allow. Живой deny-тест не проводился | ⚠ (механика понятна на уровне доков) |

### Блок E. Качество и приватность

| ID | Что проверить | Как | Ожидание | Факт | Вердикт |
|----|---------------|-----|----------|------|---------|
| E23 | Модель-lead | Прогнать скилл на маленьком diff моделью GLM и моделью BYOK | Соблюдаются: verbatim-вывод ревью, матрица accept/reject, формат resume-промпта | — (не проводился: скилл не установлен, воркспейс — не git-репозиторий) | — |
| E24 | Egress | Settings: Codebase Indexing и телеметрия; что отправляется | Для приватных проектов индексирование выключено | ⚠ по докам: функции «Codebase Indexing» в доках 3.14 нет. Ближайшее — Wiki: для генерации код-контекст уходит в выбранный модель-сервис, результат хранится локально (`~/.zcode/v2/repo-wiki/<hash>/wiki.json`), авто-обновление только если wiki уже существует. Телеметрия: Optimization Program выключена по умолчанию, отключается Settings → General; device-id в `~/.zcode/v2/telemetry-state.json`; Memory «ничего не загружает». Настройки UI в этой сессии не осматривались | ⚠ |
| E25 | Remote/WSL | Sync Skill / Plugin / MCP в WSL-workspace | Скилл и runner доступны в WSL | N/A: WSL не используется (E9 — нативный Linux). На будущее (доки): Sync доставляет только user-level скиллы/MCP/плагины; project-level skills, workspace- и plugin-MCP не синкаются; MCP-секреты пишутся на remote as-is | N/A |

### Блок F. Документация (чтение)

Прочитано 2026-09-29 (zcode.z.ai/en/docs, ~3.14), двумя фоновыми агентами.

| Страница | Что даёт | Пересечение с хабом (Knowledge / Onboarding / Health / Doctor / Task) | Решение (использовать / игнорировать / дополнить) |
|----------|----------|--------------------------------------------------------------------|---------------------------------------------------|
| ADE Tools (…/docs/ADE-tools) | UI-возможности ADE: списки воркспейсов/задач, Command Center, встроенный браузер, превью, терминал, фоновой запуск команд агентом («команда продолжает работать, ход не ждёт»; сабагенты тоже поддерживают background). Это НЕ справочник инструментов — лимиты Bash в доках не описаны (взяты из схемы инструмента и E4/E5) | Терминал/background-режим для runner | **дополнить** — фоновое execution использовать для раундов > 10 мин (уведомление + лог), лимиты брать из схемы инструмента |
| MCP (…/docs/mcp-services) | Конфиги user/workspace + fallback `.agents/mcp.json`, приоритеты, авто-подключение всех scope, построчные тумблеры, импорт из Claude/Codex/OpenCode | Тиры MCP, права | **дополнить** — тиры делать явным перечислением `mcp__server__tool` в `tools` + `disallowedTools`; конфиг держать в workspace `.zcode/config.json` |
| Commands (…/docs/commands + …/docs/plugin) | `commands/*.md`: frontmatter (`description`, `argument-hint`, `allowed-tools`, `model`, `skills`), `$ARGUMENTS`/`$1`/`$2`, имя файла `^[a-z0-9][a-z0-9_:-]{0,63}$`, вызов `/name`; «Command — простой сохранённый промпт, Skill — полный метод» | Тонкая обёртка скилла | **использовать** — command-файл с `$ARGUMENTS` и `skills: adversarial-review` для разбора `plan/high/sandbox:` |
| Memory (…/docs/memory) | Авто-память по проектам (4 категории фактов), локальные markdown в `~/.zcode/cli/memories/projects/<project>/…`, включается в Settings → General, ничего не загружает наружу | Knowledge | **дополнить** — нижний авто-слой (предпочтения, слабые места агента); каноническая база знаний остаётся в хабе (память не версионируется в git, нет UI) |
| Wiki (…/docs/repo-wiki) | AI-гид по репо (модули, потоки, точки расширения, Mermaid), генерация по кнопке, авто-обновление; хранится локально одним JSON вне репо | PROJECT_MAP / Onboarding | **дополнить** — черновик/ускоритель для PROJECT_MAP.md; итог переносить в репозиторий (машино-локально, без истории) |
| Goal Mode (…/docs/goal) | `/goal <цель>`: агент сам крутит раунды до подтверждения «реальными уликами» (файлы, вывод команд, тесты); незакрытые todo блокируют | Цикл ревью | **использовать** — цель формулировать из acceptance criteria задачи Level 2; длинные механические итерации — Goal Mode, ревью/принятие — за хабовским циклом |
| Automations (…/docs/automations) | Пресетные расписания (Hourly…Monthly + Custom), задача = инструкция + локальный проект + режим полномочий + модель; read-only шаблоны (Daily risk scan, Weekday standup digest); лимит 20 задач, только локальные воркспейсы | Project Health | **использовать** — рутинные проверки здоровья по расписанию; флагманские doctor-прогоны — в хабе (лимит 20) |
| Idle-time Task (…/docs/idle-time-tasks) | Отложенные задачи в глобальную очередь, бесплатное выполнение в простой, без обещанного времени старта; требует активной Coding Plan подписки | Doctor-прогоны, черновики PROJECT_MAP | **использовать** — сбрасывать туда разовые аудиты и черновики карт проектов |
| Task & File Management (…/docs/task-management) | UI-сессии задач (группы/поиск/авто-архивация), дерево файлов с git-статусами, фильтр «Show changed files only», drag-and-drop файлов в чат, Git Graph | Task-контекст | **дополнить** — UI не заменяет версионируемый контекст Level 2 в репо; «changed files only» использовать на ревью, файл задачи таскать в чат |
| Remote Development (…/docs/remote-development) | SSH/WSL/Docker-воркспейсы: агент, терминал, git — в целевой среде; ничего не синкается автоматически; Sync Skill/MCP/Plugin — только user-level; project-level skills, workspace/plugin MCP — вне синка; MCP-секреты на remote as-is | WSL/SSH sync | **игнорировать** (пока) / учесть — сейчас не используется; при появлении SSH-воркспейса скилл доставлять плагином или руками |

## 5. Варианты портирования

**Вариант A. Порт «как есть» с Codex CLI.** Runner = кастомный subagent (или скрипт). Ревьюер = Codex. Сохраняется протокол; зависимости: Codex CLI, bwrap, `/tmp`.
Подходит, если E4–E8, E12, E13 подтверждены.

**Вариант B. Нативный.** Ревьюер = кастомный subagent другой модели через BYOK (`tools: Read, Grep, Glob`, при необходимости `Bash` для тестов). Без Codex CLI и bwrap. Минусы: нет resume сессии (история передаётся в каждом раунде), тот же харнесс.
Подходит, если E4–E8 не подтверждены (нет Linux/WSL, Bash-лимиты).

**Критерий выбора:** если E4, E6, E8, E12, E13 = ✅ → A; иначе → B.

**Промежуточный итог прогона 2026-09-29:** E4 ✅, E8 ✅, E11 ✅ (model только из файла агента), E13 ✅, E5 ⚠ (auto-background при max-timeout, но с сохранением lifecycle), E12 — (нужно подтверждение записи в `~/.zcode/agents/`), E6 ❌ (Codex CLI не установлен — единственный блокер A). Linux/bwrap/`/tmp`/subagents готовы к варианту A; вариант B доступен немедленно и без внешних зависимостей. Рекомендация: выбирать A только при готовности установить Codex CLI; иначе стартовать с B.

## 6. Решение

- Выбранный вариант: **B — нативный сабагент-ревьюер** (владелец решения подтвердил 2026-09-29)
- Обоснование (ссылки на ID экспериментов): E6 ❌ — Codex CLI не установлен, единственный блокер варианта A; B доступен немедленно и без внешних зависимостей (среда Linux/`/tmp`/subagents готова: E4 ✅, E8 ✅, E9 ✅, E13 ✅, но для B не требуется). Ревьюер — BYOK-модель `openrouter/openai/gpt-5.3-codex` (OpenRouter, настроена 2026-09-29): другое семейство, чем lead-модель GLM. Реализация — локальный плагин `it/zcode/plugins/adversarial-review/` (+ `plugins/marketplace.json`, маркет `dev-it-zcode`): `skills/adversarial-review/SKILL.md` (хирургический, EN, 43 КБ) + `references/prompts.md` + `agents/adversarial-reviewer.md` (read-only: `[Read, Grep, Glob]`) + `agents/adversarial-reviewer-exec.md` (+ Bash, `sandbox:workspace-write`) + `commands/adversarial-review.md` + `PORT.md`. Доставка — установка плагина через UI (после провала symlink-подхода, см. E12)
- Изменения в скилле (заполнить по результатам):
  - [x] Раскладка: плоские имена скиллов
  - [x] Замена Plan Mode-детекта (формулировка ZCode «Plan mode is active» совпадает)
  - [x] Замена `subagent_type/model` на кастомный агент (model фиксируется в файле агента — E11)
  - [x] Замена путей `~/.claude/...` на `~/.zcode/skills/...` (резолв `references/prompts.md`, 2 тира)
  - [x] Временные файлы: `/tmp` сохранён с префиксом `ar-*` (E14); в Plan mode — инлайн-body, без записи
  - [x] Гейт структурных исправлений: batch-pause сохранён (Step 6.3 порта)
  - [x] Ограничение `description` ≤ 1024 (369 симв.)
  - [x] Вынос промптов в `references/` (`references/prompts.md`; роль ревьюера — в файлах агентов)

## 7. Последствия и риски

- Политика (уровни A–D) реализуется только hooks плагина (F13).
- Два внешних получателя кода (вариант B): Z.ai (lead-модель) и OpenRouter/OpenAI (ревьюер `openrouter/openai/gpt-5.3-codex`). Флаг `external_model_allowed` обязателен.
- Скиллы и кастомные агенты подхватываются при старте сессии: после установки или правки agent-файлов нужен перезапуск сессии ZCode (подтверждено живым вызовом Agent tool).
- **Кастомные агенты доставляются только плагином** (компонент `agents`, адресация `<plugin>:<name>`); standalone `~/.zcode/agents/` не читается — эмпирическая коррекция F8. Правки исходника плагина не hot-reload: bump версии → refresh рынка → Update → новая сессия.
- Вариант B: нет resume — каждый раунд ≥ 2 несёт полную историю раундов в промпте; стоимость растёт с числом раундов (компенсация — полная независимость ревьюера от контекста lead'а).
- Ревьюер по умолчанию физически read-only (исчерпывающий `tools: Read, Grep, Glob`, F9) — сильнее программной защиты мастера; exec-вариант (+ Bash) защищён prompt-запретом + обязательными снапшотами мутаций.
- Beta-статус кастомных subagents: возможны изменения.
- Версионная привязка: ZCode обновляется часто (3.14.x); фиксируйте проверенную версию: **3.14.3-7762** (проверено 2026-09-29).
- Раунды ревью > 10 мин (max timeout 600 000 мс) автоматически уходят в background: протоколу runner'а нужно уметь ждать уведомление и читать лог-файл (E5), а не рассчитывать на синхронный вывод.
- Уточнение к F9: встроенный general-purpose subagent в 3.14.3 имеет доступ к MCP-инструментам; ограничение действует для кастомных агентов с исчерпывающим `tools`-списком, при этом `mcp__<server>__<tool>` можно перечислять явно, wildcards игнорируются (E14/E22).

## 8. Журнал

| Дата | Версия ZCode | Кто | Что сделано |
|------|--------------|-----|-------------|
| 2026-09-29 | 3.14.3-7762 (desktop, Linux) | ZCode-агент (GLM-5.3), автозапуск | Проведены E4, E5, E7, E8, E9, E11, E13, E14 (частично), E21, E22 (по докам), E24 (по докам); блок F прочитан (10 страниц доков); E1 закрыт диагностикой исходника (лимиты пройдены). Не проводились (UI/интерактив/подтверждение): E2, E3, E10, E12, E15–E20, E23; E25 — N/A (нет WSL). Блокер варианта A: Codex CLI не установлен (E6). Разделы 3, 5, 7 обновлены по результатам |
| 2026-09-29 | 3.14.3-7762 (desktop, Linux) | ZCode-агент (GLM-5.3), по плану, утверждённому владельцем (вариант B, BYOK до интеграции, хирургический EN-порт) | Реализован вариант B: порт `it/zcode/adversarial-review-zcode/` (SKILL.md 43 КБ ≤ 100 КБ, description 369 ≤ 1024; `references/prompts.md`; `agents/adversarial-reviewer.md` read-only + `adversarial-reviewer-exec.md` с Bash, `model: openrouter/openai/gpt-5.3-codex`, BYOK настроен пользователем; command-обёртка; `PORT.md`). Установлено в `~/.zcode/{skills,agents,commands}` symlink'ами (подтверждено планом). Проверено: лимиты E1-формата, читаемость через symlink, протокольная симуляция (REVIEW_ID, diff-канал `ar-diff-*.patch`, снапшоты). Не проверено (требуют новой сессии): discovery скилла/агентов и живой раунд через BYOK — Agent tool текущей сессии кастомный тип не видит (попытка зафиксирована); смоук-репо `/tmp/ar-smoke-repo` подготовлено. Разделы 3, 6, 7 обновлены |
| 2026-09-29 | 3.14.3-7762 (desktop, Linux) | ZCode-агент (GLM-5.3); диагноз по live-транскрипту пользователя | **Смоук в новой сессии: скилл/команда/prompts.md/diff-канал/снапшоты работают; dispatch агента провалился** (`Agent type 'adversarial-reviewer' not found`) при валидном файле. Диагноз: `~/.zcode/agents/` не входит в discovery (коррекция F8) — агенты только через плагин (эталон `documents:visual-judge`: frontmatter `name/description/model/thoughtLevel/tools` YAML-списком, адресация `<plugin>:<name>`). Исправление: порт переструктурирован в локальный плагин `it/zcode/plugins/adversarial-review/` + `marketplace.json` (`dev-it-zcode`); SKILL.md переведён на namespaced dispatch (`adversarial-review:adversarial-reviewer[-exec]`) и новый резолв prompts.md; symlink-установка из `~/.zcode` удалена (возвращено исходное состояние). Разделы 2 (F8), 3 (E12, E16/E17), 6, 7 обновлены |
| 2026-09-29 | 3.14.3-7762 (desktop, Linux) | ZCode-агент (GLM-5.3); live-транскрипты пользователя (смоук, 2 раунда) | **Смоук-валидация успешна (E12, E16, E17, E23 закрыты; E1–E3 частично)**: пользователь установил плагин через UI (Add Marketplace `it/zcode/plugins` → Install). Live-прогон `/adversarial-review code` в `/tmp/ar-smoke-repo`: скилл и command из плагина, dispatch `adversarial-review:adversarial-reviewer` через BYOK (`openrouter/openai/gpt-5.3-codex`) успешен; раунд 1 — REVISE, 2×high (оба заложенных дефекта найдены; prose RU, литералы EN); lead: матрица, верификация глубже ревьюера, эмпирический смоук-тест (вскрыл доп. дефект за рамками находок — раскрыт ревьюеру), verbatim-вывод, снапшоты чистые (включая ожидаемый exit 1 от sha256sum без plan-файла); раунд 2 (full-history) — REVISE, 1×high (новая валидная находка: окно truncate при записи), severity убывает. Ожидается финал цикла (раунд 3 / APPROVED, Step 8, Step 9 cleanup) — механический. Разделы 3 (E12, E16/E17, E23), статус обновлены |
| 2026-09-29 | 3.14.3-7762 (desktop, Linux) | live-транскрипт пользователя (смоук, раунды 2–3) | Раунд 2: fix staging (mkstemp+fsync+os.replace, исходник удаляется после публикации) верифицирован симуляцией сбоя записи; раунд 3 ревьюера — REVISE, high (symlink-утечка: isfile/open следуют по симлинкам — вне заложенных дефектов) + medium (mkstemp 0600 теряет mode исходника); lead: re-scope #1 (полный запрет симлинков → realpath-контейнмент избыточен; O_NOFOLLOW отвергнут за непереносимость), accept #2 (chmod mode на temp до публикации), 4-тестовая верификация; max-severity high×3 — осознанно продолжен без паузы (находки новые — сходимость, не зацикливание; допустимо, сигнал мягкий). Терминальный статус (APPROVED / Step 8 / Step 9 cleanup) не наблюдался — по решению владельца валидация продолжится на первом реальном проекте. Непроверенное живьём до пилота: exec-ревьюер (`sandbox:workspace-write`), режимы plan / code-vs-plan, >50 файлов, Plan-mode инлайн-путь, терминалы NOT VERIFIED / ABORT |
