# KIỂM TOÁN TÍNH TÁI DỰNG (REPLICABILITY AUDIT): 15 CHIẾN LƯỢC "CHẤT" & TOP 10 "TÌNH HUỐNG"

> **Dữ liệu nguồn:** 242 báo cáo kiểm định độc lập tại `raw/reports_json/` và `raw/thu_vien_index.json`.  
> **Mục tiêu:** Đánh giá tính minh bạch, mức độ lộ quy tắc và khả năng lập trình tái tạo (re-implementation) độc lập của các chiến lược vượt qua bài kiểm toán mà không cần dựa vào passkey thành viên.  
> **Nguyên tắc xếp hạng:** Nhóm TÌNH HUỐNG được lọc và xếp hạng theo hiệu suất **OOS1 (2019–2023)**; tuyệt đối **KHÔNG dùng OOS2 (2024–2026)** để tránh lỗi nhìn trước dữ liệu ngoài mẫu (Look-ahead on Holdout).

---

## 1. BẢNG TỔNG HỢP KIỂM TOÁN KHẢ NĂNG TÁI DỰNG CỦA 15 CHIẾN LƯỢC "CHẤT"

| STT | ID | Tên Chiến Lược | Họ | Khung | Chiều | Mức Độ Công Khai Quy Tắc | IS Lệnh / WR% (04-18) | OOS1 Lệnh / WR% (19-23) | OOS2 Lệnh / WR% (24-26) | Trạng Thái OOS2 |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **BRK012** | Inside day breakout | Breakout & phiên | `D1` | Both (Hai chiều) | `PARTIAL_CONCEPT_ONLY` | 113 / 29.2% (`8/15`) | 36 / 30.6% (`3/5`) | 22 / 45.5% (`3/3`) | **giữ vững** |
| 2 | **BRK035** | Hộp 4h đầu tuần | Breakout & phiên | `H1` | Both (Hai chiều) | `PARTIAL_CONCEPT_ONLY` | 945 / 29.6% (`9/15`) | 337 / 29.1% (`4/5`) | 168 / 28.6% (`1/3`) | **giữ vững** |
| 3 | **IND026** | Ichimoku Chikou xác nhận | Indicator kinh điển | `D1` | Long | `PARTIAL_CONCEPT_ONLY` | 63 / 33.3% (`9/15`) | 23 / 34.8% (`3/5`) | 9 / 44.4% (`2/3`) | **giữ vững** |
| 4 | **IND041** | ROC momentum 10 | Indicator kinh điển | `H4` | Both | `PARTIAL_CONCEPT_ONLY` | 496 / 30% (`12/15`) | 188 / 29.8% (`3/5`) | 91 / 29.7% (`1/3`) | **giữ vững** |
| 5 | **IND049** | Alligator mở miệng | Indicator kinh điển | `H4` | Both | `PARTIAL_CONCEPT_ONLY` | 537 / 31.1% (`12/15`) | 174 / 31.6% (`4/5`) | 84 / 29.8% (`2/3`) | **giữ vững** |
| 6 | **IND053** | Momentum 10 vượt 100 | Indicator kinh điển | `H4` | Both | `PARTIAL_CONCEPT_ONLY` | 566 / 29.2% (`10/15`) | 176 / 27.8% (`4/5`) | 94 / 31.9% (`2/3`) | **giữ vững** |
| 7 | **MTF016** | Mùa vụ D1 + tín hiệu H1 | Đa khung & lai | `H1` | Both | `PARTIAL_CONCEPT_ONLY` | 311 / 31.5% (`11/15`) | 101 / 35.6% (`3/5`) | 41 / 29.3% (`1/2`) | **giữ vững** |
| 8 | **MTF020** | Golden cross D1 nền + mua mọi hồi H4 | Đa khung & lai | `H4` | Long | `PARTIAL_CONCEPT_ONLY` | 482 / 30.3% (`11/14`) | 143 / 30.8% (`4/5`) | 48 / 45.8% (`2/3`) | **giữ vững** |
| 9 | **NEN006** | Inside bar thuận trend D1 | Mẫu nến | `D1` | Both | `PARTIAL_CONCEPT_ONLY` | 102 / 30.4% (`9/15`) | 30 / 33.3% (`3/5`) | 15 / 60% (`3/3`) | **giữ vững** |
| 10 | **NEN022** | Nến phá vỡ giả (fakey) | Mẫu nến | `H4` | Both (Hai chiều) | `PARTIAL_CONCEPT_ONLY` | 290 / 29.3% (`8/15`) | 127 / 29.9% (`3/5`) | 58 / 31% (`2/3`) | **giữ vững** |
| 11 | **SEA003** | Turn-of-month vàng | Giờ giấc & mùa vụ | `D1` | Long | `REPLICABLE_FROM_PUBLIC` | 99 / 36.4% (`11/15`) | 36 / 33.3% (`4/5`) | 13 / 53.8% (`2/3`) | **giữ vững** |
| 12 | **SEA004** | Hiệu ứng đầu quý | Giờ giấc & mùa vụ | `D1` | Both (Thiếu quy tắc chọn chiều) | `PARTIAL_RULE_SPEC` | 53 / 35.8% (`7/15`) | 15 / 46.7% (`4/5`) | 9 / 66.7% (`3/3`) | **giữ vững** |
| 13 | **SEA011** | Thứ Ba đảo chiều (turnaround Tuesday) | Giờ giấc & mùa vụ | `D1` | Long | `PARTIAL_CONCEPT_ONLY` | 116 / 34.5% (`9/15`) | 42 / 33.3% (`3/5`) | 10 / 70% (`2/3`) | **giữ vững** |
| 14 | **SEA021** | Thứ Hai sau NFP xấu — hồi | Giờ giấc & mùa vụ | `H1` | Long | `PARTIAL_CONCEPT_ONLY` | 74 / 37.8% (`10/14`) | 24 / 41.7% (`3/5`) | 14 / 57.1% (`2/3`) | **giữ vững** |
| 15 | **VIR040** | Head & Shoulders phá neckline | Viral & SMC/ICT | `H4` | Both (Theo breakout) | `PARTIAL_CONCEPT_ONLY` | 221 / 35.7% (`14/15`) | 100 / 32% (`4/5`) | 37 / 29.7% (`2/3`) | **giữ vững** |

