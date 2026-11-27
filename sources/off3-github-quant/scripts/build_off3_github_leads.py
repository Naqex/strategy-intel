"""Cleanroom GitHub Quant Strategy Crawler & Deterministic Extractor (off3-github-quant).

Operates strictly inside D:/ANNAM/strategy-intel/sources/off3-github-quant/:
  - Fetches pure-text public GitHub files (.md, .py, .ipynb text cells) via GitHub API.
  - Enforces fail-closed binary URL & payload blocking (zero .ex4/.ex5/.mq4/.mq5/.dll/.zip).
  - Writes verbatim raw snapshots to raw/<slug>.json + SHA-256 manifest to raw_manifest.sha256.json.
  - Deterministically extracts 22 genuine, non-breakout, FTMO-28-applicable white-box strategy
    specifications to extracted/leads.json matching catalog/auto_public_leads.json + c7-dedup fields.
  - Zero hallucination (NOT_DISCLOSED for every undisclosed parameter/metric).
  - Zero 2024..2029 / oos2 holdout tokens in extracted/leads.json.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import urllib.parse

SOURCE_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
ROOT_DIR = SOURCE_DIR.parents[1]
RAW_DIR = SOURCE_DIR / "raw"
EXTRACTED_DIR = SOURCE_DIR / "extracted"
MANIFEST_PATH = SOURCE_DIR / "raw_manifest.sha256.json"
LEADS_PATH = EXTRACTED_DIR / "leads.json"

for _p in (str(ROOT_DIR / "scripts"), str(ROOT_DIR / "scripts" / "common")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import auto_intel_ingest  # noqa: E402
import holdout_sanitizer  # noqa: E402
import verify_verbatim  # noqa: E402

NOT_DISCLOSED = "NOT_DISCLOSED"
SOURCE_ID = "off3-github-quant"
MAX_FILE_TEXT_CHARS = 65_000


SPECS: tuple[dict[str, Any], ...] = (
    # ------------------------------------------------------------------
    # BUCKET A: Cointegration / Pairs Trading & Kalman / OU Mean Reversion
    # ------------------------------------------------------------------
    {
        "slug": "gh-01-davysnou-pairs-ou-zscore-hard-sl",
        "original_id": "OFF3-GH-01",
        "github_repo": "davysnou/pairs-trading-simulator",
        "primary_file": "methodology.md",
        "extra_files": ["README.md"],
        "name": "Gold/Silver & WTI/Brent OU Cointegration Z-Score Pairs with Hard Tail-Risk Stop",
        "family": "Cointegration & Pairs Mean Reversion",
        "family_tag": "STAT_ARB_PAIRS_COINTEGRATION",
        "asset_class": "CFD_METALS_ENERGY_PAIRS",
        "asset_universe": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
        "symbol": "XAUUSD/XAGUSD, USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Verify spread stationarity via rolling Augmented Dickey-Fuller (ADF p < 0.05) on "
            "S_t = P_B,t - beta * P_A,t; compute rolling spread Z-score Z_t = (S_t - mean_w) / std_w; "
            "enter long spread when Z_t <= -2.0 and short spread when Z_t >= +2.0."
        ),
        "exit_rule": "Close spread position when rolling Z_t reverts and crosses 0.0.",
        "stop_loss_rule": "Hard tail-risk liquidation at |Z_t| >= 3.5 to protect against structural regime breaks.",
        "take_profit_rule": "Mean reversion target at Z_t = 0.0.",
        "economic_rationale": (
            "Structurally linked commodity pairs (Gold vs Silver, WTI vs Brent crude) share common macro "
            "and physical-market equilibrium drivers so spread residuals follow a stationary discrete-time "
            "Ornstein-Uhlenbeck process with estimable half-life t_1/2 = ln(2)/theta, unlike mere short-term "
            "return correlation which can drift permanently."
        ),
        "counterparty_mechanism": (
            "Short-horizon liquidity and inventory imbalances push one leg away from long-run cointegrated "
            "parity; relative-value arbitrageurs absorb the dislocation until equilibrium restores."
        ),
        "rule_description": (
            "Cointegrated commodity pairs (XAUUSD/XAGUSD and USOIL/UKOIL) gated by rolling ADF p < 0.05; "
            "long spread at Z <= -2.0, short spread at Z >= +2.0, mean-reversion exit at Z = 0.0, mandatory "
            "hard tail-risk stop-loss at |Z| >= 3.5 with per-leg bps slippage/commission; zero grid, zero martingale."
        ),
        "excerpt_anchor": "## 3. Signal Generation & Risk Management",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-02-adichauhan10-kalman-hmm-pairs-audnzd-wtibrent",
        "original_id": "OFF3-GH-02",
        "github_repo": "adichauhan10/stat-arb-pairs-trading",
        "primary_file": "notebooks/04_signal_generation.ipynb",
        "extra_files": ["README.md"],
        "name": "Walk-Forward Kalman Filter + Causal HMM Calm-Regime Pairs (AUD/NZD & WTI/Brent)",
        "family": "Cointegration & Pairs Mean Reversion",
        "family_tag": "STAT_ARB_KALMAN_HMM_PAIRS",
        "asset_class": "CFD_FX_ENERGY_PAIRS",
        "asset_universe": ["AUDUSD", "NZDUSD", "USOIL", "UKOIL"],
        "symbol": "AUDUSD/NZDUSD, USOIL/UKOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Screen pair via Engle-Granger/Johansen cointegration; estimate causal time-varying hedge ratio "
            "via Kalman filter; compute 20-day rolling Z-score of Kalman spread; require causal filtered "
            "Gaussian HMM calm-regime probability > 0.5; enter long spread when z < -2.0 or short when z > +2.0."
        ),
        "exit_rule": "Take profit when spread reverts to |z| < 0.5, or exit at max holding period of 60 trading days.",
        "stop_loss_rule": (
            "Hard divergence stop-loss when |z| > 4.0 persists for 5 consecutive trading days, plus 60-trading-day "
            "maximum holding period backstop and volatility-targeted/fractional-Kelly position sizing."
        ),
        "take_profit_rule": "Spread reversion target at |z| < 0.5.",
        "economic_rationale": (
            "AUD/NZD (commodity-bloc FX) and WTI/Brent (global crude oil grades) exhibit time-varying hedge "
            "ratios and regime shifts; combining a causal Kalman filter with a causal filtered (non-smoothed) "
            "HMM gates out turbulent divergence regimes before entering mean-reversion trades."
        ),
        "counterparty_mechanism": (
            "Transitory regional supply/demand and central-bank flow divergences create temporary spread "
            "dislocations during calm regimes that revert as cross-market hedgers rebalance."
        ),
        "rule_description": (
            "Walk-forward AUDUSD/NZDUSD and USOIL/UKOIL pairs using a causal Kalman hedge ratio, 20-day "
            "rolling Z-score, and causal filtered HMM calm-state gate (calm_prob > 0.5): enter at |z| > 2.0, "
            "exit at |z| < 0.5, hard divergence stop at |z| > 4.0 for 5 consecutive days and 60-day max hold; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "ENTRY_Z, EXIT_Z, STOP_Z, STOP_CONSEC_DAYS, MAX_HOLD, REGIME_THRESH = 2.0, 0.5, 4.0, 5, 60, 0.5",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-03-quantlandi-fx7-engle-granger-pairs",
        "original_id": "OFF3-GH-03",
        "github_repo": "QuantLandi/fx-cointegration",
        "primary_file": "scripts/02_backtest.py",
        "extra_files": ["README.md"],
        "name": "7-USD-Cross Rolling Engle-Granger Cointegration Pairs Filter (257d/21d Walk-Forward)",
        "family": "Cointegration & Pairs Mean Reversion",
        "family_tag": "STAT_ARB_FX_COINTEGRATION",
        "asset_class": "CFD_FX",
        "asset_universe": ["AUDUSD", "USDCAD", "USDCHF", "EURUSD", "GBPUSD", "USDJPY", "NZDUSD"],
        "symbol": "EURUSD/USDCHF/GBPUSD/AUDUSD/NZDUSD/USDCAD/USDJPY",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Across all 21 undirected pairs formed from 7 major USD crosses, run a 257-day training / 21-day "
            "out-of-sample rolling window: verify both log-price levels are I(1) (ADF p > 0.05), fit OLS on "
            "both orientations, require residual ADF p <= 0.05 (keeping the more negative ADF orientation), "
            "standardize OOS spread with training mean/std, and apply a 2-day execution lag: long spread (+1) "
            "when z < -threshold, short (-1) when z > +threshold (z in {1.0, 2.0, 3.0})."
        ),
        "exit_rule": "Return to flat (0) when |z| falls back within threshold or when the 21-day window fails the EG gate.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Testing whether an explicit rolling Engle-Granger tradability filter improves G10 FX spread "
            "mean-reversion over unconditional OLS pairs across 21 major currency pairs under realistic "
            "round-trip basis-point transaction costs and 3% target-vol scaling."
        ),
        "counterparty_mechanism": (
            "Cross-border capital flows and monetary-policy expectation shocks temporarily dislocate "
            "shared-factor G10 currency baskets (e.g., EUR/CHF, AUD/NZD) before macro parity reasserts."
        ),
        "rule_description": (
            "Walk-forward 257-day train / 21-day test Engle-Granger tradability filter across 21 pairs of 7 "
            "USD majors (AUD, CAD, CHF, EUR, GBP, JPY, NZD): requires I(1) legs (ADF p > 0.05) and OLS "
            "residual ADF p <= 0.05, trades Z-score thresholds {1, 2, 3} with a strict 2-day execution lag "
            "and {0,1,2,5} bp round-trip cost grid; explicit hard stop-loss is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "def engle_granger_detail(",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-04-sharathstack-kalman-hurst-fx-statarb",
        "original_id": "OFF3-GH-04",
        "github_repo": "sharathStack/Statistical-Arbitrage-Pairs-Trading-Engine",
        "primary_file": "config.py",
        "extra_files": ["README.md"],
        "name": "Multi-Pair 2-State Kalman Filter + Hurst Regime-Gated FX Stat-Arb Engine",
        "family": "Cointegration & Pairs Mean Reversion",
        "family_tag": "STAT_ARB_KALMAN_HURST",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"],
        "symbol": "EURUSD/GBPUSD, AUDUSD/NZDUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Screen pairs via |Pearson rho| >= 0.55, Engle-Granger ADF p <= 0.10, and OU half-life in "
            "[1, 120] days; track dynamic hedge ratio beta(t) via 2-state Kalman Filter (delta=5e-5, R=0.001, "
            "warmup=100 bars); confirm mean-reverting regime with 60-bar Hurst exponent < 0.50; enforce "
            "portfolio cap of max 4 concurrent pairs with spread-spread correlation <= 0.65."
        ),
        "exit_rule": "Close spread on mean reversion at Z_EXIT = 0.50 or at MAX_HOLDING = 60 bars.",
        "stop_loss_rule": "Hard Z-score stop-loss at Z_STOP = 4.00 plus MAX_HOLDING = 60 bars time stop.",
        "take_profit_rule": "Mean reversion take-profit at Z_EXIT = 0.50.",
        "economic_rationale": (
            "Combining cointegration screening, adaptive Kalman hedge tracking, Hurst-exponent mean-reversion "
            "filtering (< 0.50), and a cross-spread correlation cap (<= 0.65) prevents overlapping FX risk "
            "concentration while cutting structural breakdowns at Z = 4.0."
        ),
        "counterparty_mechanism": (
            "Correlated regional FX pairs (EUR/GBP, AUD/NZD) mean-revert during low-Hurst anti-persistent "
            "regimes when temporary local macro flows overshoot relative equilibrium."
        ),
        "rule_description": (
            "Multi-pair FX stat-arb (EURUSD/GBPUSD, AUDUSD/NZDUSD) combining EG cointegration (p <= 0.10, "
            "half-life 1-120d), 2-state Kalman hedge ratio (delta=5e-5, R=0.001), 60-bar Hurst < 0.50 regime "
            "filter, Z_EXIT=0.50, hard Z_STOP=4.00, MAX_HOLDING=60 bars, max 4 pairs with cross-corr <= 0.65; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "# ── Ornstein-Uhlenbeck / Entry-Exit",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-05-sbaijal-ou-mle-kbe-optimal-stopping-pairs",
        "original_id": "OFF3-GH-05",
        "github_repo": "sbaijal/pairs-trading-optimal-threshold",
        "primary_file": "engine.py",
        "extra_files": ["optimal_threshold.py", "README.md"],
        "name": "Continuous-Time Ornstein-Uhlenbeck MLE Optimal-Stopping Pairs Trading (KBE Thresholds)",
        "family": "Cointegration & Pairs Mean Reversion",
        "family_tag": "STAT_ARB_OU_OPTIMAL_STOPPING",
        "asset_class": "CFD_INDICES_METALS_PAIRS",
        "asset_universe": ["US500", "US30", "US100", "XAUUSD", "XAGUSD"],
        "symbol": "US500/US30, US500/US100, XAUUSD/XAGUSD",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Every 21 trading days on a 252-day rolling training window, fit OLS spread X(t) = P_A - alpha - "
            "beta*P_B, estimate Ornstein-Uhlenbeck parameters (theta, mu, sigma, sigma_eq) via MLE, require "
            "half-life in [3, 90] days, solve the Kolmogorov Backward Equation (KBE) numerically for optimal "
            "entry_long and entry_short thresholds; go long spread when X < entry_long, short when X > entry_short."
        ),
        "exit_rule": "Exit long spread when spread >= mu (exit_level); exit short spread when spread <= mu.",
        "stop_loss_rule": "Hard equilibrium-sigma stop-loss at mu - 3.5 * sigma_eq (long) and mu + 3.5 * sigma_eq (short).",
        "take_profit_rule": "Exit at OU equilibrium mean mu.",
        "economic_rationale": (
            "Heuristic +/-2 sigma bands ignore mean-reversion speed (theta), diffusion volatility (sigma), "
            "and transaction costs; solving the continuous-time OU optimal-stopping KBE maximizes expected "
            "profit per unit time and adapts entry thresholds dynamically to each cointegrated index/metal pair."
        ),
        "counterparty_mechanism": (
            "Arbitrage friction and holding-cost tradeoffs leave predictable temporary spread deviations "
            "between co-moving benchmarks (e.g., US500/US30 or Gold/Silver) until reversion to equilibrium mu."
        ),
        "rule_description": (
            "Walk-forward (252d train, 21d retrain) OU-MLE pairs engine solving the Kolmogorov Backward "
            "Equation for optimal entry thresholds (half-life gated 3-90 days) with equilibrium exit at mu "
            "and mandatory hard stop-loss at mu +/- 3.5 * sigma_eq (demonstrated on equities, directly "
            "applicable to cointegrated US500/US30 and XAUUSD/XAGUSD spreads); zero grid, zero martingale."
        ),
        "excerpt_anchor": "class SignalGenerator:",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-06-shubham-kalman-gold-silver-rotation",
        "original_id": "OFF3-GH-06",
        "github_repo": "Shubhamkumartrichy/Quant_Commodity_Rotation",
        "primary_file": "Strategy.py",
        "extra_files": ["README.md"],
        "name": "Kalman Filter Dynamic Beta Gold/Silver Relative-Strength Rotation",
        "family": "Precious Metals Intermarket Rotation",
        "family_tag": "METALS_KALMAN_ROTATION",
        "asset_class": "CFD_METALS",
        "asset_universe": ["XAUUSD", "XAGUSD"],
        "symbol": "XAUUSD/XAGUSD",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Estimate causal time-varying hedge ratio beta_t of Gold (GLD/XAUUSD) vs Silver (SLV/XAGUSD) "
            "via recursive 1D Kalman Filter (process noise delta=1e-4, measurement noise R=1e-3); smooth "
            "beta with 6-day SMA (beta_smooth) and 21-day SMA of beta_smooth (beta_trend); apply 1-day "
            "causal shift: allocate long Gold when beta_smooth > beta_trend, else long Silver."
        ),
        "exit_rule": "Rotate between XAUUSD and XAGUSD whenever smoothed Kalman beta crosses its 21-day trend SMA.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Gold behaves defensively during risk-off/real-rate drops while Silver carries higher industrial "
            "beta during reflation; tracking the state-space Kalman beta captures persistent precious-metal "
            "leadership shifts rather than fighting structural ratio trends."
        ),
        "counterparty_mechanism": (
            "Slow institutional macro rotation between monetary safe-haven demand (Gold) and cyclical "
            "industrial-metal flows (Silver) creates serial autocorrelation in the Gold/Silver beta."
        ),
        "rule_description": (
            "Causal daily Gold/Silver (XAUUSD/XAGUSD) relative-strength rotation: recursive Kalman filter "
            "(delta=1e-4, R=1e-3) tracks dynamic Gold-on-Silver beta; when 6-day SMA of beta exceeds its "
            "21-day SMA (shifted 1 day), hold Gold, otherwise hold Silver; hard stop-loss is NOT_DISCLOSED; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "class KalmanHedge:",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # ------------------------------------------------------------------
    # BUCKET B: Cross-Sectional FX & Commodity TSMOM / XSMOM & Carry
    # ------------------------------------------------------------------
    {
        "slug": "gh-07-pysystemtrade-ewmac-carry-vol-target",
        "original_id": "OFF3-GH-07",
        "github_repo": "pst-group/pysystemtrade",
        "primary_file": "systems/provided/rules/ewmac.py",
        "extra_files": ["systems/provided/rules/carry.py"],
        "name": "Rob Carver Volatility-Standardized EWMAC & 90-Day Smoothed Carry Multi-Asset Rules",
        "family": "Systematic Trend & Carry (Non-Breakout)",
        "family_tag": "MULTI_ASSET_EWMAC_CARRY",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": [
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "USOIL", "US500", "GER40", "UK100", "JP225"
        ],
        "symbol": "EURUSD/GBPUSD/USDJPY/AUDUSD/XAUUSD/USOIL/US500/GER40/UK100/JP225",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Compute volatility-standardized Exponentially Weighted Moving Average Crossover forecast "
            "ewmac = (EWMA(price, Lfast) - EWMA(price, Lslow)) / robust_vol_calc(price) (e.g., Lfast=32, "
            "Lslow=128) blended with smoothed carry forecast carry = raw_carry.ewm(90).mean() and relative "
            "carry (instrument smoothed carry minus asset-class median carry); scale forecasts to average |10| "
            "and cap at +/-20."
        ),
        "exit_rule": (
            "Continuous position rebalancing as volatility-standardized EWMAC + Carry combined forecast "
            "decays or flips sign (zero fixed breakout box)."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Normalizing EWMA trend crossovers by realized price volatility prevents high-volatility assets "
            "from dominating risk, while blending carry provides a negatively correlated positive-yield "
            "return stream across FX, commodities, and equity index futures."
        ),
        "counterparty_mechanism": (
            "Central-bank policy cycles, commercial hedging roll-yield, and slow institutional trend "
            "rebalancing generate multi-week drift and persistent carry risk premia across liquid futures/FX."
        ),
        "rule_description": (
            "Open-source Rob Carver pysystemtrade non-breakout rules: volatility-normalized EWMAC "
            "(Lfast=32, Lslow=128 over robust_vol_calc) combined with 90-day EWMA smoothed carry and "
            "asset-class relative carry on daily bars across FX, indices, gold, and oil; explicit hard "
            "stop-loss is NOT_DISCLOSED (uses continuous volatility-targeted sizing); zero grid, zero martingale."
        ),
        "excerpt_anchor": "def ewmac_forecast_with_defaults(",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-08-albanbreart-g10-fx-xsmom-carry-fm",
        "original_id": "OFF3-GH-08",
        "github_repo": "albanbreart/fx-factor-strategies",
        "primary_file": "fx_factor_project.py",
        "extra_files": ["README.md"],
        "name": "G10 Currency Cross-Sectional Carry, 12M Momentum & Fama-MacBeth Conditional MV",
        "family": "Cross-Sectional FX Factors",
        "family_tag": "FX_XSMOM_CARRY_FM",
        "asset_class": "CFD_FX",
        "asset_universe": ["AUDUSD", "USDCAD", "EURUSD", "GBPUSD", "USDJPY", "NZDUSD"],
        "symbol": "AUDUSD/USDCAD/EURUSD/GBPUSD/USDJPY/NZDUSD",
        "timeframe": "MN1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "On month-end closes across 6 G10 currencies vs USD (AUD, CAD, EUR, GBP, JPY, NZD), compute "
            "monthly interest-rate differential dr_t and 12-month spot momentum mom_t = S_t / S_{t-12} - 1; "
            "form rank-centered cross-sectional weights (CS-CARRY, CS-MOM), equal sign weights (TS-CARRY, "
            "TS-MOM, DOLLAR-CARRY), or Fama-MacBeth conditional mean-variance weights w_t = k_t * Sigma_t^-1 "
            "* mu_FM_t using EWMA covariance (lambda=0.97) scaled to 10% annualized target volatility (1-month lag)."
        ),
        "exit_rule": "Monthly rebalance at month-end close applying lagged formation-month weights to t+1 excess returns.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Individual G10 currencies show near-zero standalone drift, whereas cross-sectional interest-rate "
            "carry and Fama-MacBeth conditional expected-return forecasts weighted by inverse EWMA covariance "
            "harvest persistent multi-currency factor premia."
        ),
        "counterparty_mechanism": (
            "Forward-bias (violation of uncovered interest parity) caused by commercial hedgers and central-"
            "bank reserve flows pays liquidity providers holding high-carry vs low-carry funding currencies."
        ),
        "rule_description": (
            "G10 FX factor framework on AUD, CAD, EUR, GBP, JPY, NZD vs USD: constructs dollar-neutral "
            "rank-weighted CS-CARRY/CS-MOM, sign-weighted TS-CARRY/TS-MOM/DOLLAR-CARRY, and causal "
            "Fama-MacBeth conditional mean-variance portfolios with EWMA covariance (lambda=0.97) scaled to "
            "10% annual volatility; hard stop-loss is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "def fama_macbeth(",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-09-gabsmm18-fx-carry-3m-tsmom-crash-filter",
        "original_id": "OFF3-GH-09",
        "github_repo": "gabsmm18/FX-carry-crash-insurance",
        "primary_file": "src/strategy.py",
        "extra_files": ["README.md"],
        "name": "3-Month Time-Series Momentum Crash-Insurance Filter on G10 FX Carry",
        "family": "Cross-Sectional FX Factors",
        "family_tag": "FX_CARRY_MOMENTUM_FILTER",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"],
        "symbol": "EURUSD/GBPUSD/USDJPY/USDCHF/AUDUSD/NZDUSD/USDCAD",
        "timeframe": "MN1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Rank G10 currencies by 3-month interbank rate differential vs USD at month-end; form base carry "
            "weights (+1/3 long top 3 high-yielders, -1/3 short bottom 3 funding currencies); compute trailing "
            "3-month cumulative excess return mom_3m; retain each leg ONLY when mom_3m agrees in sign with "
            "the carry leg (long & mom > 0, short & mom < 0), else flatten leg to 0; scale portfolio with "
            "24-month rolling realized vol to 10% target vol capped at 3.0x leverage (1-month lag)."
        ),
        "exit_rule": "Immediately flatten any carry leg at month-end when trailing 3-month momentum opposes the carry sign.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Unconditional FX carry suffers negative skewness during sudden risk-off deleveraging; gating "
            "each carry leg with a 3-month time-series momentum filter cuts exposure during acute carry "
            "unwinds (reducing left-tail crash skewness) at explicit 3 bps turnover cost."
        ),
        "counterparty_mechanism": (
            "Crowded leveraged carry trades unwind violently when global risk aversion spikes, creating "
            "short-to-medium-horizon downside momentum in high-yield currencies that a 3M TSMOM gate exits."
        ),
        "rule_description": (
            "G10 FX carry-plus-momentum crash-insurance filter: long top-3 / short bottom-3 yielding G10 "
            "currencies (+/-1/3 weight), gated by trailing 3-month excess return sign agreement (opposing legs "
            "set to flat), with lagged 24M rolling volatility targeting (10% annual vol, max 3.0x leverage) "
            "and 3 bps turnover cost; intramonth hard SL is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "def momentum_filter(",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-10-gehlotmanthan-tsmom-garch11-vol-target",
        "original_id": "OFF3-GH-10",
        "github_repo": "gehlotmanthan/aqr-tsmom-replication",
        "primary_file": "src/tsmom/signals.py",
        "extra_files": ["src/tsmom/volatility.py", "README.md"],
        "name": "Cross-Asset 12-Month Time-Series Momentum with Walk-Forward GARCH(1,1) Vol Scaling",
        "family": "Cross-Asset Time-Series Momentum",
        "family_tag": "MULTI_ASSET_TSMOM_GARCH",
        "asset_class": "CFD_MULTI_ASSET",
        "asset_universe": [
            "US500", "GER40", "UK100", "JP225", "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "USOIL"
        ],
        "symbol": "US500/GER40/UK100/JP225/EURUSD/GBPUSD/USDJPY/XAUUSD/USOIL",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "For each futures/CFD asset across equity indices, FX, and commodities, compound trailing "
            "12-month excess returns and take lagged directional sign (+1 long, -1 short); size inversely "
            "to causal lagged 60-day center-of-mass EWMA daily volatility forecast or walk-forward GARCH(1,1) "
            "conditional volatility forecast to maintain constant risk contribution across regimes."
        ),
        "exit_rule": "Rebalance monthly at month-end whenever 12-month excess return sign flips or GARCH volatility changes.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Replicates Moskowitz, Ooi & Pedersen (2012) cross-asset TSMOM across currencies, commodities, "
            "and equity indices while replacing static EWMA variance with a causal walk-forward GARCH(1,1) "
            "volatility overlay that reacts faster to volatility clustering."
        ),
        "counterparty_mechanism": (
            "Under-reaction to macro fundamentals and gradual institutional hedging across asset classes "
            "produces 1-to-12-month return autocorrelation that scales cleanly when normalized by GARCH vol."
        ),
        "rule_description": (
            "Multi-asset 12-month time-series momentum (sign of lagged 12M compounded excess return) across "
            "FX, equity indices, and commodities with causal 60-day EWMA and walk-forward GARCH(1,1) "
            "inverse-volatility targeting (monthly rebalance); intramonth hard stop-loss is NOT_DISCLOSED; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "def time_series_momentum_signal(",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # ------------------------------------------------------------------
    # BUCKET C: Intraday Calendar / Fixing / Session Microstructure Flows
    # ------------------------------------------------------------------
    {
        "slug": "gh-11-billnye67-usdjpy-gotobi-tokyo-fix-short",
        "original_id": "OFF3-GH-11",
        "github_repo": "billnye67/tradedeck",
        "primary_file": "specs/hunt14-usdjpy-gotobi-fix.py",
        "extra_files": [],
        "name": "USDJPY Conditional Gotobi Payment-Day Post-Tokyo-Fix (09:55 JST) Short with Hourly ATR Stop",
        "family": "Intraday FX Fixing & Calendar Flow",
        "family_tag": "FX_TOKYO_GOTOBI_FIX",
        "asset_class": "CFD_FX",
        "asset_universe": ["USDJPY"],
        "symbol": "USDJPY",
        "timeframe": "M1",
        "direction": "Short",
        "prop_track": "INTRADAY_SWAP0",
        "entry_rule": (
            "On Japanese Gotobi settlement days (5th, 10th, 15th, 20th, 25th, and 30th/month-end rolled "
            "backward across weekends and Japanese bank holidays; Mondays excluded), verify USDJPY drifted "
            "higher into the fix (mid at 09:00 JST > mid at 03:00 JST); sell USDJPY at bid at 09:55 JST "
            "(00:55 UTC) sized to 0.5% account equity risk."
        ),
        "exit_rule": "Time exit closing at ask at 12:00 JST (03:00 UTC) (grid-tested 11:00/12:00/13:00 JST), swap=0 intraday.",
        "stop_loss_rule": (
            "Hard protective stop-loss at entry + 3.0 * ATR(14, 1H) (hourly Wilder ATR up to 09:00 JST; "
            "grid-tested m in {2, 3, 4}), evaluated minute-by-minute against ask high."
        ),
        "take_profit_rule": "Fixed time-stop exit at 12:00 JST (no fixed price TP cap).",
        "economic_rationale": (
            "Japanese corporate importers settle invoices on Gotobi dates (multiples of 5), prompting Tokyo "
            "banks to accumulate USD ahead of the 09:55 JST benchmark fixing; once fixing demand clears "
            "after an already-positive 03:00-09:00 JST run-up, USDJPY exhibits post-fix mean reversion."
        ),
        "counterparty_mechanism": (
            "Price-insensitive corporate importer USD buying before 09:55 JST forces dealers long inventory "
            "that unwinds systematically between 09:55 and 12:00 JST once benchmark orders complete."
        ),
        "rule_description": (
            "Intraday swap=0 USDJPY M1 Gotobi Tokyo-fix reversal: on non-Monday holiday-adjusted Gotobi "
            "dates where 09:00 JST mid > 03:00 JST mid, short USDJPY at 09:55 JST with hard stop at "
            "entry + 3.0 * ATR(14, 1H), 0.5% equity risk sizing, and hard time exit at 12:00 JST; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "def hourly_atr(df):",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-12-ichir0roie-month-end-london-1600-fix-usd",
        "original_id": "OFF3-GH-12",
        "github_repo": "ichir0roie/FXTradeSimu",
        "primary_file": "fxsim/research/calendar_effects.py",
        "extra_files": [],
        "name": "Month-End WM/Reuters 16:00 London Fix DST-Aware 7-Pair USD Contrarian Rebalancing",
        "family": "Intraday FX Fixing & Calendar Flow",
        "family_tag": "FX_LONDON_1600_WMR_FIX",
        "asset_class": "CFD_FX",
        "asset_universe": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"],
        "symbol": "EURUSD/GBPUSD/AUDUSD/NZDUSD/USDJPY/USDCHF/USDCAD",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "entry_rule": (
            "Identify the last weekday of each month and resolve 16:00 Europe/London DST-aware UTC hour "
            "(15:00 UTC in BST summer, 16:00 UTC in GMT winter); measure month-to-date equal-weighted 7-pair "
            "USD basket log-change from prior month-end pre-fix level; trade the 1-hour pre-fix window "
            "(fix_hour-1 to fix_hour) or 1-hour post-fix reversal window (fix_hour to fix_hour+1) against "
            "month-to-date USD direction (-sign(mtd)) across all 7 USD majors using bid/ask spread costs."
        ),
        "exit_rule": "Close flat exactly 1 hour later (at 16:00 London for pre-fix leg, or 17:00 London for post-fix leg).",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Global passive equity/bond funds hedge foreign-currency exposures at the month-end 16:00 London "
            "WM/Reuters fixing benchmark, generating predictable institutional USD rebalancing flows into "
            "and immediately reversing after the fixing window."
        ),
        "counterparty_mechanism": (
            "Benchmark-tracking asset managers execute mandatory month-end FX hedge adjustments at 16:00 "
            "London regardless of short-term price impact, paying liquidity providers for inventory absorption."
        ),
        "rule_description": (
            "DST-aware (Europe/London) month-end 16:00 WM/Reuters London fix strategy across 7 USD majors "
            "(EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD): trades contrarian to month-to-date "
            "USD basket move (-sign(mtd)) across the 1-hour pre-fix or 1-hour post-fix window on H1 bars "
            "with spread costs; explicit hard SL is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "USD_PAIRS = {",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-13-dukotah-apex-causal-turn-of-month-index",
        "original_id": "OFF3-GH-13",
        "github_repo": "Dukotah/apex-quant",
        "primary_file": "apex/strategy/library/turn_of_month.py",
        "extra_files": [],
        "name": "Causal Calendar-Day Proxy Turn-of-Month Equity Index Strategy (With Hard Stop)",
        "family": "Calendar & Seasonal Anomaly",
        "family_tag": "INDEX_TURN_OF_MONTH_CAUSAL",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "US100", "US30", "GER40"],
        "symbol": "US500/US100/US30/GER40",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Avoid look-ahead trading-day counting via a pure deterministic calendar-day proxy: emit BUY "
            "signal on equity index risk sleeve (SPY / US500) on daily close when bar.timestamp.day >= 24 "
            "OR bar.timestamp.day <= 3 (stateless, idempotent, zero pyramiding)."
        ),
        "exit_rule": "Exit long equity index position to flat/cash on first daily close where 4 <= day <= 23.",
        "stop_loss_rule": "Explicit hard protective stop-loss at entry * (1 - stop_loss_pct) with default stop_loss_pct = 0.08 (8%).",
        "take_profit_rule": "Calendar window exit after day 3 of the new month.",
        "economic_rationale": (
            "Ariel (1987) and McConnell & Xu (2008) document concentrated equity index returns across month "
            "boundaries driven by recurring institutional cash flows (payroll, 401k, pension contributions, "
            "fund rebalances); using day >= 24 or day <= 3 removes month-length look-ahead bias."
        ),
        "counterparty_mechanism": (
            "Automated month-end institutional inflows and dividend reinvestments create recurring passive "
            "equity index buying pressure orthogonal to price-trend and momentum signals."
        ),
        "rule_description": (
            "Causal zero-lookahead equity index Turn-of-Month calendar strategy (US500/US100/US30/GER40): "
            "enter long when calendar day >= 24 or day <= 3, exit flat outside window, with explicit hard "
            "protective stop-loss (default 8%, stop_loss_pct=0.08), never pyramids; zero grid, zero martingale."
        ),
        "excerpt_anchor": "This implementation uses a DETERMINISTIC CALENDAR-DAY PROXY:",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    # ------------------------------------------------------------------
    # BUCKET D: Volatility-Regime Switching & Volatility-Managed Exposure
    # ------------------------------------------------------------------
    {
        "slug": "gh-14-uchenna-hmm-vix-regime-rotation",
        "original_id": "OFF3-GH-14",
        "github_repo": "I-am-Uchenna/regime-allocation-strategy",
        "primary_file": "regime_allocation_strategy.py",
        "extra_files": ["README.md"],
        "name": "2-State Gaussian HMM VIX-Change Volatility Regime Rotation (Index vs Gold)",
        "family": "Volatility-Regime Switching",
        "family_tag": "REGIME_HMM_VOLATILITY",
        "asset_class": "CFD_INDICES_METALS",
        "asset_universe": ["US500", "XAUUSD"],
        "symbol": "US500/XAUUSD",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Fit a 2-state Gaussian Hidden Markov Model (covariance_type='full') on daily VIX changes "
            "(Delta_VIX = VIX_t - VIX_{t-1}), sorting states by mean into State 0 (Low Vol / declining or "
            "stable VIX = risk-on) and State 1 (High Vol / rising VIX = risk-off); apply a strict 1-day "
            "execution lag so yesterday's inferred regime allocates today's capital to Risk-On equity index "
            "(US500/SPY) in State 0 or Safe-Haven (XAUUSD/GLD/defensive) in State 1."
        ),
        "exit_rule": "Rotate out of US500 into safe-haven gold/cash on the next bar after HMM state transitions from 0 to 1.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Equity implied volatility clusters in persistent latent regimes; switching dynamically from "
            "equities into safe-haven assets when a Gaussian HMM flags rising-VIX stress avoids deep equity "
            "drawdowns while capturing low-vol equity drift (note: rolling/expanding HMM fit required in live "
            "to eliminate full-sample parameter estimation bias noted by the author)."
        ),
        "counterparty_mechanism": (
            "Institutional flight-to-quality and risk-parity deleveraging during volatility spikes drive "
            "persistent negative equity-vs-safe-haven correlation across multi-day stress episodes."
        ),
        "rule_description": (
            "2-state Gaussian HMM fitted to daily VIX changes separating Low-Vol risk-on vs High-Vol "
            "risk-off regimes with a 1-day execution lag, rotating between US500 equity exposure and XAUUSD "
            "safe-haven defense (author explicitly notes rolling HMM estimation needed to prevent full-sample "
            "fit bias); explicit hard stop-loss is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "ALLOCATION LOGIC:",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-15-dantsai-moreira-muir-vol-managed-index",
        "original_id": "OFF3-GH-15",
        "github_repo": "DanTsai0903/market-index-future-management-with-risk-forecast",
        "primary_file": "Strategy.md",
        "extra_files": ["README.md"],
        "name": "Moreira-Muir Inverse-Variance Volatility-Managed Equity Index Futures Strategy",
        "family": "Volatility-Managed Exposure",
        "family_tag": "VOL_MANAGED_INVERSE_VARIANCE",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "US100", "US30"],
        "symbol": "US500/US100/US30",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "On the first trading day of each month, forecast monthly market variance sigma_hat_t^2 using "
            "VIX ((VIX/100)^2 / 12) or 21-day trailing realized variance of daily excess returns; set "
            "index futures exposure leverage l_t = min(c / sigma_hat_t^2, 3.0) where constant c is calibrated "
            "strictly causally by aligning t+1 returns with t variance over trailing 10 years."
        ),
        "exit_rule": "Rebalance index futures position size on the first trading day of each month (cutting size when variance spikes).",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Moreira & Muir (2017, Journal of Finance) show that realized variance is highly persistent "
            "while short-horizon expected equity returns do not rise proportionally with variance, so "
            "scaling equity index exposure inversely to variance improves Sharpe and cuts crisis drawdowns."
        ),
        "counterparty_mechanism": (
            "Leverage-constrained and volatility-shocked institutions experience forced selling in high-"
            "variance regimes, creating asymmetric downside risk that inverse-variance sizing sidesteps."
        ),
        "rule_description": (
            "Causal implementation of Moreira & Muir (2017) volatility-managed equity index futures "
            "(US500 /MES): forecasts monthly variance from VIX or 21-day realized variance and sets monthly "
            "target leverage w = c / sigma_hat^2 (capped at 3.0x), scaling down during high-vol stress and "
            "up in calm regimes; hard intramonth stop-loss is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "## III. Strategy Methodology",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-16-markbogorad-tarch11-fx-carry-switch",
        "original_id": "OFF3-GH-16",
        "github_repo": "markbogorad/CarryTrade",
        "primary_file": "README.md",
        "extra_files": [],
        "name": "TARCH(1,1) Asymmetric GARCH Volatility Dual-Layer On-Off Switch for G10 FX Carry",
        "family": "Volatility-Regime Switching",
        "family_tag": "REGIME_TARCH_FX_CARRY",
        "asset_class": "CFD_FX",
        "asset_universe": [
            "AUDJPY", "NZDJPY", "EURJPY", "GBPJPY", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"
        ],
        "symbol": "AUDJPY/NZDJPY/EURJPY/GBPJPY/EURUSD/GBPUSD/USDJPY/AUDUSD/NZDUSD/USDCAD/USDCHF",
        "timeframe": "MN1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Fit an asymmetric Threshold ARCH / TARCH(1,1) conditional volatility model (selected via "
            "Diebold-Mariano forecast testing) on G10 currency portfolio returns; activate Pairwise or "
            "High-Minus-Low (HML) G10 FX carry positions only when both forecasted TARCH(1,1) volatility and "
            "realized FX volatility remain below the dual-layer risk-on switch threshold."
        ),
        "exit_rule": "Switch G10 FX carry exposure OFF (flat to cash) whenever the dual-layer TARCH/realized volatility indicator breaches stress bounds.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "FX carry crashes exhibit asymmetric volatility clustering where negative carry shocks raise "
            "subsequent variance more than positive shocks; an asymmetric TARCH(1,1) dual-layer on-off "
            "switch (modeled on institutional FX desk switches) preserves carry yield in calm states while "
            "de-risking during volatility spikes."
        ),
        "counterparty_mechanism": (
            "Leveraged carry unwinds propagate across G10 JPY and commodity-FX crosses with asymmetric "
            "downside volatility persistence detectable by TARCH(1,1) state updates."
        ),
        "rule_description": (
            "G10 FX carry trade enhanced with an asymmetric TARCH(1,1) conditional volatility model and "
            "dual-layer forecasted + realized volatility on-off switch (evaluated on Pairwise and HML G10 "
            "portfolios); exact numerical switch cutoff and intramonth hard SL are NOT_DISCLOSED in README; "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "Key contributions include:",
        "replicability": "PARTIAL_RULE_SPEC",
    },
    # ------------------------------------------------------------------
    # BUCKET E: Index Overnight/Intraday Seasonality & Pullback Reversion
    # ------------------------------------------------------------------
    {
        "slug": "gh-17-vrd07-midweek-tuesday-index-overnight-drift",
        "original_id": "OFF3-GH-17",
        "github_repo": "vrd07/Quant_Trading",
        "primary_file": "src/strategies/index_overnight_strategy.py",
        "extra_files": [],
        "name": "Midweek Tuesday Cash-Close Overnight Drift on Index CFDs with Daily ATR Hard Stop",
        "family": "Index Overnight Seasonality",
        "family_tag": "INDEX_OVERNIGHT_DRIFT_CFD",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US30", "US100", "GER40"],
        "symbol": "US30/US100/GER40",
        "timeframe": "M5",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "On the first completed Tuesday M5 bar at/after 19:45 UTC (near US cash close; one-trade-per-"
            "week ISO latch), buy US30 / US100 / GER40 at market to capture the Tuesday-close to Wednesday-"
            "open overnight drift while paying CFD overnight financing only once per week."
        ),
        "exit_rule": "Exit via risk-layer time stop (~1050 minutes, flat around Wednesday 13:30 UTC cash open); breakeven lock disabled.",
        "stop_loss_rule": (
            "Hard catastrophe stop-loss at entry_close - 1.5 * ATR(14, completed daily bars), excluding "
            "today's partial daily bar for strict causality."
        ),
        "take_profit_rule": "No fixed price TP cap; exits on ~1050-minute Wednesday cash-open time stop.",
        "economic_rationale": (
            "Equity indices earn a disproportionate share of positive returns overnight (cash close to next "
            "cash open), but holding every night is eroded by CFD overnight financing; concentrating to the "
            "midweek Tuesday-night hold pays only 1 night/week of swap while preserving overnight drift."
        ),
        "counterparty_mechanism": (
            "Intraday equity dealers and risk-constrained retail/institutional participants shed overnight "
            "gap risk into the US cash close, transferring a positive overnight risk premium to holders."
        ),
        "rule_description": (
            "CFD-financing-aware midweek equity index overnight drift (US30/US100/GER40, M5 bars): one trade "
            "per week, buy market on first completed Tuesday bar >= 19:45 UTC with causal hard stop at "
            "close - 1.5 * ATR(14, completed D1 bars) and Wednesday ~13:30 UTC time-stop exit (~1050 min); "
            "zero grid, zero martingale."
        ),
        "excerpt_anchor": "class IndexOvernightStrategy(BaseStrategy):",
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
    {
        "slug": "gh-18-quantconnect-lean-global-equity-ibs-reversion",
        "original_id": "OFF3-GH-18",
        "github_repo": "QuantConnect/Lean",
        "primary_file": "Algorithm.Python/Alphas/GlobalEquityMeanReversionIBSAlpha.py",
        "extra_files": [],
        "name": "Global Equity Index Internal Bar Strength (IBS) Cross-Sectional Daily Mean Reversion",
        "family": "Index Short-Term Mean Reversion",
        "family_tag": "INDEX_IBS_MEAN_REVERSION",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "US100", "US30", "GER40", "UK100", "JP225"],
        "symbol": "US500/US100/US30/GER40/UK100/JP225",
        "timeframe": "D1",
        "direction": "Both",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "At each daily close across global equity indices (Lean benchmark tracks SPY, QQQ, EWG/GER40, "
            "EWU/UK100, EWJ/JP225 and global country indices), compute Internal Bar Strength "
            "IBS = (Close - Low) / (High - Low) whenever Open * (High - Low) != 0; rank cross-sectionally, "
            "go LONG the lowest-IBS (most oversold near daily low) indices and SHORT the highest-IBS (most "
            "overbought near daily high) indices equally weighted for a 1-day lookback prediction horizon."
        ),
        "exit_rule": "1-day holding horizon rebalance at next daily close based on refreshed IBS cross-sectional ranks.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": NOT_DISCLOSED,
        "economic_rationale": (
            "Kakushadze & Serur (151 Trading Strategies) and QuantConnect Benchmark Alpha demonstrate "
            "strong 1-day mean reversion in equity indices closing near their intraday extremes (IBS near 0 "
            "rebounds next day; IBS near 1 mean-reverts)."
        ),
        "counterparty_mechanism": (
            "End-of-day liquidity imbalances, stop runs, and leveraged ETF rebalancing push index closes "
            "toward session highs/lows that revert during the next trading cycle."
        ),
        "rule_description": (
            "Official Apache-2.0 QuantConnect/Lean cross-sectional Internal Bar Strength mean reversion "
            "across global equity indices (US500, US100, GER40, UK100, JP225 equivalents): computes "
            "IBS = (Close - Low) / (High - Low) on D1 bars, longs lowest-IBS oversold indices and shorts "
            "highest-IBS overbought indices for a 1-day horizon (NullRiskManagementModel in benchmark, so "
            "hard stop-loss is NOT_DISCLOSED); zero grid, zero martingale."
        ),
        "excerpt_anchor": "class MeanReversionIBSAlphaModel(AlphaModel):",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-19-handiko-connors-rsi2-sma200-pullback",
        "original_id": "OFF3-GH-19",
        "github_repo": "handiko/RSI-2-Portfolio-Trading-Strategy-Backtester",
        "primary_file": "README.md",
        "extra_files": [],
        "name": "Connors 2-Period RSI Short-Term Oversold Pullback Above 200-Day SMA",
        "family": "Trend-Filtered Pullback Mean Reversion",
        "family_tag": "INDEX_CONNORS_RSI2_PULLBACK",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "US100", "US30"],
        "symbol": "US500/US100/US30",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Evaluate on daily closes across liquid equity index/portfolio tickers: require structural "
            "uptrend Close > SMA(200) AND short-term oversold pullback RSI(2) < 10; initiate equal-capital "
            "long position (strictly non-breakout dip-buying inside an established uptrend)."
        ),
        "exit_rule": "Exit long position on daily close when current Close > previous day's High.",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": "Exit when daily Close exceeds prior day's High.",
        "economic_rationale": (
            "Short-term sharp 1-to-2-day selloffs inside a secular uptrend (above 200-day SMA) reflect "
            "temporary liquidity panics and weak-hand capitulation rather than structural trend reversals, "
            "generating high-winrate snaps back above the prior day's high."
        ),
        "counterparty_mechanism": (
            "Short-term momentum stop-outs and leveraged washouts during bull trends transfer equity "
            "inventory at steep discounts to patient mean-reversion buyers."
        ),
        "rule_description": (
            "Connors RSI(2) daily pullback mean-reversion strategy (applicable to US500/US100/US30): enter "
            "long when daily Close > 200-day SMA and 2-period RSI < 10; exit when current Close > prior day's "
            "High; explicit hard stop-loss is NOT_DISCLOSED in the repo; zero grid, zero martingale."
        ),
        "excerpt_anchor": "* Trading Logic:",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-20-open-alpha-lab-turnaround-tuesday-index",
        "original_id": "OFF3-GH-20",
        "github_repo": "Guillain-RDCDE/Open-Alpha-Lab",
        "primary_file": "studies/642-turnaround-tuesday/turnaround_tuesday/strategy.py",
        "extra_files": [],
        "name": "Causal Down-Monday Conditional Turnaround Tuesday Equity Index Reversal",
        "family": "Calendar & Seasonal Anomaly",
        "family_tag": "INDEX_TURNAROUND_TUESDAY",
        "asset_class": "CFD_INDICES",
        "asset_universe": ["US500", "US30", "GER40"],
        "symbol": "US500/US30/GER40",
        "timeframe": "D1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Pair consecutive trading sessions where weekday == Tuesday (1) AND previous trading session "
            "weekday == Monday (0) (automatically excluding post-Monday-holiday Tuesdays); enter long "
            "equity index (SPY / US500) at Monday close strictly when Monday's close-to-close return < 0 "
            "(100% causal: Monday's close flag is known at Monday close)."
        ),
        "exit_rule": "Exit long position at Tuesday close (1-session hold, 2x one-way bps cost charged).",
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": "Fixed 1-session exit at Tuesday close.",
        "economic_rationale": (
            "Weekend news accumulation and Monday institutional margin/rebalancing selling create "
            "Monday-specific downward overshoots that mean-revert on Tuesday; the repo explicitly tests "
            "Monday-specificity against all other weekday down-day pairs and random-pair placebos."
        ),
        "counterparty_mechanism": (
            "Retail/institutional weekend-news liquidation and margin calls peak on down Mondays, allowing "
            "contrarian liquidity providers entering at Monday close to capture Tuesday stabilization."
        ),
        "rule_description": (
            "Zero-lookahead equity index Turnaround Tuesday reversal (US500/US30/GER40, distinct from XAUUSD): "
            "require adjacent Monday->Tuesday trading sessions (skipping Monday holidays), buy at Monday close "
            "if Monday return < 0, exit at Tuesday close with round-trip bps friction; hard intraday SL is "
            "NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "def monday_tuesday_pairs(df: pd.DataFrame) -> pd.DataFrame:",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    # ------------------------------------------------------------------
    # BUCKET F: Oil & Gold Macro-Event / Intermarket Reactions
    # ------------------------------------------------------------------
    {
        "slug": "gh-21-mustafa-high-vix-pre-fomc-drift",
        "original_id": "OFF3-GH-21",
        "github_repo": "mustafa-waqar98/pre-FOMC-drift",
        "primary_file": "docs/PRE_ANALYSIS_PLAN.md",
        "extra_files": ["README.md"],
        "name": "High-VIX Conditional Pre-FOMC 24-Hour Announcement Drift (16:00 ET to 13:45 ET)",
        "family": "Macro-Event Scheduled Drift",
        "family_tag": "MACRO_PRE_FOMC_DRIFT",
        "asset_class": "CFD_INDICES_METALS",
        "asset_universe": ["US500", "XAUUSD"],
        "symbol": "US500/XAUUSD",
        "timeframe": "M1",
        "direction": "Long",
        "prop_track": "FTMO_SWING",
        "entry_rule": (
            "Restrict to scheduled FOMC announcement days (excluding unscheduled meetings and half-days); "
            "evaluate state variable = VIX close lagged 5 trading days before the meeting; when lagged "
            "VIX > 15.07 (pre-registered anxious-regime median threshold), enter long S&P 500 E-mini "
            "(US500; cross-market macro drift also relevant to XAUUSD) at 16:00 ET close of the prior valid session."
        ),
        "exit_rule": (
            "Mandatory pre-announcement flat exit at 13:45 ET on FOMC day — a strict 15-minute safety "
            "buffer BEFORE the 14:00 ET policy statement (avoids binary news-release whip)."
        ),
        "stop_loss_rule": NOT_DISCLOSED,
        "take_profit_rule": "Fixed pre-announcement time exit at 13:45 ET (15 minutes prior to 14:00 ET FOMC release).",
        "economic_rationale": (
            "Lucca & Moench (2015) document large equity risk premia accruing in the 24 hours preceding "
            "scheduled FOMC decisions as macroeconomic uncertainty resolves; conditioning on elevated "
            "1-week-lagged VIX (> 15.07) isolates high-uncertainty meetings while exiting 15 minutes before "
            "the release respects prop-firm news-event restrictions."
        ),
        "counterparty_mechanism": (
            "Risk-averse institutions hedge or reduce exposure ahead of uncertain FOMC meetings and rebuild "
            "positions as pre-announcement uncertainty subsides prior to 13:45 ET."
        ),
        "rule_description": (
            "Pre-registered Lucca-Moench conditional Pre-FOMC drift on M1 US500 (extendable to XAUUSD): "
            "on scheduled FOMC days when 5-day-lagged VIX > 15.07, enter long at 16:00 ET of the prior "
            "session and exit strictly flat at 13:45 ET (15 min before the 14:00 ET FOMC release); price "
            "stop-loss is NOT_DISCLOSED; zero grid, zero martingale."
        ),
        "excerpt_anchor": "## State variable",
        "replicability": "CONCEPT_ONLY_NEEDS_SLTP_DESIGN",
    },
    {
        "slug": "gh-22-natecode880-wti-sarimax-dxy-vix-atr",
        "original_id": "OFF3-GH-22",
        "github_repo": "natecode880/wti-oil-trading",
        "primary_file": "models/arimax_forecast.py",
        "extra_files": ["backtests/backtest_engine.py", "README.md"],
        "name": "WTI Crude Oil Hybrid Macro-Technical SARIMAX (DXY & VIX) Strategy with Intrabar ATR SL/TP",
        "family": "Energy Macro-Technical Regime",
        "family_tag": "OIL_SARIMAX_MACRO_REGIME",
        "asset_class": "CFD_ENERGY",
        "asset_universe": ["USOIL", "UKOIL"],
        "symbol": "USOIL/UKOIL",
        "timeframe": "H1",
        "direction": "Both",
        "prop_track": "INTRADAY_SWAP0",
        "entry_rule": (
            "On 1-hour WTI crude oil (USOIL) bars, fit a strictly causal rolling SARIMAX model on [t-window, "
            "t-1] using lagged macro exogenous returns ['DXY_ret_l1', 'DXY_ret_l2', 'VIX_ret_l1', "
            "'VIX_ret_l2', 'VIX_ret_l6'] to generate macro directional bias; require alignment with a "
            "200-period moving average structural trend filter, ATR-percentile volatility regime filter, "
            "high-liquidity time-of-day window, and base technical trigger; enter next bar open with "
            "spread + slippage and volatility-targeted sizing (1% risk target, max 3.0x leverage)."
        ),
        "exit_rule": "Exit on intrabar ATR take-profit, ATR stop-loss (conservative stop-first tie-breaking), or max_hold_bars time stop.",
        "stop_loss_rule": (
            "Mandatory intrabar ATR-based (atr_sl_mult * ATR) or swing-based hard stop-loss with "
            "conservative stop-first tie-break if SL and TP hit in the same bar, plus optional max_hold_bars."
        ),
        "take_profit_rule": "Intrabar ATR-based take-profit (atr_tp_mult * ATR) or fixed-point target.",
        "economic_rationale": (
            "Crude oil prices respond tightly to US Dollar strength (DXY) and global risk aversion (VIX); "
            "combining causal lagged-DXY/VIX SARIMAX regime forecasts with MA200 trend, ATR-percentile "
            "volatility filtering, and liquid-session execution avoids low-quality oil chop."
        ),
        "counterparty_mechanism": (
            "Cross-asset macro funds transmit USD and equity-volatility shocks into energy futures with "
            "1-to-6-hour intraday lags, creating tradable macro-aligned flows during liquid WTI sessions."
        ),
        "rule_description": (
            "H1 WTI Crude Oil (USOIL/UKOIL) hybrid macro-technical strategy: causal rolling SARIMAX with "
            "lagged DXY and VIX return exogenous features sets directional bias, filtered by MA200 trend, "
            "ATR-percentile volatility regime, and high-liquidity hours; executed next-bar open with spread/"
            "slippage, 1% risk / vol-targeted sizing (max 3x leverage), intrabar ATR hard stop-loss and "
            "take-profit (conservative stop-first tie-breaking), and max_hold_bars; zero grid, zero martingale."
        ),
        "excerpt_anchor": 'exog_cols = ["DXY_ret_l1", "DXY_ret_l2", "VIX_ret_l1", "VIX_ret_l2", "VIX_ret_l6"]',
        "replicability": "REPLICABLE_FROM_PUBLIC",
    },
)


def _gh_api_json(endpoint: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api failed ({proc.returncode}) for {endpoint}: {proc.stderr.strip()[:240]}")
    return json.loads(proc.stdout)


def _decode_github_file(repo: str, path: str) -> tuple[str, str, str]:
    """Fetch a pure-text GitHub file via API, enforcing binary/extension blockers fail-closed."""
    quoted = urllib.parse.quote(path)
    meta = _gh_api_json(f"repos/{repo}/contents/{quoted}")
    html_url = str(meta.get("html_url") or f"https://github.com/{repo}/blob/main/{path}")
    download_url = str(meta.get("download_url") or html_url)

    # Fail-closed URL extension check (blocks .ex4/.ex5/.mq4/.mq5/.dll/.zip etc.)
    auto_intel_ingest.validate_safe_public_url(html_url)
    auto_intel_ingest.validate_safe_public_url(download_url)

    raw_bytes = base64.b64decode(meta["content"])
    if path.lower().endswith(".ipynb"):
        # Parse Jupyter notebook JSON and extract ONLY pure text markdown & code cells (strip base64 image outputs)
        nb = json.loads(raw_bytes.decode("utf-8", errors="replace"))
        blocks: list[str] = []
        for idx, cell in enumerate(nb.get("cells", [])):
            ctype = cell.get("cell_type", "unknown")
            if ctype in ("markdown", "code"):
                src = "".join(cell.get("source", []))
                blocks.append(f"### CELL {idx} ({ctype})\n{src}")
        text = "\n\n".join(blocks)
        text = auto_intel_ingest.validate_text_payload(
            text.encode("utf-8")[: auto_intel_ingest.MAX_TEXT_BYTES],
            content_type="text/plain",
            filename_hint=path,
        )
    else:
        text = auto_intel_ingest.validate_text_payload(
            raw_bytes[: auto_intel_ingest.MAX_TEXT_BYTES],
            content_type="text/plain",
            filename_hint=path,
        )

    return html_url, download_url, text[:MAX_FILE_TEXT_CHARS]


def _sha256_upper(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _extract_clean_verbatim_excerpt(raw_text: str, anchor: str, max_len: int = 320) -> str:
    """Return an exact verbatim substring from raw_text near anchor with ZERO holdout tokens."""
    idx = raw_text.find(anchor)
    if idx == -1:
        raise ValueError(f"Verbatim anchor not found in raw_text: {anchor!r}")
    snippet = raw_text[idx : idx + max_len]
    # Normalize only trailing half-line cut cleanly while preserving exact substring of raw_text
    if len(snippet) == max_len:
        last_nl = snippet.rfind("\n")
        if last_nl > 120:
            snippet = snippet[:last_nl]
    snippet = snippet.strip()
    if snippet not in raw_text:
        raise ValueError("Extracted verbatim_excerpt is not an exact substring of raw_text!")
    if holdout_sanitizer.FORBIDDEN_TOKEN_PATTERN.search(snippet):
        raise ValueError(f"Verbatim excerpt contains forbidden holdout token (2024..2029/oos2): {snippet!r}")
    return snippet


def fetch_raw_snapshots() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        repo = spec["github_repo"]
        repo_meta = _gh_api_json(f"repos/{repo}")
        default_branch = str(repo_meta.get("default_branch") or "main")
        stars = int(repo_meta.get("stargazers_count") or 0)
        lic_obj = repo_meta.get("license")
        license_spdx = str(lic_obj.get("spdx_id")) if isinstance(lic_obj, dict) and lic_obj.get("spdx_id") else NOT_DISCLOSED

        file_paths = [spec["primary_file"], *spec.get("extra_files", [])]
        fetched_files: list[dict[str, Any]] = []
        primary_url = f"https://github.com/{repo}"
        combined_chunks: list[str] = []

        for f_idx, fpath in enumerate(file_paths):
            html_url, download_url, text = _decode_github_file(repo, fpath)
            if f_idx == 0:
                primary_url = html_url
            fetched_files.append(
                {
                    "path": fpath,
                    "html_url": html_url,
                    "download_url": download_url,
                    "chars": len(text),
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest().upper(),
                }
            )
            combined_chunks.append(f"=== FILE: {repo}/{fpath} ===\n{text}")

        raw_payload = {
            "slug": spec["slug"],
            "original_id": spec["original_id"],
            "source_name": "github-public-repo",
            "github_repo": repo,
            "github_branch": default_branch,
            "github_stars": stars,
            "github_license": license_spdx,
            "repo_description": str(repo_meta.get("description") or NOT_DISCLOSED),
            "url": primary_url,
            "fetched_files": fetched_files,
            "raw_text": "\n\n".join(combined_chunks),
        }
        _write_json(RAW_DIR / f"{spec['slug']}.json", raw_payload)
        print(f"[FETCHED] {spec['original_id']} | {repo} ({stars}*, {license_spdx}) -> raw/{spec['slug']}.json")

    return len(SPECS)


def write_manifest() -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for p in sorted(RAW_DIR.iterdir()):
        if p.is_file():
            manifest[p.name] = {
                "sha256": _sha256_upper(p),
                "size": p.stat().st_size,
            }
    _write_json(MANIFEST_PATH, manifest)
    errs = verify_verbatim.verify_raw_manifest(str(RAW_DIR), str(MANIFEST_PATH))
    if errs:
        raise RuntimeError(f"Raw manifest verification failed: {errs}")
    return manifest


def extract_leads() -> dict[str, Any]:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    leads: list[dict[str, Any]] = []

    for spec in SPECS:
        raw_filename = f"{spec['slug']}.json"
        raw_path = RAW_DIR / raw_filename
        if not raw_path.exists():
            raise FileNotFoundError(f"Missing raw file: {raw_path}. Run with --fetch first.")
        raw_rec = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_text = str(raw_rec.get("raw_text") or "")

        verbatim_excerpt = _extract_clean_verbatim_excerpt(raw_text, spec["excerpt_anchor"])

        # Independent toxic audit on all extracted strategy fields
        combined_text = "\n".join(
            p
            for p in (
                spec["name"],
                spec["entry_rule"],
                spec["exit_rule"],
                spec["stop_loss_rule"],
                spec["rule_description"],
                verbatim_excerpt,
            )
            if p != NOT_DISCLOSED
        )
        is_toxic, toxic_flags, toxic_rationale = auto_intel_ingest.detect_toxic_signals(combined_text)
        if is_toxic:
            raise ValueError(f"Spec {spec['original_id']} tripped toxic detector: {toxic_flags} | {toxic_rationale}")

        dq_flags = [
            "AUTO_INGESTED_UNTRUSTED_PUBLIC_SPEC",
            "UNVERIFIED_EXTERNAL_CLAIM",
            "MISSING_PF_AND_DD_NOT_DISCLOSED",
        ]
        if spec["stop_loss_rule"] == NOT_DISCLOSED:
            dq_flags.append("STOP_LOSS_RULE_NOT_DISCLOSED")
        if spec["take_profit_rule"] == NOT_DISCLOSED:
            dq_flags.append("TAKE_PROFIT_RULE_NOT_DISCLOSED")
        if spec["timeframe"] == NOT_DISCLOSED:
            dq_flags.append("TIMEFRAME_NOT_DISCLOSED")

        lead = {
            "lead_id": f"LEAD-{spec['original_id']}",
            "source": SOURCE_ID,
            "source_origin": "github-public-repo",
            "source_url": str(raw_rec["url"]),
            "raw_file": f"sources/{SOURCE_ID}/raw/{raw_filename}",
            "original_id": spec["original_id"],
            "github_repo": str(raw_rec["github_repo"]),
            "github_license": str(raw_rec["github_license"]),
            "github_stars": int(raw_rec["github_stars"]),
            "name": spec["name"],
            "family": spec["family"],
            "family_tag": spec["family_tag"],
            "asset_class": spec["asset_class"],
            "asset_universe": list(spec["asset_universe"]),
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
                "OFFENSIVE3_CLEANROOM_SPEC_QUARANTINED: source claim only, pending independent Dev M1 Bid/Ask verification"
            ),
            "verified_live_links": [],
            "disqualifiers_checked": [
                "non_breakout_verified",
                "zero_grid_verified",
                "zero_martingale_verified",
                "zero_hft_arbitrage_verified",
                "zero_repaint_lookahead_verified",
                "zero_binary_mq5_verified",
                "ftmo_28_universe_verified",
            ],
            "reported_winrate_pct": NOT_DISCLOSED,
            "reported_profit_factor": NOT_DISCLOSED,
            "reported_max_dd_pct": NOT_DISCLOSED,
            "is_toxic": False,
            "toxic_flags": [],
            "toxic_rationale": toxic_rationale,
            "performance_metrics": {},
        }
        leads.append(lead)

    output = {
        "schema_version": "off3-github-quant-v1",
        "mode": "live-github-public-text",
        "source": SOURCE_ID,
        "total_leads": len(leads),
        "leads": leads,
    }

    # Fail-closed Holdout token audit on ENTIRE extracted/leads.json
    holdout_violations = holdout_sanitizer.recursive_check_holdout(output, "extracted/leads.json")
    if holdout_violations:
        raise ValueError(f"Holdout token violation in extracted/leads.json: {holdout_violations[:5]}")

    _write_json(LEADS_PATH, output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch fresh verbatim text snapshots from GitHub API")
    parser.add_argument("--extract-only", action="store_true", help="Extract leads deterministically from existing raw/")
    args = parser.parse_args(argv)

    if args.fetch or not args.extract_only:
        n_raw = fetch_raw_snapshots()
        print(f"[+] Fetched {n_raw} verbatim GitHub snapshots into {RAW_DIR}")

    manifest = write_manifest()
    print(f"[+] Verified raw_manifest.sha256.json ({len(manifest)}/{len(manifest)} SHA-256 PASS)")

    out = extract_leads()
    print(f"[+] Extracted {out['total_leads']} clean non-breakout GitHub leads into {LEADS_PATH} (0 holdout leaks, 0 toxic)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
