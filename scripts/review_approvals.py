#!/usr/bin/env python3
"""Validate explicit human decisions and emit a vendor-neutral approved-rate record."""
import argparse,json
from pathlib import Path
from review_engine import approvals
p=argparse.ArgumentParser();p.add_argument('analysis');p.add_argument('decisions');p.add_argument('output');a=p.parse_args()
Path(a.output).write_text(json.dumps(approvals(json.loads(Path(a.analysis).read_text()),json.loads(Path(a.decisions).read_text())),indent=2,allow_nan=False))
