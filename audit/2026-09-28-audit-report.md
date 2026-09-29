# Аудит ZCode — 28.09.2026 (ЭТАП 0)

Метод: только read-only команды (`ls`, `find`, `cat`, `cmp`, `pgrep`, `git status`) плюс официальный
гайд `zcode-guide:zcode-configuration-guide` из кэша плагинов. Единственное изменение по итогам —
`chmod 600` на два файла с API-ключами (раздел 7).

---

## 1. Установка и версия

| Параметр | Значение |
|---|---|
| Версия | **3.11.2** (актуальная на сайте — 3.14.3) |
| Способ установки | системный пакет (.deb): бинарник `/opt/ZCode/zcode` |
| Desktop-entries | системный `/usr/share/applications/zcode.desktop` + пользовательский `~/.local/share/applications/zcode.desktop` |
| Протокол ОС | `zcode://` (deep link) зарегистрирован на уровне ОС |
| CLI-флаг `--version` | отсутствует — вызов бинарника поднимает GUI; версия видна в логах (`[arms] ... version=3.11.2`) |
| Автообновление | выключено (`autoDownloadAndInstallUpdates: false`, `receivePreviewUpdates: false`) → обновление только вручную |
| Аутентификация | Z.ai Coding Plan через OAuth (`providerFamilyDomain: zai`), модели GLM-5.3 / GLM-5.3-Flash |
| Доп. провайдеры в config | OpenRouter (gemini-3.8-flash, gpt-5.3-codex) — настроены, ключ см. раздел 4 |

**Процессы.** Приложение запущено (~15 процессов: main, zygote, network/node-сервисы, `zcode-host-local-1`,
4× `zcode-cli`, `zcode-node-repl-mcp`). Это хост текущих сессий — закрывать нельзя. Опасение
«случайно поднятого фонового процесса» снято.

---

## 2. Карта конфигурации (сверено с официальным гайдом)

| Ресурс | User scope | Workspace scope | Сейчас |
|---|---|---|---|
| Инструкции AGENTS.md | `~/.zcode/AGENTS.md` | `<repo>/AGENTS.md` (поиск вверх от cwd до корня проекта) | user: **нет**; project: **2 из 7** |
| MCP / hooks / состояние плагинов | `~/.zcode/cli/config.json` | `<repo>/.zcode/config.json` (или `zcode.json`) | **оба отсутствуют** |
| Skills | `~/.zcode/skills/`, `~/.agents/skills/` | `<repo>/.zcode/skills/`, `.agents/skills/` | **ни одного своего** |
| Commands | `~/.zcode/commands/`, `~/.agents/commands/` | аналогично | **нет** |
| Плагины | маркетплейсы → кэш `~/.zcode/cli/plugins/cache/` | — | 8 в кэше, 2 маркетплейса |

Правила слияния (из гайда): user-скоуп перекрывает workspace; одноимённые skills/commands —
первый по порядку обнаружения выигрывает; **workspace-MCP теперь подключаются автоматически**
(«открывайте только те workspaces, которым доверяете»); hooks требуют `hooks.enabled: true`;
события хуков — ровно семь (`SessionStart` … `Stop`).

Активные skills сейчас — только от официальных плагинов: `browser-use`, `document-skills`
(docx/pdf/pptx/xlsx), `skill-creator`, `zcode-guide`. Дополнительно в кэше: android-emulator,
computer-use, ios-simulator, restore-legacy-sessions. Маркетплейсы: официальный CDN ZCode +
`anthropics/claude-plugins-official` (GitHub).

**Вывод:** вся extension-поверхность (правила, skills, MCP, hooks) — чистый лист. Строить
Engineering Hub можно с нуля, ничего не ломая. `~/.claude` и `~/.agents` отсутствуют —
мигрировать нечего.

---

## 3. Где ZCode хранит состояние (модель workspace)

