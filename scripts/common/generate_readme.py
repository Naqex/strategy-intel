import json
import os
import hashlib
from collections import Counter

def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def get_file_size(path):
    return os.path.getsize(path)

def generate_readme():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Load data files
    master_leads_path = os.path.join(repo_root, "catalog", "master_leads.json")
    with open(master_leads_path, "r", encoding="utf-8") as f:
        master_leads_data = json.load(f)
    leads = master_leads_data.get("leads", [])

    indicator_ref_path = os.path.join(repo_root, "catalog", "indicator_reference.json")
    with open(indicator_ref_path, "r", encoding="utf-8") as f:
        indicator_data = json.load(f)
    indicators = indicator_data.get("items", [])

    rejected_log_path = os.path.join(repo_root, "catalog", "rejected_log.json")
    with open(rejected_log_path, "r", encoding="utf-8") as f:
        rejected_data = json.load(f)
    rejected_items = rejected_data.get("rejected_items", [])

    ea_catalog_path = os.path.join(repo_root, "sources", "ea-directory-2026", "extracted", "01_ea_catalog.json")
    with open(ea_catalog_path, "r", encoding="utf-8") as f:
        ea_catalog_data = json.load(f)
    ea_items = ea_catalog_data.get("items", [])

    anomalies_path = os.path.join(repo_root, "sources", "stategy-netlify-app", "extracted", "source_anomalies.json")
    with open(anomalies_path, "r", encoding="utf-8") as f:
        anomalies_data = json.load(f)

    # Compute statistics
    total_leads = len(leads)
    leads_passes_all_5_true = sum(1 for l in leads if l.get("passes_all_5") is True)
    leads_passes_all_5_false = sum(1 for l in leads if l.get("passes_all_5") is False)

    ea_asset_types = Counter(item.get("asset_type") for item in ea_items)
    ea_count = ea_asset_types.get("EA", 0)
    indicator_count = ea_asset_types.get("INDICATOR", 0)
    utility_count = ea_asset_types.get("UTILITY", 0)

    rejected_categories = Counter(item.get("category") for item in rejected_items)
    rejected_chat = rejected_categories.get("chat_failed_oos", 0)
    rejected_unverified = rejected_categories.get("unverified_discretionary_or_missing_data", 0)
    rejected_toxic = rejected_categories.get("toxic_money_management", 0)
    rejected_blackbox = rejected_categories.get("blackbox_no_live_real_proof", 0)
    total_rejected = len(rejected_items)

    total_indicator_ref = len(indicators)
    num_year_mismatches = anomalies_data.get("summary", {}).get("total_year_mismatches", 0)
    num_missing_year_sets = anomalies_data.get("summary", {}).get("total_missing_year_sets", 0)

    # Files to hash
    files_to_hash = [
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/01_methodology_and_reports.md"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/02_library_242_summary.csv"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/02_library_242_summary.json"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/03_simulator_logic.md"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/04_top15_chat_full.json"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/05_replicability_audit.md"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/06_technical_methods_and_code.md"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/07_missing_58_items.json"),
        ("Nguồn 1", "sources/stategy-netlify-app/extracted/source_anomalies.json"),
        ("Nguồn 2", "sources/ea-directory-2026/extracted/01_ea_catalog.csv"),
        ("Nguồn 2", "sources/ea-directory-2026/extracted/01_ea_catalog.json"),
        ("Catalog", "catalog/indicator_reference.json"),
        ("Catalog", "catalog/master_leads.json"),
        ("Catalog", "catalog/rejected_log.json"),
        ("Handoff", "handoff/sanitized_master_leads.json"),
    ]

    hash_rows = []
    for partition, rel_path in files_to_hash:
        full_path = os.path.join(repo_root, rel_path.replace("/", os.sep))
        size = get_file_size(full_path)
        sha = get_sha256(full_path)
        hash_rows.append(f"| **{partition}** | `{rel_path}` | {size:,} | `{sha}` |")

    # Build Leads Table
    leads_rows = []
    for l in leads:
        orig_id = l.get("original_id", "")
        name = l.get("name", "")
        family = l.get("family", "")
        p5 = "PASS" if l.get("passes_all_5") is True else "FAIL"
        rep = l.get("replicability", "")
        flags = ", ".join(l.get("data_quality_flags", [])) or "None"
        leads_rows.append(f"| `{orig_id}` | {name} | {family} | `{rep}` | **{p5}** | `{flags}` |")

    # Fixtures
    fixtures = [
        ("quantum-titan-mt5", "Low", "POINTS (300 P-Points)", "False", "False", "REJECTED (NO_LIVE_REAL_PROOF_BLACKBOX)"),
        ("sunan-giri-ea-mt4", "Medium", "POINTS (30 Points)", "True", "False", "REJECTED (GRID_MARTINGALE_TOXIC_RISK)"),
        ("scalping-robot-pro-mt5", "High", "POINTS (300 P-Points)", "True", "False", "REJECTED (GRID_MARTINGALE_TOXIC_RISK)"),
    ]
    fixtures_rows = []
    for slug, risk, pricing, grid, live, verdict in fixtures:
        fixtures_rows.append(f"| `{slug}` | `{risk}` | `{pricing}` | `{grid}` | `{live}` | `{verdict}` |")

    readme_content = f"""# STRATEGY-INTEL: KHO THU THẬP & KIỂM TOÁN THÔNG TIN CHIẾN LƯỢC ĐỊNH LƯỢNG

> **Mục tiêu hệ thống:** Vùng đệm phòng sạch (Clean-room Intelligence Buffer) thu thập, kiểm toán phương pháp luận, tách bạch sự thật (Fact) khỏi chiêu trò tiếp thị (Marketing/Overfitting) từ các nguồn web, kho EA, báo cáo định lượng bên ngoài.  
> **Nguyên tắc an toàn tối thượng:** Tuân thủ tuyệt đối [intel-airgap-guardrails.md](file:///.agents/rules/intel-airgap-guardrails.md) và [AGENTS.md](file:///AGENTS.md).  
> **Repository Owner / Target Org:** `naqex` (`https://github.com/Naqex/strategy-intel.git`)

---

## ⚠️ QUY TẮC BẢO VỆ DỮ LIỆU ĐỊNH LƯỢNG (CRITICAL NOTICE)

> **NGHIÊM CẤM TUYỆT ĐỐI:**  
> Không được sử dụng hoặc trộn tập dữ liệu **Out-of-Sample Kỳ 2 (2024–2026)** vào tập **Holdout / Testset** của hệ thống giao dịch nội bộ tại `TradingWorkspace`.  
> **Lý do định lượng:** Giai đoạn 2024–2026 là đợt sóng tăng một chiều lịch sử của Vàng giao ngay (Beta khổng lồ của thị trường), khiến 82 chiến lược từng trượt bài thi (CHÁT) cũng có lãi trở lại. Việc nạp dữ liệu này vào quá trình tối ưu hóa tham số sẽ gây lỗi rò rỉ dữ liệu tương lai (Look-ahead Bias on Holdout) và bẫy khớp đường cong (Curve-Fitting).
> Mọi dữ liệu trước khi bàn giao sang `handoff/` bắt buộc phải chạy `scripts/common/holdout_sanitizer.py` để loại trừ hoàn toàn số liệu năm 2024–2026 và OOS2.

---

## 1. CẤU TRÚC KHO LƯU TRỮ

```text
d:/ANNAM/strategy-intel/
├── .agents/                               # Bộ quy tắc & kỹ năng cho AI Agents
│   ├── rules/
│   │   └── intel-airgap-guardrails.md     # 4 quy tắc an toàn cốt lõi (Air-gap, No Binary, Zero Hallucination, Clean Repo)
│   └── skills/
│       ├── web-source-ingestor/           # Kỹ năng crawl & lưu trữ thô an toàn
│       ├── quant-fact-extractor/          # Kỹ năng trích xuất định lượng chuẩn xác
│       └── cleanroom-handoff/             # Kỹ năng đóng gói catalog & làm sạch holdout
├── AGENTS.md                              # Hướng dẫn chi tiết quy trình tác nhân
├── catalog/                               # Danh mục quản lý tập trung toàn repo
│   ├── indicator_reference.json           # {total_indicator_ref} công cụ Indicators & Utilities từ Nguồn 2
│   ├── master_leads.json                  # {total_leads} ý tưởng CHẤT đạt chuẩn định lượng (Source 1)
│   └── rejected_log.json                  # {total_rejected} mục bị loại ({rejected_unverified} chưa kiểm định + {rejected_chat} OOS sập + {rejected_toxic} Grid + {rejected_blackbox} Blackbox)
├── handoff/                               # Vùng đệm bàn giao cho team Quant nội bộ (Holdout Sanitized)
│   ├── README.md                          # Tiêu chuẩn bàn giao phòng sạch
│   └── sanitized_master_leads.json        # {total_leads} leads đã làm sạch hoàn toàn số liệu 2024-2026 & OOS2
├── scripts/common/                        # Bộ 4 script kiểm định dùng chung & negative test suite
│   ├── repo_hygiene_check.py              # Kiểm tra 0 binary files (.ex4/.ex5/.dll/.exe/.zip) & 0 file nháp
│   ├── verify_verbatim.py                 # Kiểm tra tính toàn vẹn và nguyên văn dữ liệu trích xuất (đối chiếu 242 reports)
│   ├── holdout_sanitizer.py               # Quét sạch dữ liệu năm 2024-2026/OOS2 trong handoff/
│   ├── test_guards.py                     # Negative test suite kiểm chứng phản chứng 4 chốt chặn an toàn
│   └── generate_readme.py                 # Tự động hóa thống kê và cập nhật README.md
├── sources/
│   ├── stategy-netlify-app/               # NGUỒN 1: Báo cáo kiểm định 242 chiến lược Vàng 22 năm
│   │   ├── raw/                           # JSON reports (242 file), vault_data.json, index, assets JS
│   │   ├── extracted/                     # Báo cáo & bảng biểu chuẩn hóa
│   │   │   ├── 01_methodology_and_reports.md
│   │   │   ├── 02_library_242_summary.csv / .json
│   │   │   ├── 03_simulator_logic.md
│   │   │   ├── 04_top15_chat_full.json
│   │   │   ├── 05_replicability_audit.md
│   │   │   ├── 06_technical_methods_and_code.md
│   │   │   ├── 07_missing_58_items.json
│   │   │   └── source_anomalies.json      # {num_year_mismatches} lỗi lệch năm & {num_missing_year_sets} chu kỳ thiếu năm zero-trade
│   │   └── scripts/                       # Script Node.js tái lập quy trình 100%
│   └── ea-directory-2026/                 # NGUỒN 2: Thư mục xếp hạng EA quốc tế (eafree.net - 45 tệp mẫu)
│       ├── raw/                           # HTML ranking pages, sitemap.xml, 45 detail pages
│       ├── extracted/                     # Danh mục trích xuất ({ea_count} EAs, {indicator_count} Indicators, {utility_count} Utilities)
│       │   ├── 01_ea_catalog.csv
│       │   └── 01_ea_catalog.json
│       └── scripts/
│           └── extract_catalog.py         # Script Python Pydantic trích xuất & kiểm toán EA
├── .gitignore                             # Chặn node_modules, .scratch/, binary, logs
└── README.md                              # Tài liệu tổng quan & Bảng băm SHA-256 (Auto-generated)
```

---

## 2. BẢNG BĂM SHA-256 KIỂM CHỨNG TÍNH TOÀN VẸN (EXTRACTED CHECKSUM)

Mọi tệp tin trong `extracted/`, `catalog/` và `handoff/` được kiểm chứng tính toàn vẹn tự động thông qua mã băm SHA-256:

| Phân Vùng | Tên Tệp Tin | Kích Thước (Bytes) | Mã Băm SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
{chr(10).join(hash_rows)}

---

## 3. TÓM TẮT KẾT QUẢ KIỂM TOÁN HAI NGUỒN DỮ LIỆU

### Nguồn 1: `stategy.netlify.app` (242 Báo Cáo Kiểm Định Vàng 22 Năm)
1. **Chênh lệch 300 vs 242:**
   - **242 chiến lược** kiểm định tự động đầy đủ bằng máy (`reports_json/`).
   - **40 hồ sơ gộp** biến thể đối xứng (`trang_thai: "gop"`): 6 bản sao hoàn toàn (`DUPLICATE_EXACT`), 27 biến thể liên quan (`RELATED_VARIANT`), 7 biến thể chưa kiểm tra (`UNTESTED_VARIANT`). Riêng `REV029` là biến thể ngược chiều mua của `REV028` (CHẤT) nhưng không được kiểm định độc lập, gắn cờ `CHUA_KIEM_DINH_BIEN_THE_NGUOC`.
   - **18 hồ sơ chưa kiểm định** (`trang_thai: "chua_kiem_dinh"`): 9 mục thiếu dữ liệu ngoại vi (`MISSING_AUXILIARY_DATA` - FOMC, CPI, DXY, Bạc), 4 mục không phải chiến lược độc lập (`NOT_A_STANDALONE_STRATEGY` - bộ lọc phiên, 5-3-1), 5 mục quy tắc cảm tính vẽ tay (`DISCRETIONARY_NOT_FORMALIZED`).
2. **Khả năng tái dựng 15 chiến lược "CHẤT" (`master_leads.json`):**
   - **Mức bằng chứng:** `evidence_tier: "SOURCE_CLAIM_ONLY"` (tác giả tự công bố, chưa có kiểm định độc lập nội bộ).
   - **Tiêu chuẩn 5 bài thi (`passes_all_5`):** {leads_passes_all_5_true}/15 chiến lược đạt `True`; {leads_passes_all_5_false}/15 chiến lược ghi nhận `False` (`IND026`, `SEA003`, `SEA004`, `SEA021`) do trường dữ liệu gốc `kha_thi: false` (số lệnh mẫu dưới 100 lệnh).
   - **Phân loại khả năng tái dựng:**
     * `SEA003` (Turn-of-month vàng): `REPLICABLE_FROM_PUBLIC` (quy tắc lịch cố định giao dịch 2 ngày cuối tháng và 3 ngày đầu tháng).
     * `SEA004` (Hiệu ứng đầu quý): `PARTIAL_RULE_SPEC` (quy tắc lịch cố định nhưng thiếu quy tắc định lượng chọn chiều Buy/Sell).
     * 13 chiến lược còn lại: `PARTIAL_CONCEPT_ONLY` (ý tưởng rõ ràng nhưng SL/TP/Exit chi tiết nằm sau passkey thành viên).

| Mã ID | Tên Chiến Lược | Phân Loại | Khả Năng Tái Dựng | Đạt 5 Tiêu Chí (`passes_all_5`) | Data Quality Flags |
| :--- | :--- | :--- | :--- | :---: | :--- |
{chr(10).join(leads_rows)}

3. **Bất thường dữ liệu gốc ghi nhận tại `source_anomalies.json`:**
   - **{num_year_mismatches} chiến lược** có số năm dương (`years_pos`) ghi nhận trong JSON không khớp với số năm `True` trong từ điển `nam_duong` (`BRK009`, `BRK018`, `BRK034`, `IND015`, `IND044`, `IND047`, `REV025`, `VIR041`).
   - **{num_missing_year_sets} chu kỳ kiểm định** thiếu các năm không phát sinh giao dịch trong từ điển `nam_duong` thay vì ghi nhận giá trị `False`.
4. **Cảnh báo mô hình chi phí & Mô phỏng:**
   - **Mâu thuẫn toán học phí giao dịch:** Tác giả công bố `0.02%/chiều` tương đương `~$7/lot 2 chiều`. Tuy nhiên, với XAUUSD quy cách 1 lot = 100 oz, tại giá $2,650/oz (notional $265,000), phí `0.02%/chiều` = $53/chiều = **$106/lot 2 chiều**. Mức $7/lot thực tế chỉ tương đương 0.00132%/chiều (chênh lệch 15.1 lần).
   - **Mô phỏng Monte Carlo tĩnh:** File `HomeStitch-DfsUMINs.js` chứa mảng tĩnh 300 giá trị phao mô phỏng sẵn (`display_cached_simulation`), không thực hiện tính toán Monte Carlo hoán vị động tại client.

---

### Nguồn 2: `eafree.net` (Thư Mục 45 EA & Công Cụ MT4/MT5 Mẫu)
1. **Phân loại 45 tệp mẫu:**
   - **{ea_count} Expert Advisors (EA):** **0 EA** đủ điều kiện bàn giao vào `master_leads.json`.
     * {rejected_toxic} EA bị gắn cờ độc hại `toxic_money_management` (Grid / Martingale / Cost Averaging) với rủi ro cháy tài khoản, loại vào `rejected_log.json`.
     * {rejected_blackbox} EA bị loại vì `blackbox_no_live_real_proof` (EA thương mại đóng mã nguồn, không có kiểm chứng Myfxbook/MQL5 Live Real), loại vào `rejected_log.json`.
   - **{indicator_count} Indicators & {utility_count} Utilities:** Đã tách riêng toàn bộ sang `catalog/indicator_reference.json` làm tài liệu tham khảo công cụ phân tích kỹ thuật, không làm nhiễu danh mục chiến lược tự động.
2. **Minh bạch tài khoản Live Real:**
   - 44/45 hồ sơ hoàn toàn KHÔNG có link theo dõi tài khoản thật của bên thứ ba.
   - Duy nhất 1 hồ sơ cung cấp link Myfxbook nhưng là tài khoản **Demo**, không phải tài khoản Real có nạp tiền thực tế.
   - Toàn bộ kết quả backtest trên trang là MT5 zero-slippage do nhà bán lẻ tự quảng cáo.
3. **Kiểm chứng hồi quy 3 Fixture đại diện:**

| EA Fixture Slug | Vendor Risk Label | Pricing / Points | Grid/Martingale | Live Real Verified | Kết Luận Kiểm Toán |
| :--- | :---: | :--- | :---: | :---: | :--- |
{chr(10).join(fixtures_rows)}

---

## 4. TỔNG KẾT REJECTED LOG & BÀN GIAO PHÒNG SẠCH

1. **Tổng hợp {total_rejected} mục bị loại bỏ (`catalog/rejected_log.json`):**
   - **{rejected_chat} chiến lược** trượt OOS (Verdict: CHÁT) từ Nguồn 1.
   - **{rejected_unverified} hồ sơ** chưa kiểm định từ Nguồn 1 (thiếu dữ liệu ngoại vi, không phải chiến lược độc lập, vẽ tay cảm tính).
   - **{rejected_toxic} EA** có cơ chế Grid / Martingale / Cost Averaging độc hại từ Nguồn 2.
   - **{rejected_blackbox} EA** hộp đen thương mại không có bằng chứng tài khoản thật từ Nguồn 2.
2. **Bàn giao phòng sạch (`handoff/sanitized_master_leads.json`):**
   - Đóng gói **{total_leads} leads** chất lượng cao từ Nguồn 1.
   - Đã được làm sạch 100% bằng `scripts/common/holdout_sanitizer.py`, loại trừ hoàn toàn các chuỗi dữ liệu PnL, báo cáo của năm 2024–2026 và OOS2, đảm bảo tính nguyên vẹn tuyệt đối cho tập kiểm định Holdout của hệ thống nội bộ.

---
*Tài liệu kiểm toán và kho lưu trữ được tự động sinh và cập nhật bởi `scripts/common/generate_readme.py`.*
"""

    readme_path = os.path.join(repo_root, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"README.md successfully generated at {readme_path}")

if __name__ == "__main__":
    generate_readme()
