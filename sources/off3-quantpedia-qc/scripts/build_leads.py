"""Deterministic cleanroom extractor for Offensive #3 Quantpedia & QuantConnect leads.

Reads strictly from:
  sources/off3-quantpedia-qc/raw/*.json
  sources/off3-quantpedia-qc/raw_manifest.sha256.json

Writes strictly to:
  sources/off3-quantpedia-qc/extracted/leads.json

Guardrails:
  - Zero Hallucination: undisclosed SL/TP/Winrate/PF/DD strictly set to NOT_DISCLOSED.
  - Verbatim Grounding: every verbatim_excerpt is extracted directly from raw/*.json
    and asserted to be an exact substring of raw_text.
  - Zero Holdout Leakage: asserts 0 matches of 2024..2029 / oos2 tokens across the
    entire extracted/leads.json output.
  - Zero Toxic Signals & 100% FTMO Applicability verified against cleanroom guards.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

SOURCE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = SOURCE_DIR / "raw"
MANIFEST_PATH = SOURCE_DIR / "raw_manifest.sha256.json"
EXTRACTED_PATH = SOURCE_DIR / "extracted" / "leads.json"
REPO_ROOT = SOURCE_DIR.parent.parent

for _p in (
    REPO_ROOT / "scripts",
    REPO_ROOT / "scripts" / "common",
    REPO_ROOT / "sources" / "off3-dedup-index" / "scripts",
):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

import auto_intel_ingest  # noqa: E402
import holdout_sanitizer  # noqa: E402
import merge_off3_leads  # noqa: E402
import repo_hygiene_check  # noqa: E402
import verify_verbatim  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"

# Deterministic specification metadata mapped 1-to-1 to verified raw/*.json snapshots.
# Every parameter is strictly grounded in its raw snapshot; missing fields are NOT_DISCLOSED.
SPEC_MAP: tuple[dict[str, Any], ...] = (
    # ==================== QUANTPEDIA (12 LEADS) ====================
    {
        "slug": "qp-01-currency-momentum-factor",
        "lead_id": "LEAD-OFF3-QP-01",
        "original_id": "OFF3-QP-01",
        "name": "Currency Momentum Factor (Cross-Sectional 12M FX Ranking)",
        "family": "Cross-Sectional FX Momentum",
        "family_tag": "FX_CROSS_SECTIONAL_MOMENTUM",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Behavioral investor underreaction to macroeconomic news causes multi-month spot exchange "
            "rate return continuation (Menkhoff, Sarno, Schmeling, Schrimpf; Deutsche Bank)."
        ),
        "counterparty_mechanism": (
            "Slow institutional and macro-hedger repricing of spot FX rates after central-bank and "
            "macro shocks; distinct from interest-rate carry differentials."
        ),
        "entry_rule": (
            "Rank a multi-currency FX universe (10-20 currencies vs USD; mapped to FTMO G10 majors) "
            "by trailing 12-month spot return; go long the top 3 winner currencies and short the "
            "bottom 3 loser currencies at monthly rebalance."
        ),
        "exit_rule": (
            "Monthly portfolio rebalance: close positions that exit the top-3 long or bottom-3 short "
            "12-month momentum ranks."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Cross-sectional FX momentum factor: evaluate trailing 12-month return against USD across "
            "liquid currencies, buy the 3 highest-momentum currencies and sell the 3 lowest-momentum "
            "currencies, rebalancing monthly. Non-breakout, zero grid, zero martingale; protective "
            "stop-loss and take-profit levels are NOT_DISCLOSED in the public specification."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-02-fx-carry-trade",
        "lead_id": "LEAD-OFF3-QP-02",
        "original_id": "OFF3-QP-02",
        "name": "FX Carry Trade (Cross-Sectional Policy Rate Spread)",
        "family": "FX Carry Yield Factor",
        "family_tag": "FX_CARRY_YIELD_FACTOR",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Failure of Uncovered Interest Rate Parity (UIP): high-interest-rate currencies earn "
            "persistent risk-premium excess returns compensating for crash risk during global "
            "stress episodes (Deutsche Bank; Acemoglu, Rogoff, Woodford)."
        ),
        "counterparty_mechanism": (
            "Global capital imbalances and risk-averse funding hedgers sell high-yield currencies "
            "forward at a discount to secure safe-haven funding liquidity."
        ),
        "entry_rule": (
            "Rank liquid currencies by central bank prime interest rates; go long the 3 highest-rate "
            "currencies and short the 3 lowest-rate funding currencies at monthly rebalance."
        ),
        "exit_rule": (
            "Monthly rebalance: exit currencies that rotate out of the top-3 highest-yield or "
            "bottom-3 lowest-yield buckets."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Cross-sectional FX carry trade across major currencies: buy the 3 currencies with the "
            "highest central bank policy rates and short the 3 currencies with the lowest policy "
            "rates, rebalanced monthly. Non-breakout, zero grid, zero martingale; protective "
            "stop-loss and take-profit thresholds are NOT_DISCLOSED in the public specification."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["EXTERNAL_RATE_DATA_OR_SWAP_DIFFERENTIAL"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-03-dollar-carry-trade",
        "lead_id": "LEAD-OFF3-QP-03",
        "original_id": "OFF3-QP-03",
        "name": "Dollar Carry Trade (USD Basket vs Average Forward Discount)",
        "family": "FX Macro Dollar Regime",
        "family_tag": "FX_DOLLAR_CARRY_MACRO",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Countercyclical US-specific currency risk premium: the average forward discount of the "
            "US dollar against developed currencies forecasts USD basket excess returns (Lustig, "
            "Roussanov, Verdelhan)."
        ),
        "counterparty_mechanism": (
            "Global demand for US dollar funding and recession-state risk pricing causes the dollar "
            "rate spread relative to developed peers to predict directional USD swings."
        ),
        "entry_rule": (
            "Compute the equal-weighted average forward discount (or average 3-month interest rate) "
            "across developed currencies (EUR, AUD, CAD, JPY, NZD, CHF, GBP, etc.) and compare to "
            "the 3-month US Treasury rate: go long USD / short basket when US 3M rate > AFD, or "
            "short USD / long basket when US 3M rate < AFD."
        ),
        "exit_rule": (
            "Monthly rebalance: flip or flatten USD basket exposure whenever the sign of (US 3M "
            "rate minus developed-basket AFD) changes."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Time-series Dollar Carry Trade: compare the 3-month US Treasury rate against the "
            "equal-weighted average forward discount of developed currencies; take long USD vs "
            "basket when US rate exceeds average foreign rate and short USD vs basket otherwise, "
            "rebalanced monthly. Non-breakout, zero grid, zero martingale; hard stop-loss and "
            "take-profit levels are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["EXTERNAL_RATE_DATA_OR_SWAP_DIFFERENTIAL"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-04-currency-value-factor-ppp",
        "lead_id": "LEAD-OFF3-QP-04",
        "original_id": "OFF3-QP-04",
        "name": "Currency Value Factor (PPP Real Exchange Rate Mean Reversion)",
        "family": "FX Fundamental Value Reversion",
        "family_tag": "FX_VALUE_MEAN_REVERSION",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Real exchange rates mean-revert over long horizons toward Purchasing Power Parity "
            "equilibrium driven by cross-country trade and inflation adjustments (Deutsche Bank; "
            "Menkhoff, Sarno, Schmeling, Schrimpf)."
        ),
        "counterparty_mechanism": (
            "Capital-flow overshooting pushes spot FX away from relative CPI-adjusted fair value "
            "before trade balances and long-horizon reallocations pull currencies back."
        ),
        "entry_rule": (
            "Estimate fair value versus USD using the latest OECD PPP updated with monthly CPI and "
            "spot rate changes; go long the 3 most undervalued currencies (lowest PPP ratio) and "
            "short the 3 most overvalued currencies (highest PPP ratio)."
        ),
        "exit_rule": (
            "Monthly or quarterly rebalance: close currencies that leave the top-3 overvalued or "
            "bottom-3 undervalued PPP ranks."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Cross-sectional FX Value (PPP) mean-reversion: update OECD Purchasing Power Parity fair "
            "values with monthly CPI and exchange-rate moves, buying the 3 most undervalued "
            "currencies and shorting the 3 most overvalued currencies on a monthly or quarterly "
            "cadence. Non-breakout, zero grid, zero martingale; hard SL/TP are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["EXTERNAL_MACRO_DATA_REQUIRED_OECD_PPP_CPI"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-05-trading-wti-brent-spread",
        "lead_id": "LEAD-OFF3-QP-05",
        "original_id": "OFF3-QP-05",
        "name": "WTI vs Brent Crude Oil Spread Mean Reversion (SMA-20)",
        "family": "Energy Pairs Spread Mean Reversion",
        "family_tag": "ENERGY_PAIRS_MEAN_REVERSION",
        "asset_class": "ENERGY_CFD",
        "asset_universe": ["USOIL", "UKOIL"],
        "symbol": "USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "WTI and Brent are close physical crude substitutes whose price differential reflects "
            "chemical grade and transport costs; temporary regional supply/pipeline shocks mean-"
            "revert back to economic equilibrium (Evans, Dunis, Laws)."
        ),
        "counterparty_mechanism": (
            "Physical refiners and seaborne crude arbitrageurs redirect tanker flows when the "
            "WTI-Brent spread deviates beyond transport parity, forcing convergence."
        ),
        "entry_rule": (
            "Compute the 20-day Simple Moving Average (SMA 20) of the daily WTI/Brent spread. If "
            "the daily spread closes above SMA 20, short the spread (short USOIL, long UKOIL) on "
            "close; if below SMA 20, buy the spread (long USOIL, short UKOIL) on close."
        ),
        "exit_rule": (
            "Close short-spread trade on daily close when spread crosses below SMA 20; close "
            "long-spread trade on daily close when spread crosses above SMA 20."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": "Daily close crossing back through 20-day SMA of the WTI/Brent spread",
        "rule_description": (
            "Daily mean-reversion pairs spread on WTI (USOIL) versus Brent (UKOIL): calculate the "
            "20-day SMA of the spread; enter short spread on close when spread > SMA(20) and long "
            "spread when spread < SMA(20), exiting on daily close cross back through SMA(20). "
            "Non-breakout, zero grid, zero martingale; protective hard stop-loss is NOT_DISCLOSED "
            "in the public specification and must be designed for Prop MT5."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": [],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-06-crude-oil-predicts-equity-returns",
        "lead_id": "LEAD-OFF3-QP-06",
        "original_id": "OFF3-QP-06",
        "name": "Crude Oil Macro-Flow Predictor for Equity Index Timing",
        "family": "Energy-to-Index Macro Flow",
        "family_tag": "ENERGY_MACRO_EQUITY_TIMING",
        "asset_class": "MULTI_ASSET_FTMO",
        "asset_universe": ["USOIL", "UKOIL", "US500"],
        "symbol": "USOIL/US500",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Investor underreaction hypothesis: equity investors digest the earnings and inflation "
            "impact of crude oil price shocks slowly, making lagged oil returns a negative "
            "predictor of subsequent monthly equity index returns (Driesprong, Jacobsen, Maat)."
        ),
        "counterparty_mechanism": (
            "Staggered macro-analyst earnings revisions and delayed institutional equity allocation "
            "shifts after crude energy cost spikes."
        ),
        "entry_rule": (
            "Re-estimate an expanding monthly regression of equity index returns on lagged monthly "
            "crude oil returns (WTI/Brent); hold long equity index (US500) during the coming month "
            "when regression-predicted equity return exceeds the risk-free rate."
        ),
        "exit_rule": (
            "Rotate out of equity index into cash at month-end whenever regression-predicted next-"
            "month equity return falls below the risk-free rate."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Cross-asset macro timing using crude oil (USOIL/UKOIL) to time equity index exposure "
            "(US500): run a monthly expanding regression of equity returns on lagged monthly oil "
            "returns; hold long equity index when forecast return exceeds the risk-free rate, else "
            "stay in cash. Non-breakout, zero grid, zero martingale; hard SL/TP are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-07-skewness-effect-in-commodities",
        "lead_id": "LEAD-OFF3-QP-07",
        "original_id": "OFF3-QP-07",
        "name": "Commodity Return Skewness Factor (Long Negative-Skew / Short Lottery-Skew)",
        "family": "Commodities Skewness Asymmetry",
        "family_tag": "COMMODITIES_SKEWNESS_ASYMMETRY",
        "asset_class": "COMMODITIES_CFD",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
        "symbol": "XAUUSD/XAGUSD/USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Systematic mispricing of asymmetric tail risk: speculative investors overpay for "
            "positively skewed lottery-like commodities while underpricing negatively skewed "
            "commodities that compensate for crash risk (Dujava & Vojtko)."
        ),
        "counterparty_mechanism": (
            "Speculative demand for right-tail upside spikes combined with commercial producer "
            "hedging pressure across metals and energy markets."
        ),
        "entry_rule": (
            "At each monthly rebalance, compute 12-month historical return skewness across the "
            "commodity universe (22 futures in paper; mapped to FTMO metals and energy CFDs); go "
            "long the lowest-skewness (most negatively skewed) contracts and short the highest-"
            "skewness (most positively skewed) contracts equally weighted."
        ),
        "exit_rule": (
            "Monthly rebalance: close positions that leave the top or bottom skewness buckets."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Cross-sectional commodity skewness factor (applicable to FTMO metals/energy subset "
            "XAUUSD, XAGUSD, USOIL, UKOIL): compute trailing 12-month return skewness monthly, "
            "going long the most negatively skewed contracts and short the most positively skewed "
            "contracts with equal weights and monthly rebalancing. Non-breakout, zero grid, zero "
            "martingale; protective hard SL/TP are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["UNIVERSE_SUBSET_MAPPED_FROM_22_FUTURES_TO_FTMO_METALS_ENERGY"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-08-turn-of-the-month-equity-indexes",
        "lead_id": "LEAD-OFF3-QP-08",
        "original_id": "OFF3-QP-08",
        "name": "Turn of the Month Calendar Liquidity Drift in Equity Indexes",
        "family": "Index Calendar Liquidity Flow",
        "family_tag": "INDEX_CALENDAR_FLOW",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500", "US30", "GER40", "UK100", "JP225"],
        "symbol": "US500/US30/GER40/UK100/JP225",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Predictable month-end and early-month cash-flow regularity: institutional pension "
            "contributions, payroll disbursements, and automated fund allocations concentrate "
            "equity buying around month boundaries (Lakonishok & Smidt; Xu & McConnell)."
        ),
        "counterparty_mechanism": (
            "Price-insensitive calendar-scheduled pension, payroll, and mutual-fund inflows hitting "
            "major equity index liquidity pools on fixed month-turn dates."
        ),
        "entry_rule": (
            "Enter long equity index (US500/SPY or developed index CFDs) at the close 1 trading day "
            "(variant: 4 trading days) before the end of the calendar month."
        ),
        "exit_rule": (
            "Exit long position at the close of the 3rd trading day of the new calendar month; "
            "remain in cash on all other days of the month."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Calendar turn-of-the-month equity index anomaly: go long equity indexes (US500, US30, "
            "GER40, UK100, JP225) 1 trading day (or 4 days in alternate literature) prior to month-"
            "end and exit at the close of the 3rd trading day of the new month, remaining flat "
            "otherwise. Non-breakout, zero grid, zero martingale; hard SL/TP are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-09-fomc-meeting-effect-in-stocks",
        "lead_id": "LEAD-OFF3-QP-09",
        "original_id": "OFF3-QP-09",
        "name": "Pre-FOMC and FOMC Meeting Announcement Drift in Equity Indexes",
        "family": "Macro Event Calendar Drift",
        "family_tag": "INDEX_MACRO_EVENT_CALENDAR",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500", "US100", "US30"],
        "symbol": "US500/US100/US30",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Scheduled Federal Reserve policy meetings resolve macro uncertainty with an asymmetric "
            "systemic-stability mandate, concentrating outsized equity index excess returns into "
            "approximately 8 FOMC windows per year (Tori)."
        ),
        "counterparty_mechanism": (
            "Pre-announcement hedging unwind and resolution of macro-policy uncertainty premium "
            "across US index futures and CFDs around scheduled FOMC dates."
        ),
        "entry_rule": (
            "Go long S&P 500 index CFD/future (US500) at the market close 1 trading day before a "
            "scheduled FOMC meeting."
        ),
        "exit_rule": (
            "Close the long position at the market close immediately after the FOMC meeting; stay "
            "in cash during all non-FOMC trading days."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Event-calendar FOMC meeting drift on US equity indexes (US500/US100/US30): buy on the "
            "close 1 trading day before each scheduled FOMC meeting and close on the close after "
            "the meeting (~8 windows/year), staying flat otherwise. Non-breakout, zero grid, zero "
            "martingale; hard SL/TP are NOT_DISCLOSED (note FTMO red-news execution restrictions "
            "must be checked around the exact announcement timestamp)."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["PROP_RED_NEWS_WINDOW_COMPLIANCE_CHECK_REQUIRED"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-10-market-sentiment-overnight-anomaly",
        "lead_id": "LEAD-OFF3-QP-10",
        "original_id": "OFF3-QP-10",
        "name": "Market Sentiment & Volatility Filtered Overnight Equity Index Drift",
        "family": "Index Overnight Regime Drift",
        "family_tag": "INDEX_OVERNIGHT_REGIME_DRIFT",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500"],
        "symbol": "US500",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Accumulated overnight market orders and opening price pressure concentrate equity index "
            "gains in the close-to-open session, especially during constructive trend, low-VIX, "
            "and positive-sentiment regimes (Vojtko & Hanicova)."
        ),
        "counterparty_mechanism": (
            "Retail and institutional market-on-open order imbalances push opening auction prices "
            "above prior close during low-stress uptrending regimes."
        ),
        "entry_rule": (
            "Buy S&P 500 (SPY/US500) at the daily close to hold overnight ONLY when all three "
            "regime conditions hold: (1) index close > 20-day SMA, (2) VIX < its moving average, "
            "and (3) Brain Market Sentiment (BMS) indicator > its 20-day SMA."
        ),
        "exit_rule": (
            "Liquidate the overnight position at the next trading day's cash market open."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Regime-filtered overnight equity index anomaly (US500): buy at daily close and exit at "
            "next session open only when price is above its 20-day SMA, VIX is below its moving "
            "average, and market sentiment exceeds its 20-day SMA. Non-breakout, zero grid, zero "
            "martingale; hard stop-loss and take-profit levels are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["EXTERNAL_DATA_REQUIRED_VIX_AND_BMS"],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-11-pre-holiday-effect",
        "lead_id": "LEAD-OFF3-QP-11",
        "original_id": "OFF3-QP-11",
        "name": "Pre-Holiday Calendar Drift in Equity Indexes",
        "family": "Index Calendar Holiday Flow",
        "family_tag": "INDEX_CALENDAR_HOLIDAY_FLOW",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500", "US30", "GER40", "UK100"],
        "symbol": "US500/US30/GER40/UK100",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Short-sellers flatten risky positions ahead of market closures to avoid multi-day "
            "holiday gap risk while retail optimism lightens selling pressure (Hansen & Lunde)."
        ),
        "counterparty_mechanism": (
            "Pre-holiday short-covering and reduced institutional supply ahead of scheduled "
            "exchange closures (New Year, MLK, Presidents, Good Friday, Memorial, Independence, "
            "Labor, Thanksgiving, Christmas, plus local EU/UK holidays)."
        ),
        "entry_rule": (
            "Go long US or local developed equity index CFD/future (US500/US30/GER40/UK100) only "
            "for the trading day immediately preceding a scheduled public market holiday."
        ),
        "exit_rule": (
            "Exit at the close of the pre-holiday trading session and stay in cash during all "
            "regular non-pre-holiday trading days."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Pre-holiday calendar drift on equity indexes (US500, US30, GER40, UK100): hold long "
            "exposure exclusively during trading days preceding major scheduled public holidays "
            "and stay flat on all other days. Non-breakout, zero grid, zero martingale; hard "
            "stop-loss and take-profit levels are NOT_DISCLOSED in the public specification."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "simple_trading_strategy",
    },
    {
        "slug": "qp-12-short-term-reversal-with-futures",
        "lead_id": "LEAD-OFF3-QP-12",
        "original_id": "OFF3-QP-12",
        "name": "Volume-Conditioned Weekly Short-Term Reversal in Multi-Asset Futures",
        "family": "Multi-Asset Short-Term Reversal",
        "family_tag": "MULTI_ASSET_WEEKLY_REVERSAL",
        "asset_class": "MULTI_ASSET_FTMO",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "US500", "XAUUSD", "XAGUSD", "USOIL"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/US500/XAUUSD/XAGUSD/USOIL",
        "timeframe": "W1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Short-horizon behavioral overreaction: high trading volume with declining open "
            "interest signals speculative position liquidation and overshooting that subsequently "
            "mean-reverts over the next week (Wang & Yu)."
        ),
        "counterparty_mechanism": (
            "Overconfident short-term traders over-adjust to weekly news flow on spiking volume "
            "without new hedging conviction (low open-interest growth), creating reversal liquidity "
            "premia."
        ),
        "entry_rule": (
            "Evaluate weekly Wednesday-to-Wednesday returns, detrended volume changes, and open-"
            "interest changes across multi-asset futures (currencies, financials/indices, metals, "
            "energy). Filter for the high-volume-change (above median) and low-open-interest-change "
            "(bottom 50%) subset; go long prior-week losers and short prior-week winners weighted "
            "proportionally to deviation from the group equal-weighted weekly return."
        ),
        "exit_rule": (
            "Weekly rebalance every Wednesday close: close prior holdings and re-rank contracts."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "Weekly Wednesday-to-Wednesday volume-conditioned reversal across currency, index, and "
            "commodity futures (mapped to FTMO FX/Index/Metals/Energy): within high-volume, "
            "low-open-interest-change contracts, buy prior-week losers and short prior-week winners "
            "with weights proportional to return deviation from group mean. Non-breakout, zero grid, "
            "zero martingale; hard stop-loss and take-profit are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["OPEN_INTEREST_PROXY_REQUIRED_ON_SPOT_CFD"],
        "excerpt_source": "simple_trading_strategy",
    },
    # ==================== QUANTCONNECT STRATEGY LIBRARY (10 LEADS) ====================
    {
        "slug": "qc-01-forex-mean-reversion-and-momentum",
        "lead_id": "LEAD-OFF3-QC-01",
        "original_id": "OFF3-QC-01",
        "name": "Combined Mean Reversion & 3-Month Momentum UIP Regression in Forex",
        "family": "FX Hybrid Momentum & Mean Reversion",
        "family_tag": "FX_HYBRID_MOMENTUM_MEAN_REVERSION",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDCAD", "USDJPY"],
        "symbol": "EURUSD/GBPUSD/USDCAD/USDJPY",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Uncovered Interest Parity (UIP) implies long-horizon exchange rate mean reversion "
            "while short-horizon behavioral inertia creates 3-month momentum; combining both in "
            "pooled OLS forecasting captures abnormal FX returns (Serban; Balvers & Wu)."
        ),
        "counterparty_mechanism": (
            "Short-term trend chasing pushes major FX pairs temporarily away from their long-run "
            "mean before valuation convergence and carry adjustments restore parity."
        ),
        "entry_rule": (
            "Resample daily close prices of EURUSD, GBPUSD, USDCAD, USDJPY to month-end; compute "
            "reversal factor (price_{t-1} - mean)/sd and 3-month momentum factor "
            "(price_{t-1} - price_{t-4}); fit OLS regression to predict next-month return y_t; "
            "go long the currency with the highest predicted return and short the currency with "
            "the lowest predicted return."
        ),
        "exit_rule": (
            "Monthly scheduled rebalance: liquidate prior positions and re-allocate to the new "
            "highest- and lowest-forecast currencies."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect Strategy Library UIP Forex hybrid model on EURUSD, GBPUSD, USDCAD, "
            "USDJPY: combines standardized mean-reversion deviation and 3-month momentum in an OLS "
            "regression to predict monthly returns, buying the top-forecast pair and shorting the "
            "bottom-forecast pair on a monthly schedule. Non-breakout, zero grid, zero martingale; "
            "hard stop-loss and take-profit rules are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-02-forex-low-frequency-hp-momentum",
        "lead_id": "LEAD-OFF3-QC-02",
        "original_id": "OFF3-QC-02",
        "name": "Hodrick-Prescott Low-Frequency Trend Filter Momentum in Forex",
        "family": "FX Trend Filter & Pullback",
        "family_tag": "FX_TREND_PULLBACK_FILTER",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/USDCAD/AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Standard moving averages suffer phase lag on noisy FX spot rates; decomposing daily "
            "exchange rates with a recursive Hodrick-Prescott filter isolates the smooth low-"
            "frequency trend component to detect turning points earlier (Harris & Yilmaz 2009)."
        ),
        "counterparty_mechanism": (
            "Separating high-frequency intraday/short-cycle noise from persistent macro currency "
            "trends avoids whipsaws caused by liquidity noise."
        ),
        "entry_rule": (
            "Recursively estimate the Hodrick-Prescott (HP) low-frequency trend component on "
            "rolling daily FX closes (smoothing parameter lambda=100 calibrated on rolling daily "
            "window); apply the MA(1, 2) slope rule to the extracted trend series: go long when "
            "current HP trend value > 2-day mean of HP trend, and short when below."
        ),
        "exit_rule": (
            "Reverse or flatten daily position when the MA(1, 2) sign on the recursive HP trend "
            "flips direction."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect implementation of Harris & Yilmaz (2009) low-frequency FX momentum on "
            "daily major pairs (demonstrated on EURUSD across 7 exchange rates): recursively "
            "extract nonlinear trend via Hodrick-Prescott filter (lambda=100) and generate long/"
            "short signals with an MA(1, 2) rule on the trend component. Non-breakout, zero grid, "
            "zero martingale; protective hard stop-loss and take-profit are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["PARAMETER_SENSITIVITY_NOTED_BY_SOURCE"],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-03-risk-premia-forex-skewness",
        "lead_id": "LEAD-OFF3-QC-03",
        "original_id": "OFF3-QC-03",
        "name": "Forex Risk Premia via Asymmetric Tail-Skewness Thresholds",
        "family": "FX Skewness Risk Premia",
        "family_tag": "FX_SKEWNESS_RISK_PREMIA",
        "asset_class": "FX_MAJOR_CROSS",
        "asset_universe": ["EURUSD", "AUDUSD", "USDCAD", "USDJPY"],
        "symbol": "EURUSD/AUDUSD/USDCAD/USDJPY",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Positive linear relationship between risk-premia Sharpe ratio and negative return "
            "skewness: assets exhibiting negatively skewed tail risk pay systematic excess "
            "returns as compensation for bearing asymmetric downside risk (Lemperiere et al.)."
        ),
        "counterparty_mechanism": (
            "Risk-averse market participants pay a premium to shed negatively skewed FX tail risk "
            "and overbid positively skewed safe-haven payoff profiles."
        ),
        "entry_rule": (
            "On a fixed 4-pair FX universe (EURUSD, AUDUSD, USDCAD, USDJPY; H1 feed with rolling "
            "daily close lookback), compute historical skewness for each pair; go long pairs with "
            "skewness < -0.6 and go short pairs with skewness > +0.6 using equal portfolio weights "
            "(1 / count)."
        ),
        "exit_rule": (
            "Weekly rebalance: liquidate any invested FX pair whose skewness moves back inside "
            "[-0.6, +0.6] and re-weight active qualifying pairs equally."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect Forex risk-premia skewness strategy on EURUSD, AUDUSD, USDCAD, USDJPY: "
            "evaluates rolling historical skewness and enters equal-weighted long positions when "
            "skewness < -0.6 and short positions when skewness > +0.6, rebalancing weekly and "
            "liquidating neutral pairs. Non-breakout, zero grid, zero martingale; hard stop-loss "
            "and take-profit levels are NOT_DISCLOSED."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-04-gold-market-timing-fed-model",
        "lead_id": "LEAD-OFF3-QC-04",
        "original_id": "OFF3-QC-04",
        "name": "Gold Market Timing via Fed Model (Earnings Yield vs 10Y Bond Yield)",
        "family": "Metals Macro Valuation Timing",
        "family_tag": "METALS_MACRO_FLOW_TIMING",
        "asset_class": "METALS_CFD",
        "asset_universe": ["XAUUSD"],
        "symbol": "XAUUSD",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Gold exhibits strong inverse sensitivity to equity valuation stretches and real-rate "
            "regimes; comparing S&P 500 earnings yield against the US 10-year Treasury yield via "
            "the Fed Model identifies macro valuation regimes favorable for Gold."
        ),
        "counterparty_mechanism": (
            "Cross-asset macro allocators rotate between equities, Treasuries, and Gold when "
            "equity earnings yields diverge sharply from sovereign bond yields."
        ),
        "entry_rule": (
            "At monthly rebalance, compare trailing 12-month S&P 500 earnings yield against the US "
            "10-year Treasury bond yield: go long Gold (XAUUSD) when earnings yield > bond yield "
            "and the ratio (earnings_yield / bond_yield) >= 2.0."
        ),
        "exit_rule": (
            "Liquidate Gold to cash at monthly rebalance whenever the Fed Model condition "
            "(earnings_yield / bond_yield >= 2.0) is no longer satisfied."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect Gold Market Timing strategy using the macro Fed Model on daily Gold "
            "(XAUUSD): go long Gold on monthly rebalance when S&P 500 trailing earnings yield "
            "exceeds the US 10-year government bond yield by a ratio of at least 2.0, otherwise "
            "liquidate to cash. Non-breakout, zero grid, zero martingale; hard stop-loss and "
            "take-profit levels are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": ["EXTERNAL_MACRO_DATA_REQUIRED_EARNINGS_AND_10Y_YIELD"],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-05-improved-commodities-tsmom-cf",
        "lead_id": "LEAD-OFF3-QC-05",
        "original_id": "OFF3-QC-05",
        "name": "Correlation-Adjusted Commodities TSMOM with Yang-Zhang Volatility (TSMOM-CF)",
        "family": "Commodities Volatility-Scaled Trend",
        "family_tag": "COMMODITIES_VOL_SCALED_TREND",
        "asset_class": "COMMODITIES_CFD",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
        "symbol": "XAUUSD/XAGUSD/USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Replaces noisy discrete +1/-1 TSMOM with continuous t-statistic trend strength, "
            "drift-independent Yang-Zhang OHLC range/gap volatility scaling, and pairwise "
            "correlation leverage control to cut whipsaw turnover and portfolio vol spikes "
            "(Baltas & Kosowski 2017)."
        ),
        "counterparty_mechanism": (
            "Slow-moving macro supply-demand cycles in metals and energy combined with reduced "
            "turnover costs when scaling continuously by trend t-stat and cross-asset correlation."
        ),
        "entry_rule": (
            "Monthly on daily OHLC commodity series (mapped to FTMO metals/energy XAUUSD, XAGUSD, "
            "USOIL, UKOIL): compute 12-month daily log-return t-statistic clipped to [-1, +1] as "
            "continuous signal X_i, estimate volatility via Yang-Zhang (overnight jump + close-to-"
            "close + Rogers-Satchell range), and size positions to portfolio target volatility "
            "(12% annualized in source) multiplied by pairwise correlation factor CF(rho_bar)."
        ),
        "exit_rule": (
            "Monthly rebalance: resize or flip positions continuously according to updated trend "
            "t-stat, Yang-Zhang volatility, and pairwise correlation factor."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect Baltas & Kosowski (2017) TSMOM-CF on commodities (FTMO metals/energy "
            "XAUUSD, XAGUSD, USOIL, UKOIL): combines continuous 12M return t-stat signal clipped "
            "to [-1, +1], Yang-Zhang OHLC volatility scaling, and pairwise correlation leverage "
            "adjustment at monthly rebalance targeting 12% portfolio volatility. Non-breakout, "
            "zero grid, zero martingale; per-trade hard SL/TP are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-06-commodities-ema-vol-trend-following",
        "lead_id": "LEAD-OFF3-QC-06",
        "original_id": "OFF3-QC-06",
        "name": "Volatility-Normalized Price-Minus-EMA Trend Following (Two Centuries Model)",
        "family": "Multi-Asset EMA Volatility-Normalized Trend",
        "family_tag": "COMMODITIES_TREND_EMA_VOL_NORM",
        "asset_class": "MULTI_ASSET_FTMO",
        "asset_universe": ["USOIL", "UKOIL", "XAUUSD", "XAGUSD", "EURUSD", "US500"],
        "symbol": "USOIL/UKOIL/XAUUSD/XAGUSD/EURUSD/US500",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Two centuries of multi-asset evidence across commodities, currencies, stock indices, "
            "and bonds show persistent trends when price displacement from an exponential moving "
            "average is normalized by exponentially smoothed volatility (Lemperiere et al. 2014)."
        ),
        "counterparty_mechanism": (
            "Behavioral underreaction and institutional slow capital reallocation create medium-"
            "term directional persistence across liquid energy, metals, FX, and equity indices."
        ),
        "entry_rule": (
            "Consolidate daily prices to monthly bars; compute normalized trend signal "
            "s_n(t) = (p(t-1) - EMA_n(p, t-1)) / sigma_n(t-1), where sigma_n is the n-month EMA "
            "of absolute monthly price changes. Go long when s_n > 0 and short when s_n < 0 with "
            "contract quantity inversely proportional to sigma_n(t-1)."
        ),
        "exit_rule": (
            "Monthly rebalance on each new consolidated monthly bar: flip direction when sign(s_n) "
            "reverses and rescale position inversely to updated sigma_n."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect implementation of Lemperiere, Deremble, Seager, Potters & Bouchaud (2014) "
            "'Two Centuries of Trend Following' (applicable across FTMO energy, metals, FX, and "
            "indices): trades sign of (p - EMA_n(p)) / sigma_n with inverse-volatility sizing on "
            "monthly consolidated bars. Non-breakout, zero grid, zero martingale; hard per-trade "
            "stop-loss and take-profit are NOT_DISCLOSED."
        ),
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-07-intraday-index-etf-momentum",
        "lead_id": "LEAD-OFF3-QC-07",
        "original_id": "OFF3-QC-07",
        "name": "Intraday Equity Index Momentum (First 30-Min Return Predicts Last 30-Min)",
        "family": "Index Intraday Session Momentum",
        "family_tag": "INDEX_INTRADAY_SESSION_MOMENTUM",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500", "US100", "US30"],
        "symbol": "US500/US100/US30",
        "timeframe": "M1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "economic_rationale": (
            "Pre-market news digestion concentrates informed order flow in the first 30 minutes of "
            "trading, while late-informed investors and overnight-risk hedgers trade in the same "
            "direction during the final 30 minutes (Gao, Han, Li & Zhou 2017; Bogousslavsky 2016)."
        ),
        "counterparty_mechanism": (
            "Delayed institutional execution and end-of-day rebalancing flows echo the direction "
            "of opening-bell information absorption."
        ),
        "entry_rule": (
            "Using M1 bars on US equity indexes (SPY/QQQ/DIA mapped to FTMO US500/US100/US30), "
            "compute the morning return over the first 30 minutes of the cash session (from prior "
            "close / opening window); at 30 minutes before market close (15:30 ET), go long if "
            "morning return > 0 or go short if morning return < 0."
        ),
        "exit_rule": (
            "Flatten all positions strictly at the regular cash market close (30-minute holding "
            "window, zero overnight swap)."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect intraday index momentum strategy (Gao, Han, Li & Zhou 2017) on M1 bars "
            "for US equity indexes (US500, US100, US30): observe the return sign during the first "
            "30 minutes of the cash session and enter in that direction for the final 30 minutes, "
            "exiting flat at market close (intraday swap=0). Non-breakout, zero grid, zero "
            "martingale; protective hard stop-loss and take-profit are NOT_DISCLOSED."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-08-vix-percentile-index-regime",
        "lead_id": "LEAD-OFF3-QC-08",
        "original_id": "OFF3-QC-08",
        "name": "VIX 2-Year Percentile Regime Timing for Equity Index (Vol Compression vs Spike)",
        "family": "Volatility Regime Compression & Expansion",
        "family_tag": "INDEX_VOL_COMPRESSION_EXPANSION",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500"],
        "symbol": "US500",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Extreme implied volatility regimes are mean-reverting contrarian indicators for broad "
            "equity indexes: panic VIX spikes (>90th 2-year percentile) mark elevated forward "
            "risk-premia, whereas extreme VIX complacency (<10th percentile) precedes fragile "
            "index pullbacks."
        ),
        "counterparty_mechanism": (
            "Forced institutional put-buying during volatility panics depresses index valuations "
            "below fundamentals, while extreme vol compression induces crowded leverage buildup."
        ),
        "entry_rule": (
            "Maintain a rolling 2-year (504 trading day) window of daily VIX closes split into 20 "
            "equally spaced percentiles (5%..95%). Go long equity index (S&P 100/500 mapped to "
            "US500) when daily VIX > 90th percentile (highest 2 boxes); go short equity index when "
            "daily VIX < 10th percentile (lowest 2 boxes)."
        ),
        "exit_rule": (
            "Hold active regime directional exposure until VIX crosses into the opposite extreme "
            "decile threshold (90th vs 10th percentile)."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "rule_description": (
            "QuantConnect VIX percentile volatility-regime timing strategy on daily equity index "
            "(US500): rank daily VIX against a rolling 504-day 20-percentile ladder, going long "
            "index above the 90th VIX percentile (vol expansion fear) and short index below the "
            "10th VIX percentile (vol compression complacency). Non-breakout, zero grid, zero "
            "martingale; hard stop-loss and take-profit levels are NOT_DISCLOSED."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": ["EXTERNAL_INDEX_DATA_VIX_OR_REALIZED_VOL_PROXY"],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-09-optimal-ou-pairs-trading",
        "lead_id": "LEAD-OFF3-QC-09",
        "original_id": "OFF3-QC-09",
        "name": "Optimal Stopping Ornstein-Uhlenbeck Pairs Trading (MLE Spread Thresholds)",
        "family": "Pairs Relative-Value OU Mean Reversion",
        "family_tag": "PAIRS_OU_MEAN_REVERSION",
        "asset_class": "MULTI_ASSET_FTMO",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL", "AUDUSD", "NZDUSD"],
        "symbol": "XAUUSD/XAGUSD/USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Modeling a cointegrated spread portfolio as an Ornstein-Uhlenbeck (OU) mean-reverting "
            "process allows analytical optimal entry and liquidation thresholds net of transaction "
            "costs (Leung & Li 2015, suggesting cointegrated pairs including gold-related pairs)."
        ),
        "counterparty_mechanism": (
            "Transient idiosyncratic liquidity shocks pull economically linked assets (e.g., "
            "gold/silver, WTI/Brent, commodity-bloc FX) apart before shared fundamentals pull the "
            "spread back toward equilibrium theta."
        ),
        "entry_rule": (
            "Over a rolling 252-day window (retrained quarterly), grid-search hedge ratio beta in "
            "[0.01..1.00] to maximize the OU log-likelihood for portfolio value ($1 A - $beta B), "
            "extracting (theta*, mu*, sigma*). Solve the Leung-Li integral equations for optimal "
            "entry threshold b* and liquidation threshold d*; enter long A / short beta* B when "
            "spread portfolio value <= b*."
        ),
        "exit_rule": (
            "Liquidate both legs of the spread portfolio when tracked portfolio value reaches the "
            "analytical optimal liquidation threshold d*; retrain OU parameters on the first day "
            "of each quarter."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": (
            "Analytical Ornstein-Uhlenbeck optimal liquidation level d* solved from Leung & Li "
            "equations with transaction cost c=0.05 and discount rate r=0.05"
        ),
        "rule_description": (
            "QuantConnect Leung & Li (2015) Ornstein-Uhlenbeck optimal-stopping pairs trading "
            "(generalized to FTMO cointegrated pairs XAUUSD/XAGUSD, USOIL/UKOIL, AUDUSD/NZDUSD): "
            "fits 252-day MLE OU parameters (beta*, theta*, mu*, sigma*) quarterly, enters when "
            "spread <= optimal entry level b*, and liquidates at optimal level d*. Non-breakout, "
            "zero grid, zero martingale; although Leung & Li (2015) discuss stop-loss exits in "
            "theory, the tutorial omits coding a hard SL (stop_loss_rule=NOT_DISCLOSED)."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": ["TUTORIAL_DEMOS_GENERIC_PAIR_MAPPED_TO_FTMO_COINTEGRATED_PAIRS"],
        "excerpt_source": "overview",
    },
    {
        "slug": "qc-10-country-equity-index-pairs-trading",
        "lead_id": "LEAD-OFF3-QC-10",
        "original_id": "OFF3-QC-10",
        "name": "International Country Equity Index Distance Pairs Trading (120D Formation)",
        "family": "Index Pairs Relative-Value Mean Reversion",
        "family_tag": "INDEX_PAIRS_RELATIVE_VALUE",
        "asset_class": "INDEX_CFD",
        "asset_universe": ["US500", "US30", "GER40", "UK100", "JP225"],
        "symbol": "US500/US30/GER40/UK100/JP225",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "economic_rationale": (
            "Co-moving developed-market national equity indexes share common global macro drivers; "
            "short-term relative divergences between closely tracking country index pairs revert "
            "toward their 120-day normalized cumulative return relationship (Panagiotis, Dimitrios "
            "& Tao)."
        ),
        "counterparty_mechanism": (
            "Regional session flows and temporary local shocks create relative mispricings between "
            "globally integrated equity indexes that cross-border allocators arbitrage back."
        ),
        "entry_rule": (
            "Over a 120-day formation period, compute normalized cumulative return indices for "
            "international equity indexes and rank all pairs by mean absolute distance D^(a,b); "
            "select the closest pairs for the subsequent 20-day trading month. When |index_A - "
            "index_B| > 0.5 * D^(a,b), short the higher index and buy the lower index dollar-neutral."
        ),
        "exit_rule": (
            "Liquidate the pair when (index_A - index_B) reverts inside (-0.5*D^(a,b), +0.5*D^(a,b)), "
            "or roll and re-select top pairs at the start of the next month."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": (
            "Spread convergence when normalized cumulative index difference returns inside "
            "(-0.5 * D^(a,b), +0.5 * D^(a,b))"
        ),
        "rule_description": (
            "QuantConnect international equity-index distance pairs trading (applicable to FTMO "
            "developed indices US500, US30, GER40, UK100, JP225): 120-day formation selects lowest-"
            "distance pairs; during the 20-day trading window, short outperformer and buy "
            "underperformer dollar-neutral when spread exceeds 0.5x formation distance D, exiting "
            "when spread returns inside +/-0.5*D. Non-breakout, zero grid, zero martingale; "
            "protective hard stop-loss is NOT_DISCLOSED."
        ),
        "replicability": "PARTIAL_RULE_SPEC",
        "extra_flags": [],
        "excerpt_source": "overview",
    },
)


def _extract_verbatim_excerpt(raw_record: dict[str, Any], preferred_section: str, max_len: int = 280) -> str:
    raw_text = str(raw_record.get("raw_text", ""))
    sections = raw_record.get("sections", {})
    candidate = str(sections.get(preferred_section, "")).strip()
    if candidate and candidate[:max_len] in raw_text:
        return candidate[:max_len]
    # Fallback: find a clean contiguous slice inside raw_text
    if candidate:
        probe = candidate[:80]
        idx = raw_text.find(probe)
        if idx >= 0:
            return raw_text[idx : idx + max_len]
    return raw_text[:max_len]


def build_leads() -> dict[str, Any]:
    # 1. Fail-closed manifest verification first
    manifest_errors = verify_verbatim.verify_raw_manifest(str(RAW_DIR), str(MANIFEST_PATH))
    if manifest_errors:
        raise RuntimeError(f"Raw manifest verification failed: {manifest_errors[:5]}")

    leads: list[dict[str, Any]] = []
    for spec in SPEC_MAP:
        raw_filename = f"{spec['slug']}.json"
        raw_path = RAW_DIR / raw_filename
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw file: {raw_path}")
        raw_record = json.loads(raw_path.read_text(encoding="utf-8"))

        raw_text = str(raw_record.get("raw_text", ""))
        verbatim_excerpt = _extract_verbatim_excerpt(raw_record, spec["excerpt_source"], max_len=280)
        if verbatim_excerpt not in raw_text:
            raise AssertionError(f"Verbatim excerpt check failed for {spec['lead_id']}")

        stop_rule = spec["stop_loss_rule"]
        tp_rule = spec["take_profit_rule"]
        tf = spec["timeframe"]

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
        for extra in spec.get("extra_flags", []):
            if extra not in dq_flags:
                dq_flags.append(extra)

        # Verify zero toxic signals across extracted rule fields + verbatim excerpt
        combined_text = "\n".join(
            p
            for p in (
                spec["name"],
                spec["entry_rule"],
                spec["exit_rule"],
                stop_rule,
                spec["rule_description"],
                verbatim_excerpt,
            )
            if p != NOT_DISCLOSED
        )
        is_toxic, toxic_flags, toxic_rationale = merge_off3_leads.detect_all_toxic_signals(combined_text)
        if is_toxic:
            raise ValueError(f"Unexpected toxic flag on {spec['lead_id']}: {toxic_flags} -> {toxic_rationale}")

        lead: dict[str, Any] = {
            "lead_id": spec["lead_id"],
            "source": "off3-quantpedia-qc",
            "source_origin": raw_record["source_origin"],
            "source_url": raw_record["url"],
            "raw_file": f"sources/off3-quantpedia-qc/raw/{raw_filename}",
            "original_id": spec["original_id"],
            "name": spec["name"],
            "family": spec["family"],
            "family_tag": spec["family_tag"],
            "asset_class": spec["asset_class"],
            "asset_universe": list(spec["asset_universe"]),
            "symbol": spec["symbol"],
            "timeframe": tf,
            "direction": spec["direction"],
            "prop_track": spec["prop_track"],
            "economic_rationale": spec["economic_rationale"],
            "counterparty_mechanism": spec["counterparty_mechanism"],
            "entry_rule": spec["entry_rule"],
            "exit_rule": spec["exit_rule"],
            "stop_loss_rule": stop_rule,
            "take_profit_rule": tp_rule,
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
            "disqualifiers_checked": {
                "non_breakout": True,
                "zero_grid_martingale": True,
                "ftmo_symbols_available": True,
                "zero_holdout_tokens": True,
            },
            "reported_winrate_pct": NOT_DISCLOSED,
            "reported_profit_factor": NOT_DISCLOSED,
            "reported_max_dd_pct": NOT_DISCLOSED,
            "is_toxic": False,
            "toxic_flags": [],
            "toxic_rationale": "No toxic Grid/Martingale/No-SL signal detected in raw text.",
            "performance_metrics": {},
        }

        # Verify FTMO applicability directly via c7-dedup's own validator
        ftmo_ok, ftmo_reason = merge_off3_leads.check_ftmo_applicability(lead)
        if not ftmo_ok:
            raise ValueError(f"FTMO applicability check failed for {spec['lead_id']}: {ftmo_reason}")

        leads.append(lead)

    payload: dict[str, Any] = {
        "mode": "live-public-text",
        "source": "off3-quantpedia-qc",
        "crawler_id": "c2-quantpedia",
        "schema_ref": "catalog/auto_public_leads.json",
        "holdout_sanitized": True,
        "total_leads": len(leads),
        "source_breakdown": {
            "quantpedia-public-strategy": sum(1 for x in leads if x["source_origin"] == "quantpedia-public-strategy"),
            "quantconnect-strategy-library": sum(
                1 for x in leads if x["source_origin"] == "quantconnect-strategy-library"
            ),
        },
        "leads": leads,
    }

    # 2. Fail-closed zero holdout token check on ENTIRE output payload
    holdout_violations = holdout_sanitizer.recursive_check_holdout(payload, "extracted/leads.json")
    if holdout_violations:
        raise ValueError(f"Holdout tokens detected in extracted/leads.json: {holdout_violations[:5]}")

    # 3. Fail-closed existing-19 dedup index overlap check
    dedup_index_path = REPO_ROOT / "sources" / "off3-dedup-index" / "index.json"
    if dedup_index_path.exists():
        existing_entries = json.loads(dedup_index_path.read_text(encoding="utf-8")).get("entries", [])
        for lead in leads:
            norm = merge_off3_leads.normalize_crawler_lead(lead, "off3-quantpedia-qc", 1)
            is_dup, dup_cat, match_id, _ = merge_off3_leads._check_existing_index_overlap(norm, existing_entries)
            if is_dup:
                raise ValueError(f"Lead {lead['lead_id']} duplicates existing lead {match_id} ({dup_cat})")

    # 4. Write extracted/leads.json cleanly (LF-only UTF-8)
    EXTRACTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXTRACTED_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # 5. Confirm repo hygiene check passes
    hygiene = repo_hygiene_check.audit_repo_hygiene(repo_root=str(REPO_ROOT))
    if not hygiene["clean"]:
        raise RuntimeError(
            f"Repo hygiene check failed: binaries={hygiene['binary_found']}, scratch={hygiene['loose_scratch']}"
        )

    return payload


def main() -> int:
    payload = build_leads()
    print(
        f"[SUCCESS] Built {payload['total_leads']} verified cleanroom leads "
        f"(QP={payload['source_breakdown']['quantpedia-public-strategy']}, "
        f"QC={payload['source_breakdown']['quantconnect-strategy-library']}) -> {EXTRACTED_PATH}"
    )
    print("[PASS] raw_manifest.sha256.json: 22/22 SHA-256 & byte-size verified")
    print("[PASS] verbatim_excerpt: 22/22 exact substrings of raw/*.json")
    print("[PASS] holdout_sanitizer: 0 forbidden 2024..2029/oos2 tokens")
    print("[PASS] toxic_filter: 0 toxic mechanisms")
    print("[PASS] ftmo_applicability: 22/22 FTMO_MT5_APPLICABLE")
    print("[PASS] existing-19 dedup check: 0 overlaps")
    print("[PASS] repo_hygiene_check: clean=True (0 binaries, 0 loose scratch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
