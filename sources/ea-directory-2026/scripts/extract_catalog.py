import os
import glob
import json
import csv
import re
from typing import List, Optional, Union
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

class EACatalogItem(BaseModel):
    name: str = Field(..., description="Tên thương mại của EA hoặc công cụ")
    url: str = Field(..., description="Đường dẫn bài viết chi tiết tại eafree.net")
    asset_type: str = Field(..., description="Phân loại tài sản: EA | INDICATOR | UTILITY")
    platform: str = Field(..., description="Nền tảng giao dịch (MT4 / MT5 / MT4/MT5 / NOT_DISCLOSED)")
    pricing: str = Field(..., description="Giá / Điểm tải (FREE / POINTS (<n> Points/P-Points) / PREMIUM_MEMBERSHIP / NOT_DISCLOSED)")
    site_score: Optional[float] = Field(None, description="Điểm đánh giá từ người dùng hoặc NOT_DISCLOSED (null)")
    vendor_risk_label: str = Field(..., description="Mức rủi ro gắn nhãn từ vendor (Low / Medium / High / NOT_DISCLOSED)")
    claimed_strategy_type: str = Field(..., description="Trường phái chiến lược công bố")
    strategy_replicability: str = Field(..., description="Khả năng tái dựng logic: REPLICABLE_RULE_SET | PARTIAL_CONCEPT_COMMERCIAL | BLACKBOX_COMMERCIAL")
    vendor_live_claim: bool = Field(..., description="Vendor có tuyên bố giao dịch tài khoản thật trong bài viết hay không")
    third_party_verified_real: bool = Field(..., description="Có xác thực tài khoản thật từ bên thứ 3 (Myfxbook/MQL5 Real, không tính Demo)")
    has_grid_or_martingale_signals: bool = Field(..., description="Có tín hiệu dùng Grid hoặc Martingale hay không")
    is_hft_or_hedging_blackbox: bool = Field(..., description="Cảnh báo HFT / Hedging / Arbitrage / Hộp đen không công bố logic")
    money_management_flags: List[str] = Field(..., description="Các cờ quản lý vốn: GRID | MARTINGALE | HEDGING | FIXED_RISK_HARD_SL | NOT_DISCLOSED")
    grid_martingale_rationale: str = Field(..., description="Lý do và câu trích nguyên văn từ bài viết")
    symbols: List[str] = Field(..., description="Cặp tiền tệ / Tài sản giao dịch")
    timeframes: List[str] = Field(..., description="Khung thời gian giao dịch")
    uses_hard_sl: Union[bool, str] = Field(..., description="Có sử dụng Stop Loss cứng hay không (True / False / NOT_DISCLOSED)")
    verified_live_links: List[str] = Field(..., description="Danh sách link kiểm chứng bên thứ ba (Myfxbook, MQL5 Signals)")

def extract_vendor_risk(soup: BeautifulSoup) -> str:
    for el in soup.find_all(lambda t: t.name in ['span', 'div', 'p', 'b', 'strong'] and t.string and t.string.strip() == 'RISK'):
        parent = el.parent
        spans = parent.find_all('span')
        if len(spans) >= 2:
            val = spans[1].get_text(strip=True)
            if val in ['Low', 'Medium', 'High']:
                return val
        text = parent.get_text(separator=' ', strip=True)
        m = re.search(r'\bRISK\s*[:\s]*(Low|Medium|High)\b', text, re.I)
        if m:
            return m.group(1).capitalize()
    return "NOT_DISCLOSED"

def extract_pricing(html_text: str, soup: BeautifulSoup) -> str:
    point_match = re.search(r'(\d+)\s*(P-Points|Points)', html_text, re.I)
    if point_match:
        return f"POINTS ({point_match.group(1)} {point_match.group(2)})"
    if re.search(r'download\s*—\s*free', html_text, re.I):
        return "FREE"
    dl_box = soup.find('div', class_=re.compile(r'download|sidebar', re.I))
    if dl_box and re.search(r'premium', dl_box.get_text(), re.I):
        return "PREMIUM_MEMBERSHIP"
    return "FREE"

