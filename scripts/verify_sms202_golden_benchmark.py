#!/usr/bin/env python3
"""Verify the immutable SMS202 model 1710 source-ingestion benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.sms202 import verify_golden_benchmark  # noqa: E402


DEFAULT_SOURCE = ROOT / "benchmarks" / "sms202" / "model_1710_source.m"
DEFAULT_EXPECTED = ROOT / "benchmarks" / "sms202" / "model_1710_expected.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Optionally anchor the fixture to the original full sms202.m corpus.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every reconstructed field and individual check.",
    )
    args = parser.parse_args()

    result = verify_golden_benchmark(
        args.source,
        args.expected,
        corpus_path=args.corpus,
    )
    payload = result.as_dict() if args.verbose else result.summary_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
