"""Pre-flight spec validator — rule-based, LLM-free.

Mencegah /goal dieksekusi sebelum spec lengkap.
Sepenuhnya deterministik — tidak ada LLM call.

Works sebagai Hermes plugin yang intercept /goal sebelum eksekutor.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from typing import Optional

PLUGIN_NAME = "preflight"
PLUGIN_VERSION = "1.0.0"

# ── Required fields ───────────────────────────────────────────────────

REQUIRED_FIELDS = {
    "owner": "Orang yang responsible. Contoh: 'abelion', 'hermes', 'autonomous'",
    "deadline": "Deadline konkret. Contoh: '2026-07-01', '4h', 'EOD today'",
    "scope": "Apa yang termasuk dan TIDAK termasuk. Minimal mention out-of-scope.",
    "success_criteria": "Bagaimana tau selesai? Harus verifiable. Minimal 1 butir checklist.",
    "stop_conditions": "Kapan agent harus berhenti? Contoh: timeout 10m, biaya > $1.",
}

OPTIONAL_FIELDS = {
    "dependencies": "Apa yang harus ada sebelum mulai.",
    "budget": "Token / uang / waktu maksimal.",
    "tasks": "Breakdown task (list of strings). Minimal 1.",
}

VERIFIABLE_SIGNALS = [
    "file", "output", "status", "count", "created", "updated",
    "deleted", "return", "response", "pass", "fail", "error", "test",
]


@dataclass
class ValidationResult:
    passed: bool
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejection_message: Optional[str] = None


def validate(spec: dict) -> ValidationResult:
    """Validate a /goal spec dict.

    Returns ValidationResult. Jika passed=False, goal HARUS ditolak.
    """
    missing = []
    warnings = []

    # ── Check required fields ─────────────────────────────────────────
    for field, hint in REQUIRED_FIELDS.items():
        val = spec.get(field, "")
        if isinstance(val, str):
            val = val.strip()
        if not val or (isinstance(val, str) and val.lower() in ("", "tbd", "unknown", "?", "-", "none", "n/a")):
            missing.append(field)

    # ── Optional tapi strongly рекомендовано ───────────────────────────
    deps = spec.get("dependencies", "")
    if not deps or (isinstance(deps, str) and deps.strip() == ""):
        warnings.append("dependencies: tidak ada — recommend diisi untuk mengurangi risiko gagal di tengah")

    # ── Quality checks ────────────────────────────────────────────────
    criteria = spec.get("success_criteria", "")
    if isinstance(criteria, str):
        if not any(s in criteria.lower() for s in VERIFIABLE_SIGNALS):
            warnings.append("success_criteria: mungkin tidak verifiable — tidak ada kata kerja measurable (output/file/status/return)")
    elif isinstance(criteria, list):
        if len(criteria) == 0:
            warnings.append("success_criteria: list kosong — minimal 1 butir")

    deadline = spec.get("deadline", "")
    if isinstance(deadline, str) and not re.search(r'\d', deadline):
        warnings.append("deadline: tidak mengandung angka — ambigu. Contoh: '2h', '2026-07-01'")

    scope = spec.get("scope", "")
    if isinstance(scope, str) and "out" not in scope.lower():
        warnings.append("scope: tidak mention out-of-scope — ambigu, risk of scope creep")

    # ── Reject if missing required fields ─────────────────────────────
    if missing:
        msg_parts = ["❌ Spec incomplete. Execution blocked.\n"]
        msg_parts.append("Missing required fields:\n")
        for f in missing:
            msg_parts.append(f"  • {f}: {REQUIRED_FIELDS[f]}\n")
        if warnings:
            msg_parts.append("\nAlso (non-blocking):\n")
            for w in warnings:
                msg_parts.append(f"  • ⚠ {w}\n")
        msg_parts.append("\nFill these fields, then re-submit /goal.")
        return ValidationResult(
            passed=False,
            missing_fields=missing,
            warnings=warnings,
            rejection_message="".join(msg_parts),
        )

    return ValidationResult(passed=True, missing_fields=[], warnings=warnings)


def format_goal_prompt(spec: dict) -> str:
    """Format a validated spec dict into a /goal prompt string."""
    lines = ["# Goal", "", f"Task: {spec.get('goal', spec.get('task', spec.get('title', 'untitled')))}"]
    lines.append(f"Owner: {spec.get('owner', 'auto')}")
    lines.append(f"Deadline: {spec.get('deadline', 'ASAP')}")
    lines.append(f"Scope: {spec.get('scope', 'N/A')}")
    lines.append(f"Dependencies: {spec.get('dependencies', 'None')}")

    criteria = spec.get("success_criteria", [])
    if isinstance(criteria, str):
        criteria = [criteria]
    lines.append("Success Criteria:")
    for c in criteria:
        lines.append(f"  [ ] {c}")

    stop = spec.get("stop_conditions", "")
    if stop:
        lines.append(f"Stop: {stop}")
    else:
        lines.append(f"Stop: 10m timeout, unsafe ops guard")

    budget = spec.get("budget", "")
    if budget:
        lines.append(f"Budget: {budget}")

    extra = spec.get("extra", "")
    if extra:
        lines.append(f"Context: {extra}")

    return "\n".join(lines)
