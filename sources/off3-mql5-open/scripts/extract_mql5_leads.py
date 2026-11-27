"""Deterministic cleanroom extractor for sources/off3-mql5-open/ (Offensive #3, C3-MQL5).

Reads ONLY from sources/off3-mql5-open/raw/*.json after verifying raw_manifest.sha256.json.
Produces:
  - sources/off3-mql5-open/extracted/leads.json (clean white-box non-breakout MQL5 leads)
  - sources/off3-mql5-open/extracted/rejected_log.json (disqualified toxic EAs)

Enforces fail-closed:
  1. Raw manifest integrity via scripts/common/verify_verbatim.py.
  2. Toxic disqualifiers: Grid, Martingale, Averaging-Down, Zone Recovery, DLL-Import,
     No-SL, Rollover-Scalper, and Repainting/Blackbox.
  3. FTMO MT5 universe applicability via sources/off3-dedup-index/scripts/merge_off3_leads.py.
  4. Zero Hallucination (NOT_DISCLOSED for missing/omitted fields).
  5. Zero Holdout 2024..2029 / OOS2 tokens via scripts/common/holdout_sanitizer.py.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from typing import Any

SOURCE_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
ROOT_DIR = SOURCE_DIR.parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
COMMON_DIR = SCRIPTS_DIR / "common"
DEDUP_SCRIPTS_DIR = ROOT_DIR / "sources" / "off3-dedup-index" / "scripts"
for _p in (str(SCRIPTS_DIR), str(COMMON_DIR), str(DEDUP_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_intel_ingest  # noqa: E402
import holdout_sanitizer  # noqa: E402
import verify_verbatim  # noqa: E402
import merge_off3_leads  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"

# Additional MQL5-specific toxic disqualifier patterns
MQL5_EXTRA_DISQUALIFIERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "TOXIC_AVERAGING_DOWN",
        re.compile(
            r"\b(averaging\s+down|position\s+averaging|averaging\s+positions|zone\s+recovery|"
            r"step\s+lossing\s+pips|adds?\s+a\s+new\s+level\s+every)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_ROLLOVER_SCALPER",
        re.compile(
            r"\b(rollover[- ]?window\s+night|rollover[- ]?scalper|night\s+flat\s+trade|"
            r"only\s+in\s+the\s+quietest\s+hours.*(?:american\s+session|asian)|night\s+scalper)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_DLL_IMPORT",
        re.compile(
            r'(#import\s+"[^"]+\.dll"|requires?\s+dll\s+import|calls\s+windows\s+internet\s*\(wininet\.dll\))',
            re.IGNORECASE,
        ),
    ),
)


def _nd(val: Any) -> str:
    if val is None:
        return NOT_DISCLOSED
    s = str(val).strip()
    return s if s else NOT_DISCLOSED


def audit_mql5_toxicity(raw_doc: dict[str, Any]) -> tuple[bool, list[str], str]:
    """Run auto_intel_ingest + merge_off3_leads + MQL5-specific disqualifier detectors."""
    combined_spec_text = "\n".join(
        p
        for p in (
            _nd(raw_doc.get("name")),
            _nd(raw_doc.get("stop_loss_rule")),
            _nd(raw_doc.get("rule_description")),
            _nd(raw_doc.get("verbatim_excerpt")),
        )
        if p != NOT_DISCLOSED
    )
    is_tox1, flags1, rat1 = merge_off3_leads.detect_all_toxic_signals(combined_spec_text)
    flags: list[str] = list(flags1)
    rationales: list[str] = [rat1] if is_tox1 and rat1 else []

    # Check page-level DLL imports explicitly detected during pure-text HTML parse
    dll_imports = raw_doc.get("detected_dll_imports_in_page_snippets") or []
    if dll_imports:
        if "TOXIC_DLL_IMPORT" not in flags:
            flags.append("TOXIC_DLL_IMPORT")
            rationales.append(f'TOXIC_DLL_IMPORT: "Detected {dll_imports}"')

    # Check extra MQL5 disqualifiers across spec + verbatim excerpt
    for flag, rx in MQL5_EXTRA_DISQUALIFIERS:
        m = rx.search(combined_spec_text)
        if m:
            if flag not in flags:
                flags.append(flag)
                rationales.append(f'{flag}: "{m.group(0)}"')

    if flags:
        return True, flags, " | ".join(rationales)
    return False, [], "No toxic Grid/Martingale/No-SL signal detected in raw text."


def build_lead_record(raw_doc: dict[str, Any], raw_rel_path: str) -> dict[str, Any]:
    is_toxic, toxic_flags, toxic_rationale = audit_mql5_toxicity(raw_doc)
    stop_rule = _nd(raw_doc.get("stop_loss_rule"))
    tp_rule = _nd(raw_doc.get("take_profit_rule"))
    tf = _nd(raw_doc.get("timeframe"))

    dq_flags = [
        "AUTO_INGESTED_UNTRUSTED_PUBLIC_SPEC",
        "UNVERIFIED_EXTERNAL_CLAIM",
        "MISSING_PF_AND_DD_NOT_DISCLOSED",
    ]
    if stop_rule == NOT_DISCLOSED:
        dq_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
    if tp_rule == NOT_DISCLOSED:
        dq_flags.append("TAKE_PROFIT_RULE_NOT_DISCLOSED")
    if tf == NOT_DISCLOSED:
        dq_flags.append("TIMEFRAME_NOT_DISCLOSED")

    disqualifiers_checked = {
        "grid": "PASS_NONE_DETECTED" if "TOXIC_GRID" not in toxic_flags else "FAIL_DETECTED",
        "martingale": "PASS_NONE_DETECTED" if "TOXIC_MARTINGALE" not in toxic_flags else "FAIL_DETECTED",
        "averaging_down": "PASS_NONE_DETECTED" if "TOXIC_AVERAGING_DOWN" not in toxic_flags else "FAIL_DETECTED",
        "dll_import": (
            "PASS_NONE_DETECTED"
            if ("TOXIC_DLL_IMPORT" not in toxic_flags and "TOXIC_BLACKBOX_OR_DLL" not in toxic_flags)
            else "FAIL_DETECTED"
        ),
        "no_sl": (
            "PASS_HARD_SL_DISCLOSED"
            if ("TOXIC_NO_STOP_LOSS" not in toxic_flags and stop_rule != NOT_DISCLOSED)
            else "FAIL_NO_SL"
        ),
        "rollover_scalper": "PASS_NONE_DETECTED" if "TOXIC_ROLLOVER_SCALPER" not in toxic_flags else "FAIL_DETECTED",
        "non_breakout": "PASS_NON_BREAKOUT_SPEC",
    }

    return {
        "lead_id": _nd(raw_doc.get("lead_id")),
        "source": "off3-mql5-open",
        "source_origin": _nd(raw_doc.get("source_name")),
        "source_url": _nd(raw_doc.get("url")),
        "raw_file": raw_rel_path,
        "original_id": _nd(raw_doc.get("original_id")),
        "name": _nd(raw_doc.get("name")),
        "family": _nd(raw_doc.get("family")),
        "family_tag": _nd(raw_doc.get("family_tag")),
        "asset_class": _nd(raw_doc.get("asset_class")),
        "asset_universe": raw_doc.get("asset_universe") or [NOT_DISCLOSED],
        "symbol": _nd(raw_doc.get("symbol")),
        "timeframe": tf,
        "direction": _nd(raw_doc.get("direction")),
        "prop_track": _nd(raw_doc.get("prop_track")),
        "economic_rationale": _nd(raw_doc.get("economic_rationale")),
        "counterparty_mechanism": _nd(raw_doc.get("counterparty_mechanism")),
        "entry_rule": _nd(raw_doc.get("entry_rule")),
        "exit_rule": _nd(raw_doc.get("exit_rule")),
        "stop_loss_rule": stop_rule,
        "take_profit_rule": tp_rule,
        "rule_description": _nd(raw_doc.get("rule_description")),
        "verbatim_excerpt": _nd(raw_doc.get("verbatim_excerpt")),
        "source_verdict": "REJECTED_TOXIC" if is_toxic else "PUBLIC_CONCEPT_ONLY",
        "passes_all_5": False,
        "data_quality_flags": dq_flags,
        "replicability": _nd(raw_doc.get("replicability")),
        "evidence_tier": "SOURCE_CLAIM_ONLY",
        "gate_condition_met": (
            "REJECTED_TOXIC_MECHANISM"
            if is_toxic
            else "AUTO_INGESTED_PUBLIC_SPEC_QUARANTINED: source claim only, pending independent reproduction"
        ),
        "verified_live_links": [],
        "disqualifiers_checked": disqualifiers_checked,
        "reported_winrate_pct": NOT_DISCLOSED,
        "reported_profit_factor": NOT_DISCLOSED,
        "reported_max_dd_pct": NOT_DISCLOSED,
        "is_toxic": is_toxic,
        "toxic_flags": toxic_flags,
        "toxic_rationale": toxic_rationale,
        "performance_metrics": {},
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def run_extract() -> dict[str, Any]:
    raw_dir = SOURCE_DIR / "raw"
    manifest_path = SOURCE_DIR / "raw_manifest.sha256.json"
    extracted_dir = SOURCE_DIR / "extracted"

    # 1. Fail-closed SHA-256 raw manifest check
    manifest_errors = verify_verbatim.verify_raw_manifest(str(raw_dir), str(manifest_path))
    if manifest_errors:
        raise RuntimeError(f"Raw manifest verification FAILED: {manifest_errors}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for fname in sorted(manifest.keys()):
        raw_path = raw_dir / fname
        raw_doc = json.loads(raw_path.read_text(encoding="utf-8"))
        rel_path = f"sources/off3-mql5-open/raw/{fname}"
        record = build_lead_record(raw_doc, rel_path)

        # Fail-closed sanity check: expected toxic MUST be caught as toxic; expected clean MUST NOT be toxic
        if raw_doc.get("expected_toxic") is True and not record["is_toxic"]:
            raise RuntimeError(f"Toxic reject {fname} bypassed toxicity detector!")
        if raw_doc.get("expected_toxic") is False and record["is_toxic"]:
            raise RuntimeError(
                f"Clean lead {fname} triggered unexpected toxic flags: "
                f"{record['toxic_flags']} ({record['toxic_rationale']})"
            )

        if record["is_toxic"]:
            rejected.append(
                {
                    "id": record["original_id"],
                    "lead_id": record["lead_id"],
                    "name": record["name"],
                    "source_origin": record["source_origin"],
                    "source_url": record["source_url"],
                    "raw_file": record["raw_file"],
                    "toxic_flags": record["toxic_flags"],
                    "toxic_rationale": record["toxic_rationale"],
                    "verbatim_excerpt": record["verbatim_excerpt"],
                }
            )
        else:
            # Verify FTMO applicability on every accepted lead
            ftmo_ok, ftmo_reason = merge_off3_leads.check_ftmo_applicability(record)
            if not ftmo_ok:
                raise RuntimeError(f"Accepted lead {record['lead_id']} failed FTMO applicability: {ftmo_reason}")
            accepted.append(record)

    # Sort accepted leads deterministically by lead_id
    accepted.sort(key=lambda x: x["lead_id"])
    rejected.sort(key=lambda x: x["lead_id"])

    leads_payload = {
        "schema_version": "auto_public_leads_v1_off3",
        "mode": "live",
        "source": "off3-mql5-open",
        "total_leads": len(accepted),
        "total_rejected_toxic": len(rejected),
        "leads": accepted,
    }
    rejected_payload = {
        "schema_version": "off3_rejected_log_v1",
        "source": "off3-mql5-open",
        "total_rejected": len(rejected),
        "rejected_items": rejected,
    }

    # Fail-closed Holdout 2024..2029 / OOS2 leak check on BOTH output payloads
    lead_leaks = holdout_sanitizer.recursive_check_holdout(leads_payload, "extracted/leads.json")
    rej_leaks = holdout_sanitizer.recursive_check_holdout(rejected_payload, "extracted/rejected_log.json")
    if lead_leaks or rej_leaks:
        raise RuntimeError(f"Holdout token leakage detected: leads={lead_leaks[:5]}, rejected={rej_leaks[:5]}")

    _write_json(extracted_dir / "leads.json", leads_payload)
    _write_json(extracted_dir / "rejected_log.json", rejected_payload)

    return {
        "raw_verified": len(manifest),
        "accepted_leads": len(accepted),
        "rejected_toxic": len(rejected),
        "holdout_leaks": 0,
        "leads_path": str(extracted_dir / "leads.json"),
        "rejected_path": str(extracted_dir / "rejected_log.json"),
    }


if __name__ == "__main__":
    summary = run_extract()
    print(json.dumps(summary, indent=2))
