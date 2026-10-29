# Task: guard-enforce-fs-boundary

- Дата: 2026-10-29
- Проект: zcode-hub
- Ветка: feature/guard-enforce-fs-boundary
- Статус: done

## Задача
Агент свободно читал `$HOME` вне `~/work` (Downloads, `~/.ssh/known_hosts`, ключи): страж работал в `shadow` и не имел правила на чтение вне workspace. Перевести стража в `enforce` и ввести жёсткую границу ФС `~/work` (G-READ-OUTSIDE) по явному запросу пользователя.

## Требования
- Блокировать чтение путей `$HOME` вне `/home/egor/work` на уровне вызовов инструментов: Read/Glob/Grep/LS + bash (readers, редиректы, источники cp/rsync, `source`)
- Покрыть bash-эвристики: `cd` за границу, файлы сценариев интерпретаторов (`python x.py`, `bash x.sh`), raw-упоминания `~/…` вне корня в `python -c` / `eval`
- Системные каталоги (`/usr`, `/etc`, `/proc`, …) остаются читаемыми; `/tmp`, `/var/tmp` — чтение и запись
- Обход для пользователя — токен Level C (10 мин); `~/.ssh` (Level D) токеном не снимается
- Исходники репозитория и развёрнутая копия `~/.zcode` синхронизированы (иначе `install_guard.py --apply` затёр бы правки)

## Ограничения
- Граница инструментальная (hook-уровень), не kernel-level: закодированные пути (base64) могут проскочить; OS-слой (bwrap) отвергнут пользователем
- fail-open при внутренних ошибках стража сохранён (осознанно, ADR-0002 п.7)
- Правки `~/.zcode` — только с явного подтверждения (получено: утверждение плана в сессии 29.10)

## Acceptance criteria
- [x] G-READ-OUTSIDE блокирует чтение вне корня во всех каналах; 26 кейсов /tmp/test_guard.py прошли
- [x] Полный автотест `hooks/test_guard.py` — 0 failed (добавлена секция strict_fs_root)
- [x] Развёрнуто: `mode=enforce`, `strict_fs_root=/home/egor/work`; `--doctor` чист; живой вызов Read из `~/Downloads` заблокирован в сессии
- [x] ADR-0002 (статус + поправка), README (ключи, раздел о границе), install_guard.py (DEFAULTS + `--strict-fs-root`) обновлены

## Изменяемые файлы
- hooks/guard.py, hooks/test_guard.py, hooks/install_guard.py
- hooks/README.md, hooks/ADR-0002-hooks-enforcement.md
- .zcode/tasks/20261029-guard-enforce-fs-boundary.md
- Вне репозитория (развёрнуто в `~/.zcode`): hooks/guard/guard.py, hooks/guard/guard.json, AGENTS.md (пункт о границе ФС)

## Итог
Правки сначала применены к развёрнутой копии `~/.zcode` (утверждённый план), затем возвращены в исходники хаба. Отличий от плана нет; `ask_supported=false` сохранён (тест `ask` не проводился — открытый вопрос ADR-0002 №1). Известный долг: полный просмотр shadow-отчёта перед переключением не выполнялся (поправка ADR-0002 п.1), ложные срабатывания отстраивать по журналу в enforce. Коммит: см. `git log -1` ветки feature/guard-enforce-fs-boundary.
