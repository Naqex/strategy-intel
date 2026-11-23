# STRATEGY-INTEL: KHO THU THẬP & KIỂM TOÁN THÔNG TIN CHIẾN LƯỢC ĐỊNH LƯỢNG

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
│   ├── indicator_reference.json           # 27 công cụ Indicators & Utilities từ Nguồn 2
│   ├── master_leads.json                  # 15 ý tưởng CHẤT đạt chuẩn định lượng (Source 1)
│   └── rejected_log.json                  # 224 mục bị loại (18 chưa kiểm định + 188 OOS sập + 4 Grid + 14 Blackbox)
├── handoff/                               # Vùng đệm bàn giao cho team Quant nội bộ (Holdout Sanitized)
│   ├── README.md                          # Tiêu chuẩn bàn giao phòng sạch
│   └── sanitized_master_leads.json        # 15 leads đã làm sạch hoàn toàn số liệu 2024-2026 & OOS2
├── scripts/common/                        # Bộ 4 script kiểm định dùng chung & negative test suite
│   ├── repo_hygiene_check.py              # Kiểm tra 0 binary files (.ex4/.ex5/.dll/.exe/.zip) & 0 file nháp
│   ├── verify_verbatim.py                 # Kiểm tra tính toàn vẹn và nguyên văn dữ liệu trích xuất (đối chiếu 242 reports)
│   ├── holdout_sanitizer.py               # Quét sạch dữ liệu năm 2024-2026/OOS2 trong handoff/
│   ├── test_guards.py                     # Negative test suite kiểm chứng phản chứng 4 chốt chặn an toàn
│   └── generate_readme.py                 # Tự động hóa thống kê và cập nhật README.md
├── sources/
│   ├── stategy-netlify-app/               # NGUỒN 1: Báo cáo kiểm định 242 chiến lược Vàng 22 năm
│   │   ├── raw/                           # JSON reports (242 file), vault_data.json, index, assets JS
│   │   ├── raw_manifest.sha256.json       # SHA-256 bất biến của 283 tệp raw nguồn 1
│   │   ├── extracted/                     # Báo cáo & bảng biểu chuẩn hóa
│   │   │   ├── 01_methodology_and_reports.md
│   │   │   ├── 02_library_242_summary.csv / .json
│   │   │   ├── 03_simulator_logic.md
│   │   │   ├── 04_top15_chat_full.json
│   │   │   ├── 05_replicability_audit.md
│   │   │   ├── 06_technical_methods_and_code.md
│   │   │   ├── 07_missing_58_items.json
│   │   │   └── source_anomalies.json      # 8 lỗi lệch năm & 40 chu kỳ thiếu năm zero-trade
│   │   └── scripts/                       # Script Node.js tái lập quy trình 100%
│   └── ea-directory-2026/                 # NGUỒN 2: Thư mục xếp hạng EA quốc tế (eafree.net - 45 tệp mẫu)
│       ├── raw/                           # HTML ranking pages, sitemap.xml, 45 detail pages
│       ├── raw_manifest.sha256.json       # SHA-256 bất biến của 48 tệp raw nguồn 2
│       ├── extracted/                     # Danh mục trích xuất (18 EAs, 25 Indicators, 2 Utilities)
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
| **Nguồn 1** | `sources/stategy-netlify-app/raw_manifest.sha256.json` | 39,802 | `CA4BDEA760281DFCCBCBB70FCD5680C200492B444CB863D0142C6ABD4E425DAE` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/01_methodology_and_reports.md` | 43,988 | `994840FC2EDFD401D9A2C1ACCE4A7D47F0A93AD54F8A16DFEC366DBAFC85C08E` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/02_library_242_summary.csv` | 65,470 | `EDE83026C7C9DB8D3E2EED402BB1FD92A5CAC175333F85F06CC1B48F3DBEF3F6` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/02_library_242_summary.json` | 431,524 | `1AFD2716C6ACDCFA584EC699D39D9C88EE0B978E71FF64D941F879F9C32F18B8` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/03_simulator_logic.md` | 13,275 | `17B38617D92DEC699FF2EFF35B6D6B8E7596E042B2ADD41D4C74EC5285495795` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/04_top15_chat_full.json` | 22,603 | `3BCB023154FE20BF127B4673D342DB3B6214E69E2E283A673B0DF59D92CEBC53` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/05_replicability_audit.md` | 42,784 | `4C48F8CA2CD667BA1F5359E2BC2DB40403E7D0FE2912A4124A78256A2EBFBFC6` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/06_technical_methods_and_code.md` | 33,817 | `DBC775275EA8976782B9B0BC8CCEA02EBFF31AB23304EB0C58BE9EE6D8C02A80` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/07_missing_58_items.json` | 38,983 | `845BB7E808972FADF9CF8653114E69ACB59675E20177C7D9484578770FB41DE5` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/source_anomalies.json` | 16,441 | `FCEA8BA6D35EFF30CD9ABD315BABFAECC36FBCA0ACA1EA7B799A41F62C7AF344` |
| **Nguồn 2** | `sources/ea-directory-2026/raw_manifest.sha256.json` | 7,280 | `F34BDA4AC1F1C2FE010FBFBF9BAA598F6FDEA45AFA2220DF152219035FFF8989` |
| **Nguồn 2** | `sources/ea-directory-2026/extracted/01_ea_catalog.csv` | 14,965 | `DC51942B3EEA0385B6C259ED04D4851025F83F87F29A1B242A4779D257A08A8E` |
| **Nguồn 2** | `sources/ea-directory-2026/extracted/01_ea_catalog.json` | 46,854 | `F3408F018CB8F8D628606F956105FC0ECD3DB766A15F1D3E119D254C67F596B8` |
| **Catalog** | `catalog/indicator_reference.json` | 17,954 | `FEB6D49E89BEF1EA63815287169B3E667664E6C9BD05D6FCDF85738A39C57E9D` |
| **Catalog** | `catalog/master_leads.json` | 26,884 | `E3EE2EC94DEEA6BB264FB083BF38AA1E302BE9ACB26B16A47A9D93C57C98A881` |
| **Catalog** | `catalog/rejected_log.json` | 169,343 | `19DC2D30863D1C1DCDDBFCCFF4EF016B31159598F32D54890D961A1881497763` |
| **Handoff** | `handoff/sanitized_master_leads.json` | 26,930 | `B5BCFFC6AFD44D73145C73D0334863DD06E923F3F54787E9A90179E9562A6690` |

---

## 3. TÓM TẮT KẾT QUẢ KIỂM TOÁN HAI NGUỒN DỮ LIỆU

### Nguồn 1: `stategy.netlify.app` (242 Báo Cáo Kiểm Định Vàng 22 Năm)
1. **Chênh lệch 300 vs 242:**
   - **242 chiến lược** kiểm định tự động đầy đủ bằng máy (`reports_json/`).
   - **40 hồ sơ gộp** biến thể đối xứng (`trang_thai: "gop"`): 5 bản sao hoàn toàn (`DUPLICATE_EXACT`), 27 biến thể liên quan (`RELATED_VARIANT`), 8 biến thể chưa kiểm tra (`UNTESTED_VARIANT`). Riêng `REV029` là biến thể bán ngược chiều của `SEA003` (Turn-of-month vàng) nhưng bản thân chưa được kiểm định độc lập, gắn cờ `UNTESTED_REVERSE_VARIANT_CANNOT_INHERIT_CHAT`.
   - **18 hồ sơ chưa kiểm định** (`trang_thai: "chua_kiem_dinh"`): 9 mục thiếu dữ liệu ngoại vi (`MISSING_AUXILIARY_DATA` - FOMC, CPI, DXY, Bạc), 4 mục không phải chiến lược độc lập (`NOT_A_STANDALONE_STRATEGY` - bộ lọc phiên, 5-3-1), 5 mục quy tắc cảm tính vẽ tay (`DISCRETIONARY_NOT_FORMALIZED`).
2. **Khả năng tái dựng 15 chiến lược "CHẤT" (`master_leads.json`):**
   - **Mức bằng chứng:** `evidence_tier: "SOURCE_CLAIM_ONLY"` (tác giả tự công bố, chưa có kiểm định độc lập nội bộ).
   - **Tiêu chuẩn 5 bài thi (`passes_all_5`):** 11/15 chiến lược đạt `True`; 4/15 chiến lược ghi nhận `False` (`IND026`, `SEA003`, `SEA004`, `SEA021`) do trường dữ liệu gốc `kha_thi: false` (số lệnh mẫu dưới 100 lệnh).
   - **Phân loại khả năng tái dựng:**
     * `SEA003` (Turn-of-month vàng): `REPLICABLE_FROM_PUBLIC` (quy tắc lịch cố định giao dịch 2 ngày cuối tháng và 3 ngày đầu tháng).
     * `SEA004` (Hiệu ứng đầu quý): `PARTIAL_RULE_SPEC` (quy tắc lịch cố định nhưng thiếu quy tắc định lượng chọn chiều Buy/Sell).
     * 13 chiến lược còn lại: `PARTIAL_CONCEPT_ONLY` (ý tưởng rõ ràng nhưng SL/TP/Exit chi tiết nằm sau passkey thành viên).

| Mã ID | Tên Chiến Lược | Phân Loại | Khả Năng Tái Dựng | Đạt 5 Tiêu Chí (`passes_all_5`) | Data Quality Flags |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `BRK012` | Inside day breakout | Breakout & phiên | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `BRK035` | Hộp 4h đầu tuần | Breakout & phiên | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `IND026` | Ichimoku Chikou xác nhận | Indicator kinh điển | `PARTIAL_CONCEPT_ONLY` | **FAIL** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON, FAILED_FEASIBILITY_UNDER_100_TRADES` |
| `IND041` | ROC momentum 10 | Indicator kinh điển | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `IND049` | Alligator mở miệng | Indicator kinh điển | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `IND053` | Momentum 10 vượt 100 | Indicator kinh điển | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `MTF016` | Mùa vụ D1 + tín hiệu H1 | Đa khung & lai | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `MTF020` | Golden cross D1 nền + mua mọi hồi H4 | Đa khung & lai | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `NEN006` | Inside bar thuận trend D1 | Mẫu nến | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `NEN022` | Nến phá vỡ giả (fakey) | Mẫu nến | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `SEA003` | Turn-of-month vàng | Giờ giấc & mùa vụ | `REPLICABLE_FROM_PUBLIC` | **FAIL** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON, FAILED_FEASIBILITY_UNDER_100_TRADES` |
| `SEA004` | Hiệu ứng đầu quý | Giờ giấc & mùa vụ | `PARTIAL_RULE_SPEC` | **FAIL** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON, FAILED_FEASIBILITY_UNDER_100_TRADES, MISSING_DIRECTION_RULE_SPEC` |
| `SEA011` | Thứ Ba đảo chiều (turnaround Tuesday) | Giờ giấc & mùa vụ | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |
| `SEA021` | Thứ Hai sau NFP xấu — hồi | Giờ giấc & mùa vụ | `PARTIAL_CONCEPT_ONLY` | **FAIL** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON, FAILED_FEASIBILITY_UNDER_100_TRADES` |
| `VIR040` | Head & Shoulders phá neckline | Viral & SMC/ICT | `PARTIAL_CONCEPT_ONLY` | **PASS** | `COMMISSION_MATH_CONTRADICTION_002PCT_VS_7USD, MISSING_PF_AND_DD_IN_PUBLIC_JSON` |

3. **Bất thường dữ liệu gốc ghi nhận tại `source_anomalies.json`:**
   - **8 chiến lược** có số năm dương (`years_pos`) ghi nhận trong JSON không khớp với số năm `True` trong từ điển `nam_duong` (`BRK009`, `BRK018`, `BRK034`, `IND015`, `IND044`, `IND047`, `REV025`, `VIR041`).
   - **40 chu kỳ kiểm định** thiếu các năm không phát sinh giao dịch trong từ điển `nam_duong` thay vì ghi nhận giá trị `False`.
4. **Cảnh báo mô hình chi phí & Mô phỏng:**
   - **Mâu thuẫn toán học phí giao dịch:** Tác giả công bố `0.02%/chiều` tương đương `~$7/lot 2 chiều`. Tuy nhiên, với XAUUSD quy cách 1 lot = 100 oz, tại giá $2,650/oz (notional $265,000), phí `0.02%/chiều` = $53/chiều = **$106/lot 2 chiều**. Mức $7/lot thực tế chỉ tương đương 0.00132%/chiều (chênh lệch 15.1 lần).
   - **Mô phỏng Monte Carlo tĩnh:** File `HomeStitch-DfsUMINs.js` chứa mảng tĩnh 300 giá trị phao mô phỏng sẵn (`display_cached_simulation`), không thực hiện tính toán Monte Carlo hoán vị động tại client.

---

### Nguồn 2: `eafree.net` (Thư Mục 45 EA & Công Cụ MT4/MT5 Mẫu)
1. **Phân loại 45 tệp mẫu:**
   - **18 Expert Advisors (EA):** **0 EA** đủ điều kiện bàn giao vào `master_leads.json`.
     * 4 EA bị gắn cờ độc hại `toxic_money_management` (Grid / Martingale / Cost Averaging) với rủi ro cháy tài khoản, loại vào `rejected_log.json`.
     * 14 EA bị loại vì `blackbox_no_live_real_proof` (EA thương mại đóng mã nguồn, không có kiểm chứng Myfxbook/MQL5 Live Real), loại vào `rejected_log.json`.
   - **25 Indicators & 2 Utilities:** Đã tách riêng toàn bộ sang `catalog/indicator_reference.json` làm tài liệu tham khảo công cụ phân tích kỹ thuật, không làm nhiễu danh mục chiến lược tự động.
2. **Minh bạch tài khoản Live Real:**
   - 44/45 hồ sơ hoàn toàn KHÔNG có link theo dõi tài khoản thật của bên thứ ba.
   - Duy nhất 1 hồ sơ cung cấp link Myfxbook nhưng là tài khoản **Demo**, không phải tài khoản Real có nạp tiền thực tế.
   - Backtest vendor trên mẫu 45 EAFree gồm cả MetaTrader 4 và MetaTrader 5 (ví dụ Sunan Giri chạy MT4 Strategy Tester lịch sử demo 90%), chưa chứng minh đủ chi phí spread biến động/slippage/swap và không được dùng làm bằng chứng hiệu suất.
3. **Kiểm chứng hồi quy 3 Fixture đại diện:**

| EA Fixture Slug | Vendor Risk Label | Pricing / Points | Grid/Martingale | Live Real Verified | Kết Luận Kiểm Toán |
| :--- | :---: | :--- | :---: | :---: | :--- |
| `quantum-titan-mt5` | `Low` | `POINTS (300 P-Points)` | `False` | `False` | `REJECTED (NO_LIVE_REAL_PROOF_BLACKBOX)` |
| `sunan-giri-ea-mt4` | `Medium` | `POINTS (30 Points)` | `True` | `False` | `REJECTED (GRID_MARTINGALE_TOXIC_RISK)` |
| `scalping-robot-pro-mt5` | `High` | `POINTS (300 P-Points)` | `True` | `False` | `REJECTED (GRID_MARTINGALE_TOXIC_RISK)` |

---

## 4. TỔNG KẾT REJECTED LOG & BÀN GIAO PHÒNG SẠCH

1. **Tổng hợp 224 mục bị loại bỏ (`catalog/rejected_log.json`):**
   - **188 chiến lược** trượt OOS (Verdict: CHÁT) từ Nguồn 1.
   - **18 hồ sơ** chưa kiểm định từ Nguồn 1 (thiếu dữ liệu ngoại vi, không phải chiến lược độc lập, vẽ tay cảm tính).
   - **4 EA** có cơ chế Grid / Martingale / Cost Averaging độc hại từ Nguồn 2.
   - **14 EA** hộp đen thương mại không có bằng chứng tài khoản thật từ Nguồn 2.
2. **Bàn giao phòng sạch (`handoff/sanitized_master_leads.json`):**
   - Đóng gói **15 leads** chất lượng cao từ Nguồn 1.
   - Đã được làm sạch 100% bằng `scripts/common/holdout_sanitizer.py`, loại trừ hoàn toàn các chuỗi dữ liệu PnL, báo cáo của năm 2024–2026 và OOS2, đảm bảo tính nguyên vẹn tuyệt đối cho tập kiểm định Holdout của hệ thống nội bộ.

---
*Tài liệu kiểm toán và kho lưu trữ được tự động sinh và cập nhật bởi `scripts/common/generate_readme.py`.*
