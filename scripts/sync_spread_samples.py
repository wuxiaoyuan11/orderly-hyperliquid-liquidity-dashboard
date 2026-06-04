from __future__ import annotations

import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_SPREAD_SAMPLES = Path("/private/tmp/orderly-spread-sampler/spread_samples_1m.csv")
PROJECT_SPREAD_SAMPLES = PROJECT_ROOT / "data" / "raw" / "spread_samples_1m_live.csv"


def main() -> None:
    if not TMP_SPREAD_SAMPLES.exists():
        raise FileNotFoundError(f"Live spread sample file does not exist: {TMP_SPREAD_SAMPLES}")

    PROJECT_SPREAD_SAMPLES.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TMP_SPREAD_SAMPLES, PROJECT_SPREAD_SAMPLES)
    print(f"Copied {TMP_SPREAD_SAMPLES} to {PROJECT_SPREAD_SAMPLES}")


if __name__ == "__main__":
    main()
