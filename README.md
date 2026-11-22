# STRATEGY AUDIT DATA EXTRACTION & METHODOLOGY AUDIT REPO

> **Target Source:** https://stategy.netlify.app/  
> **Scan & Extraction Date:** Ngày 22–23/11/2026  
> **Repository Owner / Target Org:** `naqex` (chuẩn bị cho GitHub Organization `naqex`)  
> **Phạm vi thu thập:** Toàn bộ tài nguyên và dữ liệu công khai trên hạ tầng tĩnh Netlify CDN (không can thiệp hoặc vượt tường `x-passkey`).

---

## ⚠️ QUY TẮC BẢO VỆ DỮ LIỆU ĐỊNH LƯỢNG (CRITICAL NOTICE)

> **NGHIÊM CẤM TUYỆT ĐỐI:**  
> Không được sử dụng hoặc trộn tập dữ liệu **Out-of-Sample Kỳ 2 (2024-02-01 → 2026-07-07)** vào tập **Holdout / Testset** của hệ thống giao dịch nội bộ tại `Naqex/workspace`.  
> **Lý do định lượng:** Giai đoạn 2024–2026 là đợt sóng tăng một chiều lịch sử của Vàng giao ngay (Beta khổng lồ của thị trường), khiến 82 chiến lược từng trượt bài thi (CHÁT) cũng có lãi trở lại. Việc nạp dữ liệu này vào quá trình tối ưu hóa tham số sẽ gây lỗi rò rỉ dữ liệu tương lai (Look-ahead Bias on Holdout) và bẫy khớp đường cong (Curve-Fitting).

---

## 1. CẤU TRÚC THƯ MỤC REPO

```text
d:/ANNAM/stategy-netlify-app/
├── raw/                               # Dữ liệu gốc tải trực tiếp từ server Netlify CDN
│   ├── thu_vien_index.json            # Metadata tổng hợp 300 mục của thư viện
│   ├── vault_data.json                # Dữ liệu trích xuất từ Vault (3 BC + 8 HS)
│   ├── assets/                        # 39 file JS chunk và tài nguyên tĩnh
│   └── reports_json/                  # 242 file JSON chi tiết của từng chiến lược
├── extracted/                         # Bộ file bàn giao chuẩn hóa kiểm toán
│   ├── 01_methodology_and_reports.md  # Phương pháp luận kiểm định + 3 Báo Cáo + 8 Hồ Sơ
│   ├── 02_library_242_summary.json    # Bảng tổng hợp cấu trúc 242 chiến lược
│   ├── 02_library_242_summary.csv     # Bảng tổng hợp CSV (UTF-8 BOM) cho Excel/Pandas
│   ├── 03_simulator_logic.md          # Thuật toán Phòng Mô Phỏng (Sáu ô, Monte Carlo 300)
│   ├── 04_top15_chat_full.json        # Nguyên văn JSON 15 chiến lược "CHẤT"
│   ├── 05_replicability_audit.md      # Kiểm toán tính tái dựng 15 CHẤT & Top 10 Tình Huống
│   ├── 06_technical_methods_and_code.md# Code Python, công thức LaTeX & giả định kỹ thuật
│   └── 07_missing_58_items.json       # Báo cáo đối chiếu 58 mục chênh lệch (300 - 242)
├── scripts/                           # Toàn bộ script tái lập quy trình (100% Reproducible)
│   ├── build_01_methodology.js        # Script sinh 01_methodology_and_reports.md
│   ├── build_02_library_summary.js    # Script sinh 02_library_242_summary (json + csv)
│   ├── build_03_simulator.js          # Script sinh 03_simulator_logic.md
│   ├── extract_top15_chat.js          # Script sinh 04_top15_chat_full & 05_replicability
│   ├── extract_technical_methods.js   # Script sinh 06_technical_methods_and_code.md
│   └── reconcile_300_vs_242.js        # Script đối chiếu và sinh 07_missing_58_items.json
├── .gitignore                         # Loại bỏ file rác, file tạm hệ thống
└── README.md                          # Tài liệu hướng dẫn & Bảng băm SHA256 kiểm chứng
```

