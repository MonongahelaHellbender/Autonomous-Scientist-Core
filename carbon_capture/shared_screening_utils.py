import json
from pathlib import Path

VETTED_RESULTS_PATH = Path("carbon_capture/vetted_carbon_results.json")


def load_candidate_rows(path):
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict) and "candidates" in payload:
        return payload["candidates"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported candidate payload format in {path}")


def load_retained_candidates(path=VETTED_RESULTS_PATH):
    data = load_candidate_rows(path)
    return [row for row in data if row.get("final_verdict") == "APPROVED"]


def normalize(value, low, high):
    if high == low:
        return 0.5
    scaled = (value - low) / (high - low)
    return max(0.0, min(1.0, scaled))


def clamp(value, low, high):
    return max(low, min(high, value))
