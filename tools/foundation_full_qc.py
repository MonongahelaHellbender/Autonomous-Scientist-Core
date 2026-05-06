#!/usr/bin/env python3
"""Run the maintained Foundation QC stack and write one summary artifact."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "foundation_full_qc"
LATEST_JSON = OUT_DIR / "latest_full_qc.json"
LATEST_MD = OUT_DIR / "latest_full_qc.md"


COMMANDS = [
    {
        "name": "foundation_doctor",
        "cmd": [sys.executable, "tools/foundation_doctor.py"],
        "purpose": "Compile and inspect the main Foundation app surface.",
    },
    {
        "name": "foundation_qc",
        "cmd": [sys.executable, "tools/foundation_qc.py"],
        "purpose": "Run lightweight source scans and compile checks.",
    },
    {
        "name": "foundation_major_suite",
        "cmd": [sys.executable, "tools/foundation_major_suite.py", "--goal", "Full QC renovation pass", "--save"],
        "purpose": "Index reports, scan claims, audit modules, and generate a roadmap.",
    },
    {
        "name": "autonomous_core_regression_suite",
        "cmd": [sys.executable, "autonomous_core_regression_suite.py"],
        "purpose": "Run maintained cross-lane regression checks.",
    },
    {
        "name": "foundation_app_compile",
        "cmd": [
            "/bin/sh",
            "-c",
            "find Tasuke/ui Tasuke/tools Tasuke/src Tasuke/experiments -name '*.py' -type f -print0 | xargs -0 python3 -m py_compile",
        ],
        "purpose": "Compile active Foundation app/liquid-workbench source files.",
    },
]


def run_command(item: dict) -> dict:
    completed = subprocess.run(
        item["cmd"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return {
        "name": item["name"],
        "purpose": item["purpose"],
        "cmd": item["cmd"],
        "status": "pass" if completed.returncode == 0 else "fail",
        "return_code": completed.returncode,
        "output_tail": "\n".join(output.splitlines()[-30:]),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Foundation Full QC",
        "",
        f"Created: {report['created_at']}",
        "",
        f"Overall status: `{report['overall_status']}`",
        "",
        "| Check | Status | Purpose |",
        "| --- | --- | --- |",
    ]
    for row in report["checks"]:
        lines.append(f"| {row['name']} | `{row['status']}` | {row['purpose']} |")
    lines.extend(["", "## Output Tails", ""])
    for row in report["checks"]:
        lines.extend([
            f"### {row['name']} ({row['status']})",
            "",
            "```text",
            row["output_tail"] or "(no output)",
            "```",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = [run_command(item) for item in COMMANDS]
    report = {
        "artifact_type": "foundation_full_qc_v1",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "overall_status": "pass" if all(row["status"] == "pass" for row in checks) else "fail",
        "checks": checks,
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"full_qc_{stamp}.json"
    md_path = OUT_DIR / f"full_qc_{stamp}.md"
    json_text = json.dumps(report, indent=2) + "\n"
    md_text = render_markdown(report)

    json_path.write_text(json_text)
    md_path.write_text(md_text)
    LATEST_JSON.write_text(json_text)
    LATEST_MD.write_text(md_text)

    print(json.dumps({
        "overall_status": report["overall_status"],
        "latest_json": str(LATEST_JSON),
        "latest_md": str(LATEST_MD),
    }, indent=2))

    if report["overall_status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