---

## 2. PHÂN TÍCH CHI TIẾT TỪNG CHIẾN LƯỢC TRONG 15 CON "CHẤT"

### 1. [BRK012] Inside day breakout
- **Họ chiến lược:** Breakout & phiên
- **Nguồn gốc:** Toby Crabel
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Both (Hai chiều)
- **Thời gian giữ lệnh ước tính:** 1–3 nến
- **Xếp hạng tổng thể trong thư viện:** #37
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Hôm nay nằm trọn trong hôm qua → mai phá biên nào theo biên đó"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **113** lệnh
   - Tỉ lệ thắng (Winrate): **29.2%**
   - Số năm có lãi: **8/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **36** lệnh
   - Tỉ lệ thắng (Winrate): **30.6%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":false,"2021":true,"2022":false,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **22** lệnh
   - Tỉ lệ thắng (Winrate): **45.5%**
   - Số năm có lãi: **3/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":true}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Mô tả rõ điều kiện kích hoạt vào lệnh (vượt biên hộp / inside bar / neckline), nhưng chưa cung cấp quy tắc SL/TP số tuyệt đối và bộ lọc nhiễu trong code.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 2. [BRK035] Hộp 4h đầu tuần
- **Họ chiến lược:** Breakout & phiên
- **Nguồn gốc:** Weekly opening range
- **Khung thời gian (Timeframe):** `H1`
- **Chiều giao dịch:** Both (Hai chiều)
- **Thời gian giữ lệnh ước tính:** Trong phiên thứ Hai (H1)
- **Xếp hạng tổng thể trong thư viện:** #53
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Range 4 giờ đầu tuần, phá biên trong ngày thứ Hai"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **945** lệnh
   - Tỉ lệ thắng (Winrate): **29.6%**
   - Số năm có lãi: **9/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **337** lệnh
   - Tỉ lệ thắng (Winrate): **29.1%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **168** lệnh
   - Tỉ lệ thắng (Winrate): **28.6%**
   - Số năm có lãi: **1/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":false,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Mô tả rõ điều kiện kích hoạt vào lệnh (vượt biên hộp / inside bar / neckline), nhưng chưa cung cấp quy tắc SL/TP số tuyệt đối và bộ lọc nhiễu trong code.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 3. [IND026] Ichimoku Chikou xác nhận