---

## 2. BẢNG BĂM SHA-256 KIỂM CHỨNG TÍNH TOÀN VẸN (EXTRACTED CHECKSUM)

Mọi tệp tin trong thư mục `extracted/` được kiểm chứng tính toàn vẹn thông qua mã băm SHA-256 sau:

| Tên Tệp Tin | Kích Thước (Bytes) | Mã Băm SHA-256 Checksum |
| :--- | :---: | :--- |
| `01_methodology_and_reports.md` | 34,807 | `84C581DB7739260876C69EE4DB05D4911F85023E064AA2ECB73458F1D4A3F966` |
| `02_library_242_summary.csv` | 65,470 | `EDE83026C7C9DB8D3E2EED402BB1FD92A5CAC175333F85F06CC1B48F3DBEF3F6` |
| `02_library_242_summary.json` | 431,524 | `1AFD2716C6ACDCFA584EC699D39D9C88EE0B978E71FF64D941F879F9C32F18B8` |
| `03_simulator_logic.md` | 12,226 | `7EE5BC4AF3B6AC85EFB35AB98A99DBAE6F02D8391ADE929BB2BF59FC00BB6B7D` |
| `04_top15_chat_full.json` | 22,603 | `3BCB023154FE20BF127B4673D342DB3B6214E69E2E283A673B0DF59D92CEBC53` |
| `05_replicability_audit.md` | 42,263 | `FB12B2B864B6D61A3C08686B318806E5489685B59346AF90854640657683ABBB` |
| `06_technical_methods_and_code.md` | 24,983 | `638B38D8D9D290CBB11596CF00E71F4965B9AE76CCFE0AF435A5A8491E1F7980` |
| `07_missing_58_items.json` | 23,074 | `CE1C9A8459C3D0536ED118AF36E921B33A5E7BEC13EBA265C1415273AF1942BD` |

---

## 3. TÓM TẮT ĐẶC TRƯNG KỸ THUẬT QUAN TRỌNG

1. **Chênh lệch 300 vs 242:** 
   - 242 chiến lược đã kiểm định đầy đủ bằng máy.
   - 40 hồ sơ gộp biến thể đối xứng (`trang_thai: "gop"`).
   - 18 hồ sơ chưa kiểm định (`trang_thai: "chua_kiem_dinh"`) do dựa trên vẽ tay cảm tính (trendlines).
2. **Khả năng tái dựng 15 chiến lược "CHẤT":**
   - 2 chiến lược (`SEA003`, `SEA004`) đạt mức `REPLICABLE_FROM_PUBLIC` vì dựa trên quy tắc lịch cố định.
   - 13 chiến lược còn lại ở mức `PARTIAL_CONCEPT_ONLY` do các thông số SL/TP/Exit và bộ lọc nhiễu chi tiết nằm trong bài phân tích chuyên sâu có Passkey.
3. **Mô hình chi phí & Khớp lệnh:**
   - Spread 30 points = $0.30/oz = 3 pips trên XAUUSD.
   - Commission: 0,02%/chiều (~$7/lot 2 chiều).
   - Slippage: Mô phỏng theo mất cân bằng dòng lệnh $OFI_t$.
   - Swap: Sử dụng chi phí cố định theo lệnh; không mô phỏng bảng swap thả nổi hàng ngày.
   - Drawdown: Đo trên Closed-Trade Balance (chuỗi lệnh đã đóng), không đo Floating Equity nội nến.
   - Khớp lệnh: Áp dụng Point-in-time Shift(1) tại giá mở nến sau; SL được ưu tiên chạm trước nếu cả High và Low cùng chạm trong 1 nến.

---
*Tài liệu kiểm toán và kho lưu trữ được đóng gói chuẩn hóa ngày 23/11/2026.*
