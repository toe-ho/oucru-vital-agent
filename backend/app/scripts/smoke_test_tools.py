"""python -m app.scripts.smoke_test_tools — verify vital-sqi / vitalDSP installs."""
import sys
import numpy as np


def synthetic_ppg(duration_sec: int = 30, fs: int = 100, hr_bpm: float = 70) -> list:
    t = np.linspace(0, duration_sec, duration_sec * fs)
    hr_hz = hr_bpm / 60
    signal = (
        0.6 * np.sin(2 * np.pi * hr_hz * t)
        + 0.2 * np.sin(2 * np.pi * 2 * hr_hz * t)
        + 0.05 * np.random.randn(len(t))
    )
    return signal.tolist()


def run():
    failed = 0

    print("[smoke] load_signal_file ...", end=" ")
    try:
        import pandas as pd, tempfile, os
        from app.tools.signal_loader import load_signal_file
        sig = synthetic_ppg()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            pd.DataFrame({"ppg": sig}).to_csv(f.name, index=False)
            result = load_signal_file(f.name, column="ppg", fs=100)
        os.unlink(f.name)
        assert result["n_samples"] == 3000
        print("OK")
    except Exception as e:
        print(f"FAIL — {e}")
        failed += 1

    print("[smoke] compute_sqi ...", end=" ")
    try:
        from app.tools.sqi_tools import compute_sqi
        result = compute_sqi(synthetic_ppg(), fs=100, signal_type="ppg")
        assert "sqi_score" in result
        print(f"OK (sqi={result['sqi_score']})")
    except Exception as e:
        print(f"FAIL — {e}")
        failed += 1

    print("[smoke] check_clinical_thresholds ...", end=" ")
    try:
        from app.tools.threshold_tools import check_clinical_thresholds
        result = check_clinical_thresholds(heart_rate_bpm=72.0, spo2_pct=98.0)
        assert result["flags"] == []
        print("OK")
    except Exception as e:
        print(f"FAIL — {e}")
        failed += 1

    print(f"\n{'='*40}")
    print(f"Smoke tests: {3 - failed}/3 passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run()