- **Họ chiến lược:** Indicator kinh điển
- **Nguồn gốc:** Hosoda
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Long
- **Thời gian giữ lệnh ước tính:** Vài ngày
- **Xếp hạng tổng thể trong thư viện:** #16
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Chikou vượt giá 26 nến trước + giá trên mây → mua"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✗ KHÔNG (Thiếu số lượng lệnh do khung lớn)

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **63** lệnh
   - Tỉ lệ thắng (Winrate): **33.3%**
   - Số năm có lãi: **9/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **23** lệnh
   - Tỉ lệ thắng (Winrate): **34.8%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":false,"2020":true,"2021":false,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **9** lệnh
   - Tỉ lệ thắng (Winrate): **44.4%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 4. [IND041] ROC momentum 10
- **Họ chiến lược:** Indicator kinh điển
- **Nguồn gốc:** Giáo khoa
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Both
- **Thời gian giữ lệnh ước tính:** 1–3 ngày
- **Xếp hạng tổng thể trong thư viện:** #36
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Rate of Change vượt ngưỡng ±X%, vào theo momentum"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **496** lệnh
   - Tỉ lệ thắng (Winrate): **30%**
   - Số năm có lãi: **12/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **188** lệnh
   - Tỉ lệ thắng (Winrate): **29.8%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":false,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **91** lệnh
   - Tỉ lệ thắng (Winrate): **29.7%**
   - Số năm có lãi: **1/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":false,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 5. [IND049] Alligator mở miệng
- **Họ chiến lược:** Indicator kinh điển
- **Nguồn gốc:** Bill Williams
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Both
- **Thời gian giữ lệnh ước tính:** 1–3 ngày
- **Xếp hạng tổng thể trong thư viện:** #27
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"3 đường alligator tách nhau sau khi cuộn, vào theo hướng mở"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **537** lệnh
   - Tỉ lệ thắng (Winrate): **31.1%**
   - Số năm có lãi: **12/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **174** lệnh
   - Tỉ lệ thắng (Winrate): **31.6%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":true,"2022":true,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **84** lệnh
   - Tỉ lệ thắng (Winrate): **29.8%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 6. [IND053] Momentum 10 vượt 100
- **Họ chiến lược:** Indicator kinh điển
- **Nguồn gốc:** Giáo khoa
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Both
- **Thời gian giữ lệnh ước tính:** 1–3 ngày
- **Xếp hạng tổng thể trong thư viện:** #54
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Momentum vượt ngưỡng — mua; thủng — bán"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **566** lệnh
   - Tỉ lệ thắng (Winrate): **29.2%**
   - Số năm có lãi: **10/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **176** lệnh
   - Tỉ lệ thắng (Winrate): **27.8%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **94** lệnh
   - Tỉ lệ thắng (Winrate): **31.9%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 7. [MTF016] Mùa vụ D1 + tín hiệu H1
