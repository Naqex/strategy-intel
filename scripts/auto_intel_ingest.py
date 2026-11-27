"""Air-gapped public text-only strategy intelligence auto-ingestor.

Operates strictly inside the cleanroom repository:
  sources/public-auto-ingest/raw/ + raw_manifest.sha256.json
    -> sources/public-auto-ingest/extracted/
    -> catalog/auto_public_leads.json
    -> handoff/sanitized_auto_leads.json (Holdout 2024..2029 / OOS2 scrubbed)

Guardrails:
  1. Pure text/HTML/JSON only — strict binary URL, header, and magic-byte blocker.
  2. Zero Hallucination — missing fields explicitly set to NOT_DISCLOSED + verbatim excerpts.
  3. Toxic rejection — Grid, Martingale, Averaging-Down, No-SL, and HFT-Arbitrage are rejected.
  4. Holdout sanitization — zero 2024..2029 / oos2 tokens or 2024..2099 integers in handoff/.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import urllib.request

ROOT_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
COMMON_DIR = ROOT_DIR / "scripts" / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

import holdout_sanitizer  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"
MAX_TEXT_BYTES = 512 * 1024
LIVE_TIMEOUT_SECONDS = 10

BLOCKED_BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".ex4",
        ".ex5",
        ".mq4",
        ".mq5",
        ".dll",
        ".exe",
        ".msi",
        ".bat",
        ".cmd",
        ".ps1",
        ".vbs",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bin",
        ".iso",
        ".dmg",
        ".pkg",
        ".apk",
        ".scr",
        ".com",
    }
)

ALLOWED_CONTENT_TYPE_PREFIXES: tuple[str, ...] = (
    "text/plain",
    "text/html",
    "text/markdown",
    "text/xml",
    "application/json",
    "application/ld+json",
    "application/xml",
    "application/xhtml+xml",
)

BINARY_MAGIC_SIGNATURES: tuple[bytes, ...] = (
    b"MZ",
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"Rar!\x1a\x07",
    b"7z\xbc\xaf\x27\x1c",
    b"\x1f\x8b",
    b"\x7fELF",
    b"\xca\xfe\xba\xbe",
    b"\xd0\xcf\x11\xe0",
)

DEFAULT_LIVE_PUBLIC_URLS: tuple[str, ...] = (
    "https://quantpedia.com/strategies/time-series-momentum-effect/",
    "https://quantpedia.com/strategies/dual-momentum-model/",
    "https://quantpedia.com/strategies/trend-following-effect-in-stocks/",
)

MARTINGALE_NEGATION_PHRASES: tuple[str, ...] = (
    "no martingale",
    "non-martingale",
    "zero martingale",
    "without martingale",
    "avoids martingale",
    "avoiding martingale",
    "rejects martingale",
    "does not use martingale",
    "never uses martingale",
    "no lot multiplier",
    "no leverage multiplier",
)

GRID_NEGATION_PHRASES: tuple[str, ...] = (
    "no grid",
    "non-grid",
    "zero grid",
    "without grid",
    "avoids grid",
    "avoiding grid",
    "rejects grid",
    "does not use grid",
    "never uses grid",
    "never averages down",
    "no averaging down",
    "without averaging",
    "no cost averaging",
)

_CLAUSE_SPLIT_RE = re.compile(r"(?:\.(?=\s|$)|[?!\n;])+")

TOXIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "TOXIC_MARTINGALE",
        re.compile(
            r"\b(martingale|lot\s*multiplier|recovery\s*lot|double\s*lot|doubles?\s+(?:the\s+)?lot|"
            r"geometric\s+lot\s+sizing)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_GRID",
        re.compile(
            r"\b(grid\s*trading|grid\s*strategy|grid\s*system|grid\s*step|hedging\s*grid|"
            r"averaging\s*down|cost[- ]averaging|adds?\s+losing\s+layers?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_NO_STOP_LOSS",
        re.compile(
            r"\b(no\s+stop[- ]?loss|without\s+(?:a\s+)?stop[- ]?loss|no\s+hard\s+sl|"
            r"without\s+sl|sl\s*=\s*0(?:\.0+)?(?![\d.])|zero\s+stop[- ]?loss|"
            r"never\s+uses?\s+(?:a\s+)?stop[- ]?loss|mental\s+stop\s+only)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_HFT_ARBITRAGE",
        re.compile(
            r"\b(latency\s+arbitrage|tick\s+scalping\s+exploit|broker\s+feed\s+arbitrage|"
            r"high[- ]frequency\s+tick\s+arbitrage)\b",
            re.IGNORECASE,
        ),
    ),
)

# Deterministic pure-text public strategy fixtures for --offline reproducible cleanroom verification.
OFFLINE_PUBLIC_SPECS: tuple[dict[str, Any], ...] = (
    {
        "slug": "quantpedia-tsmom-etf-daily",
        "original_id": "AUTO-QP-TSMOM-01",
        "source_name": "quantpedia-public-spec",
        "url": "https://quantpedia.com/strategies/time-series-momentum-effect/",
        "name": "Time-Series Momentum Cross-Asset ETF (Volatility Scaled)",
        "family": "Macro ETF Trend",
        "asset_class": "ETF_SPOT_ZERO_SWAP",
        "symbol": "SPY/TLT/GLD",
        "timeframe": "D1",
        "direction": "Both",
        "stop_loss_rule": "Explicit hard 2.0x ATR protective stop and monthly volatility-target rebalance",
        "rule_description": (
            "Go long liquid ETFs with positive 12-month trailing excess return and reduce to T-Bill/cash "
            "or short defensive hedge when trailing return turns negative; position sized inversely to "
            "realized volatility with a hard 2.0x ATR protective stop, zero martingale, zero grid."
        ),
        "raw_text": (
            "Public academic literature summary (Moskowitz, Ooi, Pedersen). "
            "Universe: broad liquid ETFs (SPY, TLT, GLD) with zero overnight CFD swap. "
            "Signal: sign of trailing 12-month return evaluated on D1/monthly rebalance. "
            "Risk control: volatility scaling with explicit hard 2.0x ATR protective stop; "
            "strictly avoids grid and never uses martingale. "
            "Sample vendor blog commentary mentions strong OOS2 rally during 2025 and 2026 bull markets."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "quantpedia-dual-momentum-etf",
        "original_id": "AUTO-QP-DUALMOM-02",
        "source_name": "quantpedia-public-spec",
        "url": "https://quantpedia.com/strategies/dual-momentum-model/",
        "name": "Global Equities Dual Momentum Rotation (ETF)",
        "family": "Macro ETF Rotation",
        "asset_class": "ETF_SPOT_ZERO_SWAP",
        "symbol": "SPY/EFA/AGG",
        "timeframe": "W1",
        "direction": "Long",
        "stop_loss_rule": "Absolute momentum cash-bond switch plus hard portfolio drawdown stop",
        "rule_description": (
            "Compare 12-month trailing return of US equities (SPY) vs international equities (EFA) against "
            "short-term Treasury bills; hold the stronger equity ETF only when excess return is positive, "
            "otherwise rotate to aggregate bonds (AGG) with a hard defensive stop, zero grid, zero martingale."
        ),
        "raw_text": (
            "Public rule specification (Gary Antonacci Dual Momentum). "
            "Liquid spot ETFs SPY, EFA, AGG on W1/monthly cadence with zero CFD swap exposure. "
            "Combines relative strength and absolute trend filter; uses hard stop and defensive bond rotation. "
            "Non-grid, non-martingale, no leverage multiplier."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "github-crypto-spot-donchian-d1",
        "original_id": "AUTO-GH-CRYP-03",
        "source_name": "github-public-spec",
        "url": "https://raw.githubusercontent.com/public-quant-specs/crypto-trend/main/README.md",
        "name": "Causal Crypto Spot Daily Donchian Breakout (Hard ATR Stop)",
        "family": "Crypto Spot Daily Trend",
        "asset_class": "CRYPTO_SPOT_GE_4H",
        "symbol": "BTCUSDT/ETHUSDT",
        "timeframe": "D1",
        "direction": "Long",
        "stop_loss_rule": "Mandatory hard 2.5x ATR trailing stop on daily close",
        "rule_description": (
            "Enter long spot BTCUSDT/ETHUSDT on daily close above 20-day Donchian high when above 100-day SMA; "
            "exit on 10-day Donchian low or mandatory hard 2.5x ATR protective stop; avoids sub-4H taker churn, "
            "zero grid, zero martingale."
        ),
        "raw_text": (
            "Open public specification for causal spot crypto trend following on D1 bars (frame >= 4H). "
            "Uses limit/maker-aware execution and mandatory hard 2.5x ATR stop loss. "
            "Strictly avoids grid, avoids martingale, never averages down."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "public-spec-vol-target-carry-etf",
        "original_id": "AUTO-PUB-VOLCARRY-04",
        "source_name": "public-research-spec",
        "url": "https://quantpedia.com/strategies/volatility-risk-premium-effect/",
        "name": "Cross-Asset Volatility-Scaled Defensive Trend (Partial Spec)",
        "family": "Multi-Asset Defensive",
        "asset_class": "ETF_SPOT_ZERO_SWAP",
        "symbol": "TLT/GLD/SHY",
        "timeframe": None,
        "direction": "Long",
        "stop_loss_rule": None,
        "rule_description": (
            "Allocate across defensive Treasury and Gold ETFs inversely proportional to 20-day realized volatility "
            "when regime stress rises; exact stop threshold is omitted in the public abstract."
        ),
        "raw_text": (
            "Public abstract describing inverse-volatility allocation across TLT, GLD, and SHY spot ETFs. "
            "Explicitly non-martingale and without grid. Exact bar timeframe and stop-loss multiplier are omitted."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    {
        "slug": "forum-toxic-gold-martingale-grid",
        "original_id": "AUTO-TOXIC-01",
        "source_name": "public-forum-spec",
        "url": "https://example.org/forum/gold-recovery-ea-overview.html",
        "name": "Turbo Gold Recovery Grid Bot",
        "family": "Toxic Grid/Martingale",
        "asset_class": "CFD_FX",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "direction": "Both",
        "stop_loss_rule": "None (SL=0)",
        "rule_description": "Opens grid trading layers every 50 points with 1.8x lot multiplier martingale.",
        "raw_text": (
            "This EA uses grid trading and martingale recovery with a 1.8x lot multiplier, averaging down "
            "into drawdowns with no stop loss (SL=0) until basket profit closes."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
    },
    {
        "slug": "forum-toxic-nosl-scalper",
        "original_id": "AUTO-TOXIC-02",
        "source_name": "public-forum-spec",
        "url": "https://example.org/forum/night-scalper-notes.html",
        "name": "Night Feed Latency Scalper",
        "family": "Toxic No-SL / HFT",
        "asset_class": "CFD_FX",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "direction": "Both",
        "stop_loss_rule": "Mental stop only",
        "rule_description": "Exploits broker feed latency arbitrage without stop loss.",
        "raw_text": (
            "Runs latency arbitrage during rollover and trades without stop loss using mental stop only."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
    },
)


class BinaryDownloadBlockedError(ValueError):
    """Raised fail-closed whenever a URL, header, or payload resembles a forbidden binary/archive."""


class _VisibleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []
        self.title: str = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        low = tag.lower()
        if low in ("script", "style", "noscript"):
            self._skip_depth += 1
        elif low == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        low = tag.lower()
        if low in ("script", "style", "noscript") and self._skip_depth > 0:
            self._skip_depth -= 1
        elif low == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        if self._in_title and not self.title:
            self.title = cleaned
        self._chunks.append(cleaned)

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._chunks)).strip()


def _has_blocked_extension(value: str) -> str | None:
    decoded = unquote(value or "").strip().lower()
    if not decoded:
        return None
    if decoded.endswith(".tar.gz"):
        return ".tar.gz"
    _, ext = os.path.splitext(decoded)
    if ext in BLOCKED_BINARY_EXTENSIONS:
        return ext
    for blocked in BLOCKED_BINARY_EXTENSIONS:
        if re.search(rf"{re.escape(blocked)}(?:$|[/?&#\s\"'])", decoded):
            return blocked
    return None


def validate_safe_public_url(url: str) -> str:
    """Fail-closed URL gate rejecting binary/executable/archive downloads before any network I/O."""
    if not isinstance(url, str) or not url.strip():
        raise BinaryDownloadBlockedError("Empty or non-string URL rejected.")
    clean_url = url.strip()
    parsed = urlparse(clean_url)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise BinaryDownloadBlockedError(f"Only http(s) public URLs allowed; rejected: {clean_url!r}")

    for part_name, part_val in (
        ("path", parsed.path),
        ("fragment", parsed.fragment),
    ):
        hit = _has_blocked_extension(part_val)
        if hit is not None:
            raise BinaryDownloadBlockedError(
                f"Blocked forbidden binary extension {hit!r} in URL {part_name}: {clean_url}"
            )

    for qk, qvals in parse_qs(parsed.query).items():
        for candidate in (qk, *qvals):
            hit = _has_blocked_extension(candidate)
            if hit is not None:
                raise BinaryDownloadBlockedError(
                    f"Blocked forbidden binary extension {hit!r} in URL query parameter {qk!r}: {clean_url}"
                )

    return clean_url


def validate_text_payload(
    raw_bytes: bytes,
    *,
    content_type: str = "text/plain",
    filename_hint: str = "",
) -> str:
    """Reject binary content-types, filenames, oversize bodies, magic bytes, or NUL bytes."""
    hit = _has_blocked_extension(filename_hint)
    if hit is not None:
        raise BinaryDownloadBlockedError(f"Blocked forbidden filename extension {hit!r}: {filename_hint!r}")

    mime = (content_type or "").split(";", 1)[0].strip().lower()
    if mime and not any(mime.startswith(prefix) for prefix in ALLOWED_CONTENT_TYPE_PREFIXES):
        raise BinaryDownloadBlockedError(f"Blocked non-text Content-Type: {mime!r}")

    if len(raw_bytes) > MAX_TEXT_BYTES:
        raise BinaryDownloadBlockedError(f"Payload exceeds pure-text cap ({len(raw_bytes)} > {MAX_TEXT_BYTES} B)")

    for sig in BINARY_MAGIC_SIGNATURES:
        if raw_bytes.startswith(sig):
            raise BinaryDownloadBlockedError(f"Blocked binary magic signature ({sig!r}) in response payload")

    if b"\x00" in raw_bytes[:4096]:
        raise BinaryDownloadBlockedError("Blocked NUL-byte binary payload")

    return raw_bytes.decode("utf-8", errors="replace")


def fetch_public_text_url(url: str, *, timeout: int = LIVE_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Bounded pure-text/HTML/JSON public fetch. Never downloads binaries."""
    safe_url = validate_safe_public_url(url)
    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": "StrategyIntelCleanroom/1.0 (+text-only-audit; no-binary)",
            "Accept": "text/html,application/json,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        final_url = resp.geturl() or safe_url
        validate_safe_public_url(final_url)
        ctype = resp.headers.get("Content-Type", "text/plain")
        cdisp = resp.headers.get("Content-Disposition", "")
        raw_bytes = resp.read(MAX_TEXT_BYTES + 1)
        if len(raw_bytes) > MAX_TEXT_BYTES:
            raise BinaryDownloadBlockedError(f"Remote response exceeded {MAX_TEXT_BYTES} byte pure-text cap")
        text = validate_text_payload(raw_bytes, content_type=ctype, filename_hint=cdisp)

    mime = ctype.split(";", 1)[0].strip().lower()
    title = ""
    visible_text = text
    if "html" in mime or "<html" in text[:400].lower():
        parser = _VisibleTextExtractor()
        parser.feed(text)
        title = parser.title
        visible_text = parser.get_text()

    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(final_url).path.strip("/").lower()).strip("-") or "public-page"
    return {
        "slug": f"live-{slug[:48]}",
        "original_id": f"AUTO-LIVE-{hashlib.sha256(final_url.encode('utf-8')).hexdigest()[:8].upper()}",
        "source_name": urlparse(final_url).netloc.lower(),
        "url": final_url,
        "name": title or NOT_DISCLOSED,
        "family": NOT_DISCLOSED,
        "asset_class": NOT_DISCLOSED,
        "symbol": NOT_DISCLOSED,
        "timeframe": NOT_DISCLOSED,
        "direction": NOT_DISCLOSED,
        "stop_loss_rule": NOT_DISCLOSED,
        "rule_description": visible_text[:320] if visible_text else NOT_DISCLOSED,
        "raw_text": visible_text[:4000],
        "replicability": "PARTIAL_CONCEPT_ONLY",
    }


