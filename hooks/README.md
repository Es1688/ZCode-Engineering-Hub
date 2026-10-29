# Hub guard: боевой hook (shadow → enforce)

Реализация ADR-0002. Один hook `PreToolUse`, который применяет правила Level 0 во всех режимах ZCode. Сначала работает в режиме **shadow**: ничего не блокирует, только пишет в журнал, что бы заблокировал.

## Файлы

| Файл | Назначение |
|---|---|
| `guard.py` | движок правил + подкоманды `--report`, `--doctor` |
| `install_guard.py` | установка / настройка / удаление (dry-run по умолчанию, бэкап `config.json`) |
| `test_guard.py` | 132 автотеста во временном `HOME`, реальные файлы не трогает |
| `ADR-0002-hooks-enforcement.md` | решение, правила, критерии перехода, ограничения |

## Установка (выполняете вы: это правка `~/.zcode`)

```bash
python3 test_guard.py                 # самопроверка, ожидается "0 failed"
python3 install_guard.py              # dry-run
python3 install_guard.py --apply      # shadow-режим
```

Перезапустите ZCode, затем:

```bash
python3 ~/.zcode/hooks/guard/guard.py --doctor
```

`doctor` должен показать `hooks.enabled=True`, `guard registered: True` и 0 строк `config.file.invalid / hook.run.failed`. Тестовый guard пробы (`BLOCKME`) к этому моменту лучше убрать: `python3 install_probe.py --apply --guard off` в папке пробы. Наблюдатель `probe_hook.py` можно оставить.

## Работа в shadow

Работайте как обычно 7+ дней. Раз в день-два:

```bash
python3 ~/.zcode/hooks/guard/guard.py --report 7
```

Отчёт показывает по правилам: сколько раз сработало, в скольких сессиях и примеры команд, а также программы из пропущенных вызовов Bash (проверка охвата) и неизвестные инструменты. Для каждого правила решите: срабатывание **верное** (оставить) или **ложное** (нужно подправить; пришлите примеры, я скорректирую правило).

Журнал: `~/.zcode/hooks/guard/guard.jsonl` (права 600).

## Настройка (`~/.zcode/hooks/guard/guard.json`)

| Ключ | Значение |
|---|---|
| `mode` | `off` / `shadow` / `enforce` |
| `ask_supported` | `true` только после успешного теста `ask`; иначе `ask` исполняется как `ask_fallback` |
| `ask_fallback` | `deny` (по умолчанию) или `allow` |
| `allow_once_ttl_min` | срок действия токена Level C |
| `write_allow_roots` | каталоги вне workspace, куда запись разрешена (`/tmp`, `/var/tmp`) |
| `strict_fs_root` | жёсткая граница ФС: чтение вне этого корня блокируется (пусто = выключено) |
| `read_allow_roots` | каталоги вне `strict_fs_root`, чтение которых разрешено (`/tmp`, `/var/tmp`) |
| `protected_data_names` | имена каталогов эталонных данных (`DATASTOR`, `REPORTS`, `legacy`) |
| `disabled_rules` | список ID правил, которые отключены |

Переключение режима: `python3 install_guard.py --apply --mode enforce` (и `--ask-supported yes`). Граница ФС: `python3 install_guard.py --apply --strict-fs-root ~/work` (сброс — `--strict-fs-root ''`). Перезапускать ZCode после смены режима не нужно: `guard.json` читается при каждом вызове.

## Жёсткая граница ФС (`strict_fs_root`)

Включена с 2026-10-29: `strict_fs_root=/home/egor/work`, режим `enforce`. Правило **G-READ-OUTSIDE** (Level C) блокирует чтение любых путей вне корня — файловыми инструментами (Read/Glob/Grep) и в bash: `cat`/readers, редиректы `<`, источники `cp`/`rsync`, `source`, `cd` за границу, файлы сценариев интерпретаторов (`python x.py`, `bash x.sh`) и raw-упоминания путей `~/…` вне корня в `python -c` / `eval`.

Разрешено помимо корня: чтение системных каталогов (`/usr`, `/etc`, `/proc`, …) и `read_allow_roots` (`/tmp`, `/var/tmp`); запись — `write_allow_roots`. Токен Level C снимает G-READ-OUTSIDE на 10 минут, но не трогает `~/.ssh` (G-READ-SSH, Level D).

## Level C с вашего разрешения

В `enforce`, когда агент хочет `git push` / merge в main / релиз, hook откажет. Чтобы разрешить на 10 минут, выполните **в своём терминале**:

```bash
touch ~/.zcode/hooks/guard/allow-level-c
```

Агент сам этого сделать не может (запись под запретом). Force-push и операции Level D токеном не разрешаются.

## Откат

```bash
python3 install_guard.py --apply --mode off        # выключить, не удаляя
python3 install_guard.py --uninstall --apply       # снять регистрацию (файлы и логи остаются)
```

Если ZCode после установки стал вести себя странно, сначала `--doctor`, затем откат или восстановление `config.json.bak-guard-*`.

## Что hook не умеет

Это страховка от ошибок модели, не граница безопасности. Команды через переменные и экзотическое кодирование он не разбирает; при включённой `strict_fs_root` raw-эвристика ловит упоминания путей `~/…` вне корня в `python -c` / `eval`, но не видит закодированные пути (base64 и т.п.) и содержимое запускаемых сценариев. Полный список в ADR-0002.
