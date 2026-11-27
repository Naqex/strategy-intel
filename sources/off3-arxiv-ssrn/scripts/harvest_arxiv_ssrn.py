"""Cleanroom pure-text harvester & zero-hallucination extractor for arXiv q-fin & SSRN papers.

Operates strictly inside:
    D:\\ANNAM\\strategy-intel\\sources\\off3-arxiv-ssrn\\

Guardrails:
  1. Pure text/XML/JSON/HTML metadata only — fail-closed binary/PDF/MQ5 blocker.
  2. Zero Hallucination — every raw file stores live-fetched metadata + verbatim abstract;
     every undisclosed rule parameter is explicitly set to "NOT_DISCLOSED".
  3. Zero Holdout Leakage — extracted/leads.json is strictly verified to contain ZERO
     tokens matching (?:oos2|(?<!\\d)202[4-9](?!\\d)) and ZERO 2024..2099 integers.
  4. Non-Breakout Prop Focus — 22 verifiable non-breakout white-box research leads mapped
     strictly to the 28-symbol FTMO universe (17 FX, 6 Indices, XAU/XAG, USOIL/UKOIL).
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import unquote, urlparse
import urllib.request
import xml.etree.ElementTree as ET

SOURCE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = SOURCE_DIR / "raw"
EXTRACTED_DIR = SOURCE_DIR / "extracted"
MANIFEST_PATH = SOURCE_DIR / "raw_manifest.sha256.json"
LEADS_PATH = EXTRACTED_DIR / "leads.json"

NOT_DISCLOSED = "NOT_DISCLOSED"
MAX_TEXT_BYTES = 512 * 1024
HTTP_TIMEOUT = 15

BLOCKED_EXTENSIONS = frozenset(
    {
        ".pdf",
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
    }
)

BINARY_MAGIC = (
    b"%PDF-",
    b"MZ",
    b"PK\x03\x04",
    b"Rar!\x1a\x07",
    b"7z\xbc\xaf\x27\x1c",
    b"\x1f\x8b",
    b"\x7fELF",
)

FORBIDDEN_HOLDOUT_RE = re.compile(r"(?:oos2|(?<!\d)202[4-9](?!\d))", re.IGNORECASE)

TOXIC_PATTERNS = (
    (
        "TOXIC_MARTINGALE",
        re.compile(
            r"\b(martingale|lot\s*multiplier|recovery\s*lot|double\s*lot|geometric\s+lot\s+sizing)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_GRID",
        re.compile(
            r"\b(grid\s*trading|grid\s*strategy|grid\s*system|grid\s*step|hedging\s*grid|"
            r"averaging\s*down|cost[- ]averaging)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_NO_STOP_LOSS",
        re.compile(
            r"\b(no\s+stop[- ]?loss|without\s+(?:a\s+)?stop[- ]?loss|sl\s*=\s*0(?:\.0+)?(?![\d.])|"
            r"mental\s+stop\s+only)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "TOXIC_HFT_ARBITRAGE",
        re.compile(
            r"\b(latency\s+arbitrage|tick\s+scalping\s+exploit|broker\s+feed\s+arbitrage)\b",
            re.IGNORECASE,
        ),
    ),
)

NEGATION_PHRASES = (
    "no martingale",
    "zero martingale",
    "non-martingale",
    "no grid",
    "zero grid",
    "non-grid",
    "no latency arbitrage",
    "zero latency arbitrage",
)


class _VisibleTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript") and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            cleaned = data.strip()
            if cleaned:
                self._parts.append(cleaned)

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._parts)).strip()


def validate_pure_text_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid public URL rejected: {url!r}")
    decoded_path = unquote(parsed.path).lower()
    for ext in BLOCKED_EXTENSIONS:
        if decoded_path.endswith(ext) or f"{ext}?" in decoded_path or f"{ext}/" in decoded_path:
            raise ValueError(f"Blocked binary/forbidden extension {ext!r} in URL: {url}")
    return url.strip()


def fetch_text(url: str) -> tuple[int, str, str]:
    safe_url = validate_pure_text_url(url)
    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": "StrategyIntelCleanroom/1.0 (pure-text-academic-metadata; no-binary; mailto:cleanroom@example.org)",
            "Accept": "application/json,application/atom+xml,application/xml,text/html,text/plain;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
        final_url = resp.geturl() or safe_url
        validate_pure_text_url(final_url)
        ctype = (resp.headers.get("Content-Type") or "text/plain").split(";", 1)[0].strip().lower()
        if "pdf" in ctype or "octet-stream" in ctype or "zip" in ctype:
            raise ValueError(f"Blocked binary Content-Type {ctype!r} from {final_url}")
        raw_bytes = resp.read(MAX_TEXT_BYTES + 1)
        if len(raw_bytes) > MAX_TEXT_BYTES:
            raise ValueError(f"Payload exceeds pure-text cap ({len(raw_bytes)} > {MAX_TEXT_BYTES})")
        for sig in BINARY_MAGIC:
            if raw_bytes.startswith(sig):
                raise ValueError(f"Blocked binary magic bytes {sig!r} from {final_url}")
        if b"\x00" in raw_bytes[:4096]:
            raise ValueError(f"Blocked NUL-byte payload from {final_url}")
        return int(resp.status), ctype, raw_bytes.decode("utf-8", errors="replace")


def reconstruct_openalex_abstract(inv_index: dict[str, list[int]] | None) -> str:
    if not inv_index:
        return ""
    words = sorted((pos, word) for word, positions in inv_index.items() for pos in positions)
    return re.sub(r"\s+", " ", " ".join(w for _, w in words)).strip()


def fetch_arxiv_batch(arxiv_ids: list[str]) -> dict[str, dict[str, Any]]:
    url = f"https://export.arxiv.org/api/query?id_list={','.join(arxiv_ids)}&max_results={len(arxiv_ids) + 5}"
    status, ctype, xml_text = fetch_text(url)
    root = ET.fromstring(xml_text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results: dict[str, dict[str, Any]] = {}
    for entry in root.findall("a:entry", ns):
        full_id = entry.find("a:id", ns).text.strip()
        short_id = full_id.rsplit("/", 1)[-1]
        base_id = re.sub(r"v\d+$", "", short_id)
        title = re.sub(r"\s+", " ", entry.find("a:title", ns).text or "").strip()
        summary = re.sub(r"\s+", " ", entry.find("a:summary", ns).text or "").strip()
        published = (entry.find("a:published", ns).text or "")[:10]
        authors = [a.find("a:name", ns).text.strip() for a in entry.findall("a:author", ns)]
        categories = [c.attrib.get("term", "") for c in entry.findall("a:category", ns)]
        results[base_id] = {
            "fetch_url": url,
            "http_status": status,
            "content_type": ctype,
            "arxiv_id": base_id,
            "arxiv_versioned_id": short_id,
            "published_date": published,
            "categories": categories,
            "title": title,
            "authors": authors,
            "raw_text": summary,
        }
    return results


def fetch_openalex_record(openalex_url: str) -> dict[str, Any]:
    status, ctype, body = fetch_text(openalex_url)
    data = json.loads(body)
    title = re.sub(r"\s+", " ", str(data.get("title") or "")).strip()
    authors = [
        a.get("author", {}).get("display_name", "").strip()
        for a in data.get("authorships", [])
        if a.get("author", {}).get("display_name")
    ]
    abstract = reconstruct_openalex_abstract(data.get("abstract_inverted_index"))
    ssrn_links = [
        loc.get("landing_page_url")
        for loc in data.get("locations", [])
        if "ssrn" in (loc.get("landing_page_url") or "").lower()
    ]
    return {
        "fetch_url": openalex_url,
        "http_status": status,
        "content_type": ctype,
        "openalex_id": data.get("id"),
        "doi": data.get("doi"),
        "ssrn_locations": ssrn_links,
        "publication_year": data.get("publication_year"),
        "title": title,
        "authors": authors,
        "raw_text": abstract,
    }


def fetch_repec_record(repec_url: str) -> dict[str, Any]:
    status, ctype, html = fetch_text(repec_url)
    m_title = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    title = ""
    if m_title:
        tp = _VisibleTextExtractor()
        tp.feed(m_title.group(1))
        title = tp.get_text()
    m_abs = re.search(r'<div id="abstract-body"[^>]*>(.*?)</div>', html, re.I | re.S)
    abstract = ""
    if m_abs:
        ap = _VisibleTextExtractor()
        ap.feed(m_abs.group(1))
        abstract = ap.get_text()
    if not abstract:
        m_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
        if m_desc:
            abstract = re.sub(r"\s+", " ", m_desc.group(1)).strip()
    return {
        "fetch_url": repec_url,
        "http_status": status,
        "content_type": ctype,
        "title": title,
        "raw_text": abstract,
    }


def fetch_nyfed_record(nyfed_url: str) -> dict[str, Any]:
    status, ctype, html = fetch_text(nyfed_url)
    m_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I | re.S)
    abstract = re.sub(r"\s+", " ", m_desc.group(1)).strip() if m_desc else ""
    # Also extract full paragraph abstract text if present inside main content
    m_abs = re.search(r"Abstract\s*</h\d>\s*(.*?)</div", html, re.I | re.S)
    if m_abs:
        ap = _VisibleTextExtractor()
        ap.feed(m_abs.group(1))
        full_abs = ap.get_text()
        if len(full_abs) > len(abstract):
            abstract = full_abs
    m_title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = re.sub(r"\s+", " ", m_title.group(1)).strip() if m_title else ""
    return {
        "fetch_url": nyfed_url,
        "http_status": status,
        "content_type": ctype,
        "title": title,
        "raw_text": abstract,
    }


# 22 Verified, Non-Breakout arXiv q-fin & SSRN White-Box Strategy Specifications
# Strictly mapped to our 28 FTMO symbols (17 FX, 6 Indices, XAU/XAG, USOIL/UKOIL).
PAPER_SPECS: tuple[dict[str, Any], ...] = (
    # --- DOMAIN 1: FX SESSION FIXING & WORKING-HOURS MICROSTRUCTURE (4 leads) ---
    {
        "slug": "arxiv-1501-07778-wmr-4pm-london-fix",
        "lead_id": "LEAD-OFF3-ARXIV-01",
        "original_id": "OFF3-ARXIV-01",
        "paper_id": "arXiv:1501.07778",
        "source_origin": "arxiv-q-fin-TR",
        "source_url": "https://arxiv.org/abs/1501.07778",
        "fetch_kind": "arxiv",
        "fetch_key": "1501.07778",
        "name": "WM/Reuters 16:00 London Fix Pre-Fix Microstructure Drift and Post-Fix Reversal",
        "family": "FX Session Fixing",
        "family_tag": "FX_SESSION_FIXING_WMR",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "EURGBP"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M5",
        "direction": "Both",
        "economic_rationale": (
            "Institutional portfolio managers and benchmark-tracking funds concentrate execution at the "
            "WM/Reuters 16:00 London fix, producing elevated volatility, directional pre-fix price impact, "
            "and temporary liquidity pressure distinct from other times of the trading day."
        ),
        "counterparty_mechanism": (
            "Passive index trackers, pension funds, and FX broker-dealers executing guaranteed fix orders "
            "absorb and pre-hedge concentrated client flow ahead of 16:00 London, creating transient "
            "inventory displacement that mean-reverts after the fixing window closes."
        ),
        "entry_rule": (
            "Measure directional price displacement in the pre-fix window leading into 16:00 London "
            "(WM/Reuters benchmark window); fade the pre-fix impulse immediately after the 16:00 fix "
            "window completes once liquidity normalizes (exact z-score threshold NOT_DISCLOSED in paper)."
        ),
        "exit_rule": (
            "Time-based intraday close within the post-fix reversion window before New York rollover "
            "(exact post-fix exit minute NOT_DISCLOSED in paper)."
        ),
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "arxiv-2301-13204-tokyo-gotobi-anomaly",
        "lead_id": "LEAD-OFF3-ARXIV-02",
        "original_id": "OFF3-ARXIV-02",
        "paper_id": "arXiv:2301.13204",
        "source_origin": "arxiv-q-fin-TR",
        "source_url": "https://arxiv.org/abs/2301.13204",
        "fetch_kind": "arxiv",
        "fetch_key": "2301.13204",
        "name": "Tokyo 09:55 JST Gotobi Calendar Fix Pre-Fix Long USDJPY Drift",
        "family": "FX Session Fixing",
        "family_tag": "FX_SESSION_FIXING_TOKYO_GOTOBI",
        "asset_class": "CFD_FX",
        "asset_universe": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M5",
        "direction": "Long",
        "economic_rationale": (
            "Japanese corporations follow the Gotobi payment custom of settling overseas import invoices "
            "in USD on calendar days divisible by five (5th, 10th, 15th, 20th, 25th, and month-end, "
            "shifted to the preceding business day on weekends/holidays) at the 09:55 JST Tokyo TTM fix."
        ),
        "counterparty_mechanism": (
            "Price-insensitive Japanese commercial importers buy USD against JPY through Japanese banks "
            "anchored to the 09:55 JST Telegraphic Transfer Middle (TTM) rate; domestic banks pre-hedge "
            "net USD shortage ahead of 09:55 JST."
        ),
        "entry_rule": (
            "On Gotobi business days (dates divisible by 5, shifted earlier if weekend/holiday), enter Long "
            "USDJPY during the early Tokyo pre-fix accumulation window prior to 09:55 JST (paper tests "
            "pre-fix entry hours such as 03:00 JST leading into the fix)."
        ),
        "exit_rule": "Close the Long USDJPY position at the 09:55 JST Tokyo fixing time (flat intraday, zero swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "ssrn-3521370-krohn-fx-fixings-w-pattern",
        "lead_id": "LEAD-OFF3-SSRN-03",
        "original_id": "OFF3-SSRN-03",
        "paper_id": "SSRN:3521370",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3521370",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1111/jofi.13306",
        "name": "Around-the-Clock W-Shaped FX Fixings Pre-Fix USD Drift and Post-Fix Reversal",
        "family": "FX Session Fixing",
        "family_tag": "FX_SESSION_FIXING_W_SHAPE",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M15",
        "direction": "Both",
        "economic_rationale": (
            "Across the top nine traded currencies, the U.S. dollar systematically appreciates in the "
            "hours leading into scheduled global FX fixings (Tokyo 09:55 JST, ECB/Frankfurt 14:15 CET, "
            "and WM/Reuters London 16:00) and depreciates afterward, tracing a W-shaped intraday return cycle."
        ),
        "counterparty_mechanism": (
            "Unconditional institutional demand for immediacy at major FX benchmarks forces risk-averse "
            "OTC FX dealer banks to pre-hedge anticipated USD inventory imbalance before each fix and "
            "unwind accumulated inventory afterward, especially under elevated volatility or lower liquidity."
        ),
        "entry_rule": (
            "Go Long USD (short EURUSD/GBPUSD/AUDUSD/NZDUSD, long USDJPY/USDCHF/USDCAD) during the "
            "pre-fix run-up window ahead of major FX fixes (Tokyo and London WMR fixes), then reverse "
            "Short USD immediately after each fix completes."
        ),
        "exit_rule": (
            "Close pre-fix Long USD legs at each fixing timestamp and close post-fix Short USD reversal "
            "legs at the end of the post-fix horizon before the next session fixing window."
        ),
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "ssrn-2099321-breedon-ranaldo-fx-working-hours",
        "lead_id": "LEAD-OFF3-SSRN-04",
        "original_id": "OFF3-SSRN-04",
        "paper_id": "SSRN:2099321",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2099321",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/W3121237256",
        "name": "Intraday FX Local Working-Hours Depreciation and Foreign-Hours Appreciation",
        "family": "FX Intraday Seasonality",
        "family_tag": "FX_SESSION_WORKING_HOURS",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "H1",
        "direction": "Both",
        "economic_rationale": (
            "Major currencies exhibit a systematic time-of-day return pattern: each domestic currency "
            "tends to depreciate during its local business/trading hours and appreciate during foreign "
            "trading hours, directly linked to intraday order flow."
        ),
        "counterparty_mechanism": (
            "Domestic corporate treasurers and asset managers act as net buyers of foreign currency "
            "(sellers of home currency) during domestic office hours, creating portfolio-balance order "
            "flow pressure absorbed by global FX dealers and reversed during the counterparty's session."
        ),
        "entry_rule": (
            "Sell the home currency during its domestic core trading session (e.g., short EURUSD during "
            "European local hours; long EURUSD during U.S. local hours when USD is the local currency; "
            "long USDJPY during Tokyo hours and short USDJPY during U.S. hours)."
        ),
        "exit_rule": "Close or flip at the boundary of the regional trading session prior to daily rollover (zero swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # --- DOMAIN 2: OVERNIGHT & INTRADAY EQUITY-INDEX DRIFT & MOMENTUM (4 leads) ---
    {
        "slug": "ssrn-2440866-gao-market-intraday-momentum",
        "lead_id": "LEAD-OFF3-SSRN-05",
        "original_id": "OFF3-SSRN-05",
        "paper_id": "SSRN:2440866",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866",
        "fetch_kind": "repec",
        "fetch_key": "https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html",
        "name": "Equity-Index Market Intraday Momentum (First Half-Hour Predicts Last Half-Hour)",
        "family": "Index Intraday Momentum",
        "family_tag": "INDEX_INTRADAY_MOMENTUM_30M",
        "asset_class": "CFD_INDEX",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M30",
        "direction": "Both",
        "economic_rationale": (
            "The return during the first half-hour of the regular equity session (measured from prior "
            "day's close to 30 minutes after cash open) positively predicts the return during the final "
            "half-hour of the session, with stronger predictability on high-volatility and macro-release days."
        ),
        "counterparty_mechanism": (
            "Infrequent institutional portfolio rebalancing and late-informed traders defer order "
            "execution into the liquid closing auction window, transmitting early-session directional "
            "information into end-of-day price pressure."
        ),
        "entry_rule": (
            "Compute r1 = return from previous regular close to 30 minutes after cash open (e.g., "
            "09:30-10:00 ET for US500/US100/US30); at 30 minutes prior to cash close (15:30 ET), go Long "
            "if r1 > 0 or Short if r1 < 0 (optionally conditioned on elevated intraday volatility)."
        ),
        "exit_rule": "Close flat at the regular cash session close (16:00 ET for U.S. indices; zero overnight swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "ssrn-3760365-baltussen-gamma-hedging-intraday-mom",
        "lead_id": "LEAD-OFF3-SSRN-06",
        "original_id": "OFF3-SSRN-06",
        "paper_id": "SSRN:3760365",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365",
        "fetch_kind": "repec",
        "fetch_key": "https://ideas.repec.org/a/eee/jfinec/v142y2021i1p377-403.html",
        "name": "Dealer Gamma-Hedging Demand Cross-Asset Intraday Momentum into Close",
        "family": "Cross-Asset Intraday Momentum",
        "family_tag": "INDEX_GAMMA_INTRADAY_MOMENTUM",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225", "XAUUSD", "USOIL"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M30",
        "direction": "Both",
        "economic_rationale": (
            "Market intraday momentum generalizes across global equity, bond, commodity, and FX futures: "
            "the cumulative return from prior close up to 30 minutes before close predicts the last "
            "30-minute return, driven by mechanical end-of-day hedging of short-gamma exposures."
        ),
        "counterparty_mechanism": (
            "Options market makers carrying net short-gamma inventory and leveraged ETF sponsors must "
            "mechanically buy after rallies and sell after declines near the daily settlement/close "
            "to rebalance delta exposure, pushing prices in the direction of the day's move."
        ),
        "entry_rule": (
            "Compute the rest-of-day return R_ROD from prior session close to T_close - 30 minutes; "
            "at T_close - 30 minutes, enter Long if R_ROD > 0 or Short if R_ROD < 0, with position "
            "scaled inversely by trailing volatility (strongest on negative-gamma / elevated-vol days)."
        ),
        "exit_rule": "Exit flat at the daily cash/futures settlement close T_close (zero overnight swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "ssrn-3546173-boyarchenko-overnight-drift",
        "lead_id": "LEAD-OFF3-SSRN-07",
        "original_id": "OFF3-SSRN-07",
        "paper_id": "SSRN:3546173",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3546173",
        "fetch_kind": "nyfed",
        "fetch_key": "https://www.newyorkfed.org/research/staff_reports/sr917",
        "name": "European-Open Overnight Drift on U.S. Equity Index Futures Post-Selloff",
        "family": "Index Overnight Drift",
        "family_tag": "INDEX_OVERNIGHT_EUROPEAN_OPEN_DRIFT",
        "asset_class": "CFD_INDEX",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "H1",
        "direction": "Long",
        "economic_rationale": (
            "A disproportionately large share of 24-hour U.S. equity index futures returns accrues during "
            "the overnight window coinciding with the opening of European financial markets (02:00-03:00 ET), "
            "with markedly stronger positive drift following negative prior U.S. closing order imbalances."
        ),
        "counterparty_mechanism": (
            "Constrained U.S. equity market makers absorbing end-of-day sell pressure carry unwanted long "
            "inventory overnight at depressed prices and offload inventory as fresh European institutional "
            "liquidity arrives at European market open, producing asymmetric upward mean reversion."
        ),
        "entry_rule": (
            "Enter Long US500/US100/US30 at the pre-European open window (02:00 ET / 07:00 UTC), "
            "optionally filtered to days when prior U.S. regular-session return was negative (selloff "
            "inventory imbalance regime)."
        ),
        "exit_rule": "Exit flat after the European-open drift window (03:00 ET to U.S. cash open; zero rollover swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "arxiv-2010-01727-knuteson-overnight-intraday-split",
        "lead_id": "LEAD-OFF3-ARXIV-08",
        "original_id": "OFF3-ARXIV-08",
        "paper_id": "arXiv:2010.01727",
        "source_origin": "arxiv-q-fin-TR",
        "source_url": "https://arxiv.org/abs/2010.01727",
        "fetch_kind": "arxiv",
        "fetch_key": "2010.01727",
        "name": "Global Equity-Index Overnight Long vs. Intraday Short Return Decomposition",
        "family": "Index Overnight vs Intraday",
        "family_tag": "INDEX_OVERNIGHT_VS_INTRADAY_SPLIT",
        "asset_class": "CFD_INDEX",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225"],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Across major global stock market indices, cumulative close-to-open overnight returns have "
            "historically accounted for the bulk of positive equity gains while open-to-close regular-session "
            "intraday returns have exhibited flat-to-negative drift (tug-of-war across investor clienteles)."
        ),
        "counterparty_mechanism": (
            "Divergent trading horizons between retail/benchmark open-auction orders and institutional "
            "intraday liquidity providers create systematic close-to-open risk premia that reverse or "
            "stall during cash-market daytime trading hours."
        ),
        "entry_rule": (
            "Enter Long equity index CFD near regular cash close to capture the overnight close-to-open "
            "drift, and optionally hold a tactical daytime fade or flat cash posture during open-to-close "
            "hours (must account for FTMO index overnight financing / swap costs)."
        ),
        "exit_rule": "Close overnight Long leg at the next regular cash market open.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # --- DOMAIN 3: COMMODITY & EIA CRUDE OIL MICROSTRUCTURE (3 leads) ---
    {
        "slug": "ssrn-2275354-halova-kurov-eia-energy-inventory",
        "lead_id": "LEAD-OFF3-SSRN-09",
        "original_id": "OFF3-SSRN-09",
        "paper_id": "SSRN:2275354",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2275354",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1002/fut.21633",
        "name": "EIA Weekly Petroleum Inventory Shock Intraday Crude Oil Reaction and Reversion",
        "family": "Commodity Macro Microstructure",
        "family_tag": "COMMODITY_EIA_OIL_MICROSTRUCTURE",
        "asset_class": "CFD_ENERGY",
        "asset_universe": ["USOIL", "UKOIL"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M5",
        "direction": "Both",
        "economic_rationale": (
            "Scheduled Wednesday 10:30 ET EIA Weekly Petroleum Status Report announcements generate sharp "
            "intraday price discovery and volume/volatility surges in crude oil futures, with noisy "
            "inventory surprises causing measurable initial displacement and post-release adjustment."
        ),
        "counterparty_mechanism": (
            "Physical energy hedgers, macro funds, and liquidity providers reprice storage and supply "
            "expectations rapidly after 10:30 ET; noise in preliminary inventory surprises induces short-term "
            "liquidity overreaction that stabilizes over the subsequent NYMEX session."
        ),
        "entry_rule": (
            "Observe the initial post-EIA release impulse on USOIL/UKOIL after the Wednesday 10:30 ET "
            "release (respecting prop firm news blackout window before entering post-release); trade the "
            "post-announcement drift or overshoot reversion once initial spread spike subsides "
            "(exact entry minute and surprise threshold NOT_DISCLOSED for automated CFD execution)."
        ),
        "exit_rule": "Close flat prior to NYMEX crude oil daily settlement (14:30 ET) to avoid energy rollover swap.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "arxiv-1907-08397-mahajan-commodity-stochastic-spread",
        "lead_id": "LEAD-OFF3-ARXIV-10",
        "original_id": "OFF3-ARXIV-10",
        "paper_id": "arXiv:1907.08397",
        "source_origin": "arxiv-q-fin-TR",
        "source_url": "https://arxiv.org/abs/1907.08397",
        "fetch_kind": "arxiv",
        "fetch_key": "1907.08397",
        "name": "Cointegrated Commodity Stochastic Spread Pairs Trading (WTI-Brent and Gold-Silver)",
        "family": "Commodity Statistical Arbitrage",
        "family_tag": "COMMODITY_COINT_STOCHASTIC_SPREAD",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["USOIL", "UKOIL", "XAUUSD", "XAGUSD"],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Physically and economically linked commodities (WTI vs. Brent crude oil; Gold vs. Silver) "
            "share long-run cointegrating equilibria tested via Johansen cointegration, causing their "
            "logarithmic spread to follow a mean-reverting single-factor stochastic process."
        ),
        "counterparty_mechanism": (
            "Regional inventory bottlenecks (e.g., Cushing vs. North Sea oil flows) and temporary "
            "speculative positioning imbalances push the log-spread away from long-run parity until "
            "commercial arbitrageurs and refiners restore relative pricing."
        ),
        "entry_rule": (
            "Verify rolling Johansen cointegration on the logarithmic spread of linked commodity pairs "
            "(USOIL-UKOIL or XAUUSD-XAGUSD); fit single-factor stochastic spread parameters on a rolling "
            "training window and enter mean-reverting long/short spread positions when spread deviates "
            "beyond the estimated entry band."
        ),
        "exit_rule": "Close spread trade upon reversion to the estimated equilibrium mean (exact stop-loss NOT_DISCLOSED).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": "Reversion of logarithmic commodity spread to estimated equilibrium mean.",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "arxiv-2108-01886-he-crude-oil-bivariate-ou-kalman",
        "lead_id": "LEAD-OFF3-ARXIV-11",
        "original_id": "OFF3-ARXIV-11",
        "paper_id": "arXiv:2108.01886",
        "source_origin": "arxiv-q-fin-ST",
        "source_url": "https://arxiv.org/abs/2108.01886",
        "fetch_kind": "arxiv",
        "fetch_key": "2108.01886",
        "name": "Crude Oil Bivariate Kalman-Filter Ornstein-Uhlenbeck Short-Term Mean Reversion",
        "family": "Commodity State-Space Mean Reversion",
        "family_tag": "COMMODITY_KALMAN_OU_REVERSION",
        "asset_class": "CFD_ENERGY",
        "asset_universe": ["USOIL", "UKOIL"],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Crude oil prices decompose into two latent Ornstein-Uhlenbeck state variables estimated via "
            "Kalman filtering: a slow-moving long-term equilibrium level and a fast mean-reverting "
            "short-term transitory deviation."
        ),
        "counterparty_mechanism": (
            "Short-term supply disruptions, refinery maintenance, and futures roll imbalances drive "
            "transient deviations from the long-run marginal-cost equilibrium until physical storage "
            "adjustments pull front-month crude prices back toward equilibrium."
        ),
        "entry_rule": (
            "Estimate the latent short-term transitory factor and long-term equilibrium factor via "
            "causal Gaussian Kalman filter on USOIL/UKOIL; enter counter-trend when the short-term "
            "transitory OU state exceeds a standardized deviation threshold (exact z-threshold NOT_DISCLOSED)."
        ),
        "exit_rule": "Exit when the Kalman-filtered short-term deviation reverts toward zero (exact time-stop NOT_DISCLOSED).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # --- DOMAIN 4: GOLD / SILVER LEAD-LAG & PRECIOUS METALS MICROSTRUCTURE (3 leads) ---
    {
        "slug": "ssrn-2726505-batten-lucey-intraday-precious-metals",
        "lead_id": "LEAD-OFF3-SSRN-12",
        "original_id": "OFF3-SSRN-12",
        "paper_id": "SSRN:2726505",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2726505",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1371/journal.pone.0174232",
        "name": "Intraday 5-Minute Precious Metals Volatility-Return Seasonality (Gold and Silver)",
        "family": "Precious Metals Intraday Microstructure",
        "family_tag": "METALS_INTRADAY_SEASONALITY",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "XAGUSD"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M5",
        "direction": "Both",
        "economic_rationale": (
            "At the 5-minute intraday frequency, gold and silver exhibit strong intraday return-volatility "
            "interactions, asymmetric London/COMEX session seasonality, and cross-metal volatility "
            "transmission distinct from daily return dynamics."
        ),
        "counterparty_mechanism": (
            "Scheduled London bullion auction windows (AM/PM) and COMEX New York open/close liquidity "
            "transitions concentrate hedging flows from bullion banks and ETF authorized participants, "
            "producing predictable intraday volatility regimes and short-horizon cross-metal spillover."
        ),
        "entry_rule": (
            "Condition intraday XAUUSD/XAGUSD mean-reversion or session-drift entries on 5-minute "
            "realized volatility regime and London/COMEX session handover windows (exact trigger thresholds "
            "and filter cutoffs NOT_DISCLOSED in empirical stylized-facts study)."
        ),
        "exit_rule": "Exit flat before daily COMEX/CFD rollover (zero overnight swap; exact bar count NOT_DISCLOSED).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "journal-adrangi-gold-silver-intraday-lead-lag",
        "lead_id": "LEAD-OFF3-SSRN-13",
        "original_id": "OFF3-SSRN-13",
        "paper_id": "DOI:10.1080/096031000331644",
        "source_origin": "journal-public-research",
        "source_url": "https://doi.org/10.1080/096031000331644",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1080/096031000331644",
        "name": "15-Minute Intraday Gold-to-Silver Price Discovery and Intermarket Spread Lead-Lag",
        "family": "Precious Metals Lead-Lag",
        "family_tag": "METALS_GOLD_SILVER_LEAD_LAG",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "XAGUSD"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M15",
        "direction": "Both",
        "economic_rationale": (
            "Using 15-minute intraday data on strategically linked gold and silver markets, gold leads "
            "price discovery while silver absorbs the convergence burden through the intermarket "
            "error-correction spread."
        ),
        "counterparty_mechanism": (
            "Macro and safe-haven institutional order flow hits deeper gold liquidity first; slower "
            "repricing in thinner, higher-beta silver creates a temporary error-correction residual "
            "that closes over subsequent 15-minute intervals."
        ),
        "entry_rule": (
            "Estimate causal rolling error-correction relationship on 15-minute XAUUSD and XAGUSD "
            "returns; enter XAGUSD in the direction of the lagged XAUUSD price-discovery shock (or fade "
            "excess XAU-XAG spread residual) when the 15-minute error-correction residual breaches a "
            "volatility-normalized band (exact z-threshold NOT_DISCLOSED)."
        ),
        "exit_rule": "Close upon error-correction convergence or at end of session before rollover (zero swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "arxiv-1507-01610-temnov-ou-trailing-stop-mean-reversion",
        "lead_id": "LEAD-OFF3-ARXIV-14",
        "original_id": "OFF3-ARXIV-14",
        "paper_id": "arXiv:1507.01610",
        "source_origin": "arxiv-q-fin-TR",
        "source_url": "https://arxiv.org/abs/1507.01610",
        "fetch_kind": "arxiv",
        "fetch_key": "1507.01610",
        "name": "Ornstein-Uhlenbeck Mean Reversion with Analytical Maximum-Drawdown Trailing Stop",
        "family": "Mean Reversion with Hard Trailing Stop",
        "family_tag": "OU_MEAN_REVERSION_TRAILING_STOP",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["EURGBP", "EURAUD", "EURCAD", "XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
        "prop_track": "FTMO_SWING",
        "timeframe": "H1",
        "direction": "Both",
        "economic_rationale": (
            "Cross-rate FX pairs and cointegrated commodity spreads exhibit local Ornstein-Uhlenbeck "
            "(OU) mean-reverting dynamics; stopping the process analytically at a fixed maximum drawdown "
            "(trailing stop) bounds tail risk when mean reversion breaks down."
        ),
        "counterparty_mechanism": (
            "Temporary cross-currency or commodity-spread order imbalances mean-revert under normal "
            "liquidity regimes, while regime shifts cause trending drawdowns that must be truncated "
            "by an explicit trailing stop calibrated to OU volatility and reversion speed."
        ),
        "entry_rule": (
            "Fit local Ornstein-Uhlenbeck mean-reversion parameters (mean mu, reversion speed theta, "
            "diffusion sigma) on a rolling causal window of FX cross or spread series; enter counter-trend "
            "when price deviates from mu toward the OU boundary."
        ),
        "exit_rule": "Exit at mean reversion target or automatically upon hitting the analytical maximum-drawdown trailing stop.",
        "sl_rule": (
            "Explicit analytical trailing stop defined as a fixed maximum drawdown threshold from the "
            "running maximum of the OU trade path (derived closed-form in paper)."
        ),
        "take_profit_rule": "Exit on OU mean-reversion target or trailing-stop capture of running maximum.",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    # --- DOMAIN 5: TURN-OF-MONTH & MACRO-ANNOUNCEMENT DRIFT (3 leads) ---
    {
        "slug": "ssrn-1923197-lucca-moench-pre-fomc-drift",
        "lead_id": "LEAD-OFF3-SSRN-15",
        "original_id": "OFF3-SSRN-15",
        "paper_id": "SSRN:1923197",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1923197",
        "fetch_kind": "repec",
        "fetch_key": "https://ideas.repec.org/p/fip/fednsr/512.html",
        "name": "Pre-FOMC 24-Hour Announcement Drift on Equity Indices and Gold",
        "family": "Macro Announcement Drift",
        "family_tag": "MACRO_PRE_FOMC_DRIFT",
        "asset_class": "CFD_INDEX",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225", "XAUUSD"],
        "prop_track": "FTMO_SWING",
        "timeframe": "H1",
        "direction": "Long",
        "economic_rationale": (
            "Since scheduled FOMC policy announcements began in 1994, a remarkably large fraction of "
            "excess U.S. and international equity-index returns has accrued in the 24-hour window "
            "immediately preceding scheduled FOMC rate statements, prior to the release itself."
        ),
        "counterparty_mechanism": (
            "Risk-averse institutional investors reduce equity exposure ahead of monetary-policy "
            "uncertainty and re-enter as pre-announcement uncertainty resolves, creating a persistent "
            "pre-release risk premium earned strictly before the scheduled announcement."
        ),
        "entry_rule": (
            "Enter Long equity indices (US500/US100/US30, extendable to GER40/UK100/JP225) at 14:00 ET "
            "on the day before a scheduled FOMC monetary policy announcement (24 hours prior to release)."
        ),
        "exit_rule": (
            "Close flat immediately BEFORE the 14:00 ET FOMC announcement release (e.g., 13:45-13:55 ET "
            "to remain strictly compliant with prop firm red-news execution restrictions)."
        ),
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "ssrn-2637528-kurov-pre-macro-news-drift",
        "lead_id": "LEAD-OFF3-SSRN-16",
        "original_id": "OFF3-SSRN-16",
        "paper_id": "SSRN:2637528",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2637528",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/W3123373742",
        "name": "Pre-Announcement Intraday Drift Ahead of High-Impact U.S. Macroeconomic Releases",
        "family": "Macro Announcement Drift",
        "family_tag": "MACRO_PRE_NEWS_INTRADAY_DRIFT",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["US500", "US100", "US30", "EURUSD", "USDJPY", "XAUUSD"],
        "prop_track": "INTRADAY_SWAP0",
        "timeframe": "M5",
        "direction": "Both",
        "economic_rationale": (
            "E-mini S&P 500 and macro-sensitive futures exhibit statistically significant directional "
            "price drift beginning roughly 30 minutes prior to scheduled U.S. macroeconomic releases "
            "with high market impact, reflecting superior private forecasting and order flow."
        ),
        "counterparty_mechanism": (
            "Informed institutional forecasters and proprietary trading desks accumulate directional "
            "positions ahead of high-impact scheduled releases against uninformed passive limit orders, "
            "creating detectable pre-release drift."
        ),
        "entry_rule": (
            "Monitor causal pre-announcement directional order/return momentum during the window "
            "starting 30 minutes before scheduled high-impact U.S. macroeconomic releases (e.g., ISM, "
            "consumer sentiment, GDP/macro prints) and trade continuation strictly prior to the red-news "
            "blackout cutoff (exact confirmation threshold NOT_DISCLOSED)."
        ),
        "exit_rule": "Close flat strictly BEFORE the scheduled macro release timestamp (prop red-news lock compliant, zero swap).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "ssrn-2528692-etula-dash-for-cash-turn-of-month",
        "lead_id": "LEAD-OFF3-SSRN-17",
        "original_id": "OFF3-SSRN-17",
        "paper_id": "SSRN:2528692",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2528692",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.2139/ssrn.2528692",
        "name": "Dash for Cash: Turn-of-Month Institutional Payment-Cycle Liquidity Reversal",
        "family": "Calendar Turn-of-Month",
        "family_tag": "CALENDAR_TURN_OF_MONTH_LIQUIDITY",
        "asset_class": "CFD_INDEX",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225"],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Institutional investors face predictable month-end cash payment obligations (wages, "
            "dividends, pension disbursements, fund redemptions), generating selling pressure before "
            "month-end settlement followed by sharp turn-of-month return reversals globally."
        ),
        "counterparty_mechanism": (
            "Liquidity-constrained mutual funds, corporations, and pension managers raise cash prior "
            "to month-end settlement dates and redeploy incoming payroll/pension inflows across the "
            "turn of the month, paying a temporary liquidity premium to patient counterparties."
        ),
        "entry_rule": (
            "Long global equity indices (US500/US100/US30/GER40/UK100/JP225) at the close of trading "
            "day T-1 (or T-2) of the calendar month to capture the turn-of-month liquidity reversal; "
            "optionally pair with defensive/short posture during the pre-month-end dash-for-cash window."
        ),
        "exit_rule": "Close Long turn-of-month position at the close of trading day T+3 of the new month.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    # --- DOMAIN 6: VOLATILITY-MANAGED FX & INDEX MOMENTUM (2 leads) ---
    {
        "slug": "ssrn-2659431-moreira-muir-volatility-managed-portfolios",
        "lead_id": "LEAD-OFF3-SSRN-18",
        "original_id": "OFF3-SSRN-18",
        "paper_id": "SSRN:2659431",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2659431",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1111/jofi.12513",
        "name": "Inverse Realized-Variance Volatility-Managed Index and FX Factor Scaling",
        "family": "Volatility-Managed Allocation",
        "family_tag": "VOL_MANAGED_INVERSE_VARIANCE",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": [
            "US500", "US100", "US30", "GER40", "UK100", "JP225",
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
        ],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Realized volatility is highly persistent over short horizons whereas changes in volatility "
            "are not offset by proportional changes in expected returns; scaling risk inversely to prior "
            "realized variance avoids crash regimes and improves risk-adjusted returns."
        ),
        "counterparty_mechanism": (
            "Static-weight benchmark investors and unhedged momentum/carry participants remain fully "
            "exposed during volatility spikes and face forced deleveraging at crisis troughs, whereas "
            "volatility-managed rules cut leverage proactively before tail losses compound."
        ),
        "entry_rule": (
            "Apply dynamic position weight w_t = c / sigma^2_{t-1} (capped to prop leverage limits) "
            "to an equity-index trend/carry portfolio or FX factor portfolio, where sigma^2_{t-1} is "
            "the prior month's (or trailing 20-day) realized daily return variance and c calibrates "
            "unconditional target risk."
        ),
        "exit_rule": "Rebalance position weight monthly (or daily/weekly with turnover band) as realized variance updates.",
        "sl_rule": (
            "Implicit variance-based deleveraging scales exposure sharply downward during volatility spikes; "
            "explicit hard price stop-loss is NOT_DISCLOSED in paper."
        ),
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "ssrn-2140091-baltas-kosowski-vol-targeted-tsmom",
        "lead_id": "LEAD-OFF3-SSRN-19",
        "original_id": "OFF3-SSRN-19",
        "paper_id": "SSRN:2140091",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2140091",
        "fetch_kind": "openalex",
        "fetch_key": "https://api.openalex.org/works/https://doi.org/10.1002/9781119599364.ch3",
        "name": "Range-Volatility-Targeted Multi-Asset Time-Series Momentum (Continuous Trend Signal)",
        "family": "Volatility-Managed TSMOM",
        "family_tag": "VOL_MANAGED_TSMOM_CONTINUOUS",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
            "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
            "EURGBP", "EURAUD", "GBPAUD", "EURCAD",
            "US500", "US100", "US30", "GER40", "UK100", "JP225",
            "XAUUSD", "XAGUSD", "USOIL", "UKOIL",
        ],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Classical binary-sign time-series momentum suffers excessive whipsaw turnover when trends "
            "hover near zero and underestimates volatility with close-to-close estimators; replacing "
            "binary signs with continuous trend-strength signals and range-based (Yang-Zhang) volatility "
            "estimators sharply reduces turnover and stabilizes cross-asset risk."
        ),
        "counterparty_mechanism": (
            "Macro slow-moving capital, central-bank policy inertia, and commercial commodity hedgers "
            "create multi-week to multi-month serial correlation across FX, equity indices, metals, "
            "and energy markets."
        ),
        "entry_rule": (
            "For each instrument i in the multi-asset FTMO universe, compute a continuous trend-strength "
            "signal s_{i,t} in [-1, +1] (e.g., t-statistic of trailing return or normalized MA slope) "
            "and scale position weight by sigma_target / sigma_YZ_{i,t}, where sigma_YZ is the causal "
            "OHLC range-based Yang-Zhang volatility estimator, adjusted for pairwise asset correlation."
        ),
        "exit_rule": "Continuously resize or reverse on scheduled D1/W1/monthly rebalance as trend-strength signal decays.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    # --- DOMAIN 7: CROSS-SECTIONAL FX & COMMODITY PORTFOLIOS & SPILLOVER (3 leads) ---
    {
        "slug": "ssrn-1809776-menkhoff-currency-momentum",
        "lead_id": "LEAD-OFF3-SSRN-20",
        "original_id": "OFF3-SSRN-20",
        "paper_id": "SSRN:1809776",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1809776",
        "fetch_kind": "repec",
        "fetch_key": "https://ideas.repec.org/p/bis/biswps/366.html",
        "name": "Cross-Sectional G10 Currency Momentum Long-Short Portfolio",
        "family": "Cross-Sectional FX Momentum",
        "family_tag": "XSMOM_FX_CROSS_SECTIONAL",
        "asset_class": "CFD_FX",
        "asset_universe": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
            "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
            "EURGBP", "EURAUD", "GBPAUD", "EURCAD",
        ],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Cross-sectional sorting of currencies by trailing 1-month to 12-month excess returns "
            "generates a persistent spread between past winner and loser currencies that is largely "
            "uncorrelated with traditional business-cycle or equity risk factors."
        ),
        "counterparty_mechanism": (
            "Gradual macroeconomic information diffusion, central-bank policy path anchoring, and "
            "limits to arbitrage among FX participants cause exchange rates to under-react initially "
            "and trend cross-sectionally over 1-to-3-month holding horizons."
        ),
        "entry_rule": (
            "At month-end (or bi-weekly/monthly cadence), rank G10 currencies vs. USD by trailing "
            "1-month or 3-month return; go Long the top-ranked winner currencies and Short the "
            "bottom-ranked loser currencies (net USD-neutral basket or direct crosses like EURJPY/AUDJPY/EURGBP)."
        ),
        "exit_rule": "Hold for 1-month holding horizon and rebalance cross-sectional ranks at next period end.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "ssrn-1918987-ferraro-rogoff-rossi-oil-fx-lead-lag",
        "lead_id": "LEAD-OFF3-SSRN-21",
        "original_id": "OFF3-SSRN-21",
        "paper_id": "SSRN:1918987",
        "source_origin": "ssrn-public-research",
        "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1918987",
        "fetch_kind": "repec",
        "fetch_key": "https://ideas.repec.org/p/nbr/nberwo/17998.html",
        "name": "Daily-Frequency Crude-Oil-to-Commodity-Currency Lead-Lag (USOIL to USDCAD/CADJPY)",
        "family": "Cross-Market Commodity-FX Lead-Lag",
        "family_tag": "COMMODITY_FX_OIL_CAD_LEAD_LAG",
        "asset_class": "CFD_FX",
        "asset_universe": ["USOIL", "UKOIL", "USDCAD", "CADJPY", "AUDUSD", "NZDUSD"],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "While monthly and quarterly models show weak oil-to-FX predictability, daily-frequency "
            "changes in crude oil prices exhibit a robust short-term predictive relationship with "
            "commodity-exporting nominal exchange rates, led by the Canadian dollar (USDCAD)."
        ),
        "counterparty_mechanism": (
            "Terms-of-trade shocks from crude oil price swings immediately alter export revenue "
            "expectations for energy-exporting economies (Canada), propagating from liquid crude "
            "oil markets into FX spot rates over short daily horizons."
        ),
        "entry_rule": (
            "Compute lagged daily crude oil return on USOIL/UKOIL; enter Short USDCAD (Long CAD, "
            "or Long CADJPY) after positive oil shocks and Long USDCAD after negative oil shocks "
            "using causal rolling oil-beta regression (exact entry threshold NOT_DISCLOSED)."
        ),
        "exit_rule": "Hold for 1-to-5 trading day short-term horizon consistent with daily predictability decay (exact exit bar NOT_DISCLOSED).",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "arxiv-2308-11294-pu-network-momentum-cross-asset",
        "lead_id": "LEAD-OFF3-ARXIV-22",
        "original_id": "OFF3-ARXIV-22",
        "paper_id": "arXiv:2308.11294",
        "source_origin": "arxiv-q-fin-PM",
        "source_url": "https://arxiv.org/abs/2308.11294",
        "fetch_kind": "arxiv",
        "fetch_key": "2308.11294",
        "name": "Cross-Asset Network Momentum Spillover Portfolio (Volatility Scaled)",
        "family": "Cross-Asset Network Momentum",
        "family_tag": "CROSS_ASSET_NETWORK_MOMENTUM",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
            "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY",
            "EURGBP", "EURAUD", "GBPAUD", "EURCAD",
            "US500", "US100", "US30", "GER40", "UK100", "JP225",
            "XAUUSD", "XAGUSD", "USOIL", "UKOIL",
        ],
        "prop_track": "FTMO_SWING",
        "timeframe": "D1",
        "direction": "Both",
        "economic_rationale": (
            "Momentum risk premia spill over across economically connected asset classes (equities, "
            "currencies, and commodities); learning a sparse linear momentum-spillover graph purely "
            "from causal pricing data improves trend signals over single-asset TSMOM."
        ),
        "counterparty_mechanism": (
            "Siloed asset-class mandates cause institutional investors to adjust positions slowly "
            "across linked macro markets (e.g., commodities -> commodity FX -> equity indices), "
            "creating cross-asset momentum propagation capturable with volatility-scaled positioning."
        ),
        "entry_rule": (
            "Compute causal multi-horizon volatility-normalized momentum features across the FTMO "
            "multi-asset universe; estimate linear spillover adjacency weights on a strictly causal "
            "rolling lookback window, form each asset's network-momentum signal as the weighted sum "
            "of connected assets' momentum, and size inversely to realized asset volatility."
        ),
        "exit_rule": "Daily/weekly rebalance of volatility-scaled target weights as network momentum signals update.",
        "sl_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
)


def sha256_upper(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def detect_toxic(text: str) -> tuple[bool, list[str], str]:
    clauses = [c.strip() for c in re.split(r"(?:\.(?=\s|$)|[?!\n;])+", text) if c.strip()]
    flags: list[str] = []
    notes: list[str] = []
    for clause in clauses:
        low = clause.lower()
        for flag, rx in TOXIC_PATTERNS:
            if rx.search(clause):
                if any(neg in low for neg in NEGATION_PHRASES):
                    continue
                if flag not in flags:
                    flags.append(flag)
                    notes.append(f'{flag}: "{clause[:140]}"')
    if flags:
        return True, flags, " | ".join(notes)
    return False, [], "No toxic Grid/Martingale/No-SL signal detected in raw text."


def safe_verbatim_excerpt(raw_text: str, max_len: int = 280) -> str:
    """Return a clean verbatim slice (<= max_len chars) guaranteed free of 2024..2029/oos2 tokens."""
    cleaned = re.sub(r"\s+", " ", raw_text).strip()
    if not cleaned:
        return NOT_DISCLOSED
    excerpt = cleaned[:max_len]
    if FORBIDDEN_HOLDOUT_RE.search(excerpt):
        # Find a clean sentence-aligned verbatim slice free of forbidden holdout tokens
        for sent in re.split(r"(?<=[.!?])\s+", cleaned):
            if sent and not FORBIDDEN_HOLDOUT_RE.search(sent):
                return sent[:max_len]
        raise ValueError(f"Could not extract holdout-clean verbatim excerpt from: {cleaned[:120]}")
    return excerpt


def check_holdout_clean(obj: Any, path: str = "root") -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if FORBIDDEN_HOLDOUT_RE.search(str(k)):
                violations.append((f"{path}.{k}", f"Forbidden holdout token in key: {k}"))
            violations.extend(check_holdout_clean(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(check_holdout_clean(item, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if FORBIDDEN_HOLDOUT_RE.search(obj):
            violations.append((path, f"Forbidden holdout token in value: {obj[:120]}"))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if 2024 <= obj <= 2099:
            violations.append((path, f"Forbidden holdout year integer: {obj}"))
    return violations


def run() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Batch-fetch all arXiv records in one clean Atom API request
    arxiv_ids = [spec["fetch_key"] for spec in PAPER_SPECS if spec["fetch_kind"] == "arxiv"]
    print(f"[*] Fetching {len(arxiv_ids)} arXiv q-fin papers via export.arxiv.org API...")
    arxiv_map = fetch_arxiv_batch(arxiv_ids)

    manifest: dict[str, dict[str, Any]] = {}
    extracted_leads: list[dict[str, Any]] = []

    for spec in PAPER_SPECS:
        slug = spec["slug"]
        raw_filename = f"{slug}.json"
        raw_path = RAW_DIR / raw_filename
        raw_rel_path = f"sources/off3-arxiv-ssrn/raw/{raw_filename}"

        kind = spec["fetch_kind"]
        key = spec["fetch_key"]
        if kind == "arxiv":
            if key not in arxiv_map:
                raise RuntimeError(f"Missing arXiv record for {key}")
            fetched = arxiv_map[key]
        elif kind == "openalex":
            fetched = fetch_openalex_record(key)
            time.sleep(0.12)
        elif kind == "repec":
            fetched = fetch_repec_record(key)
            time.sleep(0.15)
        elif kind == "nyfed":
            fetched = fetch_nyfed_record(key)
            time.sleep(0.15)
        else:
            raise ValueError(f"Unknown fetch_kind: {kind}")

        raw_text = str(fetched.get("raw_text") or "").strip()
        if len(raw_text) < 120:
            raise RuntimeError(f"Verbatim abstract too short ({len(raw_text)} chars) for {slug} from {key}")

        title = str(fetched.get("title") or "").strip() or spec["name"]
        authors = fetched.get("authors") or []
        if not authors:
            # Fill verified authors for RePEc/NYFed HTML endpoints that omit structured author list
            authors = _KNOWN_AUTHORS[spec["original_id"]]

        raw_payload = {
            "slug": slug,
            "original_id": spec["original_id"],
            "paper_id": spec["paper_id"],
            "source_origin": spec["source_origin"],
            "canonical_url": spec["source_url"],
            "metadata_fetch_url": fetched["fetch_url"],
            "http_status": fetched["http_status"],
            "content_type": fetched["content_type"],
            "title": title,
            "authors": authors,
            "raw_text": raw_text,
            "categories": fetched.get("categories", []),
            "doi": fetched.get("doi"),
            "ssrn_locations": fetched.get("ssrn_locations", []),
        }
        write_json(raw_path, raw_payload)
        manifest[raw_filename] = {
            "sha256": sha256_upper(raw_path),
            "size": raw_path.stat().st_size,
        }

        # Re-read from disk to enforce strict verbatim extraction from raw/
        disk_raw = json.loads(raw_path.read_text(encoding="utf-8"))
        disk_text = disk_raw["raw_text"]
        excerpt = safe_verbatim_excerpt(disk_text, max_len=280)
        if excerpt not in re.sub(r"\s+", " ", disk_text):
            raise RuntimeError(f"Verbatim excerpt check failed for {slug}")

        rule_description = (
            f"Mechanism: {spec['economic_rationale']} "
            f"Entry: {spec['entry_rule']} "
            f"Exit: {spec['exit_rule']} "
            f"SL: {spec['sl_rule']}"
        )
        is_toxic, toxic_flags, toxic_rationale = detect_toxic(
            "\n".join((spec["entry_rule"], spec["exit_rule"], spec["sl_rule"]))
        )
        if is_toxic:
            raise RuntimeError(f"Unexpected toxic signal in clean spec {slug}: {toxic_flags}")

        dq_flags = [
            "ACADEMIC_PUBLIC_SPEC_UNVERIFIED_ON_FTMO",
            "UNVERIFIED_EXTERNAL_CLAIM",
            "MISSING_PF_AND_DD_NOT_DISCLOSED",
        ]
        if spec["sl_rule"] == NOT_DISCLOSED:
            dq_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
        if spec["take_profit_rule"] == NOT_DISCLOSED:
            dq_flags.append("TAKE_PROFIT_RULE_NOT_DISCLOSED")

        lead_record = {
            # Core auto_public_leads.json schema fields
            "lead_id": spec["lead_id"],
            "source": "off3-arxiv-ssrn",
            "source_origin": spec["source_origin"],
            "source_url": spec["source_url"],
            "raw_file": raw_rel_path,
            "original_id": spec["original_id"],
            "name": spec["name"],
            "family": spec["family"],
            "asset_class": spec["asset_class"],
            "symbol": "/".join(spec["asset_universe"]),
            "timeframe": spec["timeframe"],
            "direction": spec["direction"],
            "stop_loss_rule": spec["sl_rule"],
            "take_profit_rule": spec["take_profit_rule"],
            "rule_description": rule_description,
            "verbatim_excerpt": excerpt,
            "source_verdict": "PUBLIC_CONCEPT_ONLY",
            "passes_all_5": False,
            "data_quality_flags": dq_flags,
            "replicability": spec["replicability"],
            "evidence_tier": "SOURCE_CLAIM_ONLY",
            "gate_condition_met": (
                "AUTO_INGESTED_PUBLIC_SPEC_QUARANTINED: source claim only, pending independent reproduction"
            ),
            "verified_live_links": [],
            "reported_winrate_pct": NOT_DISCLOSED,
            "reported_profit_factor": NOT_DISCLOSED,
            "reported_max_dd_pct": NOT_DISCLOSED,
            "is_toxic": False,
            "toxic_flags": [],
            "toxic_rationale": toxic_rationale,
            "performance_metrics": {},
            # Extended Total Offensive #3 schema fields
            "title": disk_raw["title"],
            "authors": disk_raw["authors"],
            "paper_id": spec["paper_id"],
            "asset_universe": list(spec["asset_universe"]),
            "prop_track": spec["prop_track"],
            "family_tag": spec["family_tag"],
            "economic_rationale": spec["economic_rationale"],
            "counterparty_mechanism": spec["counterparty_mechanism"],
            "entry_rule": spec["entry_rule"],
            "exit_rule": spec["exit_rule"],
            "sl_rule": spec["sl_rule"],
            "disqualifiers_checked": {
                "non_breakout_verified": True,
                "no_grid_martingale": True,
                "no_hft_latency_arb": True,
                "ftmo_28_symbol_compatible": True,
                "holdout_sanitized": True,
                "pure_text_zero_binary": True,
            },
        }
        extracted_leads.append(lead_record)
        print(f"  [+] {spec['lead_id']} ({spec['paper_id']}): raw_abs={len(disk_text)} chars -> OK")

    write_json(MANIFEST_PATH, manifest)

    output_payload = {
        "mode": "live_cleanroom_text_api",
        "source": "off3-arxiv-ssrn",
        "schema_version": "auto_public_leads_v1_off3",
        "total_leads": len(extracted_leads),
        "leads": extracted_leads,
    }

    # Strict holdout leakage audit BEFORE writing extracted/leads.json
    holdout_violations = check_holdout_clean(output_payload)
    if holdout_violations:
        for loc, msg in holdout_violations[:10]:
            print(f"[!] HOLDOUT VIOLATION at {loc}: {msg}", file=sys.stderr)
        raise RuntimeError(f"Refusing to write leads.json: {len(holdout_violations)} holdout token violation(s)")

    write_json(LEADS_PATH, output_payload)
    print(
        f"\n[SUCCESS] Harvested {len(extracted_leads)} leads -> {LEADS_PATH}\n"
        f"          Manifest ({len(manifest)} raw files) -> {MANIFEST_PATH}\n"
        f"          Holdout leakage violations: 0"
    )
    return 0


_KNOWN_AUTHORS: dict[str, list[str]] = {
    "OFF3-SSRN-05": ["Lei Gao", "Yufeng Han", "Sophia Zhengzi Li", "Guofu Zhou"],
    "OFF3-SSRN-06": ["Guido Baltussen", "Zhi Da", "Sten Lammers", "Martin P. E. Martens"],
    "OFF3-SSRN-07": ["Nina Boyarchenko", "Lars Christian Larsen", "Paul Whelan"],
    "OFF3-SSRN-15": ["David O. Lucca", "Emanuel Moench"],
    "OFF3-SSRN-20": ["Lukas Menkhoff", "Lucio Sarno", "Maik Schmeling", "Andreas Schrimpf"],
    "OFF3-SSRN-21": ["Domenico Ferraro", "Kenneth Rogoff", "Barbara Rossi"],
}


if __name__ == "__main__":
    raise SystemExit(run())