def _flag_is_negated(flag: str, clause_lower: str) -> bool:
    if flag == "TOXIC_MARTINGALE":
        return any(neg in clause_lower for neg in MARTINGALE_NEGATION_PHRASES)
    if flag == "TOXIC_GRID":
        return any(neg in clause_lower for neg in GRID_NEGATION_PHRASES)
    return False


def detect_toxic_signals(text: str) -> tuple[bool, list[str], str]:
    """Detect non-negated Grid, Martingale, No-SL, or HFT-Arbitrage signals with verbatim rationale."""
    if not text or not text.strip():
        return False, [], "No toxic Grid/Martingale/No-SL signal detected in raw text."

    clauses = [c.strip() for c in _CLAUSE_SPLIT_RE.split(text) if c.strip()]
    matched_flags: list[str] = []
    excerpts: list[str] = []

    for clause in clauses:
        clause_lower = clause.lower()
        for flag, rx in TOXIC_PATTERNS:
            if rx.search(clause):
                # Category-specific negation only (hard-stop or cross-category phrases NEVER negate!)
                if _flag_is_negated(flag, clause_lower):
                    continue
                if flag not in matched_flags:
                    matched_flags.append(flag)
                    excerpts.append(f'{flag}: "{clause[:160]}"')

    if matched_flags:
        return True, matched_flags, " | ".join(excerpts)
    return False, [], "No toxic Grid/Martingale/No-SL signal detected in raw text."