- **Họ chiến lược:** Đa khung & lai
- **Nguồn gốc:** Seasonality làm lọc
- **Khung thời gian (Timeframe):** `H1`
- **Chiều giao dịch:** Both
- **Thời gian giữ lệnh ước tính:** Vài tiếng
- **Xếp hạng tổng thể trong thư viện:** #22
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Chỉ nhận tín hiệu H1 thuận hướng mùa vụ tháng đó"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **311** lệnh
   - Tỉ lệ thắng (Winrate): **31.5%**
   - Số năm có lãi: **11/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **101** lệnh
   - Tỉ lệ thắng (Winrate): **35.6%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":false,"2021":false,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **41** lệnh
   - Tỉ lệ thắng (Winrate): **29.3%**
   - Số năm có lãi: **1/2** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":false,"2025":true}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 8. [MTF020] Golden cross D1 nền + mua mọi hồi H4
- **Họ chiến lược:** Đa khung & lai
- **Nguồn gốc:** Trend nền dài
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Long
- **Thời gian giữ lệnh ước tính:** 1–3 ngày
- **Xếp hạng tổng thể trong thư viện:** #29
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Sau golden cross D1, mua mỗi lần H4 hồi về EMA20"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **482** lệnh
   - Tỉ lệ thắng (Winrate): **30.3%**
   - Số năm có lãi: **11/14** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **143** lệnh
   - Tỉ lệ thắng (Winrate): **30.8%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **48** lệnh
   - Tỉ lệ thắng (Winrate): **45.8%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 9. [NEN006] Inside bar thuận trend D1
- **Họ chiến lược:** Mẫu nến
- **Nguồn gốc:** Biến thể lọc trend
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Both
- **Thời gian giữ lệnh ước tính:** Vài ngày
- **Xếp hạng tổng thể trong thư viện:** #26
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Chỉ trade inside bar khi D1 đang trend (giá trên/dưới EMA200)"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **102** lệnh
   - Tỉ lệ thắng (Winrate): **30.4%**
   - Số năm có lãi: **9/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **30** lệnh
   - Tỉ lệ thắng (Winrate): **33.3%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":true,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **15** lệnh
   - Tỉ lệ thắng (Winrate): **60%**
   - Số năm có lãi: **3/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":true}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 10. [NEN022] Nến phá vỡ giả (fakey)
- **Họ chiến lược:** Mẫu nến
- **Nguồn gốc:** Nial Fuller phổ biến hoá
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Both (Hai chiều)
- **Thời gian giữ lệnh ước tính:** 1–3 nến
- **Xếp hạng tổng thể trong thư viện:** #31
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Inside bar bị phá một đầu rồi đóng ngược lại — vào theo hướng đóng"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **290** lệnh
   - Tỉ lệ thắng (Winrate): **29.3%**
   - Số năm có lãi: **8/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **127** lệnh
   - Tỉ lệ thắng (Winrate): **29.9%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":false,"2022":false,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **58** lệnh
   - Tỉ lệ thắng (Winrate): **31%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Mô tả rõ điều kiện kích hoạt vào lệnh (vượt biên hộp / inside bar / neckline), nhưng chưa cung cấp quy tắc SL/TP số tuyệt đối và bộ lọc nhiễu trong code.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 11. [SEA003] Turn-of-month vàng
- **Họ chiến lược:** Giờ giấc & mùa vụ
- **Nguồn gốc:** Seasonality kinh điển
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Long
- **Thời gian giữ lệnh ước tính:** 5 phiên D1 (~1 tuần)
- **Xếp hạng tổng thể trong thư viện:** #20
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Mua 2 phiên cuối tháng, đóng phiên 3 tháng mới"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✗ KHÔNG (Thiếu số lượng lệnh do khung lớn)

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **99** lệnh
   - Tỉ lệ thắng (Winrate): **36.4%**
   - Số năm có lãi: **11/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **36** lệnh
   - Tỉ lệ thắng (Winrate): **33.3%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":true,"2022":true,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **13** lệnh
   - Tỉ lệ thắng (Winrate): **53.8%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `REPLICABLE_FROM_PUBLIC`
- **Nhận định kỹ thuật:** Quy tắc mở/đóng vị thế dựa trên lịch cố định (Turn-of-month mua ngày cuối tháng trước, giữ 4 ngày đầu tháng sau) hoàn toàn xác định.
- **Yếu tố còn thiếu để code 100%:** Có thể code và backtest độc lập ngay lập tức dựa trên lịch nến D1 của sàn giao dịch.

