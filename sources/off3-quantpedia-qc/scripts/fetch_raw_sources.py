"""Cleanroom pure-text fetcher for Offensive #3 Quantpedia & QuantConnect specs.

Guardrails:
  - Operates strictly inside D:/ANNAM/strategy-intel/sources/off3-quantpedia-qc/.
  - Pure text/HTML only: fails closed on any forbidden binary extension, non-text
    Content-Type, or binary magic bytes.
  - Saves verbatim article text snapshots in raw/*.json and computes exact SHA-256
    manifest in raw_manifest.sha256.json (compatible with scripts/common/verify_verbatim.py).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
import urllib.request

SOURCE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = SOURCE_DIR / "raw"
MANIFEST_PATH = SOURCE_DIR / "raw_manifest.sha256.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
}

BLOCKED_EXTENSIONS = frozenset(
    {
        ".ex4", ".ex5", ".mq4", ".mq5", ".dll", ".exe", ".msi",
        ".bat", ".cmd", ".ps1", ".vbs", ".zip", ".rar", ".7z",
        ".tar", ".gz", ".bin", ".pdf",
    }
)

BINARY_MAGIC = (
    b"MZ", b"PK\x03\x04", b"PK\x05\x06", b"Rar!\x1a\x07",
    b"7z\xbc\xaf\x27\x1c", b"\x1f\x8b", b"\x7fELF", b"%PDF-",
)

TARGETS: tuple[dict[str, str], ...] = (
    # --- 12 Quantpedia public strategies ---
    {
        "slug": "qp-01-currency-momentum-factor",
        "original_id": "OFF3-QP-01",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/currency-momentum-factor/",
    },
    {
        "slug": "qp-02-fx-carry-trade",
        "original_id": "OFF3-QP-02",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/fx-carry-trade/",
    },
    {
        "slug": "qp-03-dollar-carry-trade",
        "original_id": "OFF3-QP-03",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/dollar-carry-trade/",
    },
    {
        "slug": "qp-04-currency-value-factor-ppp",
        "original_id": "OFF3-QP-04",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/currency-value-factor-ppp-strategy/",
    },
    {
        "slug": "qp-05-trading-wti-brent-spread",
        "original_id": "OFF3-QP-05",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/trading-wti-brent-spread/",
    },
    {
        "slug": "qp-06-crude-oil-predicts-equity-returns",
        "original_id": "OFF3-QP-06",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/crude-oil-predicts-equity-returns/",
    },
    {
        "slug": "qp-07-skewness-effect-in-commodities",
        "original_id": "OFF3-QP-07",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/skewness-effect-in-commodities/",
    },
    {
        "slug": "qp-08-turn-of-the-month-equity-indexes",
        "original_id": "OFF3-QP-08",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes/",
    },
    {
        "slug": "qp-09-fomc-meeting-effect-in-stocks",
        "original_id": "OFF3-QP-09",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/federal-open-market-committee-meeting-effect-in-stocks/",
    },
    {
        "slug": "qp-10-market-sentiment-overnight-anomaly",
        "original_id": "OFF3-QP-10",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/market-sentiment-and-an-overnight-anomaly/",
    },
    {
        "slug": "qp-11-pre-holiday-effect",
        "original_id": "OFF3-QP-11",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/pre-holiday-effect/",
    },
    {
        "slug": "qp-12-short-term-reversal-with-futures",
        "original_id": "OFF3-QP-12",
        "source_origin": "quantpedia-public-strategy",
        "url": "https://quantpedia.com/strategies/short-term-reversal-with-futures/",
    },
    # --- 10 QuantConnect Strategy Library public tutorials ---
    {
        "slug": "qc-01-forex-mean-reversion-and-momentum",
        "original_id": "OFF3-QC-01",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/combining-mean-reversion-and-momentum-in-forex-market",
    },
    {
        "slug": "qc-02-forex-low-frequency-hp-momentum",
        "original_id": "OFF3-QC-02",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/the-momentum-strategy-based-on-the-low-frequency-component-of-forex-market",
    },
    {
        "slug": "qc-03-risk-premia-forex-skewness",
        "original_id": "OFF3-QC-03",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/risk-premia-in-forex-markets",
    },
    {
        "slug": "qc-04-gold-market-timing-fed-model",
        "original_id": "OFF3-QC-04",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/gold-market-timing",
    },
    {
        "slug": "qc-05-improved-commodities-tsmom-cf",
        "original_id": "OFF3-QC-05",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/improved-momentum-strategy-on-commodities-futures",
    },
    {
        "slug": "qc-06-commodities-ema-vol-trend-following",
        "original_id": "OFF3-QC-06",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/commodities-futures-trend-following",
    },
    {
        "slug": "qc-07-intraday-index-etf-momentum",
        "original_id": "OFF3-QC-07",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/intraday-etf-momentum",
    },
    {
        "slug": "qc-08-vix-percentile-index-regime",
        "original_id": "OFF3-QC-08",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/vix-predicts-stock-index-returns",
    },
    {
        "slug": "qc-09-optimal-ou-pairs-trading",
        "original_id": "OFF3-QC-09",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/optimal-pairs-trading",
    },
    {
        "slug": "qc-10-country-equity-index-pairs-trading",
        "original_id": "OFF3-QC-10",
        "source_origin": "quantconnect-strategy-library",
        "url": "https://www.quantconnect.com/tutorials/strategy-library/pairs-trading-with-country-etfs",
    },
)


class _ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._in_title = False
        self.title_parts: list[str] = []
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript", "svg", "nav", "footer", "header"):
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3", "h4", "p", "li", "tr", "div", "section", "article", "pre"):
            self.chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "svg", "nav", "footer", "header") and self._skip > 0:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
            return
        if self._skip == 0:
            text = data.replace("\xa0", " ").strip()
            if text:
                self.chunks.append(text + " ")


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Unsupported URL scheme: {url}")
    path_lower = parsed.path.lower()
    for ext in BLOCKED_EXTENSIONS:
        if path_lower.endswith(ext):
            raise ValueError(f"Blocked binary URL extension {ext}: {url}")


def _extract_clean_body(source_origin: str, full_text: str) -> dict[str, str]:
    text = re.sub(r"[ \t]+", " ", full_text)
    text = re.sub(r"\n{2,}", "\n", text).strip()

    if source_origin == "quantpedia-public-strategy":
        # Strip top marketing banner before overview
        m_sub = re.search(r"Get subscription\s*\n", text)
        body = text[m_sub.end():] if m_sub else text
        # Strip bottom footer/comments/marketing after Source paper / Related strategies
        m_end = re.search(r"\n(?:Comments\b|Leave a Reply\b|Quantpedia Pro\b|Do you want to test)", body)
        if m_end:
            body = body[:m_end.start()]
        body = body.strip()

        def _sec(header: str, stops: tuple[str, ...]) -> str:
            pat = rf"{header}\s*\n(.*?)(?:\n(?:{'|'.join(stops)})|\Z)"
            m = re.search(pat, body, re.S | re.I)
            return m.group(1).strip() if m else ""

        stops = (
            "Fundamental reason",
            "Simple trading strategy",
            "Hedge for stocks during bear markets",
            "Out-of-sample strategy implementation",
            "Source paper",
            "Other papers",
            "Related strategies",
            "Performance",
            "Backtest",
        )
        m_first_h = re.search(r"\n(?:Fundamental reason|Simple trading strategy|Source paper)", body, re.I)
        overview = body[:m_first_h.start()].strip() if m_first_h else body[:1200]
        return {
            "overview": overview[:2500],
            "fundamental_reason": _sec("Fundamental reason", stops)[:2500],
            "simple_trading_strategy": _sec("Simple trading strategy", stops)[:3000],
            "source_paper": _sec("Source paper", ("Other papers", "Related strategies", "Comments"))[:1200],
            "raw_text": body[:9000],
        }

    # quantconnect-strategy-library
    m_start = re.search(r"\n(?:Abstract|Introduction)\s*\n", "\n" + text)
    body = text[m_start.start():] if m_start else text
    m_end = re.search(r"\n(?:Update Backtest|Accepted Answer|Permalink|person upvoted|Log in to post)\b", body)
    if m_end:
        body = body[:m_end.start()]
    body = body.strip()

    m_method = re.search(r"\nMethod\s*\n(.*?)(?:\n(?:Conclusion|Results|Reference|Summary)|\Z)", body, re.S)
    m_abs = re.search(r"(?:Abstract|Introduction)\s*\n(.*?)(?:\n(?:Method|Background|Step 1)|\Z)", body, re.S)
    m_ref = re.search(r"\nReferences?\s*\n(.*?)\Z", body, re.S)
    return {
        "overview": (m_abs.group(1).strip() if m_abs else body[:1800])[:2500],
        "method_text": (m_method.group(1).strip() if m_method else "")[:5000],
        "reference_text": (m_ref.group(1).strip() if m_ref else "")[:1200],
        "raw_text": body[:9000],
    }


def _fetch_one(target: dict[str, str]) -> dict[str, Any]:
    url = target["url"]
    _validate_url(url)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        status = int(resp.status)
        content_type = str(resp.headers.get("Content-Type", "")).lower()
        if not any(content_type.startswith(p) for p in ("text/html", "text/plain", "application/xhtml+xml")):
            raise ValueError(f"Blocked non-text Content-Type {content_type!r} for {url}")
        payload = resp.read(2 * 1024 * 1024)
        for sig in BINARY_MAGIC:
            if payload.startswith(sig):
                raise ValueError(f"Blocked binary magic signature for {url}")
        html = payload.decode("utf-8", errors="ignore")

    parser = _ArticleTextParser()
    parser.feed(html)
    page_title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    sections = _extract_clean_body(target["source_origin"], "".join(parser.chunks))
    if len(sections["raw_text"]) < 200:
        raise ValueError(f"Extracted raw_text too short ({len(sections['raw_text'])} chars) for {url}")

    return {
        "slug": target["slug"],
        "original_id": target["original_id"],
        "source_origin": target["source_origin"],
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "page_title": page_title,
        "sections": sections,
        "raw_text": sections["raw_text"],
    }


def _sha256_upper(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as ex:
        records = list(ex.map(_fetch_one, TARGETS))

    manifest: dict[str, dict[str, Any]] = {}
    for rec in records:
        fname = f"{rec['slug']}.json"
        fpath = RAW_DIR / fname
        fpath.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        manifest[fname] = {
            "sha256": _sha256_upper(fpath),
            "size": fpath.stat().st_size,
        }
        print(
            f"[OK] {rec['original_id']} | {fname:45s} | http={rec['http_status']} "
            f"| raw_chars={len(rec['raw_text']):5d} | title={rec['page_title'][:55]}"
        )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"\n[DONE] Saved {len(records)} raw text snapshots & manifest at {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