def _nd(value: Any) -> str:
    if value is None:
        return NOT_DISCLOSED
    s = str(value).strip()
    return s if s else NOT_DISCLOSED


def extract_spec_from_raw(raw_record: dict[str, Any], *, raw_rel_path: str) -> dict[str, Any]:
    """Zero-hallucination verbatim extractor: missing fields strictly become NOT_DISCLOSED."""
    raw_text = _nd(raw_record.get("raw_text"))
    rule_desc = _nd(raw_record.get("rule_description"))
    stop_rule = _nd(raw_record.get("stop_loss_rule"))
    combined_for_toxic = "\n".join(
        p for p in (raw_text, rule_desc, stop_rule) if p != NOT_DISCLOSED
    )
    is_toxic, toxic_flags, toxic_rationale = detect_toxic_signals(combined_for_toxic)

    verbatim_excerpt = raw_text[:280] if raw_text != NOT_DISCLOSED else NOT_DISCLOSED

    data_quality_flags = [
        "AUTO_INGESTED_UNTRUSTED_PUBLIC_SPEC",
        "UNVERIFIED_EXTERNAL_CLAIM",
        "MISSING_PF_AND_DD_NOT_DISCLOSED",
    ]
    if stop_rule == NOT_DISCLOSED:
        data_quality_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
    if _nd(raw_record.get("timeframe")) == NOT_DISCLOSED:
        data_quality_flags.append("TIMEFRAME_NOT_DISCLOSED")

    orig_id = _nd(raw_record.get("original_id"))
    lead_id = f"LEAD-{orig_id}" if orig_id.startswith("AUTO-") else f"LEAD-AUTO-{orig_id}"

    return {
        "lead_id": lead_id,
        "source": "public-auto-ingest",
        "source_origin": _nd(raw_record.get("source_name")),
        "source_url": _nd(raw_record.get("url")),
        "raw_file": raw_rel_path,
        "original_id": orig_id,
        "name": _nd(raw_record.get("name")),
        "family": _nd(raw_record.get("family")),
        "asset_class": _nd(raw_record.get("asset_class")),
        "symbol": _nd(raw_record.get("symbol")),
        "timeframe": _nd(raw_record.get("timeframe")),
        "direction": _nd(raw_record.get("direction")),
        "stop_loss_rule": stop_rule,
        "take_profit_rule": _nd(raw_record.get("take_profit_rule")),
        "rule_description": rule_desc,
        "verbatim_excerpt": verbatim_excerpt,
        "source_verdict": "REJECTED_TOXIC" if is_toxic else "PUBLIC_CONCEPT_ONLY",
        "passes_all_5": False,
        "data_quality_flags": data_quality_flags,
        "replicability": _nd(raw_record.get("replicability")),
        "evidence_tier": "SOURCE_CLAIM_ONLY",
        "gate_condition_met": (
            "REJECTED_TOXIC_MECHANISM"
            if is_toxic
            else "AUTO_INGESTED_PUBLIC_SPEC_QUARANTINED: source claim only, pending independent reproduction"
        ),
        "verified_live_links": [],
        "reported_winrate_pct": NOT_DISCLOSED,
        "reported_profit_factor": NOT_DISCLOSED,
        "reported_max_dd_pct": NOT_DISCLOSED,
        "is_toxic": is_toxic,
        "toxic_flags": toxic_flags,
        "toxic_rationale": toxic_rationale,
        "performance_metrics": {},
    }