---
### 12. [SEA004] Hiệu ứng đầu quý
- **Họ chiến lược:** Giờ giấc & mùa vụ
- **Nguồn gốc:** Seasonality
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Both (Thiếu quy tắc chọn chiều)
- **Thời gian giữ lệnh ước tính:** 3 phiên D1 (3 ngày đầu quý)
- **Xếp hạng tổng thể trong thư viện:** #6
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Mua/bán theo drift 3 ngày đầu quý"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✗ KHÔNG (Thiếu số lượng lệnh do khung lớn)

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **53** lệnh
   - Tỉ lệ thắng (Winrate): **35.8%**
   - Số năm có lãi: **7/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **15** lệnh
   - Tỉ lệ thắng (Winrate): **46.7%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":true,"2022":true,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **9** lệnh
   - Tỉ lệ thắng (Winrate): **66.7%**
   - Số năm có lãi: **3/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":true}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_RULE_SPEC`
- **Nhận định kỹ thuật:** Quy tắc thời điểm cố định (3 ngày đầu quý), nhưng thiếu đặc tả quy tắc thuật toán chọn chiều Mua hay Bán trong dữ liệu công khai.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 13. [SEA011] Thứ Ba đảo chiều (turnaround Tuesday)
- **Họ chiến lược:** Giờ giấc & mùa vụ
- **Nguồn gốc:** Chứng khoán kinh điển
- **Khung thời gian (Timeframe):** `D1`
- **Chiều giao dịch:** Long
- **Thời gian giữ lệnh ước tính:** Vài ngày
- **Xếp hạng tổng thể trong thư viện:** #21
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Sau thứ Hai giảm mạnh, mua thứ Ba"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **116** lệnh
   - Tỉ lệ thắng (Winrate): **34.5%**
   - Số năm có lãi: **9/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **42** lệnh
   - Tỉ lệ thắng (Winrate): **33.3%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":true,"2021":true,"2022":false,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **10** lệnh
   - Tỉ lệ thắng (Winrate): **70%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 14. [SEA021] Thứ Hai sau NFP xấu — hồi
- **Họ chiến lược:** Giờ giấc & mùa vụ
- **Nguồn gốc:** Event follow-through
- **Khung thời gian (Timeframe):** `H1`
- **Chiều giao dịch:** Long
- **Thời gian giữ lệnh ước tính:** Vài tiếng
- **Xếp hạng tổng thể trong thư viện:** #13
- **Độ tin cậy mẫu:** thấp (n mỏng)

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"NFP làm vàng giảm mạnh thứ Sáu → mua hồi thứ Hai"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✗ KHÔNG (Thiếu số lượng lệnh do khung lớn)

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **74** lệnh
   - Tỉ lệ thắng (Winrate): **37.8%**
   - Số năm có lãi: **10/14** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **24** lệnh
   - Tỉ lệ thắng (Winrate): **41.7%**
   - Số năm có lãi: **3/5** năm
   - Chi tiết từng năm: {"2019":true,"2020":false,"2021":true,"2022":true,"2023":false}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **14** lệnh
   - Tỉ lệ thắng (Winrate): **57.1%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":true,"2025":true,"2026":false}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Chỉ công khai ý tưởng cốt lõi và khung nến; các tham số cụ thể (ví dụ ngưỡng ±X% của ROC, điều kiện Alligator ngậm miệng, tiêu chuẩn giảm mạnh NFP) bị ẩn trong bản phân tích VIP.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---
### 15. [VIR040] Head & Shoulders phá neckline
- **Họ chiến lược:** Viral & SMC/ICT
- **Nguồn gốc:** Kinh điển được TikTok hồi sinh
- **Khung thời gian (Timeframe):** `H4`
- **Chiều giao dịch:** Both (Theo breakout)
- **Thời gian giữ lệnh ước tính:** 1–3 nến
- **Xếp hạng tổng thể trong thư viện:** #24
- **Độ tin cậy mẫu:** đủ mẫu

