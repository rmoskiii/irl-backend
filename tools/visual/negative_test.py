#!/usr/bin/env python3
"""
IRX Visual Render Layer — rule 7 negative test.
Spec v1.0 §12.1.

A firewall check never observed failing is not a verified check. This injects a
`visual` block referencing a scoring key into a SCRATCH COPY, confirms the
harness rejects it, and confirms the real file still passes. The real scenario is
never written to.

Usage: python3 negative_test.py <scenario.json> <registries.json> <mapping.json>
"""

import sys
import os
import json
import shutil
import tempfile
import subprocess
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(HERE, "validate_visual.py")

CASES = [
    ("scenario visual block reads jessicaLoyalty",
     "scenario", {"visualRules": [{"when": {"jessicaLoyalty": 3},
                                   "cast": {"char.jessica": {"register": "tight"}}}]}),
    ("scenario visual block reads derived loyaltyBand",
     "scenario", {"visualRules": [{"when": {"loyaltyBand": "jessica"},
                                   "framing": "turned"}]}),
    ("mapping nodeOverride keyed on alexStanding",
     "mapping", None),
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run(scn, reg, mp):
    r = subprocess.run([sys.executable, VALIDATOR, scn, reg, mp],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def main(scn_path, reg_path, map_path):
    real_before = sha(scn_path)
    passed = failed = 0
    print("=" * 74)
    print("RULE 7 NEGATIVE TEST — firewall verification (spec §12.1)")
    print("=" * 74)

    for label, target, payload in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            s = os.path.join(tmp, "scenario.json")
            r = os.path.join(tmp, "registries.json")
            m = os.path.join(tmp, "mapping.json")
            shutil.copy(scn_path, s)
            shutil.copy(reg_path, r)
            shutil.copy(map_path, m)

            if target == "scenario":
                d = json.load(open(s, encoding="utf-8"))
                v = d["nodes"]["confession"]["presentation"]["data"].setdefault("visual", {})
                v.update(payload)
                json.dump(d, open(s, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            else:
                d = json.load(open(m, encoding="utf-8"))
                d["nodeOverrides"]["confession"] = {
                    "when": {"alexStanding": "cold"},
                    "cast": {"char.jessica": {"register": "tight"}},
                }
                json.dump(d, open(m, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

            code, out = run(s, r, m)
            breached = "FIREWALL BREACH" in out
            ok = code != 0 and breached
            print(f"  [{'PASS' if ok else 'FAIL'}] rejected: {label}")
            if ok:
                line = next(l.strip() for l in out.splitlines() if "FIREWALL BREACH" in l)
                print(f"         {line}")
                passed += 1
            else:
                print(f"         NOT REJECTED (exit {code}) — rule 7 is not catching this")
                failed += 1

    code, out = run(scn_path, reg_path, map_path)
    clean = code == 0 and "FIREWALL BREACH" not in out
    print(f"  [{'PASS' if clean else 'FAIL'}] real scenario passes cleanly (no false positive)")
    passed += clean
    failed += not clean

    unchanged = sha(scn_path) == real_before
    print(f"  [{'PASS' if unchanged else 'FAIL'}] real scenario byte-identical after test")
    passed += unchanged
    failed += not unchanged

    print("=" * 74)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))