#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import mp_auth


ROOT = Path(__file__).resolve().parent
LIVE_DIR = ROOT / "outputs" / "validation" / "live_battery"
SUMMARY_PATH = LIVE_DIR / "battery_live_rerun_orchestrator_v1.json"


def interpreter_has_mp_api(interpreter: Path) -> bool:
    if not interpreter.exists():
        return False
    cmd = [
        str(interpreter),
        "-c",
        "import importlib.util; print(importlib.util.find_spec('mp_api') is not None)",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip() == "True"


def candidate_interpreters():
    paths = []
    current = Path(sys.executable)
    paths.append(current)
    scientist_env = ROOT / "scientist-env" / "bin" / "python"
    if scientist_env not in paths:
        paths.append(scientist_env)
    return paths


def choose_preferred_interpreter():
    status = []
    for path in candidate_interpreters():
        exists = path.exists()
        has_mp_api = interpreter_has_mp_api(path) if exists else False
        status.append(
            {
                "path": str(path),
                "exists": exists,
                "has_mp_api": has_mp_api,
                "is_current": path == Path(sys.executable),
            }
        )

    preferred = next((row["path"] for row in status if row["has_mp_api"]), str(Path(sys.executable)))
    return preferred, status


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_json(rel_path: str):
    return json.loads((ROOT / rel_path).read_text())


def stage_output_path(name: str) -> Path:
    return LIVE_DIR / name


def build_blocked_artifact(reason_payload: dict) -> dict:
    runtime = mp_auth.materials_project_runtime_status()
    preferred_interpreter, interpreter_status = choose_preferred_interpreter()

    missing = []
    if not any(row["has_mp_api"] for row in interpreter_status):
        missing.append("mp_api_missing_in_known_interpreters")
    if not os.environ.get("MP_API_KEY"):
        missing.append("MP_API_KEY_missing")

    artifact = {
        "artifact_type": "battery_live_rerun_orchestrator_v1",
        "status": "blocked",
        "runtime_status_current_interpreter": runtime,
        "interpreter_candidates": interpreter_status,
        "preferred_interpreter": preferred_interpreter,
        "missing_prerequisites": missing,
        "recommended_command": (
            f"MP_API_KEY=<your_key_here> '{preferred_interpreter}' "
            f"'{ROOT / 'battery_live_rerun_orchestrator.py'}' --execute"
        ),
        **reason_payload,
        "boundary_note": (
            "The live battery rerun is ready in code, but it needs a Materials Project "
            "API key and an interpreter with mp_api installed before the query stages can run."
        ),
    }
    return artifact


def compare_formula_sets(current: list[dict], stored: list[dict]) -> dict:
    current_formulas = [row["formula"] for row in current]
    stored_formulas = [row["formula"] for row in stored]
    return {
        "exact_formula_sequence_match": current_formulas == stored_formulas,
        "current_formulas": current_formulas,
        "stored_formulas": stored_formulas,
        "current_unique_formula_count": len(set(current_formulas)),
        "stored_unique_formula_count": len(set(stored_formulas)),
    }


def execute_live_rerun() -> dict:
    import battery_autonomy_audit
    import performance_engine
    import self_improving_scientist
    import sulfide_discovery
    import synthesis_validator
    import thermal_simulator
    import tunnel_physics

    baseline = sulfide_discovery.discover_baseline_candidates()
    pivot_decision = self_improving_scientist.evaluate_pivot_decision(baseline)
    pivot = self_improving_scientist.autonomous_refinement(baseline_history=baseline)

    if not pivot:
        print(f"\nLIVE RESULT: Baseline returned {len(baseline)} candidates; "
              f"pivot not triggered (baseline already >= target pool size). "
              f"Running full pipeline on baseline candidates.\n")

    candidates_to_validate = pivot if pivot else baseline
    lab_ready = synthesis_validator.validate_synthesis(candidates=candidates_to_validate)
    physics = tunnel_physics.analyze_tunnels(candidates=lab_ready)
    thermal = thermal_simulator.simulate_thermal_stability(candidates=physics)
    final = performance_engine.predict_conductivity(candidates=thermal)

    write_json(stage_output_path("discovery_history_live.json"), baseline)
    write_json(stage_output_path("discovery_history_v2_live.json"), pivot)
    write_json(stage_output_path("lab_ready_candidates_live.json"), lab_ready)
    write_json(stage_output_path("physics_validated_candidates_live.json"), physics)
    write_json(stage_output_path("thermal_validated_candidates_live.json"), thermal)
    write_json(stage_output_path("final_validated_candidates_live.json"), final)

    stored_baseline = load_json("discovery_history.json")
    stored_pivot = load_json("discovery_history_v2.json")
    stored_final = load_json("final_validated_candidates.json")

    tagged_baseline = [{**row, "lane": "baseline"} for row in baseline]
    tagged_pivot = [{**row, "lane": "pivot"} for row in pivot]
    tradeoff = battery_autonomy_audit.pivot_tradeoff_audit(tagged_baseline, tagged_pivot)
    final_snapshot = battery_autonomy_audit.final_lane_snapshot(final)

    return {
        "artifact_type": "battery_live_rerun_orchestrator_v1",
        "status": "completed",
        "mode": "live",
        "pivot_decision": pivot_decision,
        "stage_counts": {
            "baseline": len(baseline),
            "pivot": len(pivot),
            "lab_ready": len(lab_ready),
            "physics": len(physics),
            "thermal": len(thermal),
            "final": len(final),
        },
        "live_vs_stored": {
            "baseline": compare_formula_sets(baseline, stored_baseline),
            "pivot": compare_formula_sets(pivot, stored_pivot),
            "final": compare_formula_sets(final, stored_final),
        },
        "tradeoff_snapshot": {
            "pivot_weight_settings_won": tradeoff["pivot_weight_settings_won"],
            "baseline_weight_settings_won": tradeoff["baseline_weight_settings_won"],
            "tie_weight_settings": tradeoff["tie_weight_settings"],
            "pareto_frontier_formulas": tradeoff["pareto_frontier_formulas"],
        },
        "final_snapshot": final_snapshot,
        "stage_outputs": {
            "baseline": str(stage_output_path("discovery_history_live.json")),
            "pivot": str(stage_output_path("discovery_history_v2_live.json")),
            "lab_ready": str(stage_output_path("lab_ready_candidates_live.json")),
            "physics": str(stage_output_path("physics_validated_candidates_live.json")),
            "thermal": str(stage_output_path("thermal_validated_candidates_live.json")),
            "final": str(stage_output_path("final_validated_candidates_live.json")),
        },
        "boundary_note": (
            "This artifact is a separated live-rerun packet. It does not overwrite the repo's "
            "stored replay artifacts."
        ),
    }


def execute_with_preferred_interpreter_if_needed() -> int:
    preferred_interpreter, interpreter_status = choose_preferred_interpreter()
    preferred = Path(preferred_interpreter)
    current = Path(sys.executable)

    if preferred != current:
        cmd = [str(preferred), str(ROOT / "battery_live_rerun_orchestrator.py"), "--execute-internal"]
        completed = subprocess.run(cmd)
        return completed.returncode

    return execute_internal()


def execute_internal() -> int:
    if not os.environ.get("MP_API_KEY"):
        artifact = build_blocked_artifact(
            {
                "status": "blocked",
                "blocking_step": "before_live_query",
                "requested_action": "execute",
            }
        )
        write_json(SUMMARY_PATH, artifact)
        print("battery live rerun: BLOCKED")
        print("missing: MP_API_KEY")
        return 0

    if not mp_auth.materials_project_runtime_status()["mp_api_available"]:
        artifact = build_blocked_artifact(
            {
                "status": "blocked",
                "blocking_step": "before_live_query",
                "requested_action": "execute",
            }
        )
        write_json(SUMMARY_PATH, artifact)
        print("battery live rerun: BLOCKED")
        print("missing: mp_api in active interpreter")
        return 0

    artifact = execute_live_rerun()
    write_json(SUMMARY_PATH, artifact)
    print("battery live rerun: COMPLETE")
    print(f"pivot decision: {artifact['pivot_decision']['should_pivot']}")
    top = artifact['final_snapshot'].get('equal_weight_top_formula') or {}
    print(f"final top formula: {top.get('formula', 'none')}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight or execute a separated live battery rerun.")
    parser.add_argument("--execute", action="store_true", help="Run the full live rerun if prerequisites are available.")
    parser.add_argument("--execute-internal", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.execute_internal:
        raise SystemExit(execute_internal())

    if args.execute:
        raise SystemExit(execute_with_preferred_interpreter_if_needed())

    artifact = build_blocked_artifact(
        {
            "status": "preflight",
            "requested_action": "preflight_only",
        }
    )
    write_json(SUMMARY_PATH, artifact)
    print("battery live rerun preflight: COMPLETE")
    print(f"preferred interpreter: {artifact['preferred_interpreter']}")
    print(f"missing prerequisites: {artifact['missing_prerequisites']}")


if __name__ == "__main__":
    main()
