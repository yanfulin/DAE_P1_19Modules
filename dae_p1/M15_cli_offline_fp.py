
from __future__ import annotations
import argparse
import json
from .M14_bundle_reader import load_bundle
from .M13_fp_lite import fp_lite_from_bundle

def main():
    ap = argparse.ArgumentParser(description="DAE P1 fp-lite offline tool")
    ap.add_argument("bundle", help="Path to evidence bundle JSON")
    ap.add_argument("--out", help="Output JSON path (optional)")
    args = ap.parse_args()
    b = load_bundle(args.bundle)
    out = fp_lite_from_bundle(b)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(args.out)
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
