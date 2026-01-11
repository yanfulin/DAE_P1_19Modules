#!/usr/bin/env python3
"""
DAE P1 Self Test Runner (v2.0)
- Runs demo generation N times
- Validates evidence bundle JSON using included JSON Schemas (jsonschema)
- Validates fp-lite output schema (jsonschema)
- Produces a markdown report

Usage:
  python run_self_test.py --runs 10
"""

import argparse, glob, json, os, subprocess, sys, time
from datetime import datetime
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(__file__)
OUT_DIR = os.path.join(ROOT, "out")
SCHEMAS_DIR = os.path.join(ROOT, "schemas")
REPORT = os.path.join(ROOT, "TEST_REPORT_10RUNS.md")

BUNDLE_SCHEMA_FILE = os.path.join(SCHEMAS_DIR, "EvidenceBundle.schema.json")
FP_SCHEMA_FILE = os.path.join(SCHEMAS_DIR, "fp_lite_output.schema.json")

def load_schema(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_json(schema_obj, instance_obj):
    v = Draft202012Validator(schema_obj)
    errors = sorted(v.iter_errors(instance_obj), key=lambda e: e.path)
    return errors

def run_demo_once() -> str:
    # remove previous out files to avoid confusion
    os.makedirs(OUT_DIR, exist_ok=True)
    # run demo
    cmd = [sys.executable, os.path.join(ROOT, "demo_run.py")]
    subprocess.check_call(cmd)
    # find latest bundle
    bundles = sorted(glob.glob(os.path.join(OUT_DIR, "evidence_bundle_*.json")), key=os.path.getmtime)
    if not bundles:
        raise RuntimeError("No evidence bundle produced")
    return bundles[-1]

def run_fp_cli(bundle_path: str) -> dict:
    cmd = [sys.executable, "-m", "dae_p1.M15_cli_offline_fp", bundle_path]
    out = subprocess.check_output(cmd, cwd=ROOT)
    return json.loads(out.decode("utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--report", default=REPORT)
    args = ap.parse_args()

    bundle_schema = load_schema(BUNDLE_SCHEMA_FILE)
    fp_schema = load_schema(FP_SCHEMA_FILE)

    rows = []
    pass_count = 0

    start = datetime.utcnow().isoformat() + "Z"
    for i in range(1, args.runs + 1):
        t0 = time.time()
        status = "PASS"
        notes = []
        bundle_path = ""
        try:
            bundle_path = run_demo_once()
            with open(bundle_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)

            # Schema validation for bundle
            b_errors = validate_json(bundle_schema, bundle)
            if b_errors:
                status = "FAIL"
                notes.append(f"bundle_schema_errors={len(b_errors)}")
                # keep first few
                for e in b_errors[:3]:
                    notes.append(f"bundle_err: {list(e.path)} {e.message}")

            # fp-lite generation + schema validation
            fp = run_fp_cli(bundle_path)
            fp_errors = validate_json(fp_schema, fp)
            if fp_errors:
                status = "FAIL"
                notes.append(f"fp_schema_errors={len(fp_errors)}")
                for e in fp_errors[:3]:
                    notes.append(f"fp_err: {list(e.path)} {e.message}")

        except Exception as e:
            status = "FAIL"
            notes.append(f"exception={repr(e)}")

        dt = time.time() - t0
        if status == "PASS":
            pass_count += 1
        rows.append((i, status, f"{dt:.2f}s", os.path.basename(bundle_path) if bundle_path else "-", "; ".join(notes)))

    end = datetime.utcnow().isoformat() + "Z"

    # Write report
    lines = []
    lines.append("# DAE P1 Self Test Report — 10 Runs (v2.0)\n")
    lines.append(f"- Started: {start}\n- Ended: {end}\n- Runs: {args.runs}\n- Pass: {pass_count}\n- Fail: {args.runs - pass_count}\n")
    lines.append("\n## Results\n")
    lines.append("| Run | Status | Time | Bundle | Notes |\n")
    lines.append("|---:|:---:|---:|---|---|\n")
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n")

    with open(args.report, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Wrote report: {args.report}")
    if pass_count != args.runs:
        sys.exit(1)

if __name__ == "__main__":
    main()
