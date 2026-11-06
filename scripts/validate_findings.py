#!/usr/bin/env python3
"""Validate the minimum evidence metadata for a findings JSON document."""
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("findings")
    args = parser.parse_args()
    with open(args.findings, encoding="utf-8") as f: data = json.load(f)
    errors = []
    allowed = {"observed", "derived", "inferred", "recommended"}
    strengths = {"high", "medium", "low"}
    for index, finding in enumerate(data.get("findings", []), 1):
        for key in ("classification", "evidence_strength", "evidence"):
            if not finding.get(key):
                errors.append(f"finding {index}: missing {key}")
        if finding.get("classification") not in allowed:
            errors.append(f"finding {index}: invalid classification")
        if finding.get("evidence_strength") not in strengths:
            errors.append(f"finding {index}: invalid evidence strength")
        if not isinstance(finding.get("evidence"), list):
            errors.append(f"finding {index}: evidence must be a list")
    result = {"valid": not errors, "errors": errors, "findings": len(data.get("findings", []))}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
