# STRATEGY-INTEL: KHO THU THẬP & KIỂM TOÁN THÔNG TIN CHIẾN LƯỢC ĐỊNH LƯỢNG

> **Mục tiêu hệ thống:** Vùng đệm phòng sạch (Clean-room Intelligence Buffer) thu thập, kiểm toán phương pháp luận, tách bạch sự thật (Fact) khỏi chiêu trò tiếp thị (Marketing/Overfitting) từ các nguồn web, kho EA, báo cáo định lượng bên ngoài.  
> **Nguyên tắc an toàn tối thượng:** Tuân thủ tuyệt đối [intel-airgap-guardrails.md](file:///.agents/rules/intel-airgap-guardrails.md) và [AGENTS.md](file:///AGENTS.md).  
> **Repository Owner / Target Org:** `naqex` (`https://github.com/Naqex/strategy-intel.git`)

---

## ⚠️ QUY TẮC BẢO VỆ DỮ LIỆU ĐỊNH LƯỢNG (CRITICAL NOTICE)

> **NGHIÊM CẤM TUYỆT ĐỐI:**  
> Không được sử dụng hoặc trộn tập dữ liệu **Out-of-Sample Kỳ 2 (2024–2026)** vào tập **Holdout / Testset** của hệ thống giao dịch nội bộ tại `TradingWorkspace`.  
> **Lý do định lượng:** Giai đoạn 2024–2026 là đợt sóng tăng một chiều lịch sử của Vàng giao ngay (Beta khổng lồ của thị trường), khiến 82 chiến lược từng trượt bài thi (CHÁT) cũng có lãi trở lại. Việc nạp dữ liệu này vào quá trình tối ưu hóa tham số sẽ gây lỗi rò rỉ dữ liệu tương lai (Look-ahead Bias on Holdout) và bẫy khớp đường cong (Curve-Fitting).
> Mọi dữ liệu trước khi bàn giao sang `handoff/` bắt buộc phải chạy `scripts/common/holdout_sanitizer.py` để loại trừ hoàn toàn số liệu năm 2025–2026.

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
│   └── rejected_log.json                  # 224 chiến lược bị loại bỏ (18 cảm tính + 188 OOS sập + 4 Grid + 14 Blackbox)
├── handoff/                               # Vùng đệm bàn giao cho team Quant nội bộ (Holdout Sanitized)
│   ├── README.md                          # Tiêu chuẩn bàn giao phòng sạch
│   └── sanitized_master_leads.json        # 15 leads đã làm sạch hoàn toàn số liệu 2025-2026
├── scripts/common/                        # Bộ 3 script kiểm định dùng chung
│   ├── repo_hygiene_check.py              # Kiểm tra 0 binary files (.ex4/.ex5/.dll/.exe/.zip) & 0 file nháp
│   ├── verify_verbatim.py                 # Kiểm tra tính toàn vẹn và nguyên văn dữ liệu trích xuất
│   └── holdout_sanitizer.py               # Quét sạch dữ liệu năm 2025-2026 trong handoff/
├── sources/
│   ├── stategy-netlify-app/               # NGUỒN 1: Báo cáo kiểm định 242 chiến lược Vàng 22 năm
│   │   ├── raw/                           # JSON reports (242 file), vault_data.json, index, assets JS
│   │   ├── extracted/                     # 7 báo cáo & bảng biểu chuẩn hóa
│   │   │   ├── 01_methodology_and_reports.md
│   │   │   ├── 02_library_242_summary.csv / .json
│   │   │   ├── 03_simulator_logic.md
│   │   │   ├── 04_top15_chat_full.json
│   │   │   ├── 05_replicability_audit.md
│   │   │   ├── 06_technical_methods_and_code.md
│   │   │   └── 07_missing_58_items.json
│   │   └── scripts/                       # 6 script Node.js tái lập quy trình 100%
│   └── ea-directory-2026/                 # NGUỒN 2: Thư mục xếp hạng EA quốc tế (eafree.net)
│       ├── raw/                           # HTML ranking pages, sitemap.xml, 45 detail pages
│       ├── extracted/                     # Danh mục trích xuất (45 EAs: 35 Clean, 10 Grid/Martingale)
│       │   ├── 01_ea_catalog.csv
│       │   └── 01_ea_catalog.json
│       └── scripts/
│           └── extract_catalog.py         # Script Python Pydantic trích xuất & kiểm toán EA
├── .gitignore                             # Chặn node_modules, .scratch/, binary, logs
└── README.md                              # Tài liệu tổng quan & Bảng băm SHA-256
```

---

## 2. BẢNG BĂM SHA-256 KIỂM CHỨNG TÍNH TOÀN VẸN (EXTRACTED CHECKSUM)

Mọi tệp tin trong `extracted/`, `catalog/` và `handoff/` được kiểm chứng tính toàn vẹn thông qua mã băm SHA-256:

| Phân Vùng | Tên Tệp Tin | Kích Thước (Bytes) | Mã Băm SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/01_methodology_and_reports.md` | 42,797 | `BCE3FB3A0D6D97CE86410FBBDCE849D6470E5BB3D98B4A400616377F53F3E9DC` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/02_library_242_summary.csv` | 65,470 | `EDE83026C7C9DB8D3E2EED402BB1FD92A5CAC175333F85F06CC1B48F3DBEF3F6` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/02_library_242_summary.json` | 431,524 | `1AFD2716C6ACDCFA584EC699D39D9C88EE0B978E71FF64D941F879F9C32F18B8` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/03_simulator_logic.md` | 12,226 | `7EE5BC4AF3B6AC85EFB35AB98A99DBAE6F02D8391ADE929BB2BF59FC00BB6B7D` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/04_top15_chat_full.json` | 22,603 | `3BCB023154FE20BF127B4673D342DB3B6214E69E2E283A673B0DF59D92CEBC53` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/05_replicability_audit.md` | 42,263 | `FB12B2B864B6D61A3C08686B318806E5489685B59346AF90854640657683ABBB` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/06_technical_methods_and_code.md` | 33,817 | `DBC775275EA8976782B9B0BC8CCEA02EBFF31AB23304EB0C58BE9EE6D8C02A80` |
| **Nguồn 1** | `sources/stategy-netlify-app/extracted/07_missing_58_items.json` | 23,963 | `CE1C9A8459C3D0536ED118AF36E921B33A5E7BEC13EBA265C1415273AF1942BD` |
| **Nguồn 2** | `sources/ea-directory-2026/extracted/01_ea_catalog.csv` | 13,685 | `056411D5CF8BD492DC444AB09CB8BF4B1227CC301A7E21F390CC603D0674D5BC` |
| **Nguồn 2** | `sources/ea-directory-2026/extracted/01_ea_catalog.json` | 33,221 | `8CFA15BF118114CE5F1DFB0AEB5DEA8FB2479D4CCBEBD03051FC06C25DD10601` |
| **Catalog** | `catalog/indicator_reference.json` | 17,386 | `9D6FDF756C83BA55C07DAC5D0F1CCC4FF9DF1A8D9C39123BFCBFEB9CE95E08FF` |
| **Catalog** | `catalog/master_leads.json` | 23,296 | `1EFC5A3F9970C469212C63C3D2A06145378D3D45476866B1B70AFFFAFDB1A971` |
| **Catalog** | `catalog/rejected_log.json` | 66,425 | `9A290B91E8EEB0EC03248B1378AF885FA916A899F250F6543CBEF0C2F4289248` |
| **Handoff** | `handoff/sanitized_master_leads.json` | 23,352 | `CBC9E37437F1F33EBD9BF89131A4962CA942FA29693B2A0E599555661B80DB99` |

---

## 3. TÓM TẮT KẾT QUẢ KIỂM TOÁN HAI NGUỒN DỮ LIỆU

### Nguồn 1: `stategy.netlify.app` (242 Báo Cáo Kiểm Định Vàng 22 Năm)
1. **Chênh lệch 300 vs 242:** 
   - 242 chiến lược kiểm định tự động đầy đủ bằng máy.
   - 40 hồ sơ gộp biến thể đối xứng (`trang_thai: "gop"`).
   - 18 hồ sơ chưa kiểm định (`trang_thai: "chua_kiem_dinh"`) do dựa trên vẽ tay cảm tính (trendlines chủ quan).
2. **Khả năng tái dựng 15 chiến lược "CHẤT":**
   - 2 chiến lược (`SEA003`, `SEA004`) đạt mức `REPLICABLE_FROM_PUBLIC` vì dựa trên quy tắc lịch cố định (Lễ Tạ Ơn, NFP).
   - 13 chiến lược còn lại ở mức `PARTIAL_CONCEPT_ONLY` do các thông số SL/TP/Exit và bộ lọc nhiễu chi tiết nằm sau lớp khóa passkey thành viên.
3. **Mô hình chi phí & Khớp lệnh:**
   - Spread 30 points = $0.30/oz = 3 pips trên XAUUSD.
   - Commission: 0,02%/chiều (~$7/lot 2 chiều).
   - Slippage: Mô phỏng theo mất cân bằng dòng lệnh $OFI_t$.
   - Swap: Sử dụng chi phí ma sát cố định theo lệnh; **không tính swap thả nổi hàng ngày**.
   - Drawdown: Đo trên Closed-Trade Balance (chuỗi lệnh đã đóng), **không đo Floating Equity nội nến**.
   - Khớp lệnh: Áp dụng Point-in-time Shift(1) tại giá mở nến sau; SL được ưu tiên chạm trước nếu cả High và Low cùng chạm trong 1 nến.

### Nguồn 2: `eafree.net` (Thư Mục 45 EA & Công Cụ MT4/MT5)
1. **Phân loại rủi ro & Đạo đức kiểm định:**
   - **10 EA bị gắn cờ TOXIC (Grid / Martingale / Cost Averaging):** Dùng hệ số nhân lot (1.3x - 1.5x) hoặc nhồi lệnh khi giá đi ngược, không cài Hard SL. Bị loại vào `catalog/rejected_log.json`.
   - **35 EA Clean:** Sử dụng Breakout, SMC, Trend, Scalping cơ bản. Đưa vào `catalog/master_leads.json`.
2. **Minh bạch tài khoản Live:**
   - 44/45 EA hoàn toàn KHÔNG có link Myfxbook hoặc MQL5 Signal tài khoản thật được kiểm chứng.
   - Chỉ duy nhất 1 EA (`GPlus EA MT4 v1.14`) cung cấp link Myfxbook nhưng là tài khoản **Demo**, không phải tài khoản Real.
   - Toàn bộ backtest hiển thị trên website là backtest MT5 nội bộ không mô phỏng trượt giá (zero-slippage).

---
*Tài liệu kiểm toán và kho lưu trữ được đóng gói chuẩn hóa theo chuẩn phòng sạch ngày 23/11/2026.*
