#!/usr/bin/env python3
"""Install / configure / remove the Hub guard hook (PreToolUse).

Default is DRY-RUN: nothing is written. Use --apply.
  python3 install_guard.py                        # plan
  python3 install_guard.py --apply                # install in shadow mode (log only)
  python3 install_guard.py --apply --mode enforce # switch to blocking
  python3 install_guard.py --apply --ask-supported yes   # after the `ask` test passed
  python3 install_guard.py --uninstall --apply    # remove the hook entry (files and logs stay)

Safety: backs up config.json, merges into existing hooks (probe/foreign entries kept),
preserves file mode, never prints other config content.
"""
import argparse
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path

HOME = Path.home()
GUARD_DIR = HOME / ".zcode" / "hooks" / "guard"
GUARD_DST = GUARD_DIR / "guard.py"
GUARD_CFG = GUARD_DIR / "guard.json"
ZCODE_CFG = HOME / ".zcode" / "cli" / "config.json"
MARK = "hooks/guard/guard.py"
DEFAULTS = {"mode": "shadow", "ask_supported": False, "ask_fallback": "deny", "allow_once_ttl_min": 10,
            "write_allow_roots": ["/tmp", "/var/tmp"], "protected_data_names": ["DATASTOR", "REPORTS", "legacy"],
            "disabled_rules": []}


def pick_python():
    for p in ("/usr/bin/python3", shutil.which("python3")):
        if p and os.access(p, os.X_OK):
            return p
    sys.exit("python3 not found")


def is_ours(entry):
    hooks = entry.get("hooks", []) if isinstance(entry, dict) else []
    return any(isinstance(h, dict) and MARK in str(h.get("command", "")) for h in hooks)


def load_json(path, what):
    if not path.exists():
        return {}, False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit("ABORT: %s is not valid JSON (%s). Nothing changed." % (what, e))
    if not isinstance(data, dict):
        sys.exit("ABORT: %s root is not an object. Nothing changed." % what)
    return data, True


def write_json(path, data, backup):
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    if backup and path.exists():
        bak = path.with_name(path.name + ".bak-guard-" + time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(path, bak)
        print("backup:", bak)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-guard")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.fchmod(fd, mode)
        os.write(fd, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp, path)


def transform_zcode(cfg, py, uninstall):
    hooks = cfg.get("hooks")
    if hooks is None:
        hooks = {}
        if not uninstall:
            cfg["hooks"] = hooks
    if not isinstance(hooks, dict):
        sys.exit("ABORT: existing 'hooks' is not an object. Nothing changed.")
    events = hooks.get("events")
    if events is None:
        events = {}
    if not isinstance(events, dict):
        sys.exit("ABORT: existing 'hooks.events' is not an object. Nothing changed.")
    lst = events.get("PreToolUse", [])
    if not isinstance(lst, list):
        sys.exit("ABORT: hooks.events.PreToolUse is not a list. Nothing changed.")
    foreign = [e for e in lst if not is_ours(e)]
    if uninstall:
        if foreign:
            events["PreToolUse"] = foreign
        else:
            events.pop("PreToolUse", None)
        if events:
            hooks["events"] = events
        else:
            hooks.pop("events", None)
        return cfg, ["remove guard from PreToolUse (%d other entries kept)" % len(foreign), "hooks.enabled left unchanged"]
    # Shell form only: a separate `args` field makes ZCode reject the whole config.
    entry = {"hooks": [{"type": "command", "command": '"%s" "%s"' % (py, GUARD_DST), "timeoutMs": 5000}]}
    events["PreToolUse"] = foreign + [entry]
    hooks["enabled"] = True
    hooks["events"] = events
    return cfg, ["PreToolUse: +1 guard entry, %d existing kept" % len(foreign)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--mode", choices=["off", "shadow", "enforce"])
    ap.add_argument("--ask-supported", choices=["yes", "no"])
    a = ap.parse_args()
    py = pick_python()

    zcfg, existed = load_json(ZCODE_CFG, str(ZCODE_CFG))
    new_z, notes = transform_zcode(json.loads(json.dumps(zcfg)), py, a.uninstall)
    gcfg, gexisted = load_json(GUARD_CFG, str(GUARD_CFG))
    new_g = dict(DEFAULTS)
    new_g.update(gcfg)
    if a.mode:
        new_g["mode"] = a.mode
    if a.ask_supported:
        new_g["ask_supported"] = a.ask_supported == "yes"

    print("mode:        %s" % ("APPLY" if a.apply else "DRY-RUN (nothing written)"))
    print("zcode cfg:   %s (%s)" % (ZCODE_CFG, "exists" if existed else "will be created"))
    print("python:      %s" % py)
    print("guard files: %s" % GUARD_DIR)
    for n in notes:
        print(" -", n)
    if not a.uninstall:
        print("guard.json:  mode=%s ask_supported=%s (%s)" % (new_g["mode"], new_g["ask_supported"],
                                                              "update" if gexisted else "new"))
    if not a.apply:
        print("\nRe-run with --apply to write.")
        return
    if not a.uninstall:
        src = Path(__file__).with_name("guard.py")
        if not src.exists():
            sys.exit("ABORT: guard.py not found next to installer.")
        GUARD_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(GUARD_DIR, 0o700)
        shutil.copy2(src, GUARD_DST)
        os.chmod(GUARD_DST, 0o700)
        write_json(GUARD_CFG, new_g, backup=False)
    write_json(ZCODE_CFG, new_z, backup=True)
    print("\nDone. Restart ZCode to load hooks.")
    print("Self-check:   python3 %s --doctor" % GUARD_DST)
    print("Shadow review: python3 %s --report 7" % GUARD_DST)


if __name__ == "__main__":
    main()
