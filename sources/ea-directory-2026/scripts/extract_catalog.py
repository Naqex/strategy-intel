import os
import glob
import json
import csv
import re
from typing import List, Optional, Union
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

class EACatalogItem(BaseModel):
    name: str = Field(..., description="Tên thương mại của EA")
    url: str = Field(..., description="Đường dẫn bài viết chi tiết tại eafree.net")
    platform: str = Field(..., description="Nền tảng giao dịch (MT4 / MT5 / MT4/MT5 / NOT_DISCLOSED)")
    pricing: str = Field(..., description="Giá / Hình thức cấp phép (Free / Paid / Freemium)")
    site_score: Optional[float] = Field(None, description="Điểm đánh giá từ người dùng hoặc NOT_DISCLOSED (null)")
    risk_label: str = Field(..., description="Mức rủi ro gắn nhãn (Low / Medium / High / NOT_DISCLOSED)")
    claimed_strategy_type: str = Field(..., description="Trường phái chiến lược (Breakout / Mean-Reversion / Grid / Martingale / Scalping / Trend / NOT_DISCLOSED)")
    has_grid_or_martingale_signals: bool = Field(..., description="Có tín hiệu dùng Grid hoặc Martingale hay không")
    grid_martingale_rationale: str = Field(..., description="Lý do và câu trích nguyên văn từ bài viết")
    symbols: List[str] = Field(..., description="Cặp tiền tệ / Tài sản giao dịch")
    timeframes: List[str] = Field(..., description="Khung thời gian giao dịch")
    uses_hard_sl: Union[bool, str] = Field(..., description="Có sử dụng Stop Loss cứng hay không (True / False / NOT_DISCLOSED)")
    verified_live_links: List[str] = Field(..., description="Danh sách link kiểm chứng tài khoản thật (Myfxbook, MQL5 Signals)")

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

    # Full text
    full_text = soup.get_text(separator=' ', strip=True)
    text_lower = full_text.lower()

    # Platform
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
    pricing = "Free"
    if "Premium" in html:
        pricing = "Free (Premium Membership Required)"

    # Site score
    site_score = None
    rating_val = app_data.get('aggregateRating', {}).get('ratingValue')
    if rating_val:
        try:
            site_score = round(float(rating_val), 2)
        except Exception:
            pass

    # Risk Label
    risk_label = "NOT_DISCLOSED"
    if "low risk" in text_lower or "low-risk" in text_lower:
        risk_label = "Low"
    elif "high risk" in text_lower or "high-risk" in text_lower:
        risk_label = "High"
    elif "medium risk" in text_lower or "medium-risk" in text_lower:
        risk_label = "Medium"

    # Claimed Strategy Type
    claimed_type = "NOT_DISCLOSED"
    if "breakout" in text_lower:
        claimed_type = "Breakout"
    elif "scalp" in text_lower:
        claimed_type = "Scalping"
    elif "trend" in text_lower:
        claimed_type = "Trend"
    elif "mean-reversion" in text_lower or "reversion" in text_lower:
        claimed_type = "Mean-Reversion"
    elif "grid trading" in text_lower or "martingale" in text_lower or "hedging recovery" in text_lower:
        claimed_type = "Grid"
    elif "indicator" in slug.lower() or "indicator" in name.lower() or "suite" in slug.lower():
        claimed_type = "Indicator"

    # Grid / Martingale Analysis
    has_grid = False
    rationale = "Không phát hiện tín hiệu giao dịch Grid/Martingale trong tài liệu mô tả."

    sentences = re.split(r'[.!?\n]', full_text)
    # Search for trading grid / martingale keywords, excluding visual grid terms
    trading_grid_sentences = []
    for s in sentences:
        s_clean = s.strip()
        # skip visual display grids
        if any(v in s_clean.lower() for v in ['visualizes', 'calendar tab', 'heatmap', 'square of 9', 'rowatr', 'chart patterns']):
            continue
        if re.search(r'\b(martingale|cost-averaging|averaging down|lot multiplier|recovery hedging|hedging grid|grid setups|grid trading|grid strategy|grid system)\b', s_clean, re.IGNORECASE):
            trading_grid_sentences.append(s_clean)
        elif re.search(r'\bgrid\b', s_clean, re.IGNORECASE) and any(kw in s_clean.lower() for kw in ['orders', 'levels', 'recovery', 'danger', 'risk', 'avoid', 'trades']):
            trading_grid_sentences.append(s_clean)

    if trading_grid_sentences:
        target_s = trading_grid_sentences[0]
        s_lower = target_s.lower()
        # Check if denial
        is_negation = any(neg in s_lower for neg in [
            'non-grid', 'no-grid', 'no grid', 'no martingale', 'avoids', 'avoiding',
            'without grid', 'without martingale', 'never use', 'not use', 'completely avoiding',
            'strictly avoids', 'does not rely', 'unlike', 'doesn\'t use'
        ])
        if is_negation:
            has_grid = False
            rationale = f"Khẳng định KHÔNG dùng: \"{target_s}\""
        else:
            has_grid = True
            rationale = f"Cảnh báo Grid/Martingale: \"{target_s}\""

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

    # Verified live links (Myfxbook, MQL5 signals)
    verified_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        h_lower = href.lower()
        if 'myfxbook.com' in h_lower or 'mql5.com/en/signals' in h_lower or 'mql5.com/signals' in h_lower:
            verified_links.append(href)

    return EACatalogItem(
        name=name,
        url=url,
        platform=platform,
        pricing=pricing,
        site_score=site_score,
        risk_label=risk_label,
        claimed_strategy_type=claimed_type,
        has_grid_or_martingale_signals=has_grid,
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
    print(f"[*] Parsing {len(html_files)} EA detail pages from {details_dir}...")

    catalog = []
    for f in html_files:
        try:
            item = extract_ea_from_html(f)
            catalog.append(item)
        except Exception as e:
            print(f"[!] Error parsing {f}: {e}")

    # Output JSON
    json_path = os.path.join(ext_dir, '01_ea_catalog.json')
    catalog_dicts = [item.model_dump() for item in catalog]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog_dicts, f, ensure_ascii=False, indent=2)
    print(f"[+] Saved {json_path} ({len(catalog)} items)")

    # Output CSV
    csv_path = os.path.join(ext_dir, '01_ea_catalog.csv')
    fieldnames = [
        'name', 'url', 'platform', 'pricing', 'site_score', 'risk_label',
        'claimed_strategy_type', 'has_grid_or_martingale_signals',
        'grid_martingale_rationale', 'symbols', 'timeframes', 'uses_hard_sl',
        'verified_live_links'
    ]
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for item in catalog:
            writer.writerow([
                item.name,
                item.url,
                item.platform,
                item.pricing,
                item.site_score if item.site_score is not None else 'NOT_DISCLOSED',
                item.risk_label,
                item.claimed_strategy_type,
                'TRUE' if item.has_grid_or_martingale_signals else 'FALSE',
                item.grid_martingale_rationale,
                '; '.join(item.symbols),
                '; '.join(item.timeframes),
                str(item.uses_hard_sl),
                '; '.join(item.verified_live_links) if item.verified_live_links else 'NONE'
            ])
    print(f"[+] Saved {csv_path}")

    # Summary statistics
    grid_count = sum(1 for item in catalog if item.has_grid_or_martingale_signals)
    non_grid = len(catalog) - grid_count
    live_links_count = sum(len(item.verified_live_links) for item in catalog)
    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total EAs Analyzed: {len(catalog)}")
    print(f"Clean (Non-Grid / No Martingale claimed): {non_grid}")
    print(f"Toxic Risk (Grid / Martingale detected): {grid_count}")
    print(f"Verified Live Links (Myfxbook/MQL5 Signals): {live_links_count}")

if __name__ == '__main__':
    main()
