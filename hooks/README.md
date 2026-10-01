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
| `protected_data_names` | имена каталогов эталонных данных (`DATASTOR`, `REPORTS`, `legacy`) |
| `disabled_rules` | список ID правил, которые отключены |

Переключение режима: `python3 install_guard.py --apply --mode enforce` (и `--ask-supported yes`). Перезапускать ZCode после смены режима не нужно: `guard.json` читается при каждом вызове.

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

Это страховка от ошибок модели, не граница безопасности. Скрипты (`python -c`, `bash x.sh`), команды через переменные и экзотическое кодирование он не разбирает. Полный список в ADR-0002.
