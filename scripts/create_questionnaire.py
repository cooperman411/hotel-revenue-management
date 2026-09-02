#!/usr/bin/env python3
"""Create a clean, sendable hotel intake questionnaire from the shared template."""
import argparse
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "shared" / "intake" / "questionnaire.md"

def main():
    parser = argparse.ArgumentParser(description="Create a sendable hotel revenue-management questionnaire")
    parser.add_argument("--property-name", default="[Property name]")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("# Revenue Management Intake Questionnaire", f"# Revenue Management Intake Questionnaire — {args.property_name}")
    text += "\n\nPlease return this questionnaire with the requested sanitized reports. Do not include guest or employee personal information or API credentials.\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote questionnaire: {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