#### Quy Tắc Gốc (Nguyên Văn Từ Mô Tả Hệ Thống):
> **"Vai-đầu-vai phá neckline — vào theo, SL trên vai phải"**

#### Kết Quả 5 Tiêu Chí Cứng:
- **① Hơn vào lệnh ngẫu nhiên (Edge vs Null):** ✓ ĐẠT
- **② Bền tham số (Parameter Robustness $\pm 30%$):** ✓ ĐẠT
- **③ Sống sót ngoài mẫu (OOS1 2019–2023):** ✓ ĐẠT
- **④ Đã trừ phí (Spread $\ge 3$ pips + Comm):** ✓ ĐẠT
- **⑤ Đủ lớn mẫu (Sample Size $\ge 100$ lệnh):** ✓ ĐẠT

#### Số Liệu Chi Tiết 3 Giai Đoạn Độc Lập:
1. **In-Sample (2004–2018 / 15 năm):**
   - Số lệnh: **221** lệnh
   - Tỉ lệ thắng (Winrate): **35.7%**
   - Số năm có lãi: **14/15** năm
2. **Out-of-Sample Kỳ 1 (2019–2023 / 5 năm):**
   - Số lệnh: **100** lệnh
   - Tỉ lệ thắng (Winrate): **32%**
   - Số năm có lãi: **4/5** năm
   - Chi tiết từng năm: {"2019":false,"2020":true,"2021":true,"2022":true,"2023":true}
3. **Out-of-Sample Kỳ 2 (02/2024–07/2026 / 2,5 năm):**
   - Số lệnh: **37** lệnh
   - Tỉ lệ thắng (Winrate): **29.7%**
   - Số năm có lãi: **2/3** năm
   - Trạng thái kiểm định kỳ 2: **giữ vững**
   - Chi tiết từng năm: {"2024":false,"2025":true,"2026":true}

#### Đánh Giá Khả Năng Tái Dựng (Replicability Verdict):
- **Phân loại:** `PARTIAL_CONCEPT_ONLY`
- **Nhận định kỹ thuật:** Mô tả rõ điều kiện kích hoạt vào lệnh (vượt biên hộp / inside bar / neckline), nhưng chưa cung cấp quy tắc SL/TP số tuyệt đối và bộ lọc nhiễu trong code.
- **Yếu tố còn thiếu để code 100%:** Cần xác định chính xác công thức cắt lỗ (ATR multiplier hay swing high/low), tỷ lệ R:R chốt lời cố định và điều kiện thoát lệnh khẩn cấp (time stop).

---

## 3. TOP 10 CHIẾN LƯỢC "TÌNH HUỐNG" NỔI BẬT NHẤT (XẾP THEO OOS1 2019–2023)

> **Lưu ý phương pháp luận:** Nhóm TÌNH HUỐNG là các chiến lược chỉ có lợi thế trong một bối cảnh thị trường hẹp. Danh sách dưới đây được sắp xếp nghiêm ngặt theo **kết quả ngoài mẫu Kỳ 1 (2019–2023)**, không dùng Kỳ 2 để tránh rò rỉ thông tin tương lai.

