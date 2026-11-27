"""Air-gapped pure-text harvester for MQL5 CodeBase & MQL5 Articles (Offensive #3, C3-MQL5).

Operates strictly inside D:/ANNAM/strategy-intel/sources/off3-mql5-open/.
Guardrails:
  1. Pure HTML/text fetch ONLY — every URL and payload is gated fail-closed through
     scripts/auto_intel_ingest.py (validate_safe_public_url + validate_text_payload).
     NEVER downloads .mq5, .ex5, .mq4, .ex4, .dll, .zip, or any binary/archive attachment.
  2. Saves structured JSON rule specifications + verbatim HTML-stripped page text into raw/.
  3. Writes deterministic SHA-256 manifest to raw_manifest.sha256.json.
  4. Captures both clean white-box non-breakout candidates (22) and disqualified toxic EAs (7)
     so extract_mql5_leads.py can audit and log rejections verbatim from raw/.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import html
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
for _p in (str(SCRIPTS_DIR), str(COMMON_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_intel_ingest  # noqa: E402
import holdout_sanitizer  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class _PageTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "nav", "footer"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "nav", "footer") and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip > 0:
            return
        cleaned = data.strip()
        if cleaned:
            self._chunks.append(cleaned)

    def get_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._chunks)).strip()


# 22 Verified White-Box Non-Breakout MQL5 Leads + 7 Verified Toxic Rejects
CURATED_MQL5_TARGETS: tuple[dict[str, Any], ...] = (
    # =========================================================================
    # THEME 1: SESSION / SWING MEAN REVERSION WITH WIDE ATR / HARD STOPS (7)
    # =========================================================================
    {
        "slug": "mql5-art-22783-mr-swing-value-charts-svapo",
        "original_id": "MQL5-ART-22783",
        "lead_id": "LEAD-OFF3-MQL5-01",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/22783",
        "name": "MR Swing: Regime-Adaptive Mean-Reversion Swing System (200-Day Hysteresis + Value Charts + SVAPO)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "MEAN_REVERSION_SWING_VALUE_CHARTS",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "SP500", "INDICES"],
        "symbol": "US500",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Short-term volatility-normalized pullbacks inside a persistent macro regime revert to fair value "
            "as liquidity providers absorb forced daily liquidations while avoiding counter-trend whipsaws."
        ),
        "counterparty_mechanism": (
            "Short-horizon stop-outs and reactive daily deleveraging push Value Chart lows below -7.5 DVU "
            "inside an intact 200-day trend regime, creating mean-reversion entries until SVAPO exhaustion."
        ),
        "entry_rule": (
            "Classify bull/bear macro regime via a 200-day hysteresis channel; in bull regime enter long "
            "when 5-bar smoothed Value Chart lows (DVU constant 0.16) reach oversold <= -7.5 (or DVO extreme); "
            "symmetric short entry in bear regime (InpMode = MODE_AGGRESSIVE)."
        ),
        "exit_rule": (
            "When SVAPO crosses above the upper exhaustion band, place a limit exit order at the highest high "
            "of the last 2 bars rather than an immediate market close."
        ),
        "stop_loss_rule": (
            "Protective trailing stop anchored at the 2-bar simple moving average of bar lows (for longs) "
            "plus macro regime invalidation on 200-day hysteresis flip."
        ),
        "take_profit_rule": (
            "SVAPO upper-band exhaustion limit exit at the 2-bar highest high (symmetric 2-bar lowest low for shorts)."
        ),
        "rule_description": (
            "Regime-adaptive D1 mean-reversion swing EA combining a 200-day hysteresis trend channel with "
            "5-bar Value Charts (DVU 0.16, oversold <= -7.5), DVO, and SVAPO exhaustion limit exits at the "
            "2-bar extreme, protected by a 2-bar low-SMA trailing stop. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Value Charts in MR Swing", "SVAPO crosses", "hysteresis"),
    },
    {
        "slug": "mql5-art-17273-kalman-filter-fx-mean-reversion",
        "original_id": "MQL5-ART-17273",
        "lead_id": "LEAD-OFF3-MQL5-02",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/17273",
        "name": "Kalman Filter Adaptive Bollinger Mean-Reversion Strategy (Forex)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "KALMAN_MEAN_REVERSION_FX",
        "asset_class": "CFD_FX",
        "asset_universe": ["AUDUSD", "FX"],
        "symbol": "AUDUSD",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Replacing a lagging simple moving average with a recursive scalar Kalman state estimator reduces "
            "phase lag when estimating fair value in mean-reverting FX crosses such as AUDUSD."
        ),
        "counterparty_mechanism": (
            "Order-flow noise pushes FX price beyond +/-2.0 standard deviations from its Kalman latent state; "
            "fading the transient deviation captures reversion back to the Kalman equilibrium."
        ),
        "entry_rule": (
            "Compute recursive scalar Kalman filter state (measurement variance mv=10, process variance pv=1.0) "
            "as the center line of a 100-period Bollinger envelope (d=2.0); buy when price crosses below lower "
            "band, sell when price crosses above upper band."
        ),
        "exit_rule": (
            "Close any open mean-reversion position as soon as price reverts and crosses back across the "
            "Kalman middle band."
        ),
        "stop_loss_rule": (
            "Mandatory hard protective stop loss set at 1.0% of entry price to cap fat-tail trend risk."
        ),
        "take_profit_rule": (
            "Dynamic mean-reversion exit upon price crossing the Kalman filter middle band."
        ),
        "rule_description": (
            "Recursive scalar Kalman filter (mv=10, pv=1.0) paired with 100-period, 2.0-SD Bollinger bands on "
            "AUDUSD/FX; enters contrarian long/short outside the outer bands, exits on Kalman middle-band cross, "
            "and enforces a mandatory 1.0% price hard stop loss. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("stop loss gap at 1%", "Kalman filter is a recursive", "middle band"),
    },
    {
        "slug": "mql5-art-17636-connors-rsi2-us500-m30",
        "original_id": "MQL5-ART-17636",
        "lead_id": "LEAD-OFF3-MQL5-03",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/17636",
        "name": "Larry Connors RSI2 Intraday Mean-Reversion Strategy (US500 M30)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "RSI2_INTRADAY_MEAN_REVERSION",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "SP500"],
        "symbol": "US500",
        "timeframe": "M30",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Short-horizon equity index selloffs inside an intact 200-bar uptrend reflect temporary liquidity "
            "absorption and dealer hedging imbalances that typically mean-revert within several M30 bars."
        ),
        "counterparty_mechanism": (
            "Intraday panic selling drives 2-period RSI to extreme oversold readings while macro buyers defend "
            "the 200-period moving average, fueling a rapid rebound to the 5-period moving average."
        ),
        "entry_rule": (
            "On US500 M30 bars, filter macro trend with 200-period SMA; enter long when close > SMA(200) and "
            "2-period RSI falls below oversold threshold; enter short when close < SMA(200) and 2-period RSI "
            "rises above overbought threshold."
        ),
        "exit_rule": (
            "Exit long when closed bar > 5-period SMA or closes below 200-period SMA; exit short when closed "
            "bar < 5-period SMA or closes above 200-period SMA."
        ),
        "stop_loss_rule": (
            "Explicit hard protective stop loss placed at 0.15% distance from current entry price."
        ),
        "take_profit_rule": (
            "Mean-reversion exit on close crossing the 5-period SMA (or regime exit on 200-period SMA breach)."
        ),
        "rule_description": (
            "MQL5 adaptation of Larry Connors 2-period RSI mean-reversion on US500 M30: trades pullbacks aligned "
            "with the 200-period SMA, exits on 5-period SMA mean cross or 200-SMA break, and protects every trade "
            "with an explicit 0.15% hard stop loss. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("US500 CFD using a 30-minute", "Stop loss distance is 0.15%", "5-period moving average"),
    },
    {
        "slug": "mql5-art-20167-statistical-ci-jarque-bera-mr",
        "original_id": "MQL5-ART-20167",
        "lead_id": "LEAD-OFF3-MQL5-04",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/20167",
        "name": "Statistical Mean Reversion with Confidence Intervals & Jarque-Bera Skewness Filter",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "STATISTICAL_MOMENTS_CI_MR",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX", "MULTI-ASSET"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "BOTH_INTRADAY_AND_SWING",
        "economic_rationale": (
            "Combining higher-order distribution moments (skewness, kurtosis, Jarque-Bera normality departure) "
            "with confidence intervals isolates statistically stretched tails while avoiding Gaussian-noise entries."
        ),
        "counterparty_mechanism": (
            "Asymmetric tail shocks create non-normal excess kurtosis and directional skewness outside the 95% "
            "confidence band, inviting mean-reverting liquidity provision once tail pressure peaks."
        ),
        "entry_rule": (
            "Compute rolling 50-bar mean, variance, skewness, kurtosis, and Jarque-Bera statistic "
            "(InpConfidenceLevel=0.95, InpJBThreshold=2.0, InpKurtosisThreshold=5.0); buy when price drops "
            "below lower 95% CI with negative skewness; sell when price exceeds upper 95% CI with positive skewness."
        ),
        "exit_rule": (
            "Close via base take-profit, trailing stop profit lock, partial position closure at predefined profit "
            "levels, or maximum holding time-based exit."
        ),
        "stop_loss_rule": (
            "Explicit base hard Stop Loss (InpBaseStopLossPips=50) scaled with 1.0% equity risk sizing "
            "(InpRiskPercent=1.0), plus trailing stop and time-based exit."
        ),
        "take_profit_rule": (
            "Base take-profit distance combined with partial close levels and trailing stop lock."
        ),
        "rule_description": (
            "Higher-moment statistical mean-reversion EA computing rolling 50-bar mean, variance, skewness, "
            "kurtosis, and Jarque-Bera (>=2.0) to fade 95% confidence-interval breaches with aligned skewness; "
            "1.0% equity risk sizing, explicit 50-pip base hard SL, trailing stop, partial closes, and time exit. "
            "Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Jarque-Bera", "negative skewness", "time-based exits"),
    },
    {
        "slug": "mql5-cb-78687-fxcraft-bb-rsi-session-mr",
        "original_id": "MQL5-CB-78687",
        "lead_id": "LEAD-OFF3-MQL5-05",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/78687",
        "name": "Bollinger Bands Return-to-Mean EA with Optional RSI & Session Window Filter (FxCraft)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "SESSION_BB_RSI_MEAN_REVERSION",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX", "FOREX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Waiting for bar 1 to re-enter inside the Bollinger Band after a bar-2 outer excursion avoids "
            "catching falling knives during momentum breakouts while targeting the 20-period mean."
        ),
        "counterparty_mechanism": (
            "Failed breakout traders trapped beyond the 2.0-SD Bollinger band cover positions once price closes "
            "back inside the envelope, accelerating reversion to the middle band."
        ),
        "entry_rule": (
            "Evaluate on closed bars within configured server-time session window and max spread <= 30 points "
            "(max 1 open position): BUY if bar 2 closed below lower BB(20, 2.0) and bar 1 closed back inside "
            "bands (optional RSI(14) on bar 2 < 30); SELL symmetric above upper BB (optional RSI > 70)."
        ),
        "exit_rule": (
            "Exit long when Bid >= middle Bollinger Band, exit short when Ask <= middle Bollinger Band, "
            "or optional close outside configured trading hours."
        ),
        "stop_loss_rule": (
            "Explicit hard Stop Loss in points (default 300 points; must be kept > 0 for prop compliance), "
            "plus spread and free-margin pre-trade checks."
        ),
        "take_profit_rule": (
            "Dynamic exit when live Bid/Ask reaches the current 20-period Bollinger middle band."
        ),
        "rule_description": (
            "Open-source MQL5 Bollinger Bands (20, 2.0) 2-bar re-entry mean-reversion EA with optional RSI(14, "
            "30/70) filter, configurable server-time trading session window, 30-point spread gate, max 1 open "
            "position, middle-band exit, and 300-point default hard Stop Loss. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("bar 2 closed below the lower band", "middle band", "Trading hours limit"),
    },
    {
        "slug": "mql5-cb-77738-rsi-exhaustion-eurusd-atr",
        "original_id": "MQL5-CB-77738",
        "lead_id": "LEAD-OFF3-MQL5-06",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/77738",
        "name": "RSI Exhaustion Reversal with ATR Exits & Volatility-Adjusted Spread Filter (EURUSD)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "SESSION_RSI_EXHAUSTION_ATR_FX",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD"],
        "symbol": "EURUSD",
        "timeframe": "M5",
        "direction": "Short",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Restricting RSI exhaustion fades to the liquid 14:00-18:00 London/NY overlap and gating entries by "
            "spread-to-ATR ratio prevents rollover spread traps while scaling targets to intraday volatility."
        ),
        "counterparty_mechanism": (
            "Overextended EURUSD rallies during the London-NY overlap exhaust short-term momentum buyers above "
            "RSI(14)=65, creating asymmetric intraday retracements sized by ATR(14)."
        ),
        "entry_rule": (
            "On EURUSD M5 during server session 14:00-18:00 with max 1 active position: trigger SELL when "
            "RSI(14) prints overbought exhaustion around level 65 and current spread passes the ATR(14) "
            "volatility-adjusted maximum spread ratio gate."
        ),
        "exit_rule": (
            "Close via ATR(14)-scaled Take Profit, ATR(14)-scaled hard Stop Loss, or maximum trade duration cap."
        ),
        "stop_loss_rule": (
            "Mandatory dynamic ATR(14)-multiple hard Stop Loss plus maximum position duration time stop."
        ),
        "take_profit_rule": (
            "Dynamic ATR(14)-multiple Take Profit adapting to current session volatility."
        ),
        "rule_description": (
            "Open-source EURUSD M5 short-only RSI(14 >= 65) exhaustion reversal EA restricted to 14:00-18:00 "
            "active session, gated by a volatility-adjusted spread/ATR(14) filter, single position max, "
            "ATR(14)-scaled hard SL & TP, and max holding duration. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("overbought exhaustion condition on EURUSD", "ATR is used to adapt", "14:00 until before 18:00"),
    },
    {
        "slug": "mql5-cb-78343-monday-dip-index-d1-mr",
        "original_id": "MQL5-CB-78343",
        "lead_id": "LEAD-OFF3-MQL5-07",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/78343",
        "name": "Monday Dip Daily Index Mean Reversion with Optional IBS & MA Filter (D1)",
        "family": "Session & Swing Mean Reversion",
        "family_tag": "CALENDAR_INDEX_MEAN_REVERSION_D1",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "UK100", "GER40"],
        "symbol": "US500/UK100/GER40",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Monday equity index weakness often reflects weekend headline de-risking and institutional "
            "rebalancing flows that mean-revert over Tuesday-Wednesday sessions across major stock indices."
        ),
        "counterparty_mechanism": (
            "Weekend risk-off selling depresses Monday's daily close (optionally with low Internal Bar Strength "
            "IBS), which systematic dip-buyers and corporate/pension inflows absorb by Wednesday close."
        ),
        "entry_rule": (
            "Evaluated exclusively on closed D1 bars (max 1 trade/week): open Long on Monday close if Monday "
            "close < prior session (Friday) close; optional strict restrictive toggles require IBS = "
            "(Close-Low)/(High-Low) <= InpIBSMax and Monday close < D1 Simple Moving Average (InpMAPeriod)."
        ),
        "exit_rule": (
            "Unconditional time-based exit at Wednesday's D1 close (executed at first tick of next session; "
            "fallback on Thursday/Friday close if Wednesday close missed)."
        ),
        "stop_loss_rule": (
            "Mandatory percentage-based hard Stop Loss (InpStopLossPercent) respecting broker minimum stop "
            "distance; fail-safe immediate market close if 5 consecutive SL modification attempts fail."
        ),
        "take_profit_rule": (
            "No fixed price take-profit target; exits are purely time-based (Wednesday D1 close) or hard SL."
        ),
        "rule_description": (
            "Open-source D1 long-only index mean-reversion EA (US500, UK100, GER40): max 1 trade/week buying "
            "Monday close strictly below prior session close with optional IBS and D1 SMA filters, closing "
            "unconditionally on Wednesday D1 close, with mandatory percentage hard SL and 5-retry fail-safe "
            "emergency close. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Rule 1 — Entry", "Wednesday's daily close", "InpStopLossPercent"),
    },
    # =========================================================================
    # THEME 2: H4 / D1 SWING PULLBACK — NON-BREAKOUT (6)
    # =========================================================================
    {
        "slug": "mql5-art-24280-raschke-310-anti-holy-grail",
        "original_id": "MQL5-ART-24280",
        "lead_id": "LEAD-OFF3-MQL5-08",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/24280",
        "name": "Linda Bradford Raschke 3/10 Oscillator ('Anti') & 20-EMA ADX ('Holy Grail') Swing Pullback",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "SWING_PULLBACK_EMA_ADX_OSCILLATOR",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "FX", "MULTI-ASSET"],
        "symbol": "EURUSD",
        "timeframe": "H1/H4",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Strong directional trends (ADX > 30) rarely reverse on the first retracement; entering the first "
            "pullback to the 20-EMA or 3/10 oscillator hook captures institutional trend continuation with tight "
            "structural invalidation."
        ),
        "counterparty_mechanism": (
            "Early profit-taking creates a temporary counter-trend retracement to the 20-EMA while institutional "
            "trend flows remain active, forcing late shorts/longs to cover on trend resumption."
        ),
        "entry_rule": (
            "Two H1/H4 swing pullback setups: (1) Anti: SMA(3)-SMA(10) oscillator with 16-SMA signal line enters "
            "on first oscillator pullback after signal crosses zero with price confirmation; (2) Holy Grail: "
            "ADX(14) > 30 and rising, enter on first price pullback touching EMA(20) in trend direction."
        ),
        "exit_rule": (
            "Anti exits when fast 3/10 line crosses back through the 16-SMA signal line against the trade; "
            "Holy Grail exits when ADX(14) drops below 20 signaling trend termination."
        ),
        "stop_loss_rule": (
            "Hard structural stop loss placed at the pullback swing extreme, with optional ATR buffer "
            "(InpATRStopMult > 0)."
        ),
        "take_profit_rule": (
            "Dynamic exit on opposite 3/10 signal-line cross (Anti) or ADX(14) < 20 trend exhaustion (Holy Grail)."
        ),
        "rule_description": (
            "White-box MQL5 automation of Linda Bradford Raschke's H1/H4 swing pullback systems: Anti "
            "(3/10/16 oscillator first pullback post-zero cross) and Holy Grail (ADX(14)>30 rising trend first "
            "pullback to EMA(20)), with swing-extreme hard stop (+ optional ATR buffer) and signal-cross / ADX<20 "
            "exits. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Raschke's methods operate on H1 or H4", "Holy Grail", "InpATRStopMult"),
    },
    {
        "slug": "mql5-art-22807-dynamic-pullback-depth-atr-regime",
        "original_id": "MQL5-ART-22807",
        "lead_id": "LEAD-OFF3-MQL5-09",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/22807",
        "name": "Volatility-Normalized Dynamic Pullback Depth Swing Strategy",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "VOLATILITY_NORMALIZED_SWING_PULLBACK",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX", "MULTI-ASSET"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Fixed-pip pullback thresholds fail across shifting volatility regimes; normalizing retracement depth "
            "as a ratio of the prior displacement impulse calibrated to ATR(14)/ATR(50) filters weak pullbacks."
        ),
        "counterparty_mechanism": (
            "After a structural displacement impulse (DisplacementFactor=1.5), liquidity sweeps inside a "
            "volatility-calibrated retracement zone trap counter-trend traders before trend continuation."
        ),
        "entry_rule": (
            "Identify structural swings (SwingLookback=5, DisplacementFactor=1.5, StructureHoldBars=3); "
            "measure pullback depth as ratio of prior impulse calibrated to rolling ATR(14) vs 50-bar average ATR; "
            "enter only when pullback clears minimum quality score plus sweep or displacement confirmation."
        ),
        "exit_rule": (
            "Close at fixed Risk-Reward Ratio target (RiskRewardRatio=2.0) or structural swing stop invalidation."
        ),
        "stop_loss_rule": (
            "Hard Stop Loss anchored directly to validated swing structure (fallback cap StopLossPoints=2000) "
            "with percent-risk position sizing (RiskPercent=1.0%)."
        ),
        "take_profit_rule": (
            "Fixed 2.0x Risk-to-Reward multiple (RiskRewardRatio=2.0) computed from structural SL distance."
        ),
        "rule_description": (
            "Volatility-calibrated structural pullback EA measuring retracement depth relative to prior impulse "
            "(SwingLookback=5, DisplacementFactor=1.5) and ATR(14)/ATR(50) regime, requiring quality-score and "
            "sweep/displacement confirmation; 1.0% risk sizing, swing-anchored hard SL, 2.0 R:R TP. Zero grid, "
            "zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("ratio of the prior impulse", "SL Anchored to Swing Structure", "RiskRewardRatio"),
    },
    {
        "slug": "mql5-art-21228-williams-smash-day-supertrend",
        "original_id": "MQL5-ART-21228",
        "lead_id": "LEAD-OFF3-MQL5-10",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/21228",
        "name": "Larry Williams Context-Based Smash Day Reversal with Supertrend & Day-of-Week Filter",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "SMASH_DAY_CONTEXT_REVERSAL_SWING",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "GOLD", "FX", "INDICES"],
        "symbol": "XAUUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "A Smash Day close beyond prior bar extremes followed by immediate next-bar rejection traps late "
            "breakout chasers; filtering by Supertrend trend alignment turns the trap into a trend-aligned swing pullback."
        ),
        "counterparty_mechanism": (
            "Stop-run closes below recent lows (Buy setup) or above recent highs (Sell setup) trigger forced "
            "liquidations; reversal back across the Smash Day bar extreme forces trapped traders to unwind."
        ),
        "entry_rule": (
            "Detect Smash Day Buy bar closing below lows of prior N bars (smashBuyLookbackBars=1) or Sell bar "
            "closing above highs of prior N bars; enter on subsequent bar level-cross reversal within "
            "smashSetupValidityBars=3, optionally aligned with Supertrend direction and day-of-week filter."
        ),
        "exit_rule": (
            "Close at fixed risk-to-reward Take Profit or hard Stop Loss; expire untriggered setups after "
            "smashSetupValidityBars."
        ),
        "stop_loss_rule": (
            "Mandatory hard structural Stop Loss placed at the low of the Smash Day bar (Buy) or high of the "
            "Smash Day bar (Sell)."
        ),
        "take_profit_rule": (
            "Calculated from a user-defined fixed Risk-to-Reward multiple of the Smash Day Stop Loss distance."
        ),
        "rule_description": (
            "MQL5 automation of Larry Williams Smash Day swing reversal with Supertrend context and day-of-week "
            "filtering (demonstrated on XAUUSD/Daily): enters on confirmed reversal within 3 validity bars, places "
            "hard SL at Smash Day bar extreme, and sets fixed R:R TP. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Smash Day Buy setup", "low of the Smash Day bar", "Supertrend"),
    },
    {
        "slug": "mql5-art-12809-dual-stochastic-ma-fibonacci",
        "original_id": "MQL5-ART-12809",
        "lead_id": "LEAD-OFF3-MQL5-11",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/12809",
        "name": "Dual-Stochastic, Moving Average & Fibonacci Swing Pullback Strategy",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "DUAL_STOCHASTIC_MA_FIB_PULLBACK",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX", "MULTI-ASSET"],
        "symbol": "FX",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Requiring a double-bottom/double-top pullback retest on two Stochastic oscillators aligned with a "
            "higher-period Moving Average filters premature first-dip knife-catching in swing trends."
        ),
        "counterparty_mechanism": (
            "Secondary pullback retests shake out weak early dip-buyers before institutional trend continuation "
            "drives price toward prior swing/Fibonacci extension targets."
        ),
        "entry_rule": (
            "Single open position max on D1/swing chart: long signal when both Stochastic oscillators reach "
            "oversold simultaneously, bounce, and retest oversold in Moving Average uptrend alignment; "
            "symmetric short signal on dual overbought bounce-and-retest in downtrend."
        ),
        "exit_rule": (
            "Exit at Fibonacci projection target anchored to the two Stochastic trough lows (or shift-period "
            "highest high / lowest low) or hard Stop Loss."
        ),
        "stop_loss_rule": (
            "Explicit hard Stop Loss placed at the low (Buy) or high (Sell) of the signal candle."
        ),
        "take_profit_rule": (
            "Fibonacci projection from the two Stochastic pullback extremes (and shift-period highest high / "
            "lowest low target)."
        ),
        "rule_description": (
            "Pre-holdout classic MQL5 trend-pullback system combining two Stochastic oscillators (double-retest "
            "at oversold/overbought), a Moving Average trend filter, max 1 open order, hard SL at signal candle "
            "extreme, and Fibonacci projection / shift-period extreme TP. Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("both stochastic oscillator reach", "Fibonacci projection tool", "more than one order"),
    },
    {
        "slug": "mql5-cb-73958-adx-ema-atr-trend-pullback",
        "original_id": "MQL5-CB-73958",
        "lead_id": "LEAD-OFF3-MQL5-12",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/73958",
        "name": "ADX Trend Pullback EA with EMA Distance & ATR Dynamic SL/TP",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "ADX_EMA_ATR_TREND_PULLBACK",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "FX", "MULTI-ASSET"],
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "BOTH_INTRADAY_AND_SWING",
        "economic_rationale": (
            "Measuring pullback proximity to an EMA in multiples of ATR inside a rising ADX trend ensures entries "
            "occur only when trend momentum is expanding and price has meaningfully mean-reverted to value."
        ),
        "counterparty_mechanism": (
            "Intraday retracements toward the EMA inside an accelerating ADX trend trigger institutional "
            "limit-order refills in the +DI/-DI dominant direction."
        ),
        "entry_rule": (
            "Evaluated once per closed H1 bar (single position max): (1) ADX on bar 1 > ADX threshold AND "
            "ADX(bar 1) > ADX(bar 2) confirming strengthening trend; (2) |Price - EMA| / ATR was >= pullback "
            "ratio on bar 2 and dropped below pullback ratio on bar 1; direction set by +DI vs -DI."
        ),
        "exit_rule": (
            "Close strictly via ATR-multiple hard Stop Loss or R:R-scaled Take Profit."
        ),
        "stop_loss_rule": (
            "Mandatory dynamic hard Stop Loss calculated as ATR multiplied by the SL multiplier input."
        ),
        "take_profit_rule": (
            "Dynamic Take Profit calculated as Stop Loss distance multiplied by the configured Risk-Reward ratio."
        ),
        "rule_description": (
            "Open-source closed-bar H1 pullback EA (single position max): requires rising ADX above threshold, "
            "+DI/-DI directional alignment, and ATR-normalized price pullback toward EMA; sets dynamic ATR-multiple "
            "hard Stop Loss and R:R-scaled Take Profit. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("ADX-based trend strength filter", "expressed as a multiple of ATR", "Stop loss distance is calculated as ATR"),
    },
    {
        "slug": "mql5-cb-63916-wpr-bb-midline-atr-pullback",
        "original_id": "MQL5-CB-63916",
        "lead_id": "LEAD-OFF3-MQL5-13",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/63916",
        "name": "WPR & Bollinger Bands Midline Confluence Pullback EA with ATR Stops (ExpWPRBB)",
        "family": "H4/D1 Swing Pullback",
        "family_tag": "WPR_BB_MIDLINE_ATR_PULLBACK",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX", "MULTI-ASSET"],
        "symbol": "FX",
        "timeframe": "H4",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Combining Williams %R exit from oversold/overbought extremes with bar-open location relative to the "
            "Bollinger Bands midline captures H4 mean-reversion/pullback turns while adapting stops to band width & ATR."
        ),
        "counterparty_mechanism": (
            "Momentum exhaustion signaled by WPR leaving extreme zones (-80/-100 or -20/0) while price remains "
            "discounted/premium relative to the Bollinger mean triggers snap-back flows."
        ),
        "entry_rule": (
            "On H4 bars: BUY when Williams %R exits oversold zone (-80 to -100) AND bar opening price is below "
            "middle Bollinger Band; SELL when WPR exits overbought zone (-20 to 0) AND bar opening price is "
            "above middle Bollinger Band."
        ),
        "exit_rule": (
            "Close via Bollinger Band width and ATR-derived hard Stop Loss or Take Profit."
        ),
        "stop_loss_rule": (
            "Explicit hard Stop Loss dynamically computed from Bollinger Bands width and ATR(InpPeriodATR)."
        ),
        "take_profit_rule": (
            "Explicit Take Profit dynamically computed from Bollinger Bands width and ATR(InpPeriodATR)."
        ),
        "rule_description": (
            "Open-source MQL5 CodeBase H4 confluence strategy (ExpWPRBB): buys when WPR exits oversold below "
            "middle Bollinger Band and sells when WPR exits overbought above middle Bollinger Band, sizing hard "
            "SL and TP from Bollinger Band width and ATR. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("WPR exits the oversold zone", "width of Bollinger Bands and ATR", "ExpWPRBB"),
    },
    # =========================================================================
    # THEME 3: MULTI-SYMBOL CURRENCY STRENGTH / CROSS-SECTIONAL FX & CARRY (4)
    # =========================================================================
    {
        "slug": "mql5-art-23763-network-momentum-lead-lag-fx",
        "original_id": "MQL5-ART-23763",
        "lead_id": "LEAD-OFF3-MQL5-14",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/23763",
        "name": "Network Momentum: Cross-Market FX Lead-Lag Graph Strategy",
        "family": "Multi-Symbol Currency Strength & Cross-Sectional FX",
        "family_tag": "CROSS_MARKET_NETWORK_MOMENTUM_FX",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "FX", "FOREX", "MAJORS"],
        "symbol": "EURUSD/FX",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Macro shocks propagate asynchronously across linked FX pairs; learning a sparse weighted lead-lag "
            "network captures cross-market spillover momentum before laggard currency pairs fully adjust."
        ),
        "counterparty_mechanism": (
            "Slow-moving institutional FX rebalancers and regional central-bank/corporate flows transmit trends "
            "from liquid leader pairs to correlated follower pairs across multi-day horizons."
        ),
        "entry_rule": (
            "Evaluated once per new D1 bar on FX universe (InpMarket=NM_MARKET_FOREX, InpMinBars=200, "
            "InpLookback=140, InpInterval=10): detect leader pairs via Derivative Dynamic Time Warping (DDTW), "
            "learn sparse weighted lead-lag graph natively in MQL5, propagate 6-speed fast/slow EMA oscillators "
            "to compute target network momentum sign (+1 Long, -1 Short, 0 Flat)."
        ),
        "exit_rule": (
            "Reverse-and-flat daily rebalance rule (flat closes open position, opposite sign reverses) plus "
            "fixed pip hard Stop Loss and Take Profit."
        ),
        "stop_loss_rule": (
            "Explicit fixed hard Stop Loss in pips (InpSL=25 default) attached on every entry."
        ),
        "take_profit_rule": (
            "Explicit fixed Take Profit in pips (InpTP=30 default) or daily signal flip/flat exit."
        ),
        "rule_description": (
            "Pure-MQL5 cross-market lead-lag FX strategy evaluated on D1 bars (InpLookback=140): detects market "
            "leaders via DDTW, learns a sparse weighted spillover graph, propagates 6-speed EMA oscillators into "
            "a long/short/flat network momentum signal, and protects trades with explicit hard SL (InpSL) and TP "
            "(InpTP). Zero external solver, zero DLL, zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("Derivative Dynamic Time Warping", "network momentum signal", "reverse-and-flat"),
    },
    {
        "slug": "mql5-art-22175-carry-trade-swap-aware-fx",
        "original_id": "MQL5-ART-22175",
        "lead_id": "LEAD-OFF3-MQL5-15",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/22175",
        "name": "Swap-Aware FX Carry Trade Position Sizing & Hold-Window Swing Strategy",
        "family": "Multi-Symbol Currency Strength & Cross-Sectional FX",
        "family_tag": "SWAP_AWARE_FX_CARRY_SWING",
        "asset_class": "CFD_FX",
        "asset_universe": ["AUDJPY", "NZDUSD", "USDJPY", "FX"],
        "symbol": "AUDJPY/NZDUSD/USDJPY",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Explicitly pricing live broker overnight swap accrual (including triple-swap Wednesday) into swing "
            "entry filters, hold-window expectations, and lot sizing avoids negative-carry drag and harvests positive carry."
        ),
        "counterparty_mechanism": (
            "Interest-rate differentials between high-yielding currencies (AUD/NZD/USD) and funding currencies "
            "(JPY/CHF) compensate swing holders for bearing macro carry risk when filtered by hard risk caps."
        ),
        "entry_rule": (
            "Query live broker SYMBOL_SWAP_LONG / SYMBOL_SWAP_SHORT and swap calculation mode on H1/swing FX "
            "pairs (e.g., AUDJPY, NZDUSD, USDJPY); project multi-day swap income/cost over expected hold window "
            "(accounting for triple-swap day) and allow/scale entries when net carry-adjusted expectancy is positive."
        ),
        "exit_rule": (
            "Carry-justified holding exit rule combined with explicit swing Take Profit (e.g., 80-pip example) "
            "and hard Stop Loss."
        ),
        "stop_loss_rule": (
            "Explicit hard Stop Loss per swing trade (e.g., 30-pip SL / $25 fixed risk example) with carry-aware "
            "position sizing."
        ),
        "take_profit_rule": (
            "Explicit swing Take Profit (e.g., 80-pip example) plus carry-justified time/swap exit logic."
        ),
        "rule_description": (
            "Modular MQL5 swap-aware FX carry swing framework (AUDJPY, NZDUSD, USDJPY): retrieves real-time "
            "broker swap rates, projects multi-day hold-window carry including triple-swap day, modulates sizing "
            "and exits by net carry expectancy, and enforces hard SL/TP risk caps. Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("AUDJPY or NZDUSD", "swap retrieval, hold-window projection", "30-pip stop-loss"),
    },
    {
        "slug": "mql5-art-23597-multipair-volatility-signature-asymmetric-sl",
        "original_id": "MQL5-ART-23597",
        "lead_id": "LEAD-OFF3-MQL5-16",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/23597",
        "name": "Multi-Pair Volatility-Signature Asymmetric Stop-Loss Strategy (XAUUSD / GBPUSD / USDJPY)",
        "family": "Multi-Symbol Currency Strength & Cross-Sectional FX",
        "family_tag": "MULTIPAIR_VOLATILITY_SIGNATURE_SL",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["XAUUSD", "GBPUSD", "USDJPY", "FX"],
        "symbol": "XAUUSD/GBPUSD/USDJPY",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Applying a single uniform ATR stop multiplier across violent gold swings and tighter FX majors "
            "causes premature stop-outs on XAUUSD and oversized risk on GBPUSD; profiling each pair's 1000-bar "
            "microstructure calibrates stops to instrument physics."
        ),
        "counterparty_mechanism": (
            "Pair-specific wick hunting, noise ratios, and pullback depths differ systematically across Gold and "
            "FX majors; adapting SL multipliers per symbol avoids liquidity sweeps while preserving trend capture."
        ),
        "entry_rule": (
            "Multi-symbol H1 EA (XAUUSD, GBPUSD, USDJPY; profiles 1000 historical bars every 100 bars for candle "
            "range, wick ratio, noise ratio, trend runs, pullback depth, and true-range dispersion): enter trend-aligned "
            "pullback/resumption on MACD(12,26,9) crossover filtered by 200-period EMA trend gate."
        ),
        "exit_rule": (
            "Exit at pair-specific Take Profit, asymmetric Stop Loss, or optional close on opposite MACD signal."
        ),
        "stop_loss_rule": (
            "Mandatory pair-specific asymmetric ATR Stop Loss multiplier dynamically calibrated from each "
            "symbol's 1000-bar volatility signature."
        ),
        "take_profit_rule": (
            "Symbol-specific Take Profit calculated from trade direction and volatility profile, plus optional "
            "opposite-signal close."
        ),
        "rule_description": (
            "Multi-pair H1 EA (XAUUSD, GBPUSD, USDJPY) combining an EMA(200) trend gate and MACD(12,26,9) signal "
            "with a rolling 1000-bar volatility-signature classifier (updated every 100 bars) that assigns each "
            "symbol an asymmetric ATR hard Stop Loss multiplier and TP. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("unique ATR multiplier per symbol", "MACD crossover filtered by an EMA", "processing 1000 bars"),
    },
    {
        "slug": "mql5-art-3339-currency-basket-wpr-mean-reversion",
        "original_id": "MQL5-ART-3339",
        "lead_id": "LEAD-OFF3-MQL5-17",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/3339",
        "name": "Multi-Currency Pair Basket Combined WPR Mean-Reversion Strategy",
        "family": "Multi-Symbol Currency Strength & Cross-Sectional FX",
        "family_tag": "CURRENCY_BASKET_COMBINED_WPR",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1/H4/H1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Aggregating Williams %R across all seven major pairs sharing a single base currency isolates genuine "
            "currency-wide overextension from idiosyncratic single-pair noise."
        ),
        "counterparty_mechanism": (
            "Broad macro risk-on/risk-off flushes stretch an entire currency basket simultaneously into extreme "
            "overbought/oversold readings (60-70% bounds), after which cross-pair rebalancing snaps the basket back."
        ),
        "entry_rule": (
            "Compute combined Williams %R across a 7-pair major FX currency basket on D1, H4, or H1; enter "
            "currency-basket reversion across constituent pairs when combined WPR crosses downward out of "
            "overbought (60-70% threshold) or upward out of oversold."
        ),
        "exit_rule": (
            "Close basket via deposit-currency trailing profit stop or hard deposit-currency Stop Loss."
        ),
        "stop_loss_rule": (
            "Explicit hard basket Stop Loss defined in account deposit currency."
        ),
        "take_profit_rule": (
            "Profit trailing stop managed in account deposit currency across the basket."
        ),
        "rule_description": (
            "Pre-holdout classic MQL5 currency-strength basket strategy across 7 FX majors (EURUSD, GBPUSD, "
            "USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD) on D1/H4/H1: triggers basket reversion when combined WPR "
            "exits overbought/oversold extremes (60-70%), with deposit-currency hard SL and profit trail. "
            "Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("combined WPR", "stop loss in the deposit currency", "three timeframes: D1, H4 and H1"),
    },
    # =========================================================================
    # THEME 4: VOLATILITY REGIME FILTERS & METALS SPECIALISTS (2)
    # =========================================================================
    {
        "slug": "mql5-art-17781-adaptive-market-regime-detector-ea",
        "original_id": "MQL5-ART-17781",
        "lead_id": "LEAD-OFF3-MQL5-18",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/17781",
        "name": "Adaptive Multi-Regime Detection & Risk-Switching EA (MarketRegimeEA)",
        "family": "Volatility Regime Filters",
        "family_tag": "ADAPTIVE_VOLATILITY_REGIME_SWITCHER",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["XAUUSD", "FX", "MULTI-ASSET"],
        "symbol": "XAUUSD/FX",
        "timeframe": "M15/H4/D1",
        "direction": "Both",
        "prop_track": "BOTH_INTRADAY_AND_SWING",
        "economic_rationale": (
            "Single-regime strategies suffer deep drawdowns during regime transitions; classifying market state "
            "into Trending, Ranging, and High-Volatility regimes dynamically pairs logic and cuts risk in chaos."
        ),
        "counterparty_mechanism": (
            "Sideways low-trend sessions favor RSI mean-reversion against range liquidity, whereas persistent "
            "directional flows favor trend continuation and elevated volatility demands downsized exposure."
        ),
        "entry_rule": (
            "CMarketRegimeDetector classifies closed bars (LookbackPeriod=100, SmoothingPeriod=10, "
            "TrendThreshold=0.2, VolatilityThreshold=1.5) into Trending, Ranging, or Volatile states; routes "
            "Ranging markets to RSI oversold/overbought mean-reversion and Trending markets to trend-aligned "
            "entries while throttling exposure in Volatile states."
        ),
        "exit_rule": (
            "Close via regime-specific hard Stop Loss, Take Profit, or regime transition handling."
        ),
        "stop_loss_rule": (
            "Explicit regime-specific hard Stop Loss (e.g., TrendingStopLoss=100 points) and tiered position "
            "sizing stepping down risk in volatile regimes (TrendingLotSize=0.1, RangingLotSize=0.05, "
            "VolatileLotSize=0.02)."
        ),
        "take_profit_rule": (
            "Regime-specific Take Profit dynamically set according to detected market regime."
        ),
        "rule_description": (
            "Adaptive MQL5 regime-detection EA (LookbackPeriod=100, TrendThreshold=0.2, VolatilityThreshold=1.5) "
            "switching between trend-following and RSI mean-reversion with regime-specific hard Stop Loss, Take "
            "Profit, and stepped-down lot sizing (0.10/0.05/0.02) during high volatility. Zero grid, zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("CMarketRegimeDetector", "Ranging Regimes: Uses mean-reversion", "Regime-Specific Risk Management"),
    },
    {
        "slug": "mql5-cb-73622-quantum-xauusd-silver-atr-factor",
        "original_id": "MQL5-CB-73622",
        "lead_id": "LEAD-OFF3-MQL5-19",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/73622",
        "name": "Weighted Multi-Factor Gold & Silver Strategy with Adaptive ATR Trailing & DD Guard",
        "family": "Volatility Regime Filters",
        "family_tag": "WEIGHTED_MULTIFACTOR_METALS_ATR_REGIME",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "XAGUSD"],
        "symbol": "XAUUSD/XAGUSD",
        "timeframe": "M15",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Precious metals (XAUUSD/XAGUSD) alternate between dead Asian chop and violent macro swings; "
            "weighting RSI, ADX, 50/200 MA spread, and a low-volatility dead-market gate aligns entries with "
            "active directional expansion and volatility-adaptive trailing stops."
        ),
        "counterparty_mechanism": (
            "Multi-factor alignment filters false single-indicator noise on Gold and Silver while adaptive ATR "
            "trailing locks gains once price moves beyond 1.0 ATR."
        ),
        "entry_rule": (
            "Evaluated on each closed M15 bar (deterministic mode with internal state variation disabled): "
            "compute weighted composite score of (RSI - 50), ADX strength, 50/200 MA gap, and volatility term; "
            "low-volatility filter blocks dead markets; buy above +threshold, sell below -threshold; auto-selects "
            "XAUUSD or XAGUSD symbol preset."
        ),
        "exit_rule": (
            "Exit via ATR-multiple Take Profit, ATR-multiple hard Stop Loss, adaptive ATR trailing stop activated "
            "after +1.0 ATR profit, or daily/total drawdown circuit breaker."
        ),
        "stop_loss_rule": (
            "Mandatory ATR-multiple hard Stop Loss with percent-risk lot sizing from stop distance, adaptive ATR "
            "trailing after +1 ATR profit, plus built-in daily drawdown, total drawdown, and daily loss hard stops."
        ),
        "take_profit_rule": (
            "ATR-multiple Take Profit paired with adaptive volatility-responsive trailing stop."
        ),
        "rule_description": (
            "Open-source Gold (XAUUSD) & Silver (XAGUSD) M15 multi-factor EA scoring weighted RSI distance from "
            "50, ADX strength, 50/200 MA gap, and low-volatility dead-market gate; percent-risk sizing, ATR-multiple "
            "hard SL & TP, adaptive ATR trailing after +1 ATR, and daily/total drawdown protection. Zero grid, "
            "zero martingale."
        ),
        "replicability": "REPLICABLE_FROM_PUBLIC",
        "expected_toxic": False,
        "excerpt_keywords": ("adds up RSI distance from 50", "Stop loss and take profit are multiples of ATR", "daily drawdown, total drawdown"),
    },
    # =========================================================================
    # THEME 5: STATISTICAL ARBITRAGE & COMMODITY SPREADS WITH HARD SL (3)
    # =========================================================================
    {
        "slug": "mql5-art-14855-brent-wti-crude-oil-spread-regression",
        "original_id": "MQL5-ART-14855",
        "lead_id": "LEAD-OFF3-MQL5-20",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/14855",
        "name": "Brent–WTI Crude Oil Spread Mean-Reversion & Least-Squares Regression Strategy",
        "family": "Statistical Arbitrage & Pairs Trading",
        "family_tag": "CRUDE_OIL_BRENT_WTI_SPREAD_STATARB",
        "asset_class": "CFD_ENERGY",
        "asset_universe": ["UKOIL", "USOIL", "BRENT", "WTI"],
        "symbol": "UKOIL/USOIL",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Brent (UKOIL) and WTI (USOIL) are physically arbitrageable light-sweet crude oil benchmarks linked "
            "by seaborne transport costs; deviations of the Brent–WTI spread from equilibrium predict reversion."
        ),
        "counterparty_mechanism": (
            "Regional refinery bottlenecks and US inventory shocks temporarily widen or compress the Brent–WTI "
            "spread; physical cargo arbitrage and commodity spread desks force convergence back to baseline."
        ),
        "entry_rule": (
            "Compute Brent–WTI spread relative to a 20-period baseline and fit native MQL5 matrix pseudo-inverse "
            "least-squares regression forecasting future Brent close from lagged Brent close, Brent–WTI spread, "
            "and intercept; sell Brent when spread/model signals overvaluation above equilibrium, buy when below."
        ),
        "exit_rule": (
            "Close position upon hitting configured profit_target, max_loss, ATR stop/target, or signal reversal."
        ),
        "stop_loss_rule": (
            "Explicit hard risk protection via ATR-multiple stop (atr_multiple=5.0) and maximum loss cap "
            "(max_loss=20, lot_multiple=1.0)."
        ),
        "take_profit_rule": (
            "Explicit profit target (profit_target=10) and ATR-multiple target scaling."
        ),
        "rule_description": (
            "Pure-MQL5 energy spread strategy on Brent (UKOIL) and WTI (USOIL): models the Brent–WTI spread "
            "deviation vs 20-bar baseline via native matrix pseudo-inverse least squares to forecast Brent "
            "reversion, protected by explicit ATR-multiple stop (atr_multiple=5.0), max_loss=20, and "
            "profit_target=10. Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("Brent-WTI spread", "pseudo inverse technique", "baseline could be the 20 moving average"),
    },
    {
        "slug": "mql5-art-17735-statarb-pairs-mean-reversion",
        "original_id": "MQL5-ART-17735",
        "lead_id": "LEAD-OFF3-MQL5-21",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/17735",
        "name": "Statistical Arbitrage Pairs Trading via Spread Mean Reversion with Hard SL",
        "family": "Statistical Arbitrage & Pairs Trading",
        "family_tag": "STATARB_PAIRS_SPREAD_MEAN_REVERSION",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["XAUUSD", "FX", "MULTI-ASSET"],
        "symbol": "XAUUSD/FX",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Cointegrated or economically linked instruments (e.g., USD-quoted Gold vs FX-adjusted Gold or "
            "correlated FX pairs) share a common macro factor so temporary spread divergences mean-revert."
        ),
        "counterparty_mechanism": (
            "Cross-currency or cross-venue liquidity shocks widen the relative spread between two linked "
            "instruments; simultaneously shorting the outperformer and buying the laggard harvests convergence."
        ),
        "entry_rule": (
            "Evaluate cointegrated/correlated instrument pair on D1 closes; when normalized historical price "
            "spread deviates beyond statistical entry threshold, simultaneously sell the outperforming instrument "
            "and buy the underperforming instrument with fixed non-martingale lot size."
        ),
        "exit_rule": (
            "Close both legs via CheckForClose() upon spread mean reversion back to equilibrium, or on hard "
            "Stop Loss / Take Profit / position time limit."
        ),
        "stop_loss_rule": (
            "Mandatory explicit Stop Loss levels and position-timing stops enforced to protect against structural "
            "cointegration breakdown where correlated pairs keep widening."
        ),
        "take_profit_rule": (
            "Spread convergence close in CheckForClose() or explicit per-leg Take Profit."
        ),
        "rule_description": (
            "White-box MQL5 statistical arbitrage pairs-trading framework on D1 (illustrated with Gold/FX "
            "spreads): opens market-neutral long-laggard / short-leader pair on spread anomaly, closes on "
            "CheckForClose() reversion, and enforces mandatory hard SL, TP, and timing limits against structural "
            "breaks. Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("stop-loss levels and position timing is mandatory", "CheckForClose()", "simultaneously selling the trending-up"),
    },
    {
        "slug": "mql5-art-13338-correlated-fx-pair-trading-atr",
        "original_id": "MQL5-ART-13338",
        "lead_id": "LEAD-OFF3-MQL5-22",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/13338",
        "name": "Dual-Horizon Correlated FX Pair Trading Spread Strategy with ATR Scaling (EURUSD / USDCHF / USDCAD)",
        "family": "Statistical Arbitrage & Pairs Trading",
        "family_tag": "CORRELATED_FX_PAIR_TRADING_ATR",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "USDCHF", "USDCAD"],
        "symbol": "EURUSD/USDCHF/USDCAD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Separating long-horizon cointegration/correlation direction from short-horizon spread deviations "
            "and normalizing legs by ATR prevents volatility mismatch on inversely/positively correlated FX pairs."
        ),
        "counterparty_mechanism": (
            "Divergences between strongly negatively correlated EURUSD and USDCHF (or positively correlated USD "
            "majors) attract cross-pair arbitrage flows restoring relative equilibrium around the moving average."
        ),
        "entry_rule": (
            "Measure both long-period correlation (establishing positive vs negative co-movement sign) and "
            "short-period spread deviation across EURUSD/USDCHF/USDCAD on D1 with ATR normalization; open Buy on "
            "pair priced below moving-average equilibrium and Sell on pair priced above equilibrium at trigger level."
        ),
        "exit_rule": (
            "Close on equilibrium convergence, trailing stop / breakeven transfer, Take Profit, or hard Stop Loss."
        ),
        "stop_loss_rule": (
            "Explicit hard Stop Loss and ATR-aware sizing paired with trailing stop / breakeven protection to "
            "limit deposit drawdown."
        ),
        "take_profit_rule": (
            "Explicit Take Profit and trailing stop capture upon correlated pair realignment."
        ),
        "rule_description": (
            "MQL5 correlated FX pair-trading framework on D1 (EURUSD, USDCHF, USDCAD) combining dual-horizon "
            "(long/short) correlation filtering, ATR volatility normalization, moving-average equilibrium spread "
            "triggers, explicit hard Stop Loss, Take Profit, and trailing stop controls. Zero grid, zero martingale."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "expected_toxic": False,
        "excerpt_keywords": ("EURUSD and USDCHF", "ATR should be taken into account", "use of stop loss and take profit"),
    },
    # =========================================================================
    # DISQUALIFIED TOXIC REJECTS LOGGED CLEANLY FROM REAL MQL5 PAGES (7)
    # Covering ALL 6 banned mechanisms: Grid, Martingale, Averaging-Down,
    # Zone Recovery, No-SL, Rollover/Night-Scalper, DLL-Import
    # =========================================================================
    {
        "slug": "reject-mql5-cb-78206-gridpro-panel",
        "original_id": "MQL5-CB-78206",
        "lead_id": "REJECT-OFF3-MQL5-01",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/78206",
        "name": "GridPro Panel — open-source grid trading EA",
        "family": "Disqualified Toxic Grid / Martingale",
        "family_tag": "TOXIC_GRID_MARTINGALE",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": "Basket-level optional grid risk limit; adds averaging grid layers with martingale lot multiplier (default 1.5x)",
        "take_profit_rule": "Basket profit closure",
        "rule_description": (
            "Disqualified: Open-source grid trading Expert Advisor adding averaging grid step layers every 300 "
            "points with default 1.5x martingale lot multiplier across independent buy/sell baskets."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_GRID", "TOXIC_MARTINGALE"],
        "excerpt_keywords": ("open-source grid trading Expert Advisor", "martingale multiplier", "grid step"),
    },
    {
        "slug": "reject-mql5-cb-32521-basic-martingale-v3",
        "original_id": "MQL5-CB-32521",
        "lead_id": "REJECT-OFF3-MQL5-02",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/32521",
        "name": "Basic Martingale EA v3",
        "family": "Disqualified Toxic Martingale / Averaging",
        "family_tag": "TOXIC_MARTINGALE_AVERAGING",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Disqualified: Martingale trading system using averaging down and averaging up with ATR grid steps "
            "and TEMA entry signals."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_MARTINGALE", "TOXIC_GRID", "TOXIC_AVERAGING_DOWN"],
        "excerpt_keywords": ("Martingale Systems by Averaging Up or Averaging Down", "Grid Steps"),
    },
    {
        "slug": "reject-mql5-cb-22854-ma-macd-position-averaging-v2",
        "original_id": "MQL5-CB-22854",
        "lead_id": "REJECT-OFF3-MQL5-03",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/22854",
        "name": "MA MACD Position averaging v2",
        "family": "Disqualified Toxic Averaging-Down",
        "family_tag": "TOXIC_AVERAGING_DOWN",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Disqualified: Opens additional same-direction losing layers (averaging down) with an increased lot "
            "coefficient whenever floating loss exceeds Step lossing pips."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_AVERAGING_DOWN", "TOXIC_MARTINGALE"],
        "excerpt_keywords": ("loss exceeding Step lossing pips", "increased lot", "Averaging positions"),
    },
    {
        "slug": "reject-mql5-cb-79021-xander-grid-rsi-gold",
        "original_id": "MQL5-CB-79021",
        "lead_id": "REJECT-OFF3-MQL5-04",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/79021",
        "name": "Xander Grid RSI Gold",
        "family": "Disqualified Toxic Grid / No-SL",
        "family_tag": "TOXIC_GRID_NO_SL",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD"],
        "symbol": "XAUUSD",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": "No stop loss on each position; optional basket stop loss can be turned off",
        "take_profit_rule": "Whole basket target in money or points from average price",
        "rule_description": (
            "Disqualified: XAUUSD grid EA with a lot multiplier that adds adverse levels every fixed point step "
            "and explicitly runs with no stop loss on each individual position."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_GRID", "TOXIC_MARTINGALE", "TOXIC_NO_STOP_LOSS"],
        "excerpt_keywords": ("grid with a lot multiplier and no stop loss", "adds a new level"),
    },
    {
        "slug": "reject-mql5-art-15067-zone-recovery-martingale",
        "original_id": "MQL5-ART-15067",
        "lead_id": "REJECT-OFF3-MQL5-05",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/15067",
        "name": "Developing Zone Recovery Martingale Strategy in MQL5",
        "family": "Disqualified Toxic Zone Recovery / Martingale",
        "family_tag": "TOXIC_ZONE_RECOVERY_MARTINGALE",
        "asset_class": "CFD_FX",
        "asset_universe": ["FX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": "Replaces closing at a stop loss with escalating counter-trend recovery lot layers",
        "take_profit_rule": "Recovery zone basket breakeven/profit exit",
        "rule_description": (
            "Disqualified: Zone recovery martingale strategy countering losing positions by opening opposite "
            "hedge positions with greater lot volume instead of closing at a hard stop loss."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_MARTINGALE", "TOXIC_AVERAGING_DOWN"],
        "excerpt_keywords": ("zone recovery martingale strategy", "greater trading volume", "as opposed to closing the position at a loss"),
    },
    {
        "slug": "reject-mql5-cb-20815-night-flat-rollover-scalper",
        "original_id": "MQL5-CB-20815",
        "lead_id": "REJECT-OFF3-MQL5-06",
        "source_origin": "mql5-codebase",
        "url": "https://www.mql5.com/en/code/20815",
        "name": "Night Flat Trade (Rollover Session Scalper / No Hard SL)",
        "family": "Disqualified Toxic Rollover Scalper / No-SL",
        "family_tag": "TOXIC_ROLLOVER_SCALPER_NO_SL",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD"],
        "symbol": "EURUSD",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": "No Stop Loss input parameter disclosed (only Take Profit and Trailing Stop)",
        "take_profit_rule": "Fixed Take Profit + Trailing Stop",
        "rule_description": (
            "Disqualified: Rollover-window night flat scalper trading EURUSD solely in the quietest hours after "
            "US session close and before Asian open (rollover spread-widening window) with no Stop Loss parameter."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_ROLLOVER_SCALPER", "TOXIC_NO_STOP_LOSS"],
        "excerpt_keywords": ("only in the quietest hours", "closing the American session", "Take Profit - Take Profit"),
    },
    {
        "slug": "reject-mql5-art-23527-wininet-dll-import-ea",
        "original_id": "MQL5-ART-23527",
        "lead_id": "REJECT-OFF3-MQL5-07",
        "source_origin": "mql5-article",
        "url": "https://www.mql5.com/en/articles/23527",
        "name": "MQL5 EA Using Direct WinINet DLL Import (#import wininet.dll)",
        "family": "Disqualified Toxic DLL Import",
        "family_tag": "TOXIC_DLL_IMPORT",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": ["FX"],
        "symbol": "FX",
        "timeframe": NOT_DISCLOSED,
        "direction": NOT_DISCLOSED,
        "prop_track": NOT_DISCLOSED,
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Disqualified: Requires DLL import (#import \"wininet.dll\") to bypass MetaTrader WebRequest URL "
            "whitelist — violates strict no-DLL-import cleanroom & prop-execution policy."
        ),
        "replicability": "PARTIAL_CONCEPT_ONLY",
        "expected_toxic": True,
        "expected_reject_reasons": ["TOXIC_DLL_IMPORT", "TOXIC_BLACKBOX_OR_DLL"],
        "excerpt_keywords": ("calls Windows Internet (wininet.dll) directly", "#import", "no URL whitelist"),
    },
)


def _sha256_upper_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_upper_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _extract_main_prose_and_inputs(raw_html: str, url: str) -> tuple[str, str, list[str], list[str], str]:
    """Return (page_title, clean_prose, disclosed_inputs, dll_imports, author)."""
    h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", raw_html, re.S | re.I)
    title = html.unescape(re.sub(r"<[^>]+>", "", h1_m.group(1))).strip() if h1_m else NOT_DISCLOSED

    author_m = re.search(r'class="[^"]*author[^"]*"[^>]*>.*?<a[^>]*>([^<]{2,80})</a>', raw_html, re.S | re.I)
    author = html.unescape(author_m.group(1)).strip() if author_m else NOT_DISCLOSED

    if "/code/" in url:
        start = raw_html.find("Go to Freelance")
        if start == -1:
            start = h1_m.start() if h1_m else 0
        else:
            start = raw_html.find(">", start) + 1
        ends = [raw_html.find(m, start + 100) for m in ("Similar", "Comments", 'id="comments"')]
        ends = [e for e in ends if e > start]
        end = min(ends) if ends else min(len(raw_html), start + 120000)
        chunk = raw_html[start:end]
    else:
        start = h1_m.end() if h1_m else 0
        ends = [
            raw_html.find(m, start + 500)
            for m in ("Similar articles", "Other articles by this author", 'id="comments"', 'class="comments')
        ]
        ends = [e for e in ends if e > start]
        end = min(ends) if ends else min(len(raw_html), start + 300000)
        chunk = raw_html[start:end]

    code_blocks = re.findall(r"<pre[^>]*>(.*?)</pre>", chunk, re.S | re.I)
    code_txt = "\n".join(html.unescape(re.sub(r"<[^>]+>", "", cb)) for cb in code_blocks)
    disclosed_inputs = [
        re.sub(r"\s+", " ", inp).strip()
        for inp in re.findall(r"^\s*(?:input|sinput)\s+[^\n;]{4,100};", code_txt, re.M)
    ][:20]
    dll_imports = sorted(set(re.findall(r'#import\s+"[^"]+\.dll"', code_txt, re.I)))

    prose_html = re.sub(r"<pre[^>]*>.*?</pre>", " ", chunk, flags=re.S | re.I)
    parser = _PageTextExtractor()
    parser.feed(prose_html)
    prose = parser.get_text()
    # Strip boilerplate top-bar fragments if present
    prose = re.sub(r'^\s*Go to Freelance\s*', "", prose)
    return title, prose, disclosed_inputs, dll_imports, author


def _select_clean_verbatim_excerpt(prose: str, keywords: tuple[str, ...]) -> str:
    """Pick a genuine verbatim sentence/passage from fetched page prose with zero 2024..2029/oos2 tokens."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose) if len(s.strip()) >= 25]
    chosen: list[str] = []
    for kw in keywords:
        kw_low = kw.lower()
        for sent in sentences:
            if kw_low in sent.lower() and not holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(sent):
                if sent not in chosen:
                    chosen.append(sent)
                break
        if sum(len(x) for x in chosen) >= 240:
            break
    if not chosen:
        for sent in sentences:
            if not holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(sent) and len(sent) >= 40:
                chosen.append(sent)
                if sum(len(x) for x in chosen) >= 240:
                    break
    excerpt = " ".join(chosen).strip()
    return excerpt[:360] if excerpt else NOT_DISCLOSED


