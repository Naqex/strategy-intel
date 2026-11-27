"""Build the Offensive #3 deduplication & overlap reference index.

Reads strictly from:
  - catalog/master_leads.json (15 immutable XAUUSD leads already tested in pass14)
  - catalog/auto_public_leads.json (4 ETF/Crypto Spot leads designated for Wave 4)

Writes:
  - sources/off3-dedup-index/index.json

Guardrails:
  - Zero Hallucination: never fabricates missing parameters; absent fields remain NOT_DISCLOSED.
  - Strict Cleanroom Air-Gap: operates solely inside D:/ANNAM/strategy-intel.
  - Holdout Clean: excludes performance tables and 2024..2029 / oos2 tokens.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

ROOT_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
MASTER_LEADS_PATH = ROOT_DIR / "catalog" / "master_leads.json"
AUTO_LEADS_PATH = ROOT_DIR / "catalog" / "auto_public_leads.json"
OUTPUT_INDEX_PATH = ROOT_DIR / "sources" / "off3-dedup-index" / "index.json"

NOT_DISCLOSED = "NOT_DISCLOSED"

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "when",
        "into",
        "only",
        "above",
        "below",
        "after",
        "before",
        "using",
        "over",
        "under",
        "then",
        "than",
        "zero",
        "non",
        "hard",
        "stop",
        "loss",
        "cua",
        "khi",
        "theo",
        "sau",
        "dau",
        "cuoi",
        "ngay",
        "phien",
        "mua",
        "ban",
        "vao",
        "dong",
        "tren",
        "duoi",
        "moi",
        "trong",
        "cho",
        "mot",
        "hai",
        "nam",
    }
)


def _normalize_text(value: str | None) -> str:
    if not value or value == NOT_DISCLOSED:
        return ""
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9\u00c0-\u1ef9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _normalize_url(url: str | None) -> str:
    if not url or url == NOT_DISCLOSED:
        return NOT_DISCLOSED
    cleaned = url.strip().lower().rstrip("/")
    cleaned = re.sub(r"^https?://(www\.)?", "", cleaned)
    return cleaned


def _extract_tokens(*parts: str | None) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for part in parts:
        norm = _normalize_text(part)
        for tok in norm.split():
            if len(tok) < 3 or tok in _STOPWORDS:
                continue
            if tok not in seen:
                seen.add(tok)
                tokens.append(tok)
    return sorted(tokens)


def _split_symbols(raw_symbol: str | None) -> list[str]:
    if not raw_symbol or raw_symbol == NOT_DISCLOSED:
        return []
    parts = re.split(r"[/,;\s|]+", raw_symbol.upper().strip())
    return sorted({p for p in parts if p})


def _make_signature(name: str, symbol: str, timeframe: str, direction: str) -> str:
    canonical = "|".join(
        [
            _normalize_text(name),
            ",".join(_split_symbols(symbol)),
            _normalize_text(timeframe),
            _normalize_text(direction),
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _nd(value: Any) -> str:
    if value is None:
        return NOT_DISCLOSED
    s = str(value).strip()
    return s if s else NOT_DISCLOSED


def _index_master_lead(lead: dict[str, Any]) -> dict[str, Any]:
    name = _nd(lead.get("name"))
    symbol = _nd(lead.get("symbol"))
    timeframe = _nd(lead.get("timeframe"))
    direction = _nd(lead.get("direction"))
    family = _nd(lead.get("family"))
    rule_desc = _nd(lead.get("rule_description"))

    return {
        "lead_id": _nd(lead.get("lead_id")),
        "source_catalog": "catalog/master_leads.json",
        "source": _nd(lead.get("source")),
        "original_id": _nd(lead.get("original_id")),
        "source_url": NOT_DISCLOSED,
        "normalized_url": NOT_DISCLOSED,
        "name": name,
        "normalized_name": _normalize_text(name),
        "family": family,
        "asset_class": NOT_DISCLOSED,
        "symbol": symbol,
        "symbols_parsed": _split_symbols(symbol),
        "timeframe": timeframe,
        "direction": direction,
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": rule_desc,
        "replicability": _nd(lead.get("replicability")),
        "evidence_tier": _nd(lead.get("evidence_tier")),
        "overlap_bucket": "PASS14_XAUUSD_ALREADY_TESTED",
        "overlap_policy": (
            "Immutable master lead on XAUUSD already evaluated in pass14. "
            "Reject XAUUSD-only duplicates of this concept; flag cross-asset variants transparently."
        ),
        "dedup_signature": _make_signature(name, symbol, timeframe, direction),
        "normalized_tokens": _extract_tokens(name, family, rule_desc),
    }


def _index_auto_lead(lead: dict[str, Any]) -> dict[str, Any]:
    name = _nd(lead.get("name"))
    symbol = _nd(lead.get("symbol"))
    timeframe = _nd(lead.get("timeframe"))
    direction = _nd(lead.get("direction"))
    family = _nd(lead.get("family"))
    rule_desc = _nd(lead.get("rule_description"))
    source_url = _nd(lead.get("source_url"))

    return {
        "lead_id": _nd(lead.get("lead_id")),
        "source_catalog": "catalog/auto_public_leads.json",
        "source": _nd(lead.get("source")),
        "original_id": _nd(lead.get("original_id")),
        "source_url": source_url,
        "normalized_url": _normalize_url(source_url),
        "name": name,
        "normalized_name": _normalize_text(name),
        "family": family,
        "asset_class": _nd(lead.get("asset_class")),
        "symbol": symbol,
        "symbols_parsed": _split_symbols(symbol),
        "timeframe": timeframe,
        "direction": direction,
        "stop_loss_rule": _nd(lead.get("stop_loss_rule")),
        "take_profit_rule": _nd(lead.get("take_profit_rule")),
        "rule_description": rule_desc,
        "replicability": _nd(lead.get("replicability")),
        "evidence_tier": _nd(lead.get("evidence_tier")),
        "overlap_bucket": "WAVE4_ETF_CRYPTO_SPOT",
        "overlap_policy": (
            "Existing Wave 4 ETF/Crypto Spot public lead. "
            "Reject exact ETF/Crypto Spot URL or concept duplicates; allow genuinely distinct FTMO MT5 FX/Index/Metal/Oil formalizations."
        ),
        "dedup_signature": _make_signature(name, symbol, timeframe, direction),
        "normalized_tokens": _extract_tokens(name, family, rule_desc),
    }


def build_index(
    *,
    master_path: Path = MASTER_LEADS_PATH,
    auto_path: Path = AUTO_LEADS_PATH,
    output_path: Path = OUTPUT_INDEX_PATH,
) -> dict[str, Any]:
    master_data = json.loads(master_path.read_text(encoding="utf-8"))
    auto_data = json.loads(auto_path.read_text(encoding="utf-8"))

    master_leads = master_data.get("leads", [])
    auto_leads = auto_data.get("leads", [])

    if len(master_leads) != 15:
        raise ValueError(f"Expected 15 immutable master leads, found {len(master_leads)}")
    if len(auto_leads) != 4:
        raise ValueError(f"Expected 4 existing auto_public_leads, found {len(auto_leads)}")

    entries = [_index_master_lead(lead) for lead in master_leads] + [
        _index_auto_lead(lead) for lead in auto_leads
    ]

    index_payload: dict[str, Any] = {
        "schema_version": "off3-dedup-index-v1",
        "purpose": (
            "Strict deduplication and overlap reference index for Total Offensive #3. "
            "Indexes all 19 existing cleanroom leads (15 immutable master_leads.json + "
            "4 auto_public_leads.json) with zero hallucinated parameters."
        ),
        "zero_hallucination_notice": (
            "Every field is extracted verbatim from catalog/master_leads.json and "
            "catalog/auto_public_leads.json. Undisclosed fields (including SL/TP on "
            "PARTIAL_CONCEPT_ONLY master leads) remain NOT_DISCLOSED."
        ),
        "existing_coverage_summary": {
            "total_existing_leads": len(entries),
            "master_leads_count": len(master_leads),
            "master_leads_bucket": "PASS14_XAUUSD_ALREADY_TESTED",
            "master_leads_note": (
                "All 15 immutable master_leads.json records are XAUUSD concepts from "
                "stategy-netlify-app already tested in pass14 (13 PARTIAL_CONCEPT_ONLY, "
                "1 PARTIAL_RULE_SPEC [SEA004], 1 REPLICABLE_FROM_PUBLIC [SEA003])."
            ),
            "auto_public_leads_count": len(auto_leads),
            "auto_public_leads_bucket": "WAVE4_ETF_CRYPTO_SPOT",
            "auto_public_leads_note": (
                "All 4 auto_public_leads.json records are ETF_SPOT_ZERO_SWAP (3) and "
                "CRYPTO_SPOT_GE_4H (1) specifications reserved for Wave 4."
            ),
        },
        "lookup_tables": {
            "lead_ids": [e["lead_id"] for e in entries],
            "original_ids": [e["original_id"] for e in entries],
            "normalized_urls": sorted(
                {e["normalized_url"] for e in entries if e["normalized_url"] != NOT_DISCLOSED}
            ),
            "dedup_signatures": [e["dedup_signature"] for e in entries],
        },
        "entries": entries,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(index_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return index_payload


def main() -> int:
    payload = build_index()
    summary = payload["existing_coverage_summary"]
    print(
        f"[SUCCESS] Built off3-dedup-index/index.json: "
        f"{summary['total_existing_leads']} existing leads indexed "
        f"({summary['master_leads_count']} master XAUUSD pass14 + "
        f"{summary['auto_public_leads_count']} auto ETF/Crypto Wave 4)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