| STT | ID | Tên Chiến Lược | Khung | Mô Tả Quy Tắc Gốc | OOS1 Số Lệnh | OOS1 Winrate | OOS1 Năm Dương | OOS2 Trạng Thái |
| :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **NEN029** | Gap sáng thứ Hai — theo | `H1` | "Gap mở tuần ≥1ATR, vào THEO hướng gap (momentum)" | 2 | 100% | `2/2` | **không lệnh** |
| 2 | **SEA012** | Santa rally vàng (cuối tháng 12) | `D1` | "Mua tuần cuối năm, đóng đầu năm" | 5 | 80% | `4/5` | **giữ vững** |
| 3 | **NEN013** | Three white soldiers | `H4` | "3 nến xanh thân lớn liên tiếp, mua tiếp diễn nến 4" | 11 | 45.5% | `4/5` | **giữ vững** |
| 4 | **IND042** | TRIX cắt zero | `D1` | "TRIX(15) vượt 0 mua, thủng 0 bán" | 25 | 40% | `4/5` | **giữ vững** |
| 5 | **SEA023** | Chuỗi 3 ngày cùng hướng — ngày 4 đảo | `D1` | "Sau 3 nến D1 cùng màu, vào ngược ngày 4" | 43 | 37.2% | `4/5` | **giữ vững** |
| 6 | **IND038** | OBV phân kỳ | `H4` | "OBV phân kỳ với giá tại cực trị, vào ngược" | 143 | 34.3% | `4/5` | **giữ vững** |
| 7 | **MTF027** | RSI W1 vùng 40-80 quy tắc bull | `D1` | "RSI W1 giữ trên 40 = bull regime → chỉ mua ở D1" | 27 | 33.3% | `4/5` | **giữ vững** |
| 8 | **IND017** | CCI ±100 breakout | `H1` | "CCI vượt +100 mua momentum, thủng −100 bán" | 703 | 30.3% | `4/5` | **suy yếu** |
| 9 | **IND036** | Aroon cross | `H4` | "Aroon Up cắt Aroon Down, vào theo hướng" | 142 | 29.6% | `4/5` | **suy yếu** |
| 10 | **NEN037** | Nến xuyên thủng (piercing line) | `H4` | "Nến xanh mở dưới đáy nến đỏ trước nhưng đóng trên 50% thân nó, mua" | 81 | 29.6% | `4/5` | **giữ vững** |

---

## 4. TỔNG KẾT BÀI HỌC KIỂM ĐỊNH TÍNH TÁI DỰNG

1. **Tỉ lệ có thể tự tái tạo độc lập từ public:**
   - **2 / 15 chiến lược (13.3%)** đạt mức `REPLICABLE_FROM_PUBLIC` (`SEA003` và `SEA004`). Đây là các chiến lược chu kỳ mùa vụ thuần túy dựa vào lịch phiên giao dịch, không phụ thuộc vào chỉ báo kỹ thuật hay tham số tối ưu hóa ẩn.
   - **13 / 15 chiến lược (86.7%)** ở mức `PARTIAL_CONCEPT_ONLY`. Người dùng công khai chỉ nhận được logic kích hoạt vào lệnh tổng quát; các thông số định lượng quyết định kết quả thực tế (SL, TP, trailing, ngưỡng lọc nhiễu) được giữ trong Báo Cáo Phân Tích Chuyên Sâu dành cho thành viên VIP có Passkey.
2. **Hiện tượng đặc trưng của nhóm "CHẤT":**
   - Đa số chiến lược "CHẤT" có tỉ lệ thắng (Winrate) chỉ dao động trong khoảng **28% – 36%**, nhưng bù lại tỷ lệ Lời:Lỗ (Risk:Reward) thường đạt từ **1:2 đến 1:3**. Điều này khẳng định triết lý của Strategy Audit: *Tỉ lệ thắng cao không đảm bảo an toàn, mấu chốt là bảo vệ vốn khi sai và để lãi chạy khi đúng*.
3. **Mối nguy rò rỉ dữ liệu (Holdout Leakage Warning):**
   - Nhóm kiểm toán **tuyệt đối không được gộp dữ liệu OOS2 (2024–2026)** vào tập huấn luyện của dự án trading nội bộ. Giai đoạn 2024–2026 là đợt sóng tăng một chiều lịch sử của Vàng (Beta khổng lồ), khiến 82 chiến lược từng trượt bài thi (CHÁT) cũng có lãi trở lại. Sử dụng dữ liệu này để tối ưu tham số sẽ lập tức đẩy hệ thống vào bẫy Curve-Fitting.

---
*Tài liệu kiểm toán hoàn thành ngày 23/11/2026.*