| Путь | Что это |
|---|---|
| `~/.zcode/v2/` | состояние десктоп-приложения: `setting.json` (UI, recentProjects, dataBaseDir), `config.json` (провайдеры/модели/ключи), `credentials.json` (0600), `tasks-index.sqlite`, `certs/`, `crash/`, `logs/` |
| `~/.zcode/cli/` | рантайм агента: `agents/` (транскрипты 11 сессий), `artifacts/`, `exec/` (52 записи), `rollout/` (model-io `*.jsonl`), `db/db.sqlite`, `plugins/` |
| `~/.zcode/workspace/default/` | пусто |
| `~/.zcode/plugin-workspace/` | пусто |
| `/home/egor/work/.zcode/v2/` | **полная копия v2-состояния** (config.json побайтно идентичен глобальному), потому что `setting.json → dataBaseDir: /home/egor/work`; активная база задач — именно здесь (sqlite-WAL пишется) |
| `<repo>/.zcode/plans/` | авто-каталоги plan-файлов сессий (найдены в BUBBLES _jupiter, ohotskoe, Kutuncev); иной project-конфигурации нет |

Ответ на вопрос ЭТАПА 0 п.4: workspace = папка, выбранная при открытии проекта. Её путь попадает в
`dataBaseDir` / `lastWorkspaceSession`, под неё дублируется v2-состояние, а `AGENTS.md` ищется
вверх от текущего каталога до корня репозитория. В текущем workspace `/home/egor/work` AGENTS.md
нет — сессии в нём работают **без каких-либо кастомных инструкций**.

---

## 4. Безопасность

### Находки

1. **[СРЕДНЕ] API-ключи открытым текстом, права 0664.** `~/.zcode/v2/config.json` и идентичная
   копия `/home/egor/work/.zcode/v2/config.json` содержали три ключа: Z.ai Coding Plan API key,
   JWT-токен (start-plan) и ключ OpenRouter (используется в двух провайдерах). Файлы были читаемы
   группой (rw-rw-r--). Значения в отчёт не выносятся. → **исправлено 28.09: chmod 600** (раздел 7).
2. **[СРЕДНЕ] Web remote control через внешний relay.** В `setting.json`:
   `webRemoteControlExternalRelayDevice` (deviceSid `d_6Gf…`) + `webRemoteControlLastEnabledContext`
   (workspace Kutuncev, сессия sess_05c…). Если функцией не пользуетесь — отключить в настройках.
3. **[НИЗКО] Deep-link `zcode://` OS-wide** — любой сайт/приложение может пытаться открыть
   zcode-ссылки.
4. **[НИЗКО] Remote crash reporter включён** (`remoteCrashReporterEnabled=true`, staging
   `~/.zcode/v2/crash/live`) — телеметрия вендору.
5. **[ИНФО] Локальный след диалогов:** `~/.zcode/cli/rollout/*.jsonl` — полный протокол обмена с
   моделями лежит на диске в открытом виде.
6. **[ХОРОШО]** `credentials.json` 0600; `embeddedBrowserAllowInsecureCertificates: false`;
   `memoryEnabled: false`; `modelIoFullRetentionEnabled: false`.

---

## 5. Инвентаризация проектов

### Новый корень `/home/egor/work` (структурирован 07.09.2026)

- `it/projects/t-invest-skill-main`
- `science/projects/BUBBLES`, `science/projects/BUBBLES _jupiter`, `science/projects/ohotskoe`
- `it/kwork/ggsell`, `it/kwork/Kutuncev`
- `it/zcode/adversarial-review-master` + `ZCode Engineering Hub.md` (концепция Hub)
- `experiments/`, `tools/` — пустые заготовки

### Старый корень `/home/egor/PROJECTS` — ~35 каталогов

`openrouter`, `openrouter_chat`, `openrouter-agents-python`, `stelthVPN`, `VPN`,
`telegram_project`, `tg_project`, `tg_shop_bot`, `AdminBot`, `AgentAI`, `TRADE`, `FIN`, `WB`,
`n8n`, `SEISMIC`, `Wedding_planer`, `YANDEX`, `cursor` и др. В `lastWorkspaceSession` остались
следы уже не существующего `/home/egor/PROJECTS/ZCODE/{BUBBLES,restic,stelthVPN}` — была
реструктуризация. **Вывод: миграция PROJECTS → work не завершена (перенесено ~20%). Engineering
Hub должен либо доесть миграцию, либо явно охватить оба корня.**

