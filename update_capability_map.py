#!/usr/bin/env python3
"""
Update CAPABILITY_MAP.md from capabilities/capability_dictionary.csv.

This helps you align to your official 20 capability dictionary without editing markdown by hand.
"""
import csv, os

ROOT = os.path.dirname(__file__)
CSV_PATH = os.path.join(ROOT, "capabilities", "capability_dictionary.csv")
OUT_PATH = os.path.join(ROOT, "CAPABILITY_MAP.md")

def main():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    lines = []
    lines.append("# Capability Map (C01–C20) — Official Alignment\n")
    lines.append("This map is generated from `capabilities/capability_dictionary.csv`.\n")
    lines.append("| Cap ID | Official Name | Outputs | Mapped Modules | Notes |\n")
    lines.append("|---:|---|---|---|---|\n")
    for r in rows:
        lines.append(f"| {r['cap_id']} | {r.get('official_name','').strip() or '(replace)'} | {r.get('outputs','')} | {r.get('mapped_modules','')} | {r.get('notes','')} |\n")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("Wrote:", OUT_PATH)

if __name__ == "__main__":
    main()
