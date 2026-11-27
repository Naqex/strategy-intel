"""Merge, filter, and deduplicate Total Offensive #3 cleanroom crawler leads.

Inputs (strictly inside D:/ANNAM/strategy-intel):
  - sources/off3-dedup-index/index.json (19 existing cleanroom leads)
  - sources/off3-*/extracted/leads.json (all 6 Offensive #3 crawlers)
  - Optional: sources/off3-dedup-index/manual_dedup_overrides.json (auditor decisions)

Outputs:
  - catalog/auto_public_leads_v3.json (clean unique white-box Prop MT5 leads)
  - sources/off3-dedup-index/rejected_off3.json (all rejected toxic/non-FTMO/duplicate leads)
  - sources/off3-dedup-index/merge_audit_report.json (per-source counts, manifest checks, near-duplicate pairs)

Guardrails:
  - NEVER touches catalog/master_leads.json or inbox/ binaries.
  - ZERO Hallucination: missing fields explicitly set to NOT_DISCLOSED; never upgrades PARTIAL_CONCEPT_ONLY.
  - Rejects Grid, Martingale, Averaging-Down, No-SL, HFT-Arbitrage, Repainting/lookahead_on, Blackbox/DLL,
    non-FTMO assets, and duplicates (against existing 19 leads or cross-crawler overlaps).
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

ROOT_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
SCRIPTS_DIR = ROOT_DIR / "scripts"
COMMON_DIR = SCRIPTS_DIR / "common"
for _p in (str(SCRIPTS_DIR), str(COMMON_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_intel_ingest  # noqa: E402
import verify_verbatim  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"

# 28 FTMO MT5 symbols + canonical aliases commonly cited in academic / Pine / MQL5 / GitHub specs
FTMO_SYMBOL_TOKENS: frozenset[str] = frozenset(
    {
        # 17 FX pairs
        "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USDCHF", "NZDUSD",
        "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
        "EURGBP", "EURAUD", "GBPAUD", "EURCAD",
        # 6 Indices + standard index futures/CFD proxies
        "US500", "US100", "US30", "GER40", "UK100", "JP225",
        "SP500", "SPX", "SPX500", "NAS100", "NDX", "DJ30", "DJI", "DAX", "DE40", "GER30",
        "FTSE", "FTSE100", "NIKKEI", "NIKKEI225", "N225", "ES", "NQ", "YM", "FDAX",
        # 2 Metals
        "XAUUSD", "XAGUSD", "GOLD", "SILVER", "GC", "SI",
        # 2 Energy / Crude Oil
        "USOIL", "UKOIL", "WTI", "BRENT", "CRUDE", "CL", "USO",
        # 1 Crypto CFD
        "BTCUSD", "BTC", "BITCOIN",
        # Broad valid FTMO asset-class labels
        "FX", "FOREX", "G10", "MAJORS", "CROSSES", "INDICES", "INDEX",
        "METALS", "OIL", "ENERGY", "COMMODITIES", "MULTI-ASSET",
    }
)

# Strictly non-FTMO asset indicators (when no valid FTMO symbol/class is present)
NON_FTMO_ONLY_RE = re.compile(
    r"\b(single[- ]?stocks?|individual\s+equities|s&p\s*500\s+constituents|russell\s+2000\s+stocks|"
    r"0dte\s+options?|options?\s+greeks?|covered\s+call|iron\s+condor|straddle|strangle|"
    r"corporate\s+bonds?|municipal\s+bonds?|treasury\s+bills?\s+only|defi\s+yield|"
    r"altcoins?|meme\s*coins?|solana\s+meme|corn|wheat|soybeans?|lean\s+hogs|live\s+cattle|"
    r"sugar\s+futures|coffee\s+futures|natural\s+gas\s+only|a-shares?\s+only|csi\s*300\s+stocks)\b",
    re.IGNORECASE,
)

# Additional toxic mechanisms beyond auto_intel_ingest.TOXIC_PATTERNS
EXTRA_TOXIC_PATTERNS: tuple[tuple[str, re.Pattern[str], tuple[str, ...]], ...] = (
    (
        "TOXIC_REPAINTING_LOOKAHEAD",
        re.compile(
            r"\b(lookahead_on|barmerge\.lookahead_on|repaints?|repainting|future\s+leak|zig\s*zag\s+repaint)\b",
            re.IGNORECASE,
        ),
        (
            "non-repainting",
            "non repainting",
            "no repaint",
            "zero repaint",
            "not repaint",
            "never repaints",
            "without repaint",
            "avoids repaint",
            "lookahead_off",
            "no lookahead",
            "zero lookahead",
            "without lookahead",
            "avoiding lookahead",
            "no future leak",
            "zero future leak",
            "rejects lookahead",
            "filters out repaint",
            "no barmerge.lookahead_on",
        ),
    ),
    (
        "TOXIC_BLACKBOX_OR_DLL",
        re.compile(
            r"\b(invite[- ]only\s+script|closed[- ]source\s+blackbox|requires?\s+dll|dll\s+import|neural\s+blackbox\s+binary)\b",
            re.IGNORECASE,
        ),
        (
            "no dll",
            "zero dll",
            "without dll",
            "avoids dll",
            "no invite-only",
            "not invite-only",
            "open-source",
            "open source",
            "white-box",
            "whitebox",
        ),
    ),
)

_CLAUSE_SPLIT_RE = re.compile(r"(?:\.(?=\s|$)|[?!\n;])+")

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the", "and", "for", "with", "from", "that", "this", "when", "into", "only",
        "above", "below", "after", "before", "using", "over", "under", "then", "than",
        "zero", "non", "hard", "stop", "loss", "strategy", "trading", "system", "model",
        "based", "rule", "rules", "entry", "exit", "long", "short", "close", "open",
        "price", "market", "position", "signal", "signals", "filter", "ftmo", "swing",
        "intraday", "white", "box", "prop", "mt5", "public", "source", "spec",
        "not", "disclosed", "both", "daily", "bar", "bars", "candle", "candles",
    }
)

REPLICABILITY_RANK: dict[str, int] = {
    "REPLICABLE_FROM_PUBLIC": 4,
    "PARTIAL_RULE_SPEC": 3,
    "CONCEPT_ONLY_NEEDS_SLTP_DESIGN": 2,
    "PARTIAL_CONCEPT_ONLY": 1,
    NOT_DISCLOSED: 0,
}

# Known master_leads XAUUSD pass14 concept patterns for explicit overlap protection
MASTER_XAUUSD_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("LEAD-NETLIFY-BRK012", ("inside day", "inside bar breakout")),
    ("LEAD-NETLIFY-BRK035", ("4h", "monday", "opening range", "first 4")),
    ("LEAD-NETLIFY-IND026", ("ichimoku", "chikou")),
    ("LEAD-NETLIFY-IND041", ("roc", "rate of change")),
    ("LEAD-NETLIFY-IND049", ("alligator",)),
    ("LEAD-NETLIFY-IND053", ("momentum 10", "momentum crosses 100")),
    ("LEAD-NETLIFY-SEA003", ("turn-of-month", "turn of month", "turn of the month")),
    ("LEAD-NETLIFY-SEA004", ("start of quarter", "turn of quarter", "first 3 days of quarter")),
    ("LEAD-NETLIFY-SEA011", ("turnaround tuesday",)),
    ("LEAD-NETLIFY-SEA021", ("monday after nfp", "post-nfp monday")),
    ("LEAD-NETLIFY-NEN022", ("fakey", "false breakout inside bar")),
    ("LEAD-NETLIFY-VIR040", ("head & shoulders", "head and shoulders")),
)


def _nd(value: Any) -> str:
    if value is None:
        return NOT_DISCLOSED
    if isinstance(value, (list, tuple)):
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        return "/".join(cleaned) if cleaned else NOT_DISCLOSED
    s = str(value).strip()
    if not s or s.upper() in {"N/A", "NONE", "NULL", "TBD", "UNKNOWN"}:
        return NOT_DISCLOSED
    return s


def _normalize_text(text: str | None) -> str:
    if not text or text == NOT_DISCLOSED:
        return ""
    lowered = re.sub(r"[^a-z0-9\u00c0-\u1ef9]+", " ", text.lower().strip())
    return re.sub(r"\s+", " ", lowered).strip()


def _normalize_url(url: str | None) -> str:
    if not url or url == NOT_DISCLOSED:
        return NOT_DISCLOSED
    cleaned = url.strip().lower().rstrip("/")
    cleaned = re.sub(r"^https?://(www\.)?", "", cleaned)
    return cleaned


def _tokenize(*parts: str | None) -> set[str]:
    out: set[str] = set()
    for p in parts:
        norm = _normalize_text(p)
        for tok in norm.split():
            if len(tok) >= 3 and tok not in _STOPWORDS:
                out.add(tok)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _extract_universe_list(raw_item: dict[str, Any]) -> list[str]:
    raw_u = raw_item.get("asset_universe")
    if isinstance(raw_u, list):
        items = [str(x).strip() for x in raw_u if str(x).strip()]
        if items:
            return items
    elif isinstance(raw_u, str) and raw_u.strip() and raw_u.strip() != NOT_DISCLOSED:
        parts = [p.strip() for p in re.split(r"[,;/|]+", raw_u) if p.strip()]
        if parts:
            return parts

    sym = _nd(raw_item.get("symbol") or raw_item.get("symbols"))
    if sym != NOT_DISCLOSED:
        parts = [p.strip() for p in re.split(r"[,;/|]+", sym) if p.strip()]
        if parts:
            return parts
    return [NOT_DISCLOSED]


def _normalize_prop_track(raw_val: Any) -> str:
    s = _nd(raw_val)
    if s == NOT_DISCLOSED:
        return NOT_DISCLOSED
    up = s.upper().replace("-", "_").replace(" ", "_")
    if "INTRADAY" in up and "SWING" in up:
        return "BOTH_INTRADAY_AND_SWING"
    if "INTRADAY" in up or "SWAP0" in up or "SWAP_0" in up:
        return "INTRADAY_SWAP0"
    if "SWING" in up:
        return "FTMO_SWING"
    return NOT_DISCLOSED


def _normalize_replicability(raw_val: Any) -> str:
    s = _nd(raw_val)
    if s == NOT_DISCLOSED:
        return "PARTIAL_CONCEPT_ONLY"
    up = s.upper().strip()
    if up in REPLICABILITY_RANK:
        return up
    if "REPLICABLE" in up:
        return "REPLICABLE_FROM_PUBLIC"
    if "SLTP" in up:
        return "CONCEPT_ONLY_NEEDS_SLTP_DESIGN"
    if "PARTIAL_RULE" in up:
        return "PARTIAL_RULE_SPEC"
    return "PARTIAL_CONCEPT_ONLY"


def detect_all_toxic_signals(text: str) -> tuple[bool, list[str], str]:
    is_tox, flags, rationale = auto_intel_ingest.detect_toxic_signals(text)
    matched_flags = list(flags)
    excerpts = [rationale] if is_tox and rationale else []

    clauses = [c.strip() for c in _CLAUSE_SPLIT_RE.split(text or "") if c.strip()]
    for clause in clauses:
        cl = clause.lower()
        for flag, rx, negations in EXTRA_TOXIC_PATTERNS:
            if rx.search(clause):
                if any(neg in cl for neg in negations):
                    continue
                if flag not in matched_flags:
                    matched_flags.append(flag)
                    excerpts.append(f'{flag}: "{clause[:160]}"')

    if matched_flags:
        return True, matched_flags, " | ".join(excerpts)
    return False, [], "No toxic Grid/Martingale/No-SL/Repaint/Blackbox signal detected."


def check_ftmo_applicability(lead: dict[str, Any]) -> tuple[bool, str]:
    """Return (is_ftmo_applicable, reason). Rejects strictly non-FTMO stock/options/altcoin/grain specs."""
    universe_tokens = set()
    for item in lead.get("asset_universe", []):
        for tok in re.split(r"[^A-Za-z0-9]+", str(item).upper()):
            if tok:
                universe_tokens.add(tok)
    sym_str = str(lead.get("symbol", "")).upper()
    for tok in re.split(r"[^A-Za-z0-9]+", sym_str):
        if tok:
            universe_tokens.add(tok)

    has_ftmo_symbol = bool(universe_tokens & FTMO_SYMBOL_TOKENS)
    combined_asset_text = " ".join(
        [
            str(lead.get("asset_class", "")),
            str(lead.get("symbol", "")),
            " ".join(str(x) for x in lead.get("asset_universe", [])),
            str(lead.get("name", "")),
            str(lead.get("rule_description", "")),
        ]
    )

    if not has_ftmo_symbol:
        # Check if any FTMO token appears in asset_class/title/description
        text_tokens = set(re.split(r"[^A-Za-z0-9]+", combined_asset_text.upper()))
        has_ftmo_symbol = bool(text_tokens & FTMO_SYMBOL_TOKENS)

    non_ftmo_match = NON_FTMO_ONLY_RE.search(combined_asset_text)
    if non_ftmo_match and not has_ftmo_symbol:
        return False, f"NON_FTMO_ASSET_UNIVERSE: matched '{non_ftmo_match.group(0)}' with no FTMO MT5 symbol mapping"

    # Reject pure ETF-only or Crypto-Spot-only specs with no FTMO symbol
    ac_upper = str(lead.get("asset_class", "")).upper()
    if ac_upper in {"ETF_SPOT_ZERO_SWAP", "SINGLE_STOCK_EQUITY", "OPTIONS"} and not has_ftmo_symbol:
        return False, f"NON_FTMO_ASSET_CLASS: '{ac_upper}' without FTMO MT5 CFD universe"

    if not has_ftmo_symbol and lead.get("symbol") == NOT_DISCLOSED:
        return False, "NON_FTMO_MISSING_UNIVERSE: symbol and asset_universe both NOT_DISCLOSED"

    return True, "FTMO_MT5_APPLICABLE"


def _is_xauusd_only(lead: dict[str, Any]) -> bool:
    tokens = set()
    for item in lead.get("asset_universe", []):
        for tok in re.split(r"[^A-Za-z0-9]+", str(item).upper()):
            if tok and tok not in {"CFD", "METAL", "METALS", "SPOT", "USD"}:
                tokens.add(tok)
    if not tokens:
        sym = str(lead.get("symbol", "")).upper()
        for tok in re.split(r"[^A-Za-z0-9]+", sym):
            if tok:
                tokens.add(tok)
    return bool(tokens) and tokens.issubset({"XAUUSD", "GOLD", "GC", "XAU"})


def normalize_crawler_lead(raw_item: dict[str, Any], source_folder: str, idx: int) -> dict[str, Any]:
    """Normalize a crawler lead record strictly without fabricating missing parameters."""
    name = _nd(raw_item.get("name") or raw_item.get("title"))
    family = _nd(raw_item.get("family") or raw_item.get("family_tag"))
    family_tag = _nd(raw_item.get("family_tag") or raw_item.get("family"))
    universe = _extract_universe_list(raw_item)
    symbol = _nd(raw_item.get("symbol") or raw_item.get("symbols") or universe)
    timeframe = _nd(raw_item.get("timeframe") or raw_item.get("timeframes"))
    direction = _nd(raw_item.get("direction"))

    entry_rule = _nd(raw_item.get("entry_rule"))
    exit_rule = _nd(raw_item.get("exit_rule"))
    stop_loss_rule = _nd(raw_item.get("stop_loss_rule") or raw_item.get("sl_rule"))
    take_profit_rule = _nd(raw_item.get("take_profit_rule") or raw_item.get("tp_rule"))
    economic_rationale = _nd(raw_item.get("economic_rationale"))
    counterparty_mech = _nd(raw_item.get("counterparty_mechanism"))

    rule_desc = _nd(raw_item.get("rule_description"))
    if rule_desc == NOT_DISCLOSED:
        composed_parts = []
        if entry_rule != NOT_DISCLOSED:
            composed_parts.append(f"Entry: {entry_rule}")
        if exit_rule != NOT_DISCLOSED:
            composed_parts.append(f"Exit: {exit_rule}")
        if stop_loss_rule != NOT_DISCLOSED:
            composed_parts.append(f"SL: {stop_loss_rule}")
        rule_desc = " | ".join(composed_parts) if composed_parts else NOT_DISCLOSED

    verbatim_excerpt = _nd(raw_item.get("verbatim_excerpt") or raw_item.get("abstract") or raw_item.get("summary"))
    source_url = _nd(raw_item.get("source_url") or raw_item.get("url"))
    source_origin = _nd(raw_item.get("source_origin") or raw_item.get("source_name") or source_folder)
    raw_file = _nd(raw_item.get("raw_file"))
    orig_id = _nd(raw_item.get("original_id") or raw_item.get("lead_id") or f"{source_folder.upper()}-{idx:03d}")

    lead_id = _nd(raw_item.get("lead_id"))
    if lead_id == NOT_DISCLOSED:
        slug = re.sub(r"[^A-Z0-9]+", "-", orig_id.upper()).strip("-")
        lead_id = f"LEAD-OFF3-{slug}"

    replicability = _normalize_replicability(raw_item.get("replicability"))
    prop_track = _normalize_prop_track(raw_item.get("prop_track"))
    asset_class = _nd(raw_item.get("asset_class"))

    dq_flags = list(raw_item.get("data_quality_flags") or [])
    for required_flag in ("AUTO_INGESTED_UNTRUSTED_PUBLIC_SPEC", "UNVERIFIED_EXTERNAL_CLAIM"):
        if required_flag not in dq_flags:
            dq_flags.append(required_flag)
    if stop_loss_rule == NOT_DISCLOSED and "STOP_LOSS_RULE_NOT_DISCLOSED" not in dq_flags:
        dq_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
    if timeframe == NOT_DISCLOSED and "TIMEFRAME_NOT_DISCLOSED" not in dq_flags:
        dq_flags.append("TIMEFRAME_NOT_DISCLOSED")

    disqualifiers_checked = raw_item.get("disqualifiers_checked")
    if not isinstance(disqualifiers_checked, (list, dict)):
        disqualifiers_checked = ["grid_martingale_checked", "no_sl_checked", "repaint_checked"]

    return {
        "lead_id": lead_id,
        "source": source_folder,
        "source_origin": source_origin,
        "source_url": source_url,
        "raw_file": raw_file,
        "original_id": orig_id,
        "name": name,
        "family": family,
        "family_tag": family_tag,
        "asset_class": asset_class,
        "asset_universe": universe,
        "symbol": symbol,
        "timeframe": timeframe,
        "direction": direction,
        "prop_track": prop_track,
        "economic_rationale": economic_rationale,
        "counterparty_mechanism": counterparty_mech,
        "entry_rule": entry_rule,
        "exit_rule": exit_rule,
        "stop_loss_rule": stop_loss_rule,
        "take_profit_rule": take_profit_rule,
        "rule_description": rule_desc,
        "verbatim_excerpt": verbatim_excerpt,
        "source_verdict": "PUBLIC_CONCEPT_ONLY",
        "passes_all_5": False,
        "data_quality_flags": dq_flags,
        "replicability": replicability,
        "evidence_tier": "SOURCE_CLAIM_ONLY",
        "gate_condition_met": (
            "OFFENSIVE3_CLEANROOM_SPEC_QUARANTINED: source claim only, pending independent Dev M1 Bid/Ask verification"
        ),
        "verified_live_links": [],
        "disqualifiers_checked": disqualifiers_checked,
        "reported_winrate_pct": NOT_DISCLOSED,
        "reported_profit_factor": NOT_DISCLOSED,
        "reported_max_dd_pct": NOT_DISCLOSED,
        "dedup_status": "UNIQUE_OFF3",
        "overlap_flags": [],
        "performance_metrics": {},
    }


def _lead_completeness_score(lead: dict[str, Any]) -> tuple[int, int, int, int]:
    """Deterministic tie-breaker preferring richer verbatim white-box specs when deduplicating."""
    rep_rank = REPLICABILITY_RANK.get(lead.get("replicability", NOT_DISCLOSED), 0)
    non_nd_fields = sum(
        1
        for k in (
            "entry_rule",
            "exit_rule",
            "stop_loss_rule",
            "take_profit_rule",
            "economic_rationale",
            "counterparty_mechanism",
            "timeframe",
            "prop_track",
            "source_url",
            "verbatim_excerpt",
        )
        if lead.get(k) not in (None, "", NOT_DISCLOSED)
    )
    has_hard_sl = 1 if lead.get("stop_loss_rule") not in (None, "", NOT_DISCLOSED) else 0
    desc_len = len(str(lead.get("rule_description", "")))
    return (rep_rank, has_hard_sl, non_nd_fields, desc_len)


def _check_existing_index_overlap(
    lead: dict[str, Any],
    existing_entries: list[dict[str, Any]],
) -> tuple[bool, str | None, str | None, list[str]]:
    """Return (is_duplicate, dup_category, matched_existing_id, overlap_flags)."""
    overlap_flags: list[str] = []
    lead_url = _normalize_url(lead.get("source_url"))
    lead_name_norm = _normalize_text(lead.get("name"))
    lead_tokens = _tokenize(lead.get("name"), lead.get("rule_description"), lead.get("entry_rule"))
    xau_only = _is_xauusd_only(lead)
    lead_text_low = " ".join(
        [
            str(lead.get("name", "")),
            str(lead.get("rule_description", "")),
            str(lead.get("entry_rule", "")),
        ]
    ).lower()

    for ex in existing_entries:
        ex_id = ex["lead_id"]
        bucket = ex["overlap_bucket"]

        # 1. Exact lead_id or original_id match
        if lead["lead_id"] == ex_id or (
            lead["original_id"] != NOT_DISCLOSED and lead["original_id"] == ex["original_id"]
        ):
            return True, f"DUPLICATE_EXISTING_{bucket}", ex_id, overlap_flags

        # 2. Exact normalized URL match
        ex_url = ex.get("normalized_url", NOT_DISCLOSED)
        if lead_url != NOT_DISCLOSED and ex_url != NOT_DISCLOSED and lead_url == ex_url:
            if bucket == "WAVE4_ETF_CRYPTO_SPOT":
                # Same Quantpedia/GitHub URL as Wave 4 auto lead
                return True, "DUPLICATE_EXISTING_WAVE4_URL", ex_id, overlap_flags
            return True, f"DUPLICATE_EXISTING_{bucket}_URL", ex_id, overlap_flags

        # 3. Exact normalized name match
        if lead_name_norm and ex.get("normalized_name") and lead_name_norm == ex["normalized_name"]:
            if bucket == "PASS14_XAUUSD_ALREADY_TESTED" and xau_only:
                return True, "DUPLICATE_MASTER_LEAD_PASS14", ex_id, overlap_flags
            if bucket == "WAVE4_ETF_CRYPTO_SPOT":
                return True, "DUPLICATE_WAVE4_AUTO_LEAD", ex_id, overlap_flags

        # 4. High token similarity against existing entry
        ex_tokens = set(ex.get("normalized_tokens", []))
        sim = _jaccard(lead_tokens, ex_tokens)
        if sim >= 0.60:
            if bucket == "PASS14_XAUUSD_ALREADY_TESTED" and xau_only:
                return True, "DUPLICATE_MASTER_LEAD_PASS14", ex_id, overlap_flags
            if bucket == "PASS14_XAUUSD_ALREADY_TESTED":
                overlap_flags.append(f"CONCEPT_RELATED_TO_PASS14:{ex_id}")
            else:
                overlap_flags.append(f"CONCEPT_RELATED_TO_WAVE4:{ex_id}")

    # 5. Explicit XAUUSD-only concept overlap against pass14 master leads
    for master_id, phrases in MASTER_XAUUSD_CONCEPTS:
        if any(phrase in lead_text_low for phrase in phrases):
            if xau_only:
                return True, "DUPLICATE_MASTER_LEAD_PASS14_CONCEPT", master_id, overlap_flags
            flag = f"MULTI_ASSET_EXTENSION_OF_PASS14:{master_id}"
            if flag not in overlap_flags:
                overlap_flags.append(flag)

    return False, None, None, overlap_flags


def load_crawler_leads(root_dir: Path) -> tuple[list[tuple[str, list[dict[str, Any]]]], dict[str, Any]]:
    sources_dir = root_dir / "sources"
    crawler_files = sorted(sources_dir.glob("off3-*/extracted/leads.json"))
    loaded: list[tuple[str, list[dict[str, Any]]]] = []
    source_stats: dict[str, Any] = {}

    for leads_path in crawler_files:
        source_folder = leads_path.parent.parent.name
        if source_folder == "off3-dedup-index":
            continue
        raw_data = json.loads(leads_path.read_text(encoding="utf-8"))
        if isinstance(raw_data, list):
            items = raw_data
        elif isinstance(raw_data, dict):
            items = raw_data.get("leads") or raw_data.get("items") or []
        else:
            items = []

        # Also check raw_manifest.sha256.json integrity for each off3 crawler
        raw_dir = leads_path.parent.parent / "raw"
        manifest_path = leads_path.parent.parent / "raw_manifest.sha256.json"
        manifest_errors = (
            verify_verbatim.verify_raw_manifest(str(raw_dir), str(manifest_path))
            if raw_dir.exists()
            else [f"Missing raw dir: {raw_dir}"]
        )

        loaded.append((source_folder, items))
        source_stats[source_folder] = {
            "leads_file": str(leads_path.relative_to(root_dir)).replace("\\", "/"),
            "raw_input_count": len(items),
            "raw_manifest_valid": len(manifest_errors) == 0,
            "raw_manifest_errors": manifest_errors[:5],
        }

    return loaded, source_stats


def merge_and_deduplicate(
    *,
    root_dir: Path = ROOT_DIR,
    name_jaccard_threshold: float = 0.65,
    rule_jaccard_threshold: float = 0.62,
    near_dup_report_threshold: float = 0.35,
    overrides_path: Path | None = None,
) -> dict[str, Any]:
    index_path = root_dir / "sources" / "off3-dedup-index" / "index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"Dedup index missing: {index_path}. Run build_dedup_index.py first.")
    dedup_index = json.loads(index_path.read_text(encoding="utf-8"))
    existing_entries = dedup_index.get("entries", [])

    # Optional manual dedup overrides (auditor-verified cross-crawler duplicates)
    manual_drop_map: dict[str, dict[str, str]] = {}
    ov_path = overrides_path or (root_dir / "sources" / "off3-dedup-index" / "manual_dedup_overrides.json")
    if ov_path.exists():
        ov_data = json.loads(ov_path.read_text(encoding="utf-8"))
        for entry in ov_data.get("drop_as_duplicate", []):
            manual_drop_map[entry["drop_lead_id"]] = entry

    loaded_sources, source_stats = load_crawler_leads(root_dir)

    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_lead_ids: set[str] = set()

    # Stage 1: Normalize, Toxic Filter, FTMO Applicability Filter, Existing-19 Index Check
    for source_folder, raw_items in loaded_sources:
        src_accepted_pre_dedup = 0
        src_rejected = 0
        for idx, raw_item in enumerate(raw_items, start=1):
            if not isinstance(raw_item, dict):
                continue
            lead = normalize_crawler_lead(raw_item, source_folder, idx)

            # Ensure unique lead_id across crawlers before dedup
            if lead["lead_id"] in seen_lead_ids:
                suffix = hashlib.sha256(f"{source_folder}:{idx}:{lead['name']}".encode("utf-8")).hexdigest()[:6].upper()
                lead["lead_id"] = f"{lead['lead_id']}-{suffix}"
            seen_lead_ids.add(lead["lead_id"])

            # 1a. Check if crawler itself already flagged toxic / rejected
            if raw_item.get("is_toxic") is True or str(raw_item.get("source_verdict", "")).upper().startswith("REJECTED"):
                rejected.append(
                    {
                        "lead_id": lead["lead_id"],
                        "source": source_folder,
                        "name": lead["name"],
                        "source_url": lead["source_url"],
                        "category": "TOXIC_FLAGGED_BY_CRAWLER",
                        "reason": str(raw_item.get("toxic_rationale") or raw_item.get("source_verdict") or "Flagged toxic by crawler"),
                    }
                )
                src_rejected += 1
                continue

            # 1b. Independent toxic audit across all rule fields
            toxic_text = "\n".join(
                p
                for p in (
                    lead["name"],
                    lead["entry_rule"],
                    lead["exit_rule"],
                    lead["stop_loss_rule"],
                    lead["rule_description"],
                    lead["verbatim_excerpt"],
                )
                if p != NOT_DISCLOSED
            )
            is_toxic, toxic_flags, toxic_rationale = detect_all_toxic_signals(toxic_text)
            if is_toxic:
                rejected.append(
                    {
                        "lead_id": lead["lead_id"],
                        "source": source_folder,
                        "name": lead["name"],
                        "source_url": lead["source_url"],
                        "category": "TOXIC_MECHANISM_REJECTED",
                        "toxic_flags": toxic_flags,
                        "reason": toxic_rationale,
                    }
                )
                src_rejected += 1
                continue

            # 1c. FTMO MT5 applicability check
            ftmo_ok, ftmo_reason = check_ftmo_applicability(lead)
            if not ftmo_ok:
                rejected.append(
                    {
                        "lead_id": lead["lead_id"],
                        "source": source_folder,
                        "name": lead["name"],
                        "source_url": lead["source_url"],
                        "category": "NON_FTMO_OUT_OF_UNIVERSE",
                        "reason": ftmo_reason,
                    }
                )
                src_rejected += 1
                continue

            # 1d. Existing 19-lead dedup index check
            is_ex_dup, ex_cat, ex_match_id, overlap_flags = _check_existing_index_overlap(lead, existing_entries)
            if is_ex_dup:
                rejected.append(
                    {
                        "lead_id": lead["lead_id"],
                        "source": source_folder,
                        "name": lead["name"],
                        "source_url": lead["source_url"],
                        "category": ex_cat or "DUPLICATE_EXISTING_INDEX",
                        "matched_canonical_id": ex_match_id,
                        "reason": f"Overlaps existing indexed lead {ex_match_id} ({ex_cat}).",
                    }
                )
                src_rejected += 1
                continue

            lead["overlap_flags"] = overlap_flags
            candidates.append(lead)
            src_accepted_pre_dedup += 1

        source_stats[source_folder]["passed_stage1_filters"] = src_accepted_pre_dedup
        source_stats[source_folder]["rejected_stage1"] = src_rejected

    # Stage 2: Cross-crawler & intra-crawler deduplication (prefer highest completeness spec)
    # Sort candidates by completeness descending so best spec becomes canonical winner deterministically
    candidates.sort(key=lambda item: (_lead_completeness_score(item), item["lead_id"]), reverse=True)

    accepted: list[dict[str, Any]] = []
    accepted_meta: list[dict[str, Any]] = []
    near_duplicate_pairs: list[dict[str, Any]] = []

    for lead in candidates:
        lid = lead["lead_id"]
        if lid in manual_drop_map:
            ov = manual_drop_map[lid]
            rejected.append(
                {
                    "lead_id": lid,
                    "source": lead["source"],
                    "name": lead["name"],
                    "source_url": lead["source_url"],
                    "category": "DUPLICATE_CROSS_CRAWLER_AUDITED",
                    "matched_canonical_id": ov.get("canonical_lead_id", NOT_DISCLOSED),
                    "reason": ov.get("reason", "Manual auditor cross-crawler duplicate confirmation."),
                }
            )
            continue

        norm_url = _normalize_url(lead["source_url"])
        norm_name = _normalize_text(lead["name"])
        name_tokens = _tokenize(lead["name"])
        rule_tokens = _tokenize(lead["name"], lead["entry_rule"], lead["exit_rule"], lead["rule_description"])

        matched_dup: tuple[str, str, float] | None = None
        for idx_a, acc in enumerate(accepted):
            meta = accepted_meta[idx_a]

            # Exact URL match (ignore generic homepages / search pages / NOT_DISCLOSED)
            if (
                norm_url != NOT_DISCLOSED
                and meta["norm_url"] != NOT_DISCLOSED
                and norm_url == meta["norm_url"]
                and "/" in norm_url
            ):
                matched_dup = (acc["lead_id"], "DUPLICATE_EXACT_URL", 1.0)
                break

            # Exact normalized title match
            if norm_name and meta["norm_name"] and norm_name == meta["norm_name"]:
                matched_dup = (acc["lead_id"], "DUPLICATE_EXACT_NAME", 1.0)
                break

            name_sim = _jaccard(name_tokens, meta["name_tokens"])
            rule_sim = _jaccard(rule_tokens, meta["rule_tokens"])

            if name_sim >= name_jaccard_threshold and rule_sim >= 0.35:
                matched_dup = (acc["lead_id"], "DUPLICATE_HIGH_TITLE_AND_RULE_SIMILARITY", round(max(name_sim, rule_sim), 3))
                break
            if rule_sim >= rule_jaccard_threshold:
                matched_dup = (acc["lead_id"], "DUPLICATE_HIGH_RULE_SIMILARITY", round(rule_sim, 3))
                break

            # Record borderline pairs for manual auditor inspection
            if name_sim >= near_dup_report_threshold or rule_sim >= near_dup_report_threshold:
                near_duplicate_pairs.append(
                    {
                        "lead_a_id": acc["lead_id"],
                        "lead_a_source": acc["source"],
                        "lead_a_name": acc["name"],
                        "lead_b_id": lid,
                        "lead_b_source": lead["source"],
                        "lead_b_name": lead["name"],
                        "name_jaccard": round(name_sim, 3),
                        "rule_jaccard": round(rule_sim, 3),
                    }
                )

        if matched_dup is not None:
            canon_id, dup_cat, score = matched_dup
            rejected.append(
                {
                    "lead_id": lid,
                    "source": lead["source"],
                    "name": lead["name"],
                    "source_url": lead["source_url"],
                    "category": dup_cat,
                    "matched_canonical_id": canon_id,
                    "similarity_score": score,
                    "reason": f"Cross-crawler duplicate of canonical lead {canon_id} ({dup_cat}, sim={score}).",
                }
            )
            continue

        accepted.append(lead)
        accepted_meta.append(
            {
                "norm_url": norm_url,
                "norm_name": norm_name,
                "name_tokens": name_tokens,
                "rule_tokens": rule_tokens,
            }
        )

    # Sort final accepted leads deterministically by source, then lead_id
    accepted.sort(key=lambda item: (item["source"], item["lead_id"]))
    near_duplicate_pairs.sort(key=lambda item: max(item["name_jaccard"], item["rule_jaccard"]), reverse=True)

    # Compute summaries
    per_source_accepted = Counter(item["source"] for item in accepted)
    prop_track_counts = Counter(item["prop_track"] for item in accepted)
    family_counts = Counter(item["family_tag"] for item in accepted)
    replicability_counts = Counter(item["replicability"] for item in accepted)
    rejection_counts = Counter(item["category"] for item in rejected)

    for src, st in source_stats.items():
        st["final_unique_accepted"] = per_source_accepted.get(src, 0)

    dedup_summary = {
        "existing_reference_leads": len(existing_entries),
        "raw_crawler_inputs": sum(st["raw_input_count"] for st in source_stats.values()),
        "total_unique_accepted": len(accepted),
        "total_rejected": len(rejected),
        "rejection_breakdown": dict(sorted(rejection_counts.items())),
        "replicability_breakdown": dict(sorted(replicability_counts.items())),
        "per_source_accepted": dict(sorted(per_source_accepted.items())),
    }

    catalog_v3 = {
        "schema_version": "off3-catalog-v3",
        "source": "offensive3-multi-crawler-merged",
        "sources_merged": sorted(source_stats.keys()),
        "dedup_index_reference": "sources/off3-dedup-index/index.json",
        "dedup_summary": dedup_summary,
        "prop_track_breakdown": dict(sorted(prop_track_counts.items())),
        "family_breakdown": dict(sorted(family_counts.items())),
        "total_leads": len(accepted),
        "leads": accepted,
    }

    # Also collect any crawler-side pre-rejected toxic logs for unified audit trail
    crawler_pre_rejected: list[dict[str, Any]] = []
    for log_pattern in ("off3-*/extracted/*reject*.json", "off3-*/extracted/*disqualif*.json"):
        for log_path in sorted((root_dir / "sources").glob(log_pattern)):
            src_name = log_path.parent.parent.name
            if src_name == "off3-dedup-index":
                continue
            raw_log = json.loads(log_path.read_text(encoding="utf-8"))
            items = raw_log.get("rejected_items") or raw_log.get("disqualified_items") or []
            for item in items:
                if not isinstance(item, dict):
                    continue
                crawler_pre_rejected.append(
                    {
                        "lead_id": item.get("lead_id") or item.get("id") or NOT_DISCLOSED,
                        "source": src_name,
                        "name": item.get("name") or NOT_DISCLOSED,
                        "source_url": item.get("source_url") or NOT_DISCLOSED,
                        "category": "CRAWLER_PRE_REJECTED_TOXIC",
                        "toxic_flags": item.get("toxic_flags", []),
                        "reason": item.get("toxic_rationale") or item.get("reason") or "Disqualified during crawler triage",
                        "source_log_file": str(log_path.relative_to(root_dir)).replace("\\", "/"),
                    }
                )

    rejected_payload = {
        "schema_version": "off3-rejected-log-v1",
        "total_rejected": len(rejected),
        "crawler_pre_rejected_toxic_count": len(crawler_pre_rejected),
        "total_rejected_including_crawler_triage": len(rejected) + len(crawler_pre_rejected),
        "rejection_breakdown": dict(sorted(rejection_counts.items())),
        "rejected_items": rejected,
        "crawler_pre_rejected_toxic_items": crawler_pre_rejected,
    }

    audit_report = {
        "schema_version": "off3-merge-audit-v1",
        "sources_audited": source_stats,
        "dedup_summary": dedup_summary,
        "prop_track_breakdown": dict(sorted(prop_track_counts.items())),
        "family_breakdown": dict(sorted(family_counts.items())),
        "near_duplicate_pairs_for_review_count": len(near_duplicate_pairs),
        "top_near_duplicate_pairs": near_duplicate_pairs[:60],
    }

    catalog_v3_path = root_dir / "catalog" / "auto_public_leads_v3.json"
    rejected_off3_path = root_dir / "sources" / "off3-dedup-index" / "rejected_off3.json"
    audit_report_path = root_dir / "sources" / "off3-dedup-index" / "merge_audit_report.json"

    for out_p, data_obj in (
        (catalog_v3_path, catalog_v3),
        (rejected_off3_path, rejected_payload),
        (audit_report_path, audit_report),
    ):
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(data_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    return audit_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="Cleanroom repository root")
    parser.add_argument("--name-sim", type=float, default=0.65, help="Title Jaccard dedup threshold")
    parser.add_argument("--rule-sim", type=float, default=0.62, help="Rule Jaccard dedup threshold")
    args = parser.parse_args(argv)

    report = merge_and_deduplicate(
        root_dir=args.root,
        name_jaccard_threshold=args.name_sim,
        rule_jaccard_threshold=args.rule_sim,
    )
    ds = report["dedup_summary"]
    print(
        f"[SUCCESS] Offensive #3 merge complete: "
        f"raw_inputs={ds['raw_crawler_inputs']}, unique_accepted={ds['total_unique_accepted']}, "
        f"rejected={ds['total_rejected']}, near_dup_pairs={report['near_duplicate_pairs_for_review_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