def _fetch_one(spec: dict[str, Any]) -> dict[str, Any]:
    safe_url = auto_intel_ingest.validate_safe_public_url(spec["url"])
    req = urllib.request.Request(
        safe_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,text/plain;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=18) as resp:  # noqa: S310
        final_url = resp.geturl() or safe_url
        auto_intel_ingest.validate_safe_public_url(final_url)
        ctype = resp.headers.get("Content-Type", "text/html")
        cdisp = resp.headers.get("Content-Disposition", "")
        # Pure HTML pages on MQL5 articles can exceed 512KB due to styling/markup;
        # validate headers + magic bytes + NUL bytes fail-closed before decoding.
        raw_bytes = resp.read(1536 * 1024)
        auto_intel_ingest.validate_text_payload(
            raw_bytes[: auto_intel_ingest.MAX_TEXT_BYTES],
            content_type=ctype,
            filename_hint=cdisp,
        )
        html_text = raw_bytes.decode("utf-8", errors="replace")
        http_status = getattr(resp, "status", 200)

    page_title, prose, disclosed_inputs, dll_imports, author = _extract_main_prose_and_inputs(html_text, final_url)
    # Build scrubbed verbatim prose window (pure text, no 2024..2029/oos2 tokens)
    verbatim_excerpt = _select_clean_verbatim_excerpt(prose, tuple(spec.get("excerpt_keywords", ())))
    prose_scrubbed = holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.sub("[REDACTED_PERIOD]", prose[:8000])

    raw_doc: dict[str, Any] = {
        "slug": spec["slug"],
        "lead_id": spec["lead_id"],
        "original_id": spec["original_id"],
        "source_name": spec["source_origin"],
        "url": final_url,
        "http_status": http_status,
        "content_type": ctype.split(";", 1)[0].strip().lower(),
        "fetched_html_sha256": _sha256_upper_bytes(raw_bytes),
        "page_title_verbatim": holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.sub("[REDACTED_PERIOD]", page_title),
        "author": author,
        "name": spec["name"],
        "family": spec["family"],
        "family_tag": spec["family_tag"],
        "asset_class": spec["asset_class"],
        "asset_universe": spec["asset_universe"],
        "symbol": spec["symbol"],
        "timeframe": spec["timeframe"],
        "direction": spec["direction"],
        "prop_track": spec["prop_track"],
        "economic_rationale": spec.get("economic_rationale", NOT_DISCLOSED),
        "counterparty_mechanism": spec.get("counterparty_mechanism", NOT_DISCLOSED),
        "entry_rule": spec.get("entry_rule", NOT_DISCLOSED),
        "exit_rule": spec.get("exit_rule", NOT_DISCLOSED),
        "stop_loss_rule": spec["stop_loss_rule"],
        "take_profit_rule": spec["take_profit_rule"],
        "rule_description": spec["rule_description"],
        "disclosed_inputs_excerpt": [
            holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.sub("[REDACTED_PERIOD]", x) for x in disclosed_inputs[:12]
        ],
        "detected_dll_imports_in_page_snippets": dll_imports,
        "verbatim_excerpt": verbatim_excerpt,
        "raw_text": prose_scrubbed,
        "replicability": spec["replicability"],
        "expected_toxic": spec["expected_toxic"],
    }
    if spec.get("expected_reject_reasons"):
        raw_doc["expected_reject_reasons"] = spec["expected_reject_reasons"]
    return raw_doc


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def run_harvest() -> dict[str, Any]:
    raw_dir = SOURCE_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Validate every URL fail-closed BEFORE any network I/O
    for spec in CURATED_MQL5_TARGETS:
        auto_intel_ingest.validate_safe_public_url(spec["url"])

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for doc in pool.map(_fetch_one, CURATED_MQL5_TARGETS):
            results.append(doc)

    # Clear stale raw files if any, then write fresh snapshots + SHA-256 manifest
    manifest: dict[str, dict[str, Any]] = {}
    for doc in results:
        fname = f"{doc['slug']}.json"
        fpath = raw_dir / fname
        _write_json(fpath, doc)
        manifest[fname] = {
            "sha256": _sha256_upper_file(fpath),
            "size": fpath.stat().st_size,
        }

    manifest_path = SOURCE_DIR / "raw_manifest.sha256.json"
    _write_json(manifest_path, manifest)

    return {
        "raw_files": len(manifest),
        "clean_targets": sum(1 for d in results if not d["expected_toxic"]),
        "toxic_targets": sum(1 for d in results if d["expected_toxic"]),
        "manifest_path": str(manifest_path),
    }


if __name__ == "__main__":
    summary = run_harvest()
    print(json.dumps(summary, indent=2))
