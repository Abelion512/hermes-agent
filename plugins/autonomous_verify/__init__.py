"""autonomous_verify plugin — Unified verification pipeline.

Registers the ``verify_change`` tool.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


def check_requirements() -> bool:
    return True


def _run_cmd(cmd: str, cwd: str = ".") -> Dict[str, Any]:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=120
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_change(
    path: str = ".",
    task_id: Optional[str] = None,
    run_lint: bool = True,
    run_test: bool = True,
    test_pattern: str = "",
) -> str:
    """Unified verification tool. Detects project type and runs lint/test."""
    root = Path(path).resolve()
    results = {}

    # 1. Detect Project Type
    is_python = (
        (root / "pyproject.toml").exists()
        or (root / "setup.py").exists()
        or (root / "requirements.txt").exists()
    )
    is_node = (root / "package.json").exists()

    status_rows = []

    # 2. Linting
    if run_lint:
        if is_python:
            lint_res = _run_cmd("ruff check .", cwd=str(root))
            if "not found" in lint_res.get("stderr", ""):
                lint_res = _run_cmd("flake8 .", cwd=str(root))
        elif is_node:
            lint_res = _run_cmd("npm run lint", cwd=str(root))
        else:
            lint_res = {"success": False, "error": "Unknown project type"}

        icon = "✅" if lint_res.get("success") else "❌"
        status_rows.append([
            "Linting",
            icon,
            "Passed" if lint_res.get("success") else "Failed",
        ])
        results["lint"] = lint_res

    # 3. Testing
    if run_test:
        if is_python:
            cmd = "pytest"
            if test_pattern:
                cmd += f" -k {test_pattern}"
            test_res = _run_cmd(cmd, cwd=str(root))
        elif is_node:
            test_res = _run_cmd("npm test", cwd=str(root))
        else:
            test_res = {"success": False, "error": "Unknown project type"}

        icon = "✅" if test_res.get("success") else "❌"
        status_rows.append([
            "Testing",
            icon,
            "Passed" if test_res.get("success") else "Failed",
        ])
        results["test"] = test_res

    all_success = all(v.get("success", False) for v in results.values())

    # Asa-Style Visual Output
    if status_rows:
        col_widths = [
            max(len(str(row[i])) for row in status_rows)
            for i in range(len(status_rows[0]))
        ]
        formatted_status = "\n".join([
            "  ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
            for row in status_rows
        ])
    else:
        formatted_status = "No checks run."

    visual_report = f"### 🏁 Verification: {'SUCCESS' if all_success else 'FAILURE'}\n\n```status\n{formatted_status}\n```"

    if not all_success:
        visual_report += "\n\n**Errors detected:**\n"
        for k, v in results.items():
            if not v.get("success"):
                err = v.get("stderr") or v.get("stdout") or v.get("error")
                visual_report += f"- **{k.capitalize()}**: `{str(err)[:200]}...`\n"

    return visual_report


def register(ctx) -> None:
    ctx.register_tool(
        name="verify_change",
        toolset="software_development",
        schema={
            "name": "verify_change",
            "description": "Run an automated verification pipeline (lint, build, test) for code changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Root path of the project to verify (defaults to current dir).",
                    },
                    "run_lint": {
                        "type": "boolean",
                        "description": "Whether to run linting checks.",
                    },
                    "run_test": {
                        "type": "boolean",
                        "description": "Whether to run unit tests.",
                    },
                    "test_pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter tests (e.g. 'test_cli').",
                    },
                },
            },
        },
        handler=lambda args, **kw: verify_change(
            path=args.get("path", "."),
            run_lint=args.get("run_lint", True),
            run_test=args.get("run_test", True),
            test_pattern=args.get("test_pattern", ""),
            task_id=kw.get("task_id"),
        ),
        check_fn=check_requirements,
    )