### Git-состояние (7 проектов work/) — главная находка аудита

| Проект | Git | Ветка | Последний коммит | Незакоммичено | Remote |
|---|---|---|---|---|---|
| BUBBLES _jupiter | да | develop | 2026-09-14 c9ebce8 | 8 файлов | **нет** |
| Kutuncev | да | develop | 2026-09-25 70f8164 | 1 файл | **нет** |
| t-invest-skill-main | **нет** | — | — | — | — |
| BUBBLES | **нет** | — | — | — | — |
| ohotskoe | **нет** | — | — | — | — |
| ggsell | **нет** | — | — | — | — |
| adversarial-review-master | **нет** | — | — | — | — |

**Только 2 из 7 проектов под git, и у обеих репозиториев нет remote (нет бэкапа).** Это прямое
противоречие концепции «Git как центральный протокол» — первоочередной кандидат на Фазу I.

---

## 6. AGENTS.md — текущее состояние и эталон

- **User scope** `~/.zcode/AGENTS.md` — отсутствует (путь верный, файла никогда не было).
- `adversarial-review-master/AGENTS.md` — англоязычный ориентир для агентов по стороннему
  skill-репо (оркестрация Claude Code + Codex). Изучается как референс.
- `BUBBLES _jupiter/AGENTS.md` — **эталонный образец Level-1 project-правил**: цель, таблица
  «что нельзя менять», правило 1:1 с Pascal-оригиналом (порядок вычислений, константы), протокол
  валидации (порог ~5e-4), соглашения по данным. Рекомендация: взять этот формат за стандарт.

---

## 7. Действия по итогам аудита (28.09.2026)

1. `chmod 600` на `~/.zcode/v2/config.json` и `/home/egor/work/.zcode/v2/config.json` — **выполнено**.
2. Настоящий отчёт — **выполнено**.
3. Иное — сознательно отложено (см. раздел 8).

## 8. Открытые вопросы → следующие шаги

1. ~~**Execution Modes** — проверить в UI~~ — **закрыто 28.09 без UI**: режимы найдены в БД, см. §9.
2. **Git-бэкап** — единственные два репозитория без remote: создать приватные репозитории и
   запушить (решение о платформе за вами).
3. **Git для остальных 5 проектов** — инициализация по единому стандарту (Фаза I).
4. **Миграция `~/PROJECTS`** — доесть / заморозить / охватить оба корня.
5. **`~/.zcode/AGENTS.md`** (Level 0: язык, секреты, git-политика, стиль) — содержание согласовать.
6. **MCP-политика** (Tier 1–3) — пока подключён только встроенный `zcode-node-repl-mcp`.
7. **Обновление 3.11.2 → 3.14.3** — вручную, когда решите.

---

## 9. Execution Modes — расследовано из БД (добавлено 28.09, позднее)

Пункт «проверить в UI» закрыт без UI: режимы хранятся в `~/.zcode/cli/db/db.sqlite`
(таблица `local_setting` — sticky-режим per-project; колонка `session.permission` — per-session;
таблица `permission` для явных allow/deny-правил — **пуста**).

**Найденные режимы:** `plan` (чтение + план), `build` (контролируемое исполнение с подтверждениями),
`yolo` (автоподтверждение всего).

**История 57 сессий: `yolo` — 24 (42%), `build` — 17, `plan` — 16.**

Текущие per-project режимы: почти все проекты — `plan`; `build` — оба BUBBLES; `work` — `plan`
(переключён в plan в ходе этого аудита).

Выводы для политики Level A–D: yolo — самый частый режим в истории, при этом формальных
allow/deny-правил нет вообще; рабочий режим по умолчанию целесообразно перевести в `build`,
`yolo` ограничить изолированными экспериментами (детали — в техпроекте `ZCODE-HUB-DESIGN.md`, §6).