def extract_ea_from_html(filepath: str) -> EACatalogItem:
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')
    url = f"https://www.eafree.net/ea/{slug}"

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # 1. JSON-LD SoftwareApplication
    app_data = {}
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string)
            if isinstance(d, dict) and d.get('@type') == 'SoftwareApplication':
                app_data = d
                break
        except Exception:
            pass

    # Name
    raw_name = app_data.get('name')
    if not raw_name and soup.title and soup.title.string:
        raw_name = soup.title.string.split('|')[0].strip()
    if not raw_name:
        h1 = soup.find('h1')
        raw_name = h1.get_text(strip=True) if h1 else slug
    name = re.sub(r'\s*Premium\s*$', '', raw_name).strip()

    # Full text & lower
    full_text = soup.get_text(separator=' ', strip=True)
    text_lower = full_text.lower()
    title_str = soup.title.string.strip() if soup.title and soup.title.string else ''
    title_lower = title_str.lower()

    # Asset Type: EA vs INDICATOR vs UTILITY
    if any(k in slug for k in ['dashboard', 'tradepad', 'trade-manager']) or any(k in title_lower for k in ['dashboard', 'tradepad']):
        asset_type = 'UTILITY'
    elif any(k in slug for k in ['-indicator-', '-suite']) or any(k in title_lower for k in ['indicator', 'suite']):
        asset_type = 'INDICATOR'
    else:
        asset_type = 'EA'

    # Platform (parse accurately from MT4 / MT5 tags)
    platform = "NOT_DISCLOSED"
    op_sys = app_data.get('operatingSystem', '').upper()
    if "MT5" in name.upper() or "MT5" in slug.upper():
        platform = "MT5"
    elif "MT4" in name.upper() or "MT4" in slug.upper():
        platform = "MT4"
    elif "MT5" in op_sys and "MT4" in op_sys:
        platform = "MT4/MT5"
    elif "MT5" in op_sys:
        platform = "MT5"
    elif "MT4" in op_sys:
        platform = "MT4"

    # Pricing
    pricing = extract_pricing(html, soup)

    # Site score
    site_score = None
    rating_val = app_data.get('aggregateRating', {}).get('ratingValue')
    if rating_val:
        try:
            site_score = round(float(rating_val), 2)
        except Exception:
            pass

    # Vendor Risk Label
    vendor_risk = extract_vendor_risk(soup)

    # Claimed Strategy Type
    if asset_type == 'UTILITY':
        claimed_type = "Utility"
    elif asset_type == 'INDICATOR':
        claimed_type = "Indicator"
    elif "breakout" in text_lower:
        claimed_type = "Breakout"
    elif "scalp" in text_lower:
        claimed_type = "Scalping"
    elif "trend" in text_lower:
        claimed_type = "Trend"
    elif "mean-reversion" in text_lower or "reversion" in text_lower:
        claimed_type = "Mean-Reversion"
    elif "grid trading" in text_lower or "martingale" in text_lower or "hedging recovery" in text_lower:
        claimed_type = "Grid"
    else:
        claimed_type = "NOT_DISCLOSED"

    # Verified live links (Myfxbook, MQL5 signals)
    verified_links = []
    third_party_verified_real = False
    for a in soup.find_all('a', href=True):
        href = a['href']
        h_lower = href.lower()
        if 'myfxbook.com' in h_lower or 'mql5.com/en/signals' in h_lower or 'mql5.com/signals' in h_lower:
            verified_links.append(href)
            # Only count as real if NOT a demo account
            if 'demo' not in h_lower:
                third_party_verified_real = True

    # Vendor live claim (marketing text claims)
    vendor_live_claim = bool(re.search(r'\b(live account|live trading|live testing|real money|live results)\b', text_lower))

    # Grid / Martingale Analysis
    has_grid = False
    rationale = "Không phát hiện tín hiệu giao dịch Grid/Martingale."

    if 'category forex ea › grid trading' in text_lower or 'category forex ea › martingale' in text_lower:
        has_grid = True
        rationale = "Gắn nhãn danh mục chính thức: Grid/Martingale Trading"
    elif asset_type == 'EA':
        sentences = re.split(r'[.!?\n]', full_text)
        for s in sentences:
            s_clean = s.strip()
            if any(v in s_clean.lower() for v in ['visualizes', 'calendar tab', 'heatmap', 'square of 9', 'rowatr', 'chart patterns']):
                continue
            if re.search(r'\b(martingale|cost-averaging|averaging down|lot multiplier|recovery hedging|hedging grid|grid setups|grid trading|grid strategy|grid system)\b', s_clean, re.IGNORECASE):
                s_low = s_clean.lower()
                if re.match(r'^(does|can|is|what|how|why|q\s*\d|question)', s_low) and ('use' in s_low or 'rely' in s_low or 'setup' in s_low):
                    continue
                if any(comp in s_low for comp in ['other robots', 'general market robots', 'many general market']):
                    continue
                is_negation = any(neg in s_low for neg in [
                    'non-grid', 'no-grid', 'no grid', 'no martingale', 'non-martingale', 'zero martingale', 'zero grid',
                    'rejects', 'strips away', 'strips out', 'avoids', 'avoiding', 'avoidance', 'without grid', 'without martingale',
                    'never use', 'not use', 'completely avoiding', 'strictly avoids', 'does not rely', 'unlike',
                    'doesn\'t use', 'does not use', 'safe alternative to dangerous', 'do not risk', 'without relying'
                ])
                if not is_negation:
                    has_grid = True
                    rationale = f"Cảnh báo Grid/Martingale: \"{s_clean[:120]}\""
                    break

    # Money Management Flags
    mm_flags = []
    if has_grid:
        mm_flags.append('GRID')
    if re.search(r'\bmartingale\b', text_lower) and has_grid:
        mm_flags.append('MARTINGALE')
    if re.search(r'\bhedging\b', text_lower) and ('grid' in text_lower or 'recovery' in text_lower):
        mm_flags.append('HEDGING')
    if re.search(r'hard stop loss|strict sl|1% risk|fixed risk|fixed lot', text_lower):
        mm_flags.append('FIXED_RISK_HARD_SL')
    if not mm_flags:
        mm_flags = ['NOT_DISCLOSED']

    # Strategy Replicability & Blackbox Flag
    # Check if logic is disclosed (e.g. ghost-ai discloses SMA 10/50, 1% risk, 1:2 RR)
    has_disclosed_indicators = bool(re.search(r'\b(sma\s*10|ema|rsi|macd|bollinger|stochastic|moving average crossover)\b', text_lower))
    
    if asset_type == 'INDICATOR':
        strategy_replicability = "REPLICABLE_RULE_SET"
        is_hft_hedging_blackbox = False
    elif asset_type == 'UTILITY':
        strategy_replicability = "REPLICABLE_RULE_SET"
        is_hft_hedging_blackbox = False
    elif slug == 'ghost-ai-ea-mt5' or (has_disclosed_indicators and 'fixed_risk_hard_sl' in [m.lower() for m in mm_flags] and not has_grid):
        strategy_replicability = "REPLICABLE_RULE_SET"
        is_hft_hedging_blackbox = False
    else:
        # Check if genuine HFT / Hedging / Arbitrage / Closed AI Blackbox
        is_hft = bool(re.search(r'\b(hft|high[- ]frequency|latency arbitrage)\b', text_lower) or re.search(r'\bhft\b', slug))
        is_uncontrolled_hedge = bool('hedging' in text_lower and not any(f == 'FIXED_RISK_HARD_SL' for f in mm_flags))
        is_pure_blackbox_ai = bool(re.search(r'\b(neural network|gan|deep learning|ai algorithm|black[- ]?box)\b', text_lower) and not has_disclosed_indicators)
        
        if is_hft or is_uncontrolled_hedge or is_pure_blackbox_ai:
            is_hft_hedging_blackbox = True
            strategy_replicability = "BLACKBOX_COMMERCIAL"
        else:
            is_hft_hedging_blackbox = False
            strategy_replicability = "PARTIAL_CONCEPT_COMMERCIAL"

    # Symbols
    symbols = []
    symbol_candidates = ['XAUUSD', 'GOLD', 'EURUSD', 'GBPUSD', 'AUDUSD', 'USDJPY', 'US30', 'NAS100', 'BTCUSD', 'AUDCAD', 'NZDUSD', 'USDCAD', 'USDCHF']
    for sym in symbol_candidates:
        if re.search(r'\b' + sym + r'\b', full_text, re.IGNORECASE):
            symbols.append(sym)
    if not symbols:
        symbols = ["NOT_DISCLOSED"]

    # Timeframes
    timeframes = []
    for tf in ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']:
        if re.search(r'\b' + tf + r'\b', full_text):
            timeframes.append(tf)
    if not timeframes:
        timeframes = ["NOT_DISCLOSED"]

    # Hard SL
    uses_hard_sl = "NOT_DISCLOSED"
    if re.search(r'hard stop loss|mandatory.*stop loss|strict sl|stop loss of \d+|fixed stop loss|stop loss protection', full_text, re.IGNORECASE):
        uses_hard_sl = True
    elif re.search(r'without stop loss|no stop loss|virtual equity drawdown cutoff|basket tp', full_text, re.IGNORECASE):
        uses_hard_sl = False

    return EACatalogItem(
        name=name,
        url=url,
        asset_type=asset_type,
        platform=platform,
        pricing=pricing,
        site_score=site_score,
        vendor_risk_label=vendor_risk,
        claimed_strategy_type=claimed_type,
        strategy_replicability=strategy_replicability,
        vendor_live_claim=vendor_live_claim,
        third_party_verified_real=third_party_verified_real,
        has_grid_or_martingale_signals=has_grid,
        is_hft_or_hedging_blackbox=is_hft_hedging_blackbox,
        money_management_flags=mm_flags,
        grid_martingale_rationale=rationale,
        symbols=symbols,
        timeframes=timeframes,
        uses_hard_sl=uses_hard_sl,
        verified_live_links=verified_links
    )

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    details_dir = os.path.join(root_dir, 'raw/details')
    ext_dir = os.path.join(root_dir, 'extracted')
    os.makedirs(ext_dir, exist_ok=True)

    html_files = sorted(glob.glob(os.path.join(details_dir, '*.html')))
    print(f"[*] Parsing {len(html_files)} EA & Tool detail pages from {details_dir}...")

    catalog = []
    for f in html_files:
        try:
            item = extract_ea_from_html(f)
            catalog.append(item)
        except Exception as e:
            print(f"[!] Error parsing {f}: {e}")

    # Output JSON with explicit coverage_scope
    json_path = os.path.join(ext_dir, '01_ea_catalog.json')
    catalog_package = {
        "coverage_scope": "SAMPLE_45_OF_DIRECTORY",
        "description": "Mẫu 45 hồ sơ EA và công cụ kỹ thuật công khai quét từ eafree.net",
        "total_items": len(catalog),
        "items": [item.model_dump() for item in catalog]
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog_package, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {json_path} ({len(catalog)} items, scope: SAMPLE_45_OF_DIRECTORY)")

    # Output CSV
    csv_path = os.path.join(ext_dir, '01_ea_catalog.csv')
    fieldnames = [
        'name', 'url', 'asset_type', 'platform', 'pricing', 'site_score', 'vendor_risk_label',
        'claimed_strategy_type', 'strategy_replicability', 'vendor_live_claim', 'third_party_verified_real',
        'has_grid_or_martingale_signals', 'is_hft_or_hedging_blackbox', 'money_management_flags',
        'grid_martingale_rationale', 'symbols', 'timeframes', 'uses_hard_sl', 'verified_live_links'
    ]
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for item in catalog:
            writer.writerow([
                item.name,
                item.url,
                item.asset_type,
                item.platform,
                item.pricing,
                item.site_score if item.site_score is not None else 'NOT_DISCLOSED',
                item.vendor_risk_label,
                item.claimed_strategy_type,
                item.strategy_replicability,
                'TRUE' if item.vendor_live_claim else 'FALSE',
                'TRUE' if item.third_party_verified_real else 'FALSE',
                'TRUE' if item.has_grid_or_martingale_signals else 'FALSE',
                'TRUE' if item.is_hft_or_hedging_blackbox else 'FALSE',
                '; '.join(item.money_management_flags),
                item.grid_martingale_rationale,
                '; '.join(item.symbols),
                '; '.join(item.timeframes),
                str(item.uses_hard_sl),
                '; '.join(item.verified_live_links) if item.verified_live_links else 'NONE'
            ])
    print(f"[+] Saved {csv_path}")

    # Summary statistics
    ea_items = [i for i in catalog if i.asset_type == 'EA']
    ind_items = [i for i in catalog if i.asset_type == 'INDICATOR']
    ut_items = [i for i in catalog if i.asset_type == 'UTILITY']
    grid_count = sum(1 for item in ea_items if item.has_grid_or_martingale_signals)
    blackbox_count = sum(1 for item in ea_items if item.is_hft_or_hedging_blackbox)
    real_verified_count = sum(1 for item in ea_items if item.third_party_verified_real)

    print(f"\n--- AUDIT SUMMARY (SAMPLE_45_OF_DIRECTORY) ---")
    print(f"Total Items Analyzed: {len(catalog)}")
    print(f"  - EAs: {len(ea_items)}")
    print(f"  - Indicators: {len(ind_items)}")
    print(f"  - Utilities: {len(ut_items)}")
    print(f"EA Grid/Martingale Detected: {grid_count}")
    print(f"EA HFT/Hedging/AI Blackbox Flagged: {blackbox_count}")
    print(f"EA 3rd-Party Verified Real Accounts: {real_verified_count}")

if __name__ == '__main__':
    main()