def scrub_holdout_tokens(obj: Any) -> Any:
    """Recursively strip all 2024..2029 / oos2 tokens and 2024..2099 integers for handoff safety."""
    if isinstance(obj, dict):
        cleaned: dict[str, Any] = {}
        for k, v in obj.items():
            k_str = str(k)
            if holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(k_str):
                continue
            cleaned[k_str] = scrub_holdout_tokens(v)
        return cleaned
    if isinstance(obj, list):
        return [scrub_holdout_tokens(item) for item in obj]
    if isinstance(obj, str):
        return holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.sub("[REDACTED_HOLDOUT_PERIOD]", obj)
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if 2024 <= obj <= 2099:
            return NOT_DISCLOSED
        return obj
    return obj


def build_sanitized_auto_handoff(accepted_leads: list[dict[str, Any]]) -> dict[str, Any]:
    """Project accepted leads onto strict holdout_sanitizer allowlist schema and verify 0 leakage."""
    projected: list[dict[str, Any]] = []
    for lead in accepted_leads:
        clean_lead: dict[str, Any] = {}
        for key in sorted(holdout_sanitizer.ALLOWED_LEAD_KEYS):
            if key in lead:
                clean_lead[key] = lead[key]
        clean_lead["performance_metrics"] = {}
        projected.append(scrub_holdout_tokens(clean_lead))

    payload: dict[str, Any] = scrub_holdout_tokens(
        {
            "export_tier": "CLEANROOM_HOLDOUT_SANITIZED_AUTO_INGEST",
            "description": (
                "Cleanroom Auto-Ingested Public Strategy Specs "
                "(Pure Text Only, Zero Hallucination, Holdout Sanitized)"
            ),
            "gate_criteria": {
                "condition_a": "Pure text/HTML/JSON public specification only (zero binary downloads)",
                "condition_b": (
                    "Zero toxic Grid/Martingale/No-SL/HFT signals; missing fields set to NOT_DISCLOSED; "
                    "SOURCE_CLAIM_ONLY pending independent Dev backtest verification"
                ),
            },
            "total_leads": len(projected),
            "leads": projected,
        }
    )

    ok, violations = holdout_sanitizer.sanitize_and_validate(payload)
    if not ok:
        raise ValueError(f"Sanitized auto handoff failed holdout_sanitizer validation: {violations}")
    return payload


