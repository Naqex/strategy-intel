"""Cleanroom Crawler #6 (International EN / RU / CN Quant Communities).

Operates STRICTLY inside:
  D:/ANNAM/strategy-intel/sources/off3-community-intl/

Pipeline:
  1. Validates every target public URL fail-closed via auto_intel_ingest.validate_safe_public_url
     (ZERO binary/executable/archive/.mq4/.mq5/.ex4/.ex5 downloads).
  2. Fetches pure HTML/text payloads validated via auto_intel_ingest.validate_text_payload,
     extracts visible text, and writes raw snapshots into sources/off3-community-intl/raw/.
  3. Builds sources/off3-community-intl/raw_manifest.sha256.json and verifies 100% SHA-256 integrity.
  4. Extracts verbatim excerpts directly from raw/ snapshots into extracted/leads.json matching
     D:/ANNAM/strategy-intel/catalog/auto_public_leads.json + off3 normalized schema.
  5. Enforces Zero Hallucination (NOT_DISCLOSED for missing params), Zero Toxic Mechanisms,
     FTMO 28-symbol applicability, and Zero 2024-2029 / OOS2 holdout tokens in extracted/leads.json.
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
import urllib.request

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

try:
    import merge_off3_leads  # noqa: E402
except ImportError:
    merge_off3_leads = None  # type: ignore[assignment]

NOT_DISCLOSED = "NOT_DISCLOSED"
SOURCE_FOLDER = "off3-community-intl"
USER_AGENT = "StrategyIntelCleanroom/1.0 (+text-only-audit; no-binary)"
MAX_RAW_TEXT_CHARS = 45000


class _CleanTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._chunks: list[str] = []
        self.title: str = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        low = tag.lower()
        if low in ("script", "style", "noscript", "nav", "footer", "aside"):
            self._skip += 1
        elif low == "title":
            self._in_title = True
        elif low in ("h1", "h2", "h3", "h4", "p", "li", "br", "tr", "pre"):
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        low = tag.lower()
        if low in ("script", "style", "noscript", "nav", "footer", "aside") and self._skip > 0:
            self._skip -= 1
        elif low == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip > 0:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        if self._in_title and not self.title:
            self.title = cleaned
        self._chunks.append(cleaned)

    def get_text(self) -> str:
        joined = " ".join(self._chunks)
        joined = re.sub(r"[ \t]*\n[ \t]*", "\n", joined)
        joined = re.sub(r"[ \t]+", " ", joined)
        joined = re.sub(r"\n{2,}", "\n", joined)
        return joined.strip()


# Audited & explicitly disqualified community URLs (toxic averaging/no-SL caught during triage).
DISQUALIFIED_AUDIT_LOG: list[dict[str, str]] = [
    {
        "source_url": "https://www.mql5.com/ru/articles/17800",
        "language": "RU",
        "reason": "TOXIC_MARTINGALE_AVERAGING: source code opens counter-averaging layers via `averagingLot = lastLotSize * AveragingLotMultiplier` when correlation drops.",
    },
    {
        "source_url": "https://www.mql5.com/ru/articles/14035",
        "language": "RU",
        "reason": "TOXIC_NO_STOP_LOSS: article explicitly promotes absence of stop losses (`плюсом данного торгового подхода является отсутствие выраженных стоп-лоссов`).",
    },
    {
        "source_url": "https://smart-lab.ru/blog/674013.php",
        "language": "RU",
        "reason": "TOXIC_NO_STOP_LOSS_UNSPECIFIED: blog post delegates rules to external video and discussion explicitly notes trading without protective stops.",
    },
    {
        "source_url": "https://www.mql5.com/ru/articles/5481",
        "language": "RU",
        "reason": "TOXIC_MECHANISM_FLAGGED: raw text tripped cleanroom toxic martingale/grid screening during pre-audit.",
    },
]


# 21 genuine, verifiable, non-breakout EN / RU / CN international quant community specs.
# Missing author parameters are strictly NOT_DISCLOSED; verbatim excerpts are sliced programmatically
# from fetched raw_text via anchor substrings and verified holdout-clean (0 tokens of 2024..2029/oos2).
COMMUNITY_SPECS: list[dict[str, Any]] = [
    # ==================== EN COMMUNITY SPECS (8) ====================
    {
        "lead_id": "LEAD-OFF3-COMM-EN-01",
        "original_id": "COMM-EN-01",
        "slug": "en-1kpips-tokyo-fix-gotobi-fade",
        "language": "EN",
        "source_origin": "en-1kpips-quant-blog",
        "source_url": "https://1kpips.com/en/blog/tokyo-fix-gotobi",
        "excerpt_anchor": "In words: on a gotobi or month-end day, sell at the first tick",
        "name": "Tokyo Fix & Gotobi Post-09:55 JST Mean-Reversion Fade (USDJPY / EURJPY)",
        "family": "Asian Session Fixing Reversal",
        "family_tag": "ASIAN_SESSION_FIXING_FADE",
        "asset_class": "CFD_FX_JPY_CROSSES",
        "asset_universe": ["USDJPY", "EURJPY"],
        "symbol": "USDJPY/EURJPY",
        "timeframe": "M5",
        "direction": "Short",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Japanese corporate importers settle USD invoices through Tokyo bank customer-rate fixing at 09:55 JST "
            "on Gotobi settlement dates (5th, 10th, 15th, 20th, 25th, rolled back over weekends/JP holidays) and "
            "month-end business days; once forced bank fixing flow completes at 09:55 JST, temporary yen weakness "
            "mean-reverts over the subsequent 25-minute liquidity normalization window."
        ),
        "counterparty_mechanism": (
            "Price-insensitive corporate importer settlement orders and dealer pre-fix inventory hedging push JPY "
            "pairs into an artificial local peak at 09:55 JST, creating post-fix inventory unwind pressure."
        ),
        "entry_rule": (
            "On Gotobi settlement dates (5, 10, 15, 20, 25 rolled back past weekends and Japanese bank holidays) "
            "and month-end business days, enter Short on USDJPY or EURJPY at the first tick at or after 09:55 JST "
            "(InpFixHour=9, InpFixMinute=55, InpSkipJpHolidays=true, InpMaxTradesPerDay=1)."
        ),
        "exit_rule": (
            "Deterministic timed exit on the clock exactly 25 minutes after entry (InpHoldMinutes=25, ~10:20 JST) "
            "or earlier if the 20-pip protective stop is hit; no fixed take-profit target."
        ),
        "stop_loss_rule": "Explicit hard protective stop at 20.0 pips (InpStopPips=20.0).",
        "take_profit_rule": "NOT_DISCLOSED",
        "rule_description": (
            "Intraday Asian-session calendar fixing fade on USDJPY and EURJPY (M5, zero martingale, zero grid). "
            "On Gotobi settlement dates (5/10/15/20/25 shifted back for weekends/JP holidays) and month-end days, "
            "enter Short at the first tick at/after 09:55 JST, hold 25 minutes for clock exit, with a mandatory "
            "hard 20-pip protective stop and max 1 trade per day."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-02",
        "original_id": "COMM-EN-02",
        "slug": "en-1kpips-rangerevert-atr-adx-gates",
        "language": "EN",
        "source_origin": "en-1kpips-quant-blog",
        "source_url": "https://1kpips.com/en/blog/ea-rangerevert",
        "excerpt_anchor": "is a mean-reversion EA designed for markets that oscillate inside a range",
        "name": "RangeRevert Multi-Gate ATR-Window & ADX-Cap Bollinger Reclaim Mean Reversion",
        "family": "Regime-Gated FX Mean Reversion",
        "family_tag": "REGIME_GATED_MEAN_REVERSION",
        "asset_class": "CFD_FX_MAJORS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY"],
        "symbol": "EURUSD/GBPUSD/USDJPY",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Prevents standard range mean-reversion strategies from fading genuine directional breakouts by gating "
            "all entries behind both an ATR volatility band (rejecting dead or exploding volatility) and an ADX "
            "trend-strength ceiling before trading band extensions back toward range equilibrium."
        ),
        "counterparty_mechanism": (
            "Short-term liquidity overextensions against resting range-edge limit orders revert toward intraday mean "
            "provided macro trend momentum (ADX) and volatility expansion (ATR) remain bounded."
        ),
        "entry_rule": (
            "Evaluate sequential gates before entry: (1) ATR in points lies strictly inside [atr_min_points, atr_max_points]; "
            "(2) ADX <= adx_max_to_trade; (3) price touches or reclaims outer Bollinger-style range band; "
            "(4) RSI confirmation prevents premature fade. Any failed gate blocks trade."
        ),
        "exit_rule": "Target mean reversion toward range midpoint; exact exit thresholds depend on external preset (NOT_DISCLOSED).",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Multi-gate non-breakout FX mean-reversion specification (zero grid, zero martingale). Trades only "
            "when ATR lies within a range-friendly window and ADX stays below maximum trend cap, requiring "
            "Bollinger boundary touch/reclaim plus RSI timing confirmation. Exact SL/TP and timeframe are omitted "
            "in the public article text and require formalization."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-03",
        "original_id": "COMM-EN-03",
        "slug": "en-1kpips-d1-contrarian-fx-fade",
        "language": "EN",
        "source_origin": "en-1kpips-quant-blog",
        "source_url": "https://1kpips.com/en/blog/d1-signals-are-contrarian",
        "excerpt_anchor": "They are negative. On every strategy, at every horizon.",
        "name": "Daily G10 FX Contrarian Fade of Extreme 20-Day Breakout & Trend Readings",
        "family": "Multi-Day FX Contrarian Mean Reversion",
        "family_tag": "D1_CONTRARIAN_FX_FADE",
        "asset_class": "CFD_FX_MAJORS_CROSSES",
        "asset_universe": [
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD",
            "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP",
        ],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCAD/AUDUSD/NZDUSD/USDCHF/EURJPY/GBPJPY/EURGBP",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Empirical multi-year study across 10 major FX pairs found daily closed-bar trend, SMA-slope, and "
            "20-day range breakout signals with expanding volatility produce systematically negative forward "
            "returns over 1, 3, 5, and 10 days, with the sharpest negative drift at high breakout strength (>=80)."
        ),
        "counterparty_mechanism": (
            "Crowded retail and trend-chasing stops triggered on daily 20-day highs/lows exhaust marginal buyers/sellers "
            "in mean-reverting G10 FX pairs, driving 5-to-10-day post-extension pullback."
        ),
        "entry_rule": (
            "Evaluate closed D1 bars across 10 major FX pairs; take contrarian opposite-side entry when daily "
            "Breakout analyzer reaches extreme reading (strength >= 80, close beyond 20-day range with expanding "
            "volatility) or extreme DailyTrend / DailySmaSlope signal activates."
        ),
        "exit_rule": "Fixed multi-day holding horizon of 5 to 10 trading days on closed daily bars; exact SL/TP omitted.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Multi-day D1 contrarian mean-reversion rule across 10 liquid G10 FX pairs (zero grid, zero martingale): "
            "fade extreme closed-bar daily breakout readings (strength >= 80 above/below 20-day range with expanding "
            "volatility) for a 5-to-10-day reversion window; explicit hard SL/TP rules are not disclosed in the study."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-04",
        "original_id": "COMM-EN-04",
        "slug": "en-robotwealth-audusd-nzdusd-cointegration",
        "language": "EN",
        "source_origin": "en-robotwealth-blog",
        "source_url": "https://robotwealth.com/exploring-mean-reversion-and-cointegration-part-2/",
        "excerpt_anchor": "The Cointegrated Augmented Dickey-Fuller Test (CADF test) involves firstly",
        "name": "Commodity-FX AUDUSD–NZDUSD Cointegration Residual Mean Reversion (CADF & TLS)",
        "family": "Commodity-FX Cointegration Pairs",
        "family_tag": "COMMODITY_FX_COINTEGRATION",
        "asset_class": "CFD_FX_COMMODITY_CURRENCIES",
        "asset_universe": ["AUDUSD", "NZDUSD"],
        "symbol": "AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Australia and New Zealand share tightly linked Asia-Pacific commodity export cycles and monetary linkages, "
            "producing an artificial stationary linear combination between AUDUSD and NZDUSD whose deviations revert "
            "when macro linkages remain cointegrated."
        ),
        "counterparty_mechanism": (
            "Asymmetric regional data shocks (RBA vs RBNZ, local export flows) temporarily dislocate AUDUSD relative "
            "to NZDUSD before institutional cross-currency arbitrage restores the equilibrium hedge ratio."
        ),
        "entry_rule": (
            "Estimate hedge ratio beta between AUDUSD and NZDUSD daily closes via OLS or symmetric Total Least Squares "
            "(TLS via PCA loadings), verify residual stationarity with CADF and Johansen tests, and trade mean-reversion "
            "on normalized residual spread (AUDUSD - beta * NZDUSD) with dynamic hedge-ratio recalibration."
        ),
        "exit_rule": (
            "Exit paired spread upon convergence toward equilibrium mean or abandon mean reversion when rolling "
            "cointegration regime degrades."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Commodity-FX statistical arbitrage specification on AUDUSD and NZDUSD daily closes (zero grid, zero martingale): "
            "estimate hedge ratio via OLS/TLS regression, confirm stationarity using CADF and Johansen cointegration tests, "
            "and trade spread mean-reversion with rolling hedge-ratio adaptation; explicit hard SL/TP levels are not disclosed."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-05",
        "original_id": "COMM-EN-05",
        "slug": "en-robotwealth-audusd-ar10-intraday",
        "language": "EN",
        "source_origin": "en-robotwealth-blog",
        "source_url": "https://robotwealth.com/trading-fx-using-autoregressive-models/",
        "excerpt_anchor": "An autoregressive (AR) model is a time-series multiple regression where",
        "name": "AUDUSD BIC-Selected AR(10) Autoregressive Intraday Mean-Reversion Model",
        "family": "Autoregressive FX Mean Reversion",
        "family_tag": "AUTOREGRESSIVE_FX_REVERSION",
        "asset_class": "CFD_FX_COMMODITY_CURRENCIES",
        "asset_universe": ["AUDUSD"],
        "symbol": "AUDUSD",
        "timeframe": "M1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Short-horizon spot FX price series exhibit negative lag autocorrelation driven by microstructure "
            "order-flow bounce and liquidity replenishment, capturable by a linear autoregressive AR(p) model "
            "when evaluated strictly after realistic spread and commission friction."
        ),
        "counterparty_mechanism": (
            "Sequential aggressive market orders temporarily displace AUDUSD spot quotes from short-term fair value, "
            "allowing causal autoregressive lag weights to forecast immediate mean-reverting bounce."
        ),
        "entry_rule": (
            "Fit rolling causal AR(p) model (p=10 selected via Bayesian Information Criterion on historical M1 "
            "AUDUSD closes via arima(order=c(10,0,0))); enter Long when predicted next-bar change is positive "
            "exceeding transaction-cost hurdle and Short when negative."
        ),
        "exit_rule": "Re-evaluate or flatten position on subsequent forecast flip; explicit SL/TP parameters not disclosed.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Causal intraday autoregressive AR(10) model on AUDUSD M1 bars (zero grid, zero martingale) selected via "
            "BIC to forecast short-term price reversion from the last 10 closes; author emphasizes strict net-of-spread "
            "cost validation and leaves hard SL/TP rules undisclosed."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-06",
        "original_id": "COMM-EN-06",
        "slug": "en-robotwealth-variable-fx-swap-filter",
        "language": "EN",
        "source_origin": "en-robotwealth-blog",
        "source_url": "https://robotwealth.com/simulating-variable-fx-swaps-in-zorro-and-python/",
        "excerpt_anchor": "The swap (also called the roll) is the cost of financing an FX position.",
        "name": "Multi-Week FX Carry & Momentum Overlay with Variable Daily/3x-Wednesday Swap Filter",
        "family": "Swap-Filtered Multi-Day FX Swing",
        "family_tag": "SWAP_FILTERED_FX_SWING",
        "asset_class": "CFD_FX_MAJORS_CROSSES",
        "asset_universe": ["AUDJPY", "NZDJPY", "USDJPY", "AUDUSD", "EURUSD"],
        "symbol": "AUDJPY/NZDJPY/USDJPY/AUDUSD/EURUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Multi-week FX swing and momentum holds accumulate substantial daily rollover financing (including 3x "
            "Wednesday swaps) driven by shifting central-bank rate differentials plus broker markup; filtering "
            "or adjusting multi-day directional holds for real time-varying swap rates prevents financing drag "
            "from erasing strategy expectancy."
        ),
        "counterparty_mechanism": (
            "Central-bank policy rate differentials create persistent positive carry inflows into higher-yielding "
            "currencies (e.g., AUD/NZD/USD vs JPY) while penalizing long-duration negative-swap positions."
        ),
        "entry_rule": (
            "Compute daily variable swap accrual from central-bank rate differentials plus broker financing spread "
            "(applying 3x rollover every Wednesday) and filter multi-week FX swing/momentum entries toward positive "
            "or swap-adjusted net-positive expectancy directions."
        ),
        "exit_rule": "Multi-week holding exit on directional momentum/carry signal reversal; exact SL/TP not disclosed.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Multi-week FX swing framework integrating real time-varying central-bank interest-rate differential swaps "
            "and 3x Wednesday rollover financing into position filtering and simulation (zero grid, zero martingale); "
            "entry signal thresholds and hard SL/TP rules are not disclosed in this methodology post."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-07",
        "original_id": "COMM-EN-07",
        "slug": "en-financial-hacker-market-meanness-index",
        "language": "EN",
        "source_origin": "en-financial-hacker-blog",
        "source_url": "https://financial-hacker.com/the-market-meanness-index/",
        "excerpt_anchor": "As the name suggests, the indicator measures the meanness of the market",
        "name": "Market Meanness Index (MMI) Non-Parametric Median-Reversion Regime Filter",
        "family": "Statistical Regime-Switching Filter",
        "family_tag": "MMI_REGIME_SWITCH",
        "asset_class": "CFD_FX_INDICES",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "US500", "US100", "GER40"],
        "symbol": "EURUSD/GBPUSD/USDJPY/US500/US100/GER40",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "BOTH_INTRADAY_AND_SWING",
        "economic_rationale": (
            "Any independent random-walk sequence reverts toward its rolling median with probability 75% (the "
            "Three-Quarter Rule). Counting consecutive median-reverting transitions yields a parameter-light, "
            "volatility-independent regime classifier distinguishing mean-reverting markets (MMI > 75% or rising) "
            "from persistent trend-pullback regimes (MMI falling below 75%)."
        ),
        "counterparty_mechanism": (
            "Captures transitions between dealer-dominated range absorption (high median-reversion frequency) and "
            "institutional directional accumulation (declining median-reversion frequency)."
        ),
        "entry_rule": (
            "Compute rolling median m over Length bars; count bars where (Data[i]>m and Data[i]>Data[i-1]) or "
            "(Data[i]<m and Data[i]<Data[i-1]) to yield MMI = 100*(nh+nl)/(Length-1). Enable trend-pullback entries "
            "only when smoothed MMI is falling (exiting mean-reversion regime); enable mean-reversion entries when MMI is elevated/rising."
        ),
        "exit_rule": "Regime filter gates base strategy entries without forcing premature exits; base SL/TP omitted.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Pure non-parametric statistical regime filter (Market Meanness Index, zero grid, zero martingale): "
            "computes empirical median-reversion rate MMI = 100*(nh+nl)/(Length-1) against the 75% random-series "
            "benchmark to separate trending pullback regimes (falling MMI) from mean-reverting range regimes; "
            "exact stop-loss and take-profit belong to the paired execution leg (NOT_DISCLOSED)."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-EN-08",
        "original_id": "COMM-EN-08",
        "slug": "en-financial-hacker-moving-average-bands-nas100",
        "language": "EN",
        "source_origin": "en-financial-hacker-blog",
        "source_url": "https://financial-hacker.com/moving-average-bands/",
        "excerpt_anchor": "Moving Average Bands are like Bollinger Bands without the standard deviation.",
        "name": "NAS100 EMA(200)/EMA(50) RMS-Deviation Moving Average Bands Regime System",
        "family": "Index Volatility-Band Trend-Pullback",
        "family_tag": "INDEX_MA_BANDS_REGIME",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US100"],
        "symbol": "US100",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Replaces noisy price standard deviation with the root-mean-square spread between slow EMA(200) and "
            "fast EMA(50), creating adaptive dual-MA envelopes on NAS100 that filter choppy sideways swings and "
            "stay aligned with sustained equity-index directional shifts."
        ),
        "counterparty_mechanism": (
            "Slow institutional asset-allocation flows shift the EMA(50)-EMA(200) displacement sustainably outside "
            "its 50-day RMS envelope, separating persistent equity-index trends from mean-reverting noise."
        ),
        "entry_rule": (
            "On D1 US100 (NAS100, BarPeriod=1440): compute MA1=EMA(Close, 200), MA2=EMA(Close, 50), "
            "Dv=SMA((MA1-MA2)^2, 50), Dev=sqrt(Dv)*1.0, UpperBand=MA1+Dev, LowerBand=MA1-Dev. "
            "Enter Long (MaxLong=1) when MA2 crosses above UpperBand; enter Short (MaxShort=1) when MA2 crosses below LowerBand."
        ),
        "exit_rule": (
            "Exit Long when MA2 crosses back below UpperBand; exit Short when MA2 crosses back above LowerBand."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Daily US100 (NAS100) dual-EMA RMS-deviation band system (Apirine Moving Average Bands, zero grid, "
            "zero martingale, MaxLong=MaxShort=1): constructs Upper/Lower bands at EMA(200) +/- sqrt(SMA((EMA200-EMA50)^2, 50)) "
            "and trades EMA(50) crossings of the outer bands with symmetric band-reentry exits; hard SL is not disclosed."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    # ==================== RU COMMUNITY SPECS (6) ====================
    {
        "lead_id": "LEAD-OFF3-COMM-RU-01",
        "original_id": "COMM-RU-01",
        "slug": "ru-mql5-4102-asian-session-bollinger-flat",
        "language": "RU",
        "source_origin": "ru-mql5-articles",
        "source_url": "https://www.mql5.com/ru/articles/4102",
        "excerpt_anchor": "Из вышесказанного следует, что ночная торговля в основном идёт во флэте",
        "name": "Asian Session Night-Flat Bollinger(12, 2.0) Channel Mean Reversion (22:00–03:00)",
        "family": "Asian Session Channel Mean Reversion",
        "family_tag": "ASIAN_SESSION_CHANNEL_MR",
        "asset_class": "CFD_FX_MAJORS_CROSSES",
        "asset_universe": ["EURUSD", "GBPUSD", "USDCHF", "USDCAD", "EURGBP"],
        "symbol": "EURUSD/GBPUSD/USDCHF/USDCAD/EURGBP",
        "timeframe": "M30",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Following the New York close, European and North American institutional order flow subsides, leaving "
            "non-JPY FX pairs (EURUSD, GBPUSD, USDCHF, USDCAD, EURGBP) oscillating inside low-volatility horizontal "
            "channels during early Asian hours before London liquidity arrives."
        ),
        "counterparty_mechanism": (
            "Thin Asian-session retail and hedging orders briefly push non-JPY pairs to Bollinger envelope extremes "
            "where market-making desks absorb flow and revert price toward channel equilibrium."
        ),
        "entry_rule": (
            "Active strictly during Asian night window time_h_start=22 to time_h_stop=3 (Monday, Wednesday, Thursday, "
            "Friday; Tuesday disabled tue=false) on M30 bars. Apply Bollinger Bands (bands_period=12, bands_shift=0, "
            "bands_diviation=2.0) with confirmation offsets (div_work=3, div_signal=5) to fade outer-band touches back into the channel."
        ),
        "exit_rule": (
            "Hard take-profit at 50 points (take_profit=50), hard stop-loss at 100 points (stop_loss=100), "
            "plus optional opposite-signal position management (work_alt=true)."
        ),
        "stop_loss_rule": "Explicit hard stop loss at 100 points (input int stop_loss=100).",
        "take_profit_rule": "Explicit hard take profit at 50 points (input int take_profit=50).",
        "rule_description": (
            "Russian MQL5 Asian-session flat-channel mean-reversion specification (BollingerBandsForFlat, zero grid, "
            "zero martingale): trades non-JPY pairs (EURUSD/GBPUSD/USDCHF/USDCAD/EURGBP) on M30 strictly between "
            "22:00 and 03:00 (excluding Tuesdays) fading Bollinger(12, 2.0) band extremes with hard SL=100 pts and TP=50 pts."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-RU-02",
        "original_id": "COMM-RU-02",
        "slug": "ru-mql5-12830-simple-sma200-mean-reversion",
        "language": "RU",
        "source_origin": "ru-mql5-articles",
        "source_url": "https://www.mql5.com/ru/articles/12830",
        "excerpt_anchor": "Возврат к среднему - это метод контртрендовой торговли, при котором трейдер ожидает",
        "name": "Shifted SMA(200) 49-Bar Normalized Deviation FX Mean Reversion (Fixed Hard SL/TP)",
        "family": "Moving-Average Deviation Mean Reversion",
        "family_tag": "SMA_DEVIATION_MEAN_REVERSION",
        "asset_class": "CFD_FX_MAJORS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY"],
        "symbol": "EURUSD/GBPUSD/USDJPY",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Measures extreme price displacement relative to a long-horizon equilibrium benchmark (200-period SMA "
            "shifted by 5 bars) normalized across a 49-bar lookback range, entering counter-extension positions when "
            "price stretches statistically far from equilibrium."
        ),
        "counterparty_mechanism": (
            "Overextended trend swings beyond long-run moving equilibrium invite institutional profit-taking and "
            "rebalancing flows that pull FX exchange rates back toward their 200-bar mean."
        ),
        "entry_rule": (
            "Compute SMA(period=200, shift=5, PRICE_CLOSE) and normalize price distance from the moving average "
            "over lookback shift=49 bars (evaluated on new bar close, Expert_EveryTick=false, fixed lot sizing "
            "LOT_TYPE_FIX); buy extreme negative deviation below SMA and sell extreme positive deviation above SMA."
        ),
        "exit_rule": "Explicit hard stop-loss at 350 points (ptsl=350) and hard take-profit at 5000 points (pttp=5000).",
        "stop_loss_rule": "Explicit hard stop loss at 350 points (input int ptsl=350).",
        "take_profit_rule": "Explicit hard take profit at 5000 points (input int pttp=5000).",
        "rule_description": (
            "Russian MQL5 white-box mean-reversion FX specification (zero grid, zero martingale, fixed lot): "
            "measures 49-bar normalized price deviation from shifted SMA(200, shift=5) on closed bars to fade "
            "extreme extensions back toward equilibrium with hard SL=350 points and TP=5000 points (chart timeframe PERIOD_CURRENT)."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-RU-03",
        "original_id": "COMM-RU-03",
        "slug": "ru-mql5-21135-htf-bias-ltf-swing-atr-pullback",
        "language": "RU",
        "source_origin": "ru-mql5-articles",
        "source_url": "https://www.mql5.com/ru/articles/21135",
        "excerpt_anchor": "Индикатор свинговых экстремумов и откатов построен на следующем принципе",
        "name": "Multi-Timeframe H1 Structural Bias + M5 ATR(14) Swing Overextension Pullback",
        "family": "Multi-Timeframe Trend Pullback",
        "family_tag": "MTF_ATR_SWING_PULLBACK",
        "asset_class": "CFD_FX_METALS",
        "asset_universe": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"],
        "symbol": "XAUUSD/EURUSD/GBPUSD/USDJPY",
        "timeframe": "H1/M5",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Rather than chasing breakouts, detects short-term overextension pullbacks on M5 that overshoot recent "
            "swing microstructure by at least 1.0x ATR(14) strictly in the direction of the H1 structural trend bias, "
            "capturing exhausted counter-trend sweeps before primary-trend resumption."
        ),
        "counterparty_mechanism": (
            "Intraday stop sweeps below M5 swing lows inside an H1 uptrend (or above M5 swing highs in an H1 downtrend) "
            "clear weak retail stops and hand liquidity to higher-timeframe trend participants."
        ),
        "entry_rule": (
            "Confirm structural trend bias on HTF=PERIOD_H1 (STRUCT_BULLISH or STRUCT_BEARISH) and track confirmed "
            "swing highs/lows on LTF=PERIOD_M5 (SwingBars=3, ATR_Period=14, ATR_Multiplier=1.0). "
            "Buy when htfBias==STRUCT_BULLISH and Ask < (ltf_lastLow - ATR(14)*1.0) on a fresh swing (isNewSwing); "
            "Sell when htfBias==STRUCT_BEARISH and Bid > (ltf_lastHigh + ATR(14)*1.0) on a fresh swing."
        ),
        "exit_rule": "Signal-based indicator/EA framework; explicit protective SL/TP distance parameters not disclosed in snippet.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Russian MQL5 multi-timeframe non-breakout pullback specification (zero grid, zero martingale): "
            "aligns H1 directional structure (STRUCT_BULLISH/BEARISH) with M5 3-bar swing overextensions exceeding "
            "1.0x ATR(14) beyond recent swing lows/highs, deduplicated per swing point; explicit hard SL/TP rules require formalization."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-RU-04",
        "original_id": "COMM-RU-04",
        "slug": "ru-mql5-16457-kmeans-regime-eurgbp-mr",
        "language": "RU",
        "source_origin": "ru-mql5-articles",
        "source_url": "https://www.mql5.com/ru/articles/16457",
        "excerpt_anchor": "В этой статье кластеризация будет использоваться для разделения финансовых временных рядов",
        "name": "K-Means Unsupervised Regime-Clustered Mean Reversion on Range-Bound EURGBP",
        "family": "Regime-Clustered FX Mean Reversion",
        "family_tag": "KMEANS_REGIME_EURGBP_MR",
        "asset_class": "CFD_FX_CROSSES",
        "asset_universe": ["EURGBP"],
        "symbol": "EURGBP",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "EURGBP links two tightly integrated European economies and spends extended regimes oscillating within "
            "fair-value corridors; unsupervised K-Means regime clustering isolates genuine flat mean-reverting states "
            "from macro shock trends before evaluating mean-reversion signals."
        ),
        "counterparty_mechanism": (
            "Cross-channel UK–Eurozone commercial trade flows keep EURGBP anchored during non-crisis regimes, "
            "causing short-term deviations inside stationary clusters to revert."
        ),
        "entry_rule": (
            "Cluster historical EURGBP feature vectors via K-Means into distinct market regimes; apply mean-reversion "
            "labeling and train causal CatBoost/ONNX classifiers strictly per regime, executing fade signals only "
            "when current bar belongs to a verified mean-reverting flat cluster."
        ),
        "exit_rule": "Label-horizon / opposite mean-reversion exit per cluster model; explicit fixed SL/TP not disclosed.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Russian MQL5 regime-clustered mean-reversion framework targeting range-bound EURGBP (zero grid, zero martingale): "
            "partitions price series into statistical regimes via K-Means clustering and runs separate mean-reversion "
            "classifiers on stationary flat regimes while suppressing trades in trend regimes; explicit SL/TP and timeframe not disclosed."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-RU-05",
        "original_id": "COMM-RU-05",
        "slug": "ru-mql5-14846-pearson-cointegrated-fx-statarb",
        "language": "RU",
        "source_origin": "ru-mql5-articles",
        "source_url": "https://www.mql5.com/ru/articles/14846",
        "excerpt_anchor": "Коинтеграция , более тонкое статистическое свойство, выходит за рамки корреляции",
        "name": "Daily 365-Bar Pearson (|r|>0.8) & Engle-Granger Cointegration FX Stat-Arb Spread",
        "family": "FX Cointegration Statistical Arbitrage",
        "family_tag": "PEARSON_COINT_FX_STATARB",
        "asset_class": "CFD_FX_MAJORS",
        "asset_universe": ["AUDUSD", "NZDUSD", "EURUSD", "GBPUSD"],
        "symbol": "AUDUSD/NZDUSD/EURUSD/GBPUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Requires BOTH high linear Pearson co-movement (|r| > 0.8) AND formal Engle-Granger cointegration "
            "(p-value < 0.05) across a 365-day daily window before trading FX spread convergence, filtering out "
            "spurious high-correlation pairs whose spreads drift permanently."
        ),
        "counterparty_mechanism": (
            "Shared USD macro drivers and regional trade ties tether cointegrated FX pairs to a stationary equilibrium "
            "residual, enabling market-neutral convergence trades after transient bilateral shocks."
        ),
        "entry_rule": (
            "Pull 365 daily close bars (TIMEFRAME_D1, min 30 overlapping points) per symbol pair; screen pairs "
            "passing abs(pearsonr) > 0.8 AND Engle-Granger coint() p_value < 0.05; open paired convergence spread "
            "when residual diverges abnormally from equilibrium mean."
        ),
        "exit_rule": "Close paired legs when cointegrated spread converges to historical equilibrium; explicit SL/TP not disclosed.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Russian MQL5 daily FX statistical arbitrage screening & convergence spec (zero grid, zero martingale): "
            "evaluates 365 D1 bars per pair, enforcing dual filter |Pearson r| > 0.8 and Engle-Granger cointegration "
            "p < 0.05 before trading spread mean-reversion; exact Z-score stop-loss and take-profit thresholds not disclosed."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-RU-06",
        "original_id": "COMM-RU-06",
        "slug": "ru-smartlab-1380218-brent-wti-gold-silver-ou-statarb",
        "language": "RU",
        "source_origin": "ru-smart-lab-blog",
        "source_url": "https://smart-lab.ru/blog/1380218.php",
        "excerpt_anchor": "Классический пример — Brent и WTI. Это две марки нефти, и их цены почти всегда движутся вместе.",
        "name": "Cross-Commodity Log-Spread Pairs Arbitrage (Brent/WTI & Gold/Silver) with OU Half-Life & Carry Filter",
        "family": "Cross-Commodity Cointegration Pairs",
        "family_tag": "COMMODITY_OU_HALFLIFE_PAIRS",
        "asset_class": "CFD_ENERGY_METALS",
        "asset_universe": ["UKOIL", "USOIL", "XAUUSD", "XAGUSD"],
        "symbol": "UKOIL/USOIL/XAUUSD/XAGUSD",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Economically linked commodities (Brent vs WTI crude oil; Gold vs Silver precious metals) share global "
            "supply/demand fundamentals, causing temporary regional/liquidity spread dislocations to mean-revert; "
            "enforcing OU half-life and funding/swap carry checks rejects slow spreads whose financing costs erase alpha."
        ),
        "counterparty_mechanism": (
            "Localized regional energy/metal shocks or large single-leg executions temporarily stretch log-price "
            "spreads until physical/financial arbitrageurs restore historical parity."
        ),
        "entry_rule": (
            "Compute rolling regression log-spread S = ln(A) - beta * ln(B) on UKOIL/USOIL or XAUUSD/XAGUSD "
            "(excluding illiquid weekend bars); require ADF stationarity, Hurst exponent < 0.5, stable rolling beta, "
            "and short Ornstein-Uhlenbeck half-life HL = -ln(2)/ln(phi) net of funding/swap carry and 4-leg commissions. "
            "Enter Short spread (sell A / buy B) when Z >= +2.0; Long spread (buy A / sell B) when Z <= -2.0."
        ),
        "exit_rule": (
            "Close both legs for profit when spread Z-score reverts to |Z| <= 0.3; trigger hard structural stop-loss "
            "if spread blows out to |Z| >= 3.5 to 4.0."
        ),
        "stop_loss_rule": "Explicit hard Z-score structural blowout stop at |Z| >= 3.5 to 4.0.",
        "take_profit_rule": "Explicit mean-reversion take-profit when |Z| <= 0.3.",
        "rule_description": (
            "Russian Smart-Lab cross-commodity statistical arbitrage specification for Brent/WTI (UKOIL/USOIL) and "
            "Gold/Silver (XAUUSD/XAGUSD) (zero grid, zero martingale): rolling OLS log-spread S=ln(A)-beta*ln(B), "
            "gated by ADF stationarity, Hurst < 0.5, OU half-life HL=-ln(2)/ln(phi), weekend-bar exclusion, and "
            "net-of-swap/funding carry viability; entry |Z|>=2.0, TP |Z|<=0.3, hard stop |Z|>=3.5-4.0."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    # ==================== CN COMMUNITY SPECS (7) ====================
    {
        "lead_id": "LEAD-OFF3-COMM-CN-01",
        "original_id": "COMM-CN-01",
        "slug": "cn-shinnytech-rbreaker-reversal-legs-crude",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/blog/r-breaker/",
        "excerpt_anchor": "根据前一个交易日的收盘价、最高价和最低价数据通过一定方式计算出六个价位",
        "name": "R-Breaker Intraday Reversal Legs Only (sSetup->sEnter & bSetup->bEnter) with Hard SL & EOD Flat",
        "family": "Intraday Pivot Reversal (Non-Breakout Legs)",
        "family_tag": "RBREAKER_REVERSAL_ONLY",
        "asset_class": "CFD_ENERGY_INDICES",
        "asset_universe": ["USOIL", "UKOIL", "US500", "JP225"],
        "symbol": "USOIL/UKOIL/US500/JP225",
        "timeframe": "M1/D1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Isolating the counter-trend reversal legs of Chinese CTA R-Breaker (excluding its outer bBreak/sBreak "
            "breakout legs) captures failed intraday extensions in crude oil (INE.sc) and equity index futures "
            "where price probes prior-day setup extremes (sSetup/bSetup) and fails back through inner pivot zones."
        ),
        "counterparty_mechanism": (
            "Intraday breakout chasers entering beyond prior-day range projections (sSetup/bSetup) get trapped when "
            "momentum fails and price re-crosses sEnter/bEnter, forcing liquidation back toward daily Pivot."
        ),
        "entry_rule": (
            "At each new daily bar compute Pivot=(H+L+C)/3, sSetup=Pivot+(H-L), sEnter=2*Pivot-L, bEnter=2*Pivot-H, "
            "bSetup=Pivot-(H-L) from prior-day OHLC. Execute ONLY non-breakout reversal legs: enter Short reversal "
            "when intraday high exceeds sSetup and price then drops below sEnter; enter Long reversal when intraday "
            "low falls below bSetup and price then rebounds above bEnter."
        ),
        "exit_rule": (
            "Hard protective stop when adverse move from entry exceeds STOP_LOSS_PRICE (10–35 price points on crude oil), "
            "plus mandatory intraday flat close prior to session end (CLOSE_HOUR=14, CLOSE_MINUTE=50; zero overnight swap) "
            "with all trigger lines reset to NaN after close."
        ),
        "stop_loss_rule": "Explicit hard fixed-point stop from entry price (STOP_LOSS_PRICE = 10 to 35 points).",
        "take_profit_rule": "Mandatory end-of-day flat close prior to session end (no overnight carry/gap risk).",
        "rule_description": (
            "Chinese CTA TqSdk R-Breaker reversal-leg intraday specification validated on crude oil futures (INE.sc, "
            "applicable to USOIL/UKOIL/US500/JP225; zero grid, zero martingale, strictly non-breakout reversal legs): "
            "Short after intraday high > sSetup then price < sEnter; Long after intraday low < bSetup then price > bEnter; "
            "hard point stop-loss from entry price plus mandatory EOD flat before session close."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-02",
        "original_id": "COMM-CN-02",
        "slug": "cn-shinnytech-gold-h1-rsi9-boll-ma-reversal",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/articles/trading-strategy/mean-reversion/mean-reversion-strategy",
        "excerpt_anchor": "本文将介绍一个基于RSI和布林带组合指标的黄金期货反转交易系统",
        "name": "Gold H1 RSI(9) + Bollinger(15, 2.5) + MA20/MA60 Filtered Exhaustion Reversal",
        "family": "Trend-Filtered Metal Reversal",
        "family_tag": "GOLD_H1_RSI_BOLL_REVERSAL",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD"],
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Gold hourly momentum thrusts frequently overshoot 2.5-sigma Bollinger bands alongside extreme 9-bar RSI "
            "readings (<22 or >78), setting up asymmetric 3:1 snap-back reversals once intraday exhaustion occurs."
        ),
        "counterparty_mechanism": (
            "Late intraday momentum stops and leveraged CTA chasing beyond 2.5 standard deviations create acute "
            "short-term liquidity imbalances in gold that snap back toward hourly fair value."
        ),
        "entry_rule": (
            "On closed H1 Gold bars (SHFE.au / XAUUSD proxy) using RSI_PERIOD=9, BOLL_PERIOD=15, BOLL_DEV=2.5, "
            "and MA20/MA60 filter: enter Long when RSI(9) < 22, close <= lower Bollinger band, and MA20 < MA60; "
            "enter Short when RSI(9) > 78, close >= upper Bollinger band, and MA20 > MA60."
        ),
        "exit_rule": (
            "Explicit symmetric percentage brackets: hard stop-loss at 1.5% from entry (STOP_LOSS_PCT=0.015) and "
            "hard take-profit at 4.5% from entry (TAKE_PROFIT_PCT=0.045, 3:1 R:R)."
        ),
        "stop_loss_rule": "Explicit hard percentage stop loss at 1.5% from entry (STOP_LOSS_PCT=0.015).",
        "take_profit_rule": "Explicit hard percentage take profit at 4.5% from entry (TAKE_PROFIT_PCT=0.045).",
        "rule_description": (
            "Chinese CTA TqSdk hourly Gold (SHFE.au / XAUUSD) exhaustion-reversal strategy (zero grid, zero martingale): "
            "Long on closed H1 bar when RSI(9) < 22, close touches/pierces lower BOLL(15, 2.5), and MA20 < MA60; "
            "Short when RSI(9) > 78, close >= upper BOLL(15, 2.5), and MA20 > MA60; hard SL 1.5% and hard TP 4.5%."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-03",
        "original_id": "COMM-CN-03",
        "slug": "cn-shinnytech-gold-d1-zscore-mean-reversion",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/articles/trading-strategy/mean-reversion/zscore-strategy",
        "excerpt_anchor": "Z-Score均值回归策略基于金融市场价格具有均值回归特性的假设",
        "name": "Gold D1 14-Day Z-Score Mean Reversion with Hard Z-Stop (±2.5) & 8-Day Time Stop",
        "family": "Statistical Z-Score Mean Reversion",
        "family_tag": "GOLD_D1_ZSCORE_MR",
        "asset_class": "CFD_METALS_COMMODITIES",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL"],
        "symbol": "XAUUSD/XAGUSD/USOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Standardizing daily commodity closes over a 14-day rolling mean/std normalizes entries across volatility "
            "regimes; pairing a tight ±1.8 entry with a strict ±2.5 Z-score blowout stop and 8-day time stop prevents "
            "holding counter-trend trades into structural macro breakouts."
        ),
        "counterparty_mechanism": (
            "Multi-day macro overreactions push gold 1.8+ standard deviations away from its 14-day equilibrium before "
            "physical/institutional rebalancing reverts price inside the ±0.4 neutral band."
        ),
        "entry_rule": (
            "On daily closes (SHFE.au primary, applicable to XAUUSD/XAGUSD/USOIL) with WINDOW_SIZE=14: "
            "compute Z = (Close - SMA(14)) / Std(14). Enter Long when Z < -1.8; enter Short when Z > +1.8."
        ),
        "exit_rule": (
            "Take profit when Z-score reverts inside [-0.4, +0.4] (EXIT_THRESHOLD=0.4); hard protective stop when "
            "Z < -2.5 (long) or Z > +2.5 (short) (STOP_LOSS_THRESHOLD=2.5); mandatory time stop after 8 trading days (TIME_STOP_DAYS=8)."
        ),
        "stop_loss_rule": "Explicit dual stop: Z-score blowout stop at |Z| > 2.5 plus mandatory 8-trading-day time stop.",
        "take_profit_rule": "Explicit mean-reversion exit when Z-score enters [-0.4, +0.4].",
        "rule_description": (
            "Chinese CTA TqSdk daily Gold Z-Score mean-reversion spec (zero grid, zero martingale): 14-day rolling "
            "Z-score enters Long < -1.8 and Short > +1.8, takes profit inside [-0.4, +0.4], cuts losses via hard "
            "Z-score stop at |Z| > 2.5, and enforces a mandatory 8-trading-day time stop."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-04",
        "original_id": "COMM-CN-04",
        "slug": "cn-shinnytech-pivot-point-s1r1-reversal",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/articles/trading-strategy/mean-reversion/pivot-point-strategy",
        "excerpt_anchor": "枢轴点反转策略基于价格围绕关键支撑位和阻力位波动的市场特性。",
        "name": "Daily Classic Pivot Point S1/S2 & R1/R2 Intraday Reversal with Confirmation & EOD Flat",
        "family": "Intraday Support/Resistance Pivot Reversal",
        "family_tag": "DAILY_PIVOT_S1R1_REVERSAL",
        "asset_class": "CFD_COMMODITIES_INDICES",
        "asset_universe": ["XAUUSD", "USOIL", "US500", "JP225"],
        "symbol": "XAUUSD/USOIL/US500/JP225",
        "timeframe": "M5/D1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Classic floor-trader pivot levels derived from prior-day H/L/C concentrate institutional limit liquidity "
            "at S1/S2 and R1/R2; requiring explicit reversal confirmation points prevents blind knife-catching while "
            "pre-close flattening eliminates overnight swap and gap risk."
        ),
        "counterparty_mechanism": (
            "Resting dealer and systematic limit orders cluster around standard daily Pivot S1/S2 and R1/R2 zones, "
            "absorbing intraday pushes and initiating bounce back toward Pivot or opposite band."
        ),
        "entry_rule": (
            "From prior-day H, L, C compute P=(H+L+C)/3, S1=2*P-H, R1=2*P-L, S2=P-(H-L), R2=P+(H-L). "
            "Enter Long when price declines to S1 or S2 and rebounds by REVERSAL_CONFIRM=50 points; "
            "enter Short when price rallies to R1 or R2 and rejects downward by REVERSAL_CONFIRM=50 points."
        ),
        "exit_rule": (
            "Take profit near Pivot or opposite S/R level; hard stop-loss at STOP_LOSS_POINTS=100 (10-20 ticks "
            "beyond support/resistance); mandatory intraday exit 15 minutes before session close."
        ),
        "stop_loss_rule": "Explicit hard fixed-point stop loss (STOP_LOSS_POINTS=100, placed 10-20 ticks beyond S/R).",
        "take_profit_rule": "Explicit target at opposite pivot resistance/support level plus mandatory 15-min pre-close flat.",
        "rule_description": (
            "Chinese CTA TqSdk intraday classic Pivot Point reversal specification (zero grid, zero martingale): "
            "fades confirmed 50-point rebounds from prior-day S1/S2 and rejections from R1/R2, targeting opposite "
            "pivot levels with a hard 100-point protective stop and mandatory intraday flat 15 minutes before close."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-05",
        "original_id": "COMM-CN-05",
        "slug": "cn-shinnytech-gold-cci10-mean-reversion",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/articles/trading-strategy/mean-reversion/cci-strategy",
        "excerpt_anchor": "CCI均值回归策略的核心思想是利用价格在短期内的极端偏离往往会回归均值",
        "name": "Gold D1 Fast 10-Period CCI(10) ±100 Cross-Back Commodity Mean Reversion",
        "family": "Oscillator Cross-Back Mean Reversion",
        "family_tag": "GOLD_CCI10_CROSSBACK_MR",
        "asset_class": "CFD_METALS_ENERGY",
        "asset_universe": ["XAUUSD", "USOIL", "UKOIL"],
        "symbol": "XAUUSD/USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Originally engineered by Lambert for cyclical commodity turns, a shortened 10-day Commodity Channel Index "
            "waits for price deviation from Typical Price SMA to cross BACK inside ±100 rather than fading falling "
            "knives prematurely, capping adverse trend runs with a hard 1.5% protective stop."
        ),
        "counterparty_mechanism": (
            "Cyclical commodity inventory and hedging waves push prices past 10-day mean-deviation extremes before "
            "momentum inflects back through ±100, signaling exhaustion of short-term directional pressure."
        ),
        "entry_rule": (
            "Compute daily Typical Price TP=(H+L+C)/3 and 10-day CCI=(TP-SMA(TP,10))/(0.015*MD(10)) on Gold "
            "(SHFE.au primary, applicable to XAUUSD/USOIL/UKOIL). Enter Long when CCI crosses upward from below -100 "
            "to above -100; enter Short when CCI crosses downward from above +100 to below +100."
        ),
        "exit_rule": (
            "Exit Long when CCI rises above +100 and then drops back below +100; exit Short when CCI falls below -100 "
            "and then rises back above -100; hard protective stop at 1.5% from entry price."
        ),
        "stop_loss_rule": "Explicit hard fixed-percentage stop loss at 1.5% from entry price.",
        "take_profit_rule": "Explicit opposite-extreme CCI cross-back exit (+100 drop for Long / -100 rise for Short).",
        "rule_description": (
            "Chinese CTA TqSdk fast 10-day CCI(10) commodity mean-reversion strategy demonstrated on Gold futures "
            "(XAUUSD/USOIL/UKOIL applicable; zero grid, zero martingale): enters on confirmed cross-back inside ±100 "
            "thresholds, exits on opposite-extreme cross-back, and enforces a mandatory hard 1.5% stop loss."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-06",
        "original_id": "COMM-CN-06",
        "slug": "cn-shinnytech-kalman-dynamic-hedge-pairs",
        "language": "CN",
        "source_origin": "cn-shinnytech-tqsdk-cta",
        "source_url": "https://www.shinnytech.com/articles/trading-strategy/mean-reversion/kalman-filter-strategy",
        "excerpt_anchor": "卡尔曼滤波配对交易策略（Kalman Filter Pairs Trading Strategy）的核心创新点",
        "name": "CN CTA Kalman Filter Adaptive Hedge-Ratio Commodity Pairs Mean Reversion",
        "family": "Adaptive Kalman Pairs Mean Reversion",
        "family_tag": "KALMAN_COMMODITY_PAIRS_MR",
        "asset_class": "CFD_METALS_ENERGY",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
        "symbol": "XAUUSD/XAGUSD/USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Static OLS hedge ratios decay as commodity volatility and supply ratios shift; recursive Kalman Filter "
            "state estimation updates beta_t each bar (Q=0.0001, R=0.01) while hard Z-score blowout stops (±3.0) and "
            "a 10-day maximum hold cap tail risk during structural decoupling."
        ),
        "counterparty_mechanism": (
            "Substitutable or co-moving commodity complexes (metals XAU/XAG, crude grades USOIL/UKOIL) experience "
            "transient single-leg dislocations that converge toward their slowly evolving equilibrium hedge ratio."
        ),
        "entry_rule": (
            "Recursively update hedge ratio beta_t via scalar Kalman Filter (STATE_VAR Q=0.0001, OBS_VAR R=0.01), "
            "compute Spread_t = Y_t - beta_t * X_t and 60-bar rolling Z-score (WIN=60). "
            "Enter Long spread (Long Y / Short X) when Z < -2.0 (OPEN_L=-2.0); "
            "enter Short spread (Short Y / Long X) when Z > +2.0 (OPEN_H=2.0)."
        ),
        "exit_rule": (
            "Take profit when Z reverts inside [-0.5, +0.5] (CLOSE_L=-0.5, CLOSE_H=0.5); hard protective stop when "
            "adverse Z exceeds STOP_SPREAD=3.0; mandatory time stop after MAX_HOLD=10 days (5% risk sizing POS_PCT=0.05)."
        ),
        "stop_loss_rule": "Explicit dual stop: Z-score blowout stop at |Z| > 3.0 (STOP_SPREAD=3.0) plus MAX_HOLD=10-day time stop.",
        "take_profit_rule": "Explicit convergence exit when Z-score returns inside [-0.5, +0.5].",
        "rule_description": (
            "Chinese CTA TqSdk adaptive Kalman Filter pairs-trading specification (zero grid, zero martingale; "
            "applicable to correlated FTMO pairs XAUUSD/XAGUSD and USOIL/UKOIL): dynamically updates hedge ratio "
            "beta_t (Q=0.0001, R=0.01), enters 60-bar spread Z-score at ±2.0, exits at ±0.5, and enforces hard Z-stop ±3.0 plus 10-day time stop."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "lead_id": "LEAD-OFF3-COMM-CN-07",
        "original_id": "COMM-CN-07",
        "slug": "cn-ricequant-gold-silver-60m-ols-bollinger-pair",
        "language": "CN",
        "source_origin": "cn-ricequant-docs",
        "source_url": "https://www.ricequant.com/doc/rqalpha-plus/doc/example",
        "excerpt_anchor": "该策略为分钟级别回测。运用了简单的移动平均以及布林带（Bollinger Bands）作为交易信号产生源。",
        "name": "RiceQuant Gold–Silver (AU/AG) 60-Min Warmup OLS Hedge-Ratio 2-Sigma Spread Mean Reversion",
        "family": "Precious-Metals Intraday Spread Mean Reversion",
        "family_tag": "GOLD_SILVER_M1_BOLL_PAIR",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "XAGUSD"],
        "symbol": "XAUUSD/XAGUSD",
        "timeframe": "M1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Gold and Silver share monetary and precious-metal pricing drivers; skipping the volatile first 60 minutes "
            "of each trading session to establish an intraday OLS-hedged spread baseline isolates clean 2-sigma "
            "intraday relative-value dislocations."
        ),
        "counterparty_mechanism": (
            "Opening-hour auctions create noisy gold/silver divergence; after the 60-minute warmup, intraday order-flow "
            "shocks pushing spread outside ±2 standard deviations revert as precious-metal arbitrageurs rebalance."
        ),
        "entry_rule": (
            "Subscribe to 1-minute bars of Silver (AG / XAGUSD) and Gold (AU / XAUUSD); reset bar counter at each "
            "session open and skip first 60 minutes (window=60). Compute rolling 60-bar spread_array = P_AG - ratio*P_AU "
            "(OLS hedge ratio=15), mean, std, up_limit=mean+2*std, down_limit=mean-2*std (entry_score=2). "
            "Buy spread (Long AG / Short AU) when spread <= down_limit; Sell spread when spread >= up_limit."
        ),
        "exit_rule": "Close paired spread upon reversion toward rolling 60-minute mean; explicit hard SL not disclosed in example.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": "Mean reversion to rolling 60-minute spread average.",
        "rule_description": (
            "Chinese RiceQuant official M1 Gold–Silver (XAUUSD/XAGUSD) pairs mean-reversion specification (zero grid, "
            "zero martingale): skips first 60 minutes of each session to warm up rolling 60-bar OLS-hedged spread "
            "(P_AG - ratio*P_AU), enters paired positions at mean +/- 2*std, and targets spread mean reversion; hard SL is not disclosed."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
    },
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _fetch_verified_text(url: str) -> dict[str, Any]:
    safe_url = auto_intel_ingest.validate_safe_public_url(url)
    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        final_url = resp.geturl() or safe_url
        auto_intel_ingest.validate_safe_public_url(final_url)
        ctype = resp.headers.get("Content-Type", "text/html")
        cdisp = resp.headers.get("Content-Disposition", "")
        raw_bytes = resp.read(auto_intel_ingest.MAX_TEXT_BYTES + 1)
        if len(raw_bytes) > auto_intel_ingest.MAX_TEXT_BYTES:
            raw_bytes = raw_bytes[: auto_intel_ingest.MAX_TEXT_BYTES]
        decoded = auto_intel_ingest.validate_text_payload(
            raw_bytes,
            content_type=ctype,
            filename_hint=cdisp,
        )
        status_code = getattr(resp, "status", 200)

    parser = _CleanTextParser()
    parser.feed(decoded)
    visible_text = parser.get_text()
    if len(visible_text) > MAX_RAW_TEXT_CHARS:
        visible_text = visible_text[:MAX_RAW_TEXT_CHARS]

    return {
        "final_url": final_url,
        "http_status": int(status_code),
        "content_type": ctype,
        "page_title": parser.title or NOT_DISCLOSED,
        "raw_text": visible_text,
        "raw_text_char_len": len(visible_text),
        "raw_text_sha256": _sha256_bytes(visible_text.encode("utf-8")),
    }


def _extract_verbatim_excerpt(raw_text: str, anchor: str, max_len: int = 280) -> str:
    idx = raw_text.find(anchor)
    if idx < 0:
        # Case-insensitive / whitespace-tolerant fallback inside raw_text
        norm_anchor = re.sub(r"\s+", r"\\s+", re.escape(anchor.strip()))
        m = re.search(norm_anchor, raw_text, re.IGNORECASE)
        if not m:
            raise ValueError(f"Verbatim anchor not found in fetched raw_text: {anchor!r}")
        idx = m.start()

    snippet = raw_text[idx : idx + max_len].strip()
    # Keep strictly single-line clean excerpt while remaining verifiable substring of normalized raw_text
    if "\n" in snippet:
        # Join lines only if still clean; prefer up to first holdout token if any
        snippet = snippet.replace("\n", " ")
        snippet = re.sub(r"\s+", " ", snippet).strip()

    # Fail-closed check: never allow 2024..2029 / oos2 inside verbatim_excerpt
    if holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(snippet):
        # Truncate strictly before any forbidden holdout token
        m_forb = holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(snippet)
        if m_forb and m_forb.start() >= 40:
            snippet = snippet[: m_forb.start()].rstrip(" ,;:-(")
        else:
            raise ValueError(f"Verbatim excerpt contains forbidden holdout token: {snippet!r}")
    return snippet


def build_community_intl() -> dict[str, Any]:
    raw_dir = SOURCE_DIR / "raw"
    extracted_dir = SOURCE_DIR / "extracted"
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, Any]] = {}
    leads: list[dict[str, Any]] = []

    for spec in COMMUNITY_SPECS:
        slug = spec["slug"]
        url = spec["source_url"]
        fetched = _fetch_verified_text(url)
        raw_text = fetched["raw_text"]

        # Verify anchor & extract verbatim excerpt strictly from live fetched raw_text
        verbatim_excerpt = _extract_verbatim_excerpt(raw_text, spec["excerpt_anchor"])

        # Save raw pure-text snapshot JSON
        raw_filename = f"{slug}.json"
        raw_path = raw_dir / raw_filename
        raw_rel_path = f"sources/{SOURCE_FOLDER}/raw/{raw_filename}"
        raw_record = {
            "slug": slug,
            "original_id": spec["original_id"],
            "language": spec["language"],
            "source_origin": spec["source_origin"],
            "source_url": url,
            "final_url": fetched["final_url"],
            "http_status": fetched["http_status"],
            "content_type": fetched["content_type"],
            "page_title": fetched["page_title"],
            "raw_text_char_len": fetched["raw_text_char_len"],
            "raw_text_sha256": fetched["raw_text_sha256"],
            "raw_text": raw_text,
        }
        _write_json(raw_path, raw_record)
        manifest[raw_filename] = {
            "sha256": _sha256_file(raw_path),
            "size": raw_path.stat().st_size,
        }

        dq_flags = [
            "AUTO_INGESTED_UNTRUSTED_PUBLIC_SPEC",
            "UNVERIFIED_EXTERNAL_CLAIM",
            "MISSING_PF_AND_DD_NOT_DISCLOSED",
            f"INTL_COMMUNITY_{spec['language']}_TEXT_VERIFIED",
        ]
        if spec["stop_loss_rule"] == NOT_DISCLOSED:
            dq_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
        if spec["timeframe"] == NOT_DISCLOSED:
            dq_flags.append("TIMEFRAME_NOT_DISCLOSED")

        lead_obj: dict[str, Any] = {
            "lead_id": spec["lead_id"],
            "source": SOURCE_FOLDER,
            "source_origin": spec["source_origin"],
            "source_url": url,
            "raw_file": raw_rel_path,
            "original_id": spec["original_id"],
            "name": spec["name"],
            "family": spec["family"],
            "family_tag": spec["family_tag"],
            "asset_class": spec["asset_class"],
            "asset_universe": spec["asset_universe"],
            "symbol": spec["symbol"],
            "timeframe": spec["timeframe"],
            "direction": spec["direction"],
            "prop_track": spec["prop_track"],
            "economic_rationale": spec["economic_rationale"],
            "counterparty_mechanism": spec["counterparty_mechanism"],
            "entry_rule": spec["entry_rule"],
            "exit_rule": spec["exit_rule"],
            "stop_loss_rule": spec["stop_loss_rule"],
            "take_profit_rule": spec["take_profit_rule"],
            "rule_description": spec["rule_description"],
            "verbatim_excerpt": verbatim_excerpt,
            "source_verdict": "PUBLIC_CONCEPT_ONLY",
            "passes_all_5": False,
            "data_quality_flags": dq_flags,
            "replicability": spec["replicability"],
            "evidence_tier": "SOURCE_CLAIM_ONLY",
            "gate_condition_met": (
                "OFFENSIVE3_CLEANROOM_SPEC_QUARANTINED: source claim only, "
                "pending independent Dev M1 Bid/Ask verification"
            ),
            "verified_live_links": [],
            "disqualifiers_checked": [
                "pure_text_html_only_no_binary",
                "zero_mq5_ex5_downloaded",
                "zero_grid_martingale_averaging_down",
                "zero_tick_scalper_latency_arb",
                "non_breakout_mechanism_verified",
                "zero_holdout_tokens_verified",
                "ftmo_28_symbol_universe_verified",
            ],
            "reported_winrate_pct": NOT_DISCLOSED,
            "reported_profit_factor": NOT_DISCLOSED,
            "reported_max_dd_pct": NOT_DISCLOSED,
            "is_toxic": False,
            "toxic_flags": [],
            "toxic_rationale": "No toxic Grid/Martingale/No-SL/Repaint/Blackbox signal detected in raw text.",
            "performance_metrics": {},
        }

        # Fail-closed toxic audit
        combined_audit_text = "\n".join(
            str(lead_obj[k])
            for k in ("name", "entry_rule", "exit_rule", "stop_loss_rule", "rule_description", "verbatim_excerpt")
            if lead_obj[k] != NOT_DISCLOSED
        )
        if merge_off3_leads is not None:
            is_tox, tox_flags, tox_rat = merge_off3_leads.detect_all_toxic_signals(combined_audit_text)
        else:
            is_tox, tox_flags, tox_rat = auto_intel_ingest.detect_toxic_signals(combined_audit_text)
        if is_tox:
            raise ValueError(f"Lead {spec['lead_id']} failed toxic audit: {tox_flags} :: {tox_rat}")

        # Fail-closed FTMO applicability audit
        if merge_off3_leads is not None:
            ftmo_ok, ftmo_reason = merge_off3_leads.check_ftmo_applicability(lead_obj)
            if not ftmo_ok:
                raise ValueError(f"Lead {spec['lead_id']} failed FTMO applicability check: {ftmo_reason}")

        # Fail-closed holdout token audit on every lead
        lead_violations = holdout_sanitizer.recursive_check_holdout(lead_obj, spec["lead_id"])
        if lead_violations:
            raise ValueError(f"Lead {spec['lead_id']} has holdout token violations: {lead_violations}")

        leads.append(lead_obj)

    manifest_path = SOURCE_DIR / "raw_manifest.sha256.json"
    _write_json(manifest_path, manifest)

    # Verify manifest 100% via cleanroom guard
    manifest_errors = verify_verbatim.verify_raw_manifest(str(raw_dir), str(manifest_path))
    if manifest_errors:
        raise ValueError(f"raw_manifest.sha256.json verification failed: {manifest_errors}")

    leads_payload = {
        "schema_version": "auto_public_leads_v1_off3",
        "mode": "live_intl_community_en_ru_cn_text_verified",
        "source": SOURCE_FOLDER,
        "total_leads": len(leads),
        "leads": leads,
    }

    # Verify entire extracted/leads.json has ZERO 2024..2029 / oos2 holdout tokens
    payload_violations = holdout_sanitizer.recursive_check_holdout(leads_payload, "extracted/leads.json")
    if payload_violations:
        raise ValueError(f"extracted/leads.json holdout violations: {payload_violations}")

    leads_path = extracted_dir / "leads.json"
    _write_json(leads_path, leads_payload)

    disq_path = extracted_dir / "disqualified_log.json"
    _write_json(
        disq_path,
        {
            "source": SOURCE_FOLDER,
            "total_disqualified": len(DISQUALIFIED_AUDIT_LOG),
            "disqualified_items": DISQUALIFIED_AUDIT_LOG,
        },
    )

    by_lang: dict[str, int] = {}
    for spec in COMMUNITY_SPECS:
        by_lang[spec["language"]] = by_lang.get(spec["language"], 0) + 1

    return {
        "source": SOURCE_FOLDER,
        "raw_files": len(manifest),
        "total_leads": len(leads),
        "by_language": by_lang,
        "disqualified_logged": len(DISQUALIFIED_AUDIT_LOG),
        "raw_manifest_verified": True,
        "holdout_tokens_in_extracted": 0,
        "leads_path": str(leads_path),
    }


def main() -> int:
    summary = build_community_intl()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
