#!/usr/bin/env python3
"""Emit example CSV for ML training. Run from repo: python scripts/generate_synthetic_dataset.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic.generator import SyntheticMiningDataGenerator  # noqa: E402


def main() -> None:
    out = ROOT / "data" / "example_training.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    SyntheticMiningDataGenerator(seed=7).write_example_csv(str(out), n=500)
    print(out)


if __name__ == "__main__":
    main()