def _sha256_upper(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def run_ingest(
    *,
    root_dir: Path | None = None,
    mode: str = "offline",
    urls: list[str] | None = None,
    max_live_urls: int = 5,
) -> dict[str, Any]:
    """Execute the full cleanroom auto-ingest pipeline and return a structured summary."""
    root = Path(root_dir).resolve() if root_dir is not None else ROOT_DIR
    source_dir = root / "sources" / "public-auto-ingest"
    raw_dir = source_dir / "raw"
    extracted_dir = source_dir / "extracted"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    raw_records: list[dict[str, Any]] = []
    live_errors: list[dict[str, str]] = []

    if mode == "offline":
        for spec in OFFLINE_PUBLIC_SPECS:
            validate_safe_public_url(str(spec["url"]))
            raw_records.append(dict(spec))
    elif mode == "live":
        target_urls = list(urls) if urls else list(DEFAULT_LIVE_PUBLIC_URLS)
        target_urls = target_urls[: max(1, min(max_live_urls, 10))]
        for url in target_urls:
            # Always block forbidden binary URLs fail-closed BEFORE any fetch or error swallowing.
            validate_safe_public_url(url)
            try:
                raw_records.append(fetch_public_text_url(url))
            except BinaryDownloadBlockedError:
                raise
            except Exception as exc:
                live_errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
    else:
        raise ValueError(f"Unsupported ingest mode: {mode!r} (expected 'offline' or 'live')")

    # Write raw snapshots and SHA-256 manifest
    manifest: dict[str, dict[str, Any]] = {}
    extracted_specs: list[dict[str, Any]] = []

    for rec in raw_records:
        slug = re.sub(r"[^a-z0-9_-]+", "-", str(rec["slug"]).lower()).strip("-") or "item"
        raw_filename = f"{slug}.json"
        raw_path = raw_dir / raw_filename
        _write_json(raw_path, rec)
        manifest[raw_filename] = {
            "sha256": _sha256_upper(raw_path),
            "size": raw_path.stat().st_size,
        }
        spec_out = extract_spec_from_raw(rec, raw_rel_path=f"sources/public-auto-ingest/raw/{raw_filename}")
        extracted_specs.append(spec_out)

    manifest_path = source_dir / "raw_manifest.sha256.json"
    _write_json(manifest_path, manifest)

    accepted = [item for item in extracted_specs if not item["is_toxic"]]
    rejected = [item for item in extracted_specs if item["is_toxic"]]

    now_utc = datetime.now(timezone.utc).isoformat()
    _write_json(
        extracted_dir / "01_auto_extracted_specs.json",
        {
            "generated_at_utc": now_utc,
            "mode": mode,
            "total_ingested": len(extracted_specs),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "live_fetch_errors": live_errors,
            "items": extracted_specs,
        },
    )
    _write_json(
        extracted_dir / "auto_rejected_log.json",
        {
            "generated_at_utc": now_utc,
            "total_rejected": len(rejected),
            "rejected_items": [
                {
                    "id": item["original_id"],
                    "name": item["name"],
                    "source_url": item["source_url"],
                    "toxic_flags": item["toxic_flags"],
                    "toxic_rationale": item["toxic_rationale"],
                    "verbatim_excerpt": item["verbatim_excerpt"],
                }
                for item in rejected
            ],
        },
    )

    catalog_path = root / "catalog" / "auto_public_leads.json"
    _write_json(
        catalog_path,
        {
            "generated_at_utc": now_utc,
            "mode": mode,
            "source": "public-auto-ingest",
            "total_leads": len(accepted),
            "leads": accepted,
        },
    )

    handoff_payload = build_sanitized_auto_handoff(accepted)
    handoff_path = root / "handoff" / "sanitized_auto_leads.json"
    _write_json(handoff_path, handoff_payload)

    return {
        "mode": mode,
        "raw_files": len(manifest),
        "accepted_leads": len(accepted),
        "rejected_toxic": len(rejected),
        "live_fetch_errors": len(live_errors),
        "manifest_path": str(manifest_path),
        "catalog_path": str(catalog_path),
        "handoff_path": str(handoff_path),
        "holdout_sanitized": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--offline", action="store_true", help="Run deterministic offline cleanroom fixture ingest")
    mode_group.add_argument("--live", action="store_true", help="Run bounded live pure-text public fetch")
    parser.add_argument("--url", action="append", default=None, help="Explicit public text URL for --live mode")
    parser.add_argument("--max-urls", type=int, default=5, help="Maximum URLs fetched in --live mode (1..10)")
    parser.add_argument("--root", type=Path, default=None, help="Override cleanroom root directory")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON summary to stdout")
    args = parser.parse_args(argv)

    mode = "live" if args.live else "offline"
    summary = run_ingest(root_dir=args.root, mode=mode, urls=args.url, max_live_urls=args.max_urls)
    if args.as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(
            f"[SUCCESS] auto_intel_ingest ({summary['mode']}): "
            f"raw={summary['raw_files']}, accepted={summary['accepted_leads']}, "
            f"rejected_toxic={summary['rejected_toxic']}, handoff={summary['handoff_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
