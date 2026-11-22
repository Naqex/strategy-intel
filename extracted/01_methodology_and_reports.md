# BÁO CÁO TOÀN DIỆN: PHƯƠNG PHÁP LUẬN KIỂM ĐỊNH & TOÀN VĂN TÀI LIỆU NGHIÊN CỨU (STRATEGY AUDIT)

> **Nguồn trích xuất:** https://stategy.netlify.app/  
> **Thời gian quét:** Ngày 22–23/11/2026  
> **Phạm vi:** Dữ liệu công khai phục vụ kiểm toán độc lập phương pháp luận (không can thiệp hệ thống thành viên/Zalo).  
> **Ghi chú về tính toàn vẹn:** Giữ nguyên văn toàn bộ số liệu, công thức toán học LaTeX, trích dẫn tài liệu học thuật và đoạn mã Python thực thi gốc.

---

## MỤC LỤC
1. [Phương Pháp Luận Kiểm Định (Audit Methodology)](#1-phuong-phap-luan-kiem-dinh-audit-methodology)
   - [1.1. Tập Dữ Liệu Nguồn & Khung Thời Gian](#11-tap-du-lieu-nguon--khung-thoi-gian)
   - [1.2. Chi Phí Ma Sát Giao Dịch Thực Tế (Friction Costs)](#12-chi-phi-ma-sat-giao-dich-thuc-te-friction-costs)
   - [1.3. Phân Đoạn Dữ Liệu Huấn Luyện & Chấm Thi Độc Lập (In-Sample / Out-of-Sample Split)](#13-phan-doan-du-lieu-huan-luyen--cham-thi-doc-lap-in-sample--out-of-sample-split)
   - [1.4. Bộ 5 Tiêu Chí Cứng Phân Loại Chiến Lược (Pass / Fail Criteria)](#14-bo-5-tieu-chi-cung-phan-loai-chien-luoc-pass--fail-criteria)
   - [1.5. Thống Kê Phân Bổ 242 Chiến Lược & Kỳ Thi Lần 2 (2024–2026)](#15-thong-ke-phan-bo-242-chien-luoc--ky-thi-lan-2-20242026)
   - [1.6. Kết Quả Kiểm Tra Độc Lập 4 Trường Phái Phổ Biến MXH (22.938 Lệnh)](#16-ket-qua-kiem-tra-doc-lap-4-truong-phai-pho-bien-mxh-22938-lenh)
2. [Toàn Văn 3 Báo Cáo Chuyên Đề (Special Research Reports)](#2-toan-van-3-bao-cao-chuyen-de-special-research-reports)
   - [BC-01: Xác Suất Cháy Tài Khoản (Risk of Ruin)](#bc-01-xac-suat-chay-tai-khoan-risk-of-ruin)
   - [BC-02: Lời Do Quy Tắc Hay Do Giá Tự Lên? (Alpha và Beta)](#bc-02-loi-do-quy-tac-hay-do-gia-tu-len-alpha-va-beta)
   - [BC-03: Bẫy Chỉnh Số Cho Đẹp Trên Quá Khứ (Curve-Fitting)](#bc-03-bay-chinh-so-cho-dep-tren-qua-khu-curve-fitting)
3. [Toàn Văn 8 Hồ Sơ Nghiên Cứu Định Lượng (Quantitative Research Dossiers)](#3-toan-van-8-ho-so-nghien-cuu-dinh-luong-quantitative-research-dossiers)
   - [HS-01: Xác Suất Có Điều Kiện & Luật Số Lớn (Probability Foundations)](#hs-01-xac-suat-co-dieu-kien--luat-so-lon-probability-foundations)
   - [HS-02: Kiểm Định Giả Thuyết & Bẫy Đa Thử Nghiệm (Statistical Traps)](#hs-02-kiem-dinh-gia-thuyet--bay-da-thu-nghiem-statistical-traps)
   - [HS-03: Ma Trận Tương Quan & Phân Rã Nhân Tố (Matrix & PCA)](#hs-03-ma-tran-tuong-quan--phan-ra-nhan-to-matrix--pca)
   - [HS-04: Chuỗi Thời Gian, Tính Dừng & Chu Kỳ Mùa Vụ (Time Series)](#hs-04-chuoi-thoi-gian-tinh-dung--chu-ky-mua-vu-time-series)
   - [HS-05: Kỹ Nghệ Dữ Liệu Lịch Sử & Chặn Lỗi Nhìn Trước Tương Lai (Data Pipeline)](#hs-05-ky-nghe-du-lieu-lich-su--chan-loi-nhin-truoc-tuong-lai-data-pipeline)
   - [HS-06: Kiểm Chứng Ngoài Mẫu (Out-of-Sample)](#hs-06-kiem-chung-ngoai-mau-out-of-sample)
   - [HS-07: Định Cỡ Vị Thế, Chuỗi Thua Dài Nhất & Cầu Dao Tự Động (Risk Sizing & Kill Switch)](#hs-07-dinh-co-vi-the-chuoi-thua-dai-nhat--cau-dao-tu-dong-risk-sizing--kill-switch)
   - [HS-08: Cấu Trúc Vi Mô Sổ Lệnh & Chi Phí Thực Thi Thực Tế (Market Microstructure)](#hs-08-cau-truc-vi-mo-so-lenh--chi-phi-thuc-thi-thuc-te-market-microstructure)
4. [Báo Cáo Minh Bạch: Các Khu Vực Bị Khóa Thành Viên & Phễu Thu Thập (Gatekeeping Audit)](#4-bao-cao-minh-bach-cac-khu-vuc-bi-khoa-thanh-vien--pheu-thu-thap-gatekeeping-audit)

---

## 1. PHƯƠNG PHÁP LUẬN KIỂM ĐỊNH (AUDIT METHODOLOGY)

Quy trình kiểm định tại **Strategy Audit** ("Đo trước khi tin") tuân thủ các nguyên tắc toán học thống kê và tài chính định lượng nghiêm ngặt, nhằm bóc tách giữa **Alpha** (lợi thế thực chất đến từ quy tắc) và **Beta / May rủi ngẫu nhiên** (lợi nhuận nhờ sóng thị trường hoặc ép số quá khứ).

### 1.1. Tập Dữ Liệu Nguồn & Khung Thời Gian
- **Tài sản kiểm chứng:** Vàng giao ngay đối ứng Đô la Mỹ (**XAUUSD**).
- **Độ dài dữ liệu lịch sử:** **22 năm liên tục** (từ tháng 01/2004 đến tháng 07/2026).
- **Khung thời gian (Timeframes):** Bao phủ đa khung từ ngắn đến dài: `M15`, `M30`, `H1`, `H4`, `D1`.
- **Định dạng & Toàn vẹn dữ liệu:** Lưu trữ theo định dạng cột Parquet chuẩn hóa múi giờ UTC, thuật toán phát hiện khoảng trống giá (Gap Detection), lọc nhiễu tick và kiểm tra Hash toàn vẹn (ví dụ: máy chạy SHA-256 `1ABF7335…9015`).

### 1.2. Chi Phí Ma Sát Giao Dịch Thực Tế (Friction Costs)
Mọi kết quả kiểm chứng **bắt buộc phải trừ chi phí ma sát thực tế** trước khi đưa ra kết luận:
1. **Phí hoa hồng (Commission):** Mặc định tính **0,02% mỗi chiều** (tương đương **$7 / standard lot** hai chiều vào-ra).
2. **Chênh lệch giá mua - bán (Spread):** Cố định tối thiểu **30 points (3 pips)** trong điều kiện thanh khoản bình thường; nới rộng theo các khung giờ chuyển phiên.
3. **Trượt giá thực thi (Slippage):** Mô phỏng trượt giá thực tế dựa trên độ sâu sổ lệnh giới hạn (Limit Order Book) và mất cân bằng dòng lệnh (OFI), đặc biệt trong các khung giờ thanh khoản mỏng hoặc tin tức mạnh.
4. **Phí qua đêm (Swap):** Tính khấu trừ trực tiếp theo số ngày nắm giữ vị thế.

### 1.3. Phân Đoạn Dữ Liệu Huấn Luyện & Chấm Thi Độc Lập (In-Sample / Out-of-Sample Split)
Toàn bộ 22 năm dữ liệu được phân chia nghiêm ngặt thành 3 giai đoạn độc lập:
- **Giai đoạn In-Sample (Ôn bài / Tối ưu tham số):** Từ **2004 đến 2018 (15 năm)**. Đây là khoảng dữ liệu duy nhất mà người thiết kế được phép nhìn để tối ưu bộ quy tắc và tham số.
- **Giai đoạn Out-of-Sample Kỳ 1 (Chấm thi độc lập lần 1):** Từ **2019 đến 2023 (5 năm)**. Dữ liệu bị khóa hoàn toàn trong lúc xây dựng quy tắc; chỉ đưa vào máy chấm điểm sau khi quy tắc đã cố định.
- **Giai đoạn Out-of-Sample Kỳ 2 (Chấm thi độc lập lần 2):** Từ **01/02/2024 đến 07/07/2026 (hơn 2 năm)**. Ngày chấm: **16/08/2026**. Quy tắc: Chấm một lần duy nhất trên dữ liệu mới xuất hiện, khai báo luật trước khi chấm; KHÔNG thay đổi kết luận gốc (verdict) từ kỳ 1 mà chỉ bổ sung nhãn cập nhật trạng thái thực tế.
- **Kỹ thuật Purge & Embargo:** Loại bỏ các thanh nến giáp ranh giữa các giai đoạn để triệt tiêu hoàn toàn rò rỉ thông tin chuỗi thời gian (Serial Correlation Leakage).

### 1.4. Bộ 5 Tiêu Chí Cứng Phân Loại Chiến Lược (Pass / Fail Criteria)
Một chiến lược chỉ được công nhận là **ĐẠT TIÊU CHÍ (CHẤT)** khi vượt qua toàn bộ 5 bài kiểm tra:

| Mã Tiêu Chí | Tên Tiêu Chí | Nội Dung Kiểm Định Khắt Khe | Ý Nghĩa Thống Kê |
| :--- | :--- | :--- | :--- |
| **`edge_vs_null`** | ① Hơn vào lệnh ngẫu nhiên? | So sánh phân phối lợi nhuận trung bình mỗi lệnh (R/lệnh trước phí) với **300 lần vào lệnh ngẫu nhiên (Monte Carlo)** cùng số lệnh và cùng cách thoát lệnh. Hệ thống phải vượt qua ngưỡng bách phân vị **95%** ($p < 0.05$). | Bác bỏ giả thuyết vô hiệu ($H_0$), chứng minh có lợi thế thống kê thực chất (Alpha) thay vì may rủi. |
| **`ben_tham_so`** | ② Đổi tham số ±30% còn lãi? | Thử nghiệm biến thiên các thông số chỉ báo/điều kiện (ví dụ: chu kỳ RSI, EMA, ngưỡng kích hoạt) trong biên độ $pm 30%$. Toàn bộ vùng lân cận phải duy trì có lãi. | Chống bẫy khớp đường cong (Curve-Fitting) và hiện tượng tối ưu hóa quá mức (Overfitting). |
| **`song_sot_oos`** | ③ Qua kỳ chấm 1 (2019–2023)? | Hệ thống duy trì lợi nhuận dương và đường vốn ổn định trên dữ liệu Out-of-Sample 5 năm mà thuật toán chưa từng nhìn thấy. | Kiểm tra khả năng tổng quát hóa (Generalization) khi thị trường thay đổi chu kỳ biến động. |
| **`chiu_phi`** | ④ Đã trừ phí? | Lợi nhuận ròng sau khi trừ đầy đủ phí hoa hồng 0,02%/chiều, spread $ge 3$ pips và trượt giá vẫn phải dương. | Loại bỏ các chiến lược tần suất cao bị chi phí giao dịch hai chiều bào mòn hết lợi thế. |
| **`kha_thi`** | ⑤ Đủ $ge 100$ lệnh? | Tổng số lượng lệnh phát sinh trong chuỗi kiểm định phải đạt tối thiểu từ **100 lệnh** trở lên (khuyến nghị $ge 300$ lệnh). | Đảm bảo độ tin cậy của Luật số lớn (Law of Large Numbers), tránh kết luận vội vã trên mẫu nhỏ. |

### 1.5. Thống Kê Phân Bổ 242 Chiến Lược & Kỳ Thi Lần 2 (2024–2026)
Trong tổng số **300 mục** của danh bạ thư viện:
- **242 chiến lược:** Đã hoàn tất quy trình kiểm định độc lập trên dữ liệu 22 năm.
- **40 hồ sơ:** Biến thể gộp / bản đối xứng của chiến lược gốc (ví dụ: phá 3 đỉnh gộp vào phá 3 đáy).
- **18 hồ sơ:** Chưa kiểm định (do quy tắc vẽ tay, cảm tính cá nhân, không thể lập trình khách quan).

**Kết quả phân loại chính thức của 242 chiến lược:**
1. **CHẤT (Đạt tiêu chí):** **15 chiến lược** (tỉ lệ **6,2%**).
2. **TÌNH HUỐNG (Phụ thuộc bối cảnh hẹp):** **39 chiến lược** (tỉ lệ **16,1%**).
3. **CHÁT (Không đạt tiêu chí):** **188 chiến lược** (tỉ lệ **77,7%**).

**Kết quả chấm thi độc lập Kỳ 2 (2024-02-01 → 2026-07-07, chấm ngày 16/08/2026):**
- **Giữ vững (44 chiến lược):** Nhóm CHẤT / TÌNH HUỐNG tiếp tục duy trì có lãi trên dữ liệu mới 2024–2026.
- **Suy yếu (9 chiến lược):** Nhóm CHẤT / TÌNH HUỐNG bị lỗ ở kỳ 2 (verdict gốc giữ nguyên, đưa vào diện theo dõi).
- **Lãi lại (82 chiến lược):** Nhóm CHÁT có lãi trở lại trên 2024–2026 do giá vàng tăng một chiều lịch sử (Beta thị trường), kết luận gốc KHÔNG đổi.
- **Vẫn rớt (104 chiến lược):** Nhóm CHÁT tiếp tục thua lỗ trên dữ liệu mới.
- **Không lệnh (3 chiến lược):** Không phát sinh tín hiệu vào lệnh trong giai đoạn.

### 1.6. Kết Quả Kiểm Tra Độc Lập 4 Trường Phái Phổ Biến MXH (22.938 Lệnh)
Strategy Audit thực hiện thử nghiệm trên **42 chiến lược nguyên bản** thuộc 4 trường phái được chia sẻ nhiều nhất trên mạng xã hội, cho máy chạy đúng luật qua **22.938 lệnh** trên dữ liệu độc lập:
- **SMC · ICT:** 18 chiến lược — **0 chiến lược vượt qua (0%)**.
- **Phá vỡ đầu phiên (ORB / Session Breakout):** 7 chiến lược — **0 chiến lược vượt qua (0%)**.
- **Chỉ số Sức mạnh Tương đối (RSI):** 12 chiến lược — **0 chiến lược vượt qua (0%)**.
- **Đường Trung bình Động Hội tụ Phân kỳ (MACD):** 5 chiến lược — **0 chiến lược vượt qua (0%)**.
> **Kết luận:** $42 / 42$ chiến lược nguyên bản phổ biến đều thất bại khi đem ra kiểm chứng độc lập. Ngược lại, chiến lược sống sót bền vững nhất lại là quy tắc cực kỳ đơn giản: **SEA003** (Hiệu ứng lịch: Mua ở 2 ngày giao dịch cuối tháng, chốt lệnh ở ngày giao dịch thứ 3 tháng mới) — không dùng chỉ báo, đạt tiêu chí 22 năm và tiếp tục có lãi kỳ 2024–2026.

---

## 2. TOÀN VĂN 3 BÁO CÁO CHUYÊN ĐỀ (SPECIAL RESEARCH REPORTS)

### BC-01: Xác Suất Cháy Tài Khoản (Risk of Ruin)
- **Chuyên mục:** Quản trị rủi ro
- **Thời lượng:** 6 phút đọc
- **Tóm tắt ngắn:** *Chứng minh toán học vì sao tỉ lệ thắng cao vẫn có thể mất sạch vốn nếu không tính trước chuỗi thua dài nhất.*

#### 1. Dẫn nhập
Nhiều người tin rằng chỉ cần có tỉ lệ thắng (Win Rate) cao thì tài khoản sẽ an toàn. Dữ liệu kiểm chứng trên hàng nghìn lệnh cho thấy điều ngược lại.

#### 2. Phân tích trọng tâm
Xác suất chạm ngưỡng dừng cuộc chơi (Risk of Ruin) phụ thuộc vào ba yếu tố đi liền với nhau: tỉ lệ thắng thực tế, tương quan giữa độ lớn lệnh thắng và lệnh thua, và quy mô vốn đặt vào mỗi lệnh.

Hiệu ứng bờ vực (Cliff effect): Khi giữ quy mô mỗi lệnh ở mức nhỏ và kỷ luật, xác suất chạm đáy sụt giảm gần như bằng không. Nhưng khi nâng quy mô lệnh lên quá lớn, rủi ro không tăng cộng tuyến tính mà vọt thẳng lên mức chắc chắn gặp sự cố khi gặp biến động ngược.

Trong một chuỗi 1.000 lệnh, ngay cả với tỉ lệ thắng 60 trên 100 lệnh, việc xuất hiện một chuỗi thua liên tiếp từ 10 đến 12 lệnh là hiện tượng toán học bình thường. Cùng một cách vào lệnh trong thư viện, cách chốt lời sớm cho tỉ lệ thắng khoảng 48 trên 100 lệnh (cao hơn các cách chốt khác), nhưng vì lệnh thắng nhỏ còn lệnh thua chịu đủ nên cộng cả chuỗi lại có kết quả gần như tệ nhất.

#### 3. Sự thật cốt lõi (Core Truth)
> **Khi tham gia các bài thi quỹ có giới hạn sụt giảm tối đa hẹp, khoảng đệm thực sự để chịu chuỗi thua chỉ là phần hạn mức sụt giảm đó chứ không phải tổng con số danh nghĩa. Không đo trước chuỗi thua dài nhất thì không thể định cỡ lệnh an toàn.**

---

### BC-02: Lời Do Quy Tắc Hay Do Giá Tự Lên? (Alpha và Beta)
- **Chuyên mục:** Phương pháp đo
- **Thời lượng:** 5 phút đọc
- **Tóm tắt ngắn:** *Bóc tách bản chất: Kết quả đến từ lợi thế thật của bộ quy tắc (Alpha) hay chỉ đang ăn may theo một đoạn xu hướng (Beta)?*

#### 1. Dẫn nhập
Khi đánh giá một phương pháp giao dịch, điều quan trọng nhất là tách bạch giữa biến động chung của thị trường (Beta) và lợi thế riêng có của bộ quy tắc (Alpha).

#### 2. Phân tích trọng tâm
Beta là hiện tượng nước lên thuyền lên. Một quy tắc chỉ chuyên mua vào trong đúng giai đoạn vàng tăng mạnh một chiều sẽ cho kết quả trông rất đẹp, nhưng đó là kết quả của đợt sóng chứ chưa chắc là lợi thế của quy tắc.

Alpha là lợi thế thực sự sau khi đã đối chiếu với việc vào lệnh ngẫu nhiên và đi qua nhiều giai đoạn thị trường khác nhau: tăng, giảm, đi ngang và biến động gắt.

Nếu một chiến lược chỉ ăn trong một đoạn thị trường ngắn rồi gãy khi bối cảnh đổi chiều, tại Strategy Audit phương pháp đó được xếp vào nhóm Phụ thuộc bối cảnh nhất định (39 chiến lược trong thư viện) hoặc Không đạt tiêu chí (188 chiến lược), chứ không được xếp nhóm Đạt tiêu chí.

#### 3. Sự thật cốt lõi (Core Truth)
> **Trên dữ liệu mới 02/2024–07/2026, cả 15 chiến lược đạt tiêu chí vẫn có lãi. Giai đoạn này vàng tăng mạnh nên nhiều chiến lược không đạt cũng có lãi; kết luận gốc không đổi.**

---

### BC-03: Bẫy Chỉnh Số Cho Đẹp Trên Quá Khứ (Curve-fitting)
- **Chuyên mục:** Chống ép số
- **Thời lượng:** 7 phút đọc
- **Tóm tắt ngắn:** *Tại sao 4 trường phái phổ biến nhất mạng xã hội qua 22.938 lệnh đều không vượt qua bài kiểm tra độc lập?*

#### 1. Dẫn nhập
Hãy hình dung việc bắn một mũi tên lên tường rồi mới lấy bút vẽ hồng tâm bao quanh mũi tên đó. Đó chính là những gì xảy ra khi người ta liên tục chỉnh tham số chỉ báo cho vừa khít với biểu đồ quá khứ.

#### 2. Phân tích trọng tâm
Khớp đường cong (Curve-fitting) xảy ra khi người thiết kế thử hàng chục chu kỳ RSI, MA hay khung giờ khác nhau, rồi chỉ giữ lại đúng bộ số tình cờ khớp đẹp nhất với dữ liệu cũ.

Thị trường tương lai không lặp lại từng nhịp nhiễu của quá khứ. Một bộ quy tắc càng bị ép sát vào dữ liệu cũ bằng nhiều điều kiện chồng chéo thì càng dễ vỡ vụn khi gặp dữ liệu mới chưa từng thấy.

Tại Strategy Audit, chúng tôi lấy 4 trường phái được chia sẻ nhiều nhất trên mạng (42 chiến lược), cho máy chạy đúng luật qua 22.938 lệnh trên dữ liệu độc lập. Kết quả: không có chiến lược nào vượt qua bài kiểm tra.

#### 3. Sự thật cốt lõi (Core Truth)
> **Thuốc thử duy nhất chống lại bẫy ép số là tách riêng phần dữ liệu dùng lúc chỉnh luật và phần dữ liệu dùng để chấm thi (Out-of-sample). Quy tắc càng đơn giản, ít tham số tự do, càng có cơ hội sống sót thực tế.**

---

## 3. TOÀN VĂN 8 HỒ SƠ NGHIÊN CỨU ĐỊNH LƯỢNG (QUANTITATIVE RESEARCH DOSSIERS)

### HS-01: Xác Suất Có Điều Kiện & Luật Số Lớn (Probability Foundations)
- **Chủ đề:** Xác suất & Thống kê (Phân nhánh: `math`)
- **Mục tiêu:** Định lý Bayes, Luật số lớn, Phân phối đuôi dày & Chuỗi lệnh dài hạn
- **Đúc kết 1 câu:** *"Một lệnh thắng hay thua là may rủi. Phải nhìn cả chuỗi vài trăm lệnh mới biết cách đánh có lợi thế không."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle P(A \mid B) = \frac{P(B \mid A) \cdot P(A)}{P(B)} \quad ; \quad \bar{X}_n \xrightarrow{n \to \infty} \mu$$

> **Giải thích công thức:** Một lệnh đơn lẻ là ngẫu nhiên, nhưng qua chuỗi 500 đến 1.000 lệnh, kết quả hội tụ về lợi thế thực của bộ quy tắc sau khi trừ chi phí giao dịch.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Xác suất có điều kiện P(A|B) và cập nhật niềm tin theo dữ liệu thực nghiệm Bayes
- Các phân phối nền tảng: Bernoulli, Binomial, Poisson, Normal và Student-t đuôi dày
- Luật số lớn (LLN) và Định lý giới hạn trung tâm (CLT) trên chuỗi hàng nghìn lệnh
- Mô phỏng xáo trộn Monte Carlo để quan sát chuỗi thua dài nhất trước khi áp dụng

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Trong kiểm định "Đo trước khi tin", mỗi chiến lược đều được chạy qua hàng nghìn lệnh trên 22 năm dữ liệu vàng thật có tính phí. Nếu chỉ nhìn vài lệnh thắng đầu tiên mà bỏ qua chuỗi thua dài nhất, tài khoản sẽ không trụ nổi tới lúc lợi thế phát huy.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Introduction to Probability + Stat 110** — *Tác giả:* Blitzstein & Hwang (Harvard). Ghi chú: Tài liệu nền tảng về tư duy xác suất có điều kiện
- **A Man for All Markets** — *Tác giả:* Edward O. Thorp. Ghi chú: Góc nhìn lịch sử về đo lường lợi thế bằng toán học

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Mô phỏng 10.000 lần tung đồng xu trên Python, cập nhật tỉ lệ thắng ước lượng theo phân phối Beta-Binomial.

```python
import numpy as np
from scipy import stats
# Mô phỏng cập nhật Bayes cho tỉ lệ thắng qua 100 lệnh
trades = np.random.default_rng(42).random(100) < 0.54
post = stats.beta(10 + trades.sum(), 10 + (~trades).sum())
print(f"Ước lượng tỉ lệ thắng trung bình: {post.mean():.3f}")
```

---

### HS-02: Kiểm Định Giả Thuyết & Bẫy Đa Thử Nghiệm (Statistical Traps)
- **Chủ đề:** Xác suất & Thống kê (Phân nhánh: `math`)
- **Mục tiêu:** Kiểm định H0, Hiệu chỉnh Benjamini-Hochberg & Bẫy thử nghiệm hàng loạt
- **Đúc kết 1 câu:** *"Thử đủ nhiều cách thì kiểu gì cũng có một cách trông rất đẹp nhờ ăn may. Hồ sơ này chỉ cách loại những cái đẹp nhờ may."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle p_{(k)} \le \frac{k}{m}\alpha \quad ; \quad E[\max_i Z_i] \approx \sqrt{2 \ln m}$$

> **Giải thích công thức:** Khi thử nghiệm hàng trăm biến thể tham số ngẫu nhiên, luôn có những biến thể trông vượt trội thuần túy do may mắn. Phải hiệu chỉnh ngưỡng kiểm định theo tổng số lần thử m.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Kiểm định giả thuyết H0: Bộ quy tắc vào lệnh có khác biệt thực sự so với vào lệnh ngẫu nhiên?
- Bẫy Multiple Testing: Kiểm soát tỉ lệ phát hiện sai lệch (FDR Benjamini-Hochberg)
- Sai số chuẩn tự tương quan Newey-West (HAC) cho chuỗi dữ liệu theo thời gian
- Đánh giá suy giảm hiệu quả khi chọn lọc từ hàng trăm bộ tham số (Selection Bias)

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Trong 242 chiến lược được kiểm định đầy đủ tại thư viện, có tới 188 chiến lược bị xếp Không đạt tiêu chí vì không vượt qua được ngưỡng kiểm chứng thống kê khi so với vào lệnh ngẫu nhiên hoặc bị sụp đổ ở kỳ chấm lại.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **All of Statistics** — *Tác giả:* Larry Wasserman (CMU). Ghi chú: Chương 1 đến 13 — nền tảng suy luận thống kê hiện đại
- **The Deflated Sharpe Ratio (2014)** — *Tác giả:* David Bailey & Marcos López de Prado. Ghi chú: Báo cáo học thuật về bẫy thử nghiệm đa tham số

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Xây dựng bài kiểm tra hoán vị (Permutation Test) 10.000 lần xáo trộn thứ tự lệnh để đo giá trị p-value thực tế.

```python
# Kiểm tra bẫy thử nghiệm đa biến (Multiple Testing)
from scipy import stats
from statsmodels.stats.multitest import multipletests
rng = np.random.default_rng(42)
raw_pvals = [stats.ttest_1samp(rng.normal(0, 1, 500), 0).pvalue for _ in range(200)]
print("Chưa hiệu chỉnh p < 0.05:", sum(p < 0.05 for p in raw_pvals))
print("Sau Benjamini-Hochberg:", multipletests(raw_pvals, method="fdr_bh")[0].sum())
```

---

### HS-03: Ma Trận Tương Quan & Phân Rã Nhân Tố (Matrix & PCA)
- **Chủ đề:** Xác suất & Thống kê (Phân nhánh: `math`)
- **Mục tiêu:** Ma trận hiệp phương sai, Phân tích thành phần chính PCA & Co ước lượng Ledoit-Wolf
- **Đúc kết 1 câu:** *"Nhiều chiến lược trông khác nhau nhưng thật ra cùng lên cùng xuống. Gộp lại không giảm rủi ro như mình tưởng."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle \Sigma_p = w^\top \Sigma w \quad ; \quad \Sigma = Q \Lambda Q^\top$$

> **Giải thích công thức:** Phân rã trị riêng (PCA) giúp bóc tách xem nhiều chiến lược có đang phụ thuộc vào cùng một nhân tố biến động ẩn hay thực sự độc lập với nhau.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Không gian véc-tơ, tích vô hướng, trị riêng và véc-tơ riêng (Eigendecomposition)
- Phân tích thành phần chính (PCA) để tách nhiễu và nhận diện nhân tố dẫn dắt chung
- Đo lường mức độ trùng lặp tín hiệu giữa các phương pháp giao dịch cùng khung giờ
- Kỹ thuật co ma trận Ledoit-Wolf Shrinkage giảm sai số ước lượng trên mẫu hữu hạn

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Nhiều trader dùng 5 chỉ báo khác nhau trên cùng một biểu đồ và tưởng rằng đã có 5 lớp xác nhận độc lập. Khi kiểm tra ma trận tương quan trong hồ sơ Strategy Audit, cả 5 chỉ báo thực chất đều phản ánh chung một biến động trễ.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Introduction to Linear Algebra + MIT 18.06** — *Tác giả:* Gilbert Strang (MIT OCW). Ghi chú: Tài liệu chuẩn mực về đại số tuyến tính ứng dụng
- **Convex Optimization** — *Tác giả:* Stephen Boyd & Lieven Vandenberghe (Stanford). Ghi chú: Lý thuyết tối ưu hóa có ràng buộc

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Phân rã PCA trên tập chuỗi kết quả của nhiều chiến lược để kiểm tra số lượng nhân tố độc lập thực sự.

```python
import numpy as np
# Phân rã trị riêng ma trận tương quan giữa các chiến lược
corr_matrix = np.corrcoef(strategy_series_matrix)
eigvals, eigvecs = np.linalg.eigh(corr_matrix)
explained_first = eigvals[-1] / eigvals.sum()
print(f"Nhân tố lớn nhất giải thích: {explained_first:.2f} tổng biến động")
```

---

### HS-04: Chuỗi Thời Gian, Tính Dừng & Chu Kỳ Mùa Vụ (Time Series)
- **Chủ đề:** Xác suất & Thống kê (Phân nhánh: `math`)
- **Mục tiêu:** Kiểm định tính dừng ADF, Cụm biến động GARCH, Ornstein-Uhlenbeck & Hiệu ứng Lịch
- **Đúc kết 1 câu:** *"Giá có lúc chạy một chiều, có lúc quay về. Hồ sơ này chỉ cách đo xem một nhịp lặp lại là thật hay chỉ trùng hợp."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle dX_t = \theta(\mu - X_t)dt + \sigma dW_t \quad ; \quad \tau_{1/2} = \frac{\ln 2}{\theta}$$

> **Giải thích công thức:** Quá trình Ornstein-Uhlenbeck mô tả lực kéo hồi quy về trạng thái cân bằng, trong khi chu kỳ bán rã (Half-life) đo thời gian cần để độ lệch thu hẹp một nửa.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Tính dừng (Stationarity) & Kiểm định Augmented Dickey-Fuller (ADF) trên chuỗi dữ liệu
- Hiện tượng cụm biến động (Volatility Clustering) và mô hình GARCH(1,1)
- Sự khác biệt bản chất giữa Tương quan ngắn hạn (Correlation) và Đồng tích hợp (Cointegration)
- Hiệu ứng mùa vụ và thời điểm theo lịch (Seasonality & Calendar Effects) trên dữ liệu vàng

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Thực tế từ thư viện 300 chiến lược: nhóm phương pháp dựa trên thời điểm và lịch (như mua ở 2 ngày giao dịch cuối tháng, bán ở ngày giao dịch thứ 3 tháng mới — mã SEA003) lại có tỉ lệ vượt qua bài kiểm tra cao gấp khoảng 3,5 lần các nhóm chỉ báo phức tạp.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Analysis of Financial Time Series** — *Tác giả:* Ruey S. Tsay. Ghi chú: Giáo trình phân tích chuỗi thời gian định lượng
- **Quantitative Trading** — *Tác giả:* Ernest P. Chan. Ghi chú: Phương pháp kiểm chứng tính dừng và hồi quy trung bình

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Kiểm định tính dừng ADF và tính chu kỳ bán rã trên chuỗi chênh lệch dữ liệu lịch sử.

```python
# Kiểm định tính dừng ADF trên chuỗi thời gian
from statsmodels.tsa.stattools import adfuller
adf_stat, p_val, *_ = adfuller(spread_series)
print(f"ADF Statistic: {adf_stat:.3f} | p-value: {p_val:.4f}")
```

---

### HS-05: Kỹ Nghệ Dữ Liệu Lịch Sử & Chặn Lỗi Nhìn Trước Tương Lai
- **Chủ đề:** Dữ liệu & Hệ thống (Phân nhánh: `systems`)
- **Mục tiêu:** Look-ahead Bias, Survivorship Bias, Đồng bộ múi giờ UTC, Gap Detection & Parquet
- **Đúc kết 1 câu:** *"Chạy thử trên quá khứ rất dễ vô tình dùng thông tin mà lúc đó chưa có, làm kết quả đẹp giả."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle S_t = f(\mathcal{F}_{t-1}) \quad ; \quad \mathcal{F}_{t-1} \cap \{P_t, P_{t+1}, \dots\} = \emptyset$$

> **Giải thích công thức:** Điều kiện đo lường nhân quả (Filtration ℱₜ₋₁): Tín hiệu Sₜ tại thời điểm t chỉ được phép là hàm của tập thông tin đã đóng ở bước t − 1, giao với tập giá tương lai phải bằng rỗng (∅).

#### 2. Các khái niệm nền tảng (Core Concepts)
- Cấu trúc dữ liệu lịch sử: Thanh giá theo giờ/ngày, dữ liệu khớp lệnh và sổ lệnh
- Các lỗi dữ liệu chí mạng: Look-ahead bias, Survivorship bias, lệch múi giờ UTC & DST, khoảng trống giá
- Lưu trữ và truy vấn dữ liệu 22 năm tốc độ cao với định dạng cột Parquet, DuckDB và Polars
- Đối chiếu tính toàn vẹn Point-in-Time: Chỉ dùng thông tin đã đóng xong tại thời điểm ra quyết định

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Dữ liệu đầu vào lệch thì mọi con số thống kê phía sau đều vô giá trị. Toàn bộ 242 hồ sơ đo đầy đủ của Strategy Audit đều chạy trên bộ dữ liệu vàng 22 năm đã làm sạch múi giờ và khóa chặt quy tắc chỉ đọc dữ liệu đã đóng.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Advances in Financial Machine Learning** — *Tác giả:* Marcos López de Prado. Ghi chú: Chương 2–5 về cấu trúc và làm sạch dữ liệu tài chính

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Viết quy trình kiểm tra dữ liệu lịch sử bằng Polars: phát hiện khoảng trống thời gian và khóa dịch chuyển tín hiệu shift(1).

```python
# Xác thực dữ liệu lịch sử sạch với Polars
import polars as pl
bars = pl.read_parquet("gold_historical.parquet")
assert bars.filter(pl.col("close") <= 0).height == 0
# Luôn dịch tín hiệu 1 bước để chặn Look-ahead Bias
bars = bars.with_columns(pl.col("signal_raw").shift(1).alias("executable_signal"))
```

---

### HS-06: Kiểm Chứng Ngoài Mẫu (Out-of-Sample)
- **Chủ đề:** Dữ liệu & Hệ thống (Phân nhánh: `systems`)
- **Mục tiêu:** Tách dữ liệu chỉnh luật / chấm thi, Purge & Embargo, Kiểm tra độ bền ngoài mẫu
- **Đúc kết 1 câu:** *"Đặt quy tắc trên một đoạn dữ liệu rồi chấm trên đoạn khác chưa từng nhìn, giống như học một đề rồi thi một đề khác."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle T_{\text{train}} \cap [t_0 - h, \; t_1 + e] = \emptyset \quad ; \quad \Delta P_{\text{impact}} \approx c \cdot \sigma_d \sqrt{\frac{Q}{V_d}}$$

> **Giải thích công thức:** Điều kiện không rò rỉ dữ liệu (Purge & Embargo): Tập huấn luyện T_train phải cắt bỏ hoàn toàn vùng chồng lấn nhãn h và khoảng đệm e quanh tập chấm thi [t₀, t₁], đồng thời tính trượt giá theo luật căn bậc hai khối lượng Q/V_d.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Kiểm chứng ngoài mẫu: Tách bạch giai đoạn xây dựng quy tắc và giai đoạn chấm thi độc lập
- Purge & Embargo: Cắt bỏ vùng chồng lấn tại biên giới hai tập dữ liệu để chống rò rỉ thông tin
- Chấm thi nhiều vòng: Kiểm tra số năm dương, số lệnh, tỉ lệ thắng và chuỗi thua dài nhất

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Tại Strategy Audit, 15 chiến lược đạt tiêu chí trong kỳ thi đầu (2019–2023) đã được đem chấm lại trên dữ liệu vàng hoàn toàn mới từ 02/2024 đến 07/2026. Trên dữ liệu mới 02/2024–07/2026, cả 15 chiến lược đạt tiêu chí vẫn có lãi. Giai đoạn này vàng tăng mạnh nên nhiều chiến lược không đạt cũng có lãi; kết luận gốc không đổi.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Algorithmic Trading** — *Tác giả:* Ernest P. Chan. Ghi chú: Phương pháp thiết lập quy trình kiểm chứng ngoài mẫu (Out-of-sample)

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Thiết lập bộ chia chuỗi thời gian TimeSeriesSplit có khoảng cách đệm (gap) để tách tập huấn luyện và tập kiểm chứng.

```python
# Chia dữ liệu kiểm chứng theo thời gian có khoảng đệm (Purge gap)
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5, gap=10)
for train_idx, test_idx in tscv.split(historical_data):
    in_sample = historical_data.iloc[train_idx]
    out_of_sample = historical_data.iloc[test_idx]
```

---

### HS-07: Định Cỡ Vị Thế, Chuỗi Thua Dài Nhất & Cầu Dao Tự Động
- **Chủ đề:** Dữ liệu & Hệ thống (Phân nhánh: `systems`)
- **Mục tiêu:** Nguyên lý Kelly thận trọng, Điều chỉnh theo biến động EWMA & Ngắt mạch Kill Switch
- **Đúc kết 1 câu:** *"Mỗi lệnh đánh bao nhiêu để chuỗi thua dài nhất, thứ chắc chắn sẽ đến, không làm cháy tài khoản."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle f^* = p - \frac{1 - p}{b} \quad ; \quad E[L_{\max}] \approx \frac{\ln N}{-\ln(1 - p)}$$

> **Giải thích công thức:** Trong chuỗi N = 1.000 lệnh, ngay cả một hệ thống có tỉ lệ thắng p = 50% cũng gần như chắc chắn xuất hiện chuỗi thua khoảng 10 lệnh liên tiếp.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Ước tính độ dài chuỗi thua liên tiếp dài nhất theo quy mô mẫu N và tỉ lệ thắng p
- Tại sao đặt cược vượt ngưỡng an toàn chắc chắn dẫn đến chạm ngưỡng dừng cuộc chơi
- Điều chỉnh quy mô vị thế ngược chiều với độ biến động thị trường (Volatility Targeting)
- Hệ thống cầu dao tự động (Kill Switch 3 tầng): Kiểm tra trước lệnh, giám sát tức thời và ngắt khẩn cấp

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Một phương pháp có quy tắc vào lệnh tốt vẫn có thể xóa sổ tài khoản nếu thiếu quy tắc dừng khi thị trường biến động bất thường. Tại Strategy Audit, phần quản trị rủi ro và ngưỡng dừng luôn là điều kiện bắt buộc.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Active Portfolio Management** — *Tác giả:* Richard Grinold & Ronald Kahn. Ghi chú: Nguyên tắc phân bổ và kiểm soát rủi ro hệ thống

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Viết hàm tính xác suất xuất hiện chuỗi thua k lệnh liên tiếp trong N lệnh và cổng kiểm tra ngắt mạch tự động.

```python
class RiskGate:
    def __init__(self, max_consecutive_losses: int = 12):
        self.max_consecutive_losses = max_consecutive_losses
        self.tripped = False

    def check_status(self, current_loss_streak: int):
        if current_loss_streak >= self.max_consecutive_losses:
            self.tripped = True
            return False, "CẦU DAO KÍCH HOẠT: VƯỢT NGƯỠNG CHUỖI THUA CHO PHÉP"
        return True, "HỆ THỐNG TRONG NGƯỠNG AN TOÀN"
```

---

### HS-08: Cấu Trúc Vi Mô Sổ Lệnh & Chi Phí Thực Thi Thực Tế
- **Chủ đề:** Dữ liệu & Hệ thống (Phân nhánh: `systems`)
- **Mục tiêu:** Sổ lệnh giới hạn (Limit Order Book), Chênh lệch giá Bid-Ask, Trượt giá & Thanh khoản
- **Đúc kết 1 câu:** *"Giá bạn thấy chưa phải giá bạn khớp. Chênh lệch giá và trượt giá ăn mòn những lợi thế nhỏ."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\displaystyle P_{\text{micro}} = \frac{P_{\text{bid}} Q_{\text{ask}} + P_{\text{ask}} Q_{\text{bid}}}{Q_{\text{bid}} + Q_{\text{ask}}} \quad ; \quad \text{OFI}_t = \Delta Q_{\text{bid}} - \Delta Q_{\text{ask}}$$

> **Giải thích công thức:** Giá khớp thực tế luôn chịu ảnh hưởng bởi độ dày sổ lệnh và chênh lệch mua-bán (spread). Bỏ qua chi phí này là nguyên nhân hàng đầu khiến chiến lược tần suất cao thất bại.

#### 2. Các khái niệm nền tảng (Core Concepts)
- Cơ chế vận hành của sổ lệnh giới hạn: Hàng đợi giá chào mua (Bids), giá chào bán (Asks)
- Hiện tượng lựa chọn bất lợi (Adverse Selection) khi đặt lệnh chờ trong giờ tin tức
- Tác động của phí giao dịch và độ trượt giá (Slippage) lên tổng kết quả sau 1.000 lệnh
- Tại sao các chiến lược lướt sóng khung quá nhỏ thường bị chi phí hai chiều bào mòn hết lợi thế

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
Khi kiểm định tại Strategy Audit, mọi lệnh đều bị tính đầy đủ chi phí chênh lệch và trượt giá thực tế. Rất nhiều chiến lược nhìn có vẻ thắng trên lý thuyết nhưng chuyển sang Không đạt tiêu chí ngay khi tính đúng chi phí khớp lệnh.

#### 4. Tài liệu học thuật tham khảo (Academic References)
- **Trading and Exchanges** — *Tác giả:* Larry Harris. Ghi chú: Tài liệu kinh điển giải thích cấu trúc thị trường và sổ lệnh
- **Algorithmic and High-Frequency Trading** — *Tác giả:* Álvaro Cartea & Sebastian Jaimungal. Ghi chú: Toán học về cấu trúc vi mô và thực thi lệnh

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
Tính toán giá trọng số khối lượng Microprice và mất cân bằng dòng lệnh (Order Flow Imbalance) từ dữ liệu sổ lệnh.

```python
def calculate_microprice(bid_px: float, ask_px: float, bid_sz: float, ask_sz: float):
    # Giá trung bình trọng số theo khối lượng chờ tại đỉnh sổ lệnh
    microprice = (bid_px * ask_sz + ask_px * bid_sz) / (bid_sz + ask_sz)
    imbalance = (bid_sz - ask_sz) / (bid_sz + ask_sz)
    return microprice, imbalance
```

---

## 4. BÁO CÁO MINH BẠCH: CÁC KHU VỰC BỊ KHÓA THÀNH VIÊN & PHỄU THU THẬP (GATEKEEPING AUDIT)

Qua quá trình rà soát toàn bộ tài nguyên mạng và mã nguồn JavaScript của ứng dụng `https://stategy.netlify.app/`, Strategy Audit xác định các cơ chế giới hạn truy cập đối với người dùng công khai:

### 4.1. Nút "Tải Về Trọn Bộ Tài Liệu PDF" (Lead Capture Form)
- **Vị trí:** Xuất hiện tại giao diện Kho Nghiên Cứu (`/vault`).
- **Hành vi thực tế:** Không chứa liên kết direct download đến tệp `.pdf` công khai. Khi người dùng nhấp chuột, hệ thống kích hoạt modal form thu thập khách hàng tiềm năng:
  - Trường 1: Họ và tên (tối thiểu 2 ký tự).
  - Trường 2: Số điện thoại / Zalo (8–15 chữ số).
  - Trường 3: Địa chỉ Email (đúng định dạng RFC).
- **Mục đích:** Thu thập thông tin liên hệ để đội ngũ hỗ trợ gửi tài liệu thủ công qua kênh Zalo (`https://zalo.me/0566665511`) hoặc Email.

### 4.2. Báo Cáo Phân Tích Chuyên Sâu (Deep Dive Reports)
- **Vị trí:** Xuất hiện tại cửa sổ chi tiết (Modal) của từng chiến lược trong Thư viện (`/vip`).
- **Phần công khai:** Mọi người dùng đều xem được miễn phí:
  1. Tên, họ chiến lược, khung thời gian, nguồn gốc và mô tả ngắn quy tắc.
  2. Bảng trạng thái 5 tiêu chí cứng (`edge_vs_null`, `ben_tham_so`, `song_sot_oos`, `chiu_phi`, `kha_thi`).
  3. Bảng số liệu chi tiết 3 giai đoạn: In-Sample (2004–2018), Out-of-Sample Kỳ 1 (2019–2023) và Out-of-Sample Kỳ 2 (2024–2026), bao gồm số lệnh, winrate % và số năm dương.
- **Phần bị khóa:** Khối văn bản *"Báo Cáo Phân Tích Chuyên Sâu"* (chứa giải phẫu mã nguồn, bộ quy tắc vào/ra lệnh chi tiết từng nến, tham số tối ưu hóa và nhật ký lệnh) được bảo vệ bằng cơ chế xác thực `x-passkey` gửi về backend Netlify Functions / Google Apps Script (`https://script.google.com/macros/s/AKfycbyH6xzJc9J4Dj8fKJi-Rp91tfeS0tZbLtjz0m26bON4kjLKFnMLjS8btAxo66CoPDCGbA/exec?action=article`). Nếu không có passkey thành viên VIP, giao diện hiển thị lớp phủ mờ (opacity 60%, pointer-events-none) và hướng dẫn liên hệ Zalo để đăng ký thành viên.

### 4.3. Đánh Giá Khách Quan Về Mặt Kỹ Thuật
- Toàn bộ dữ liệu định lượng cốt lõi (242 file JSON chi tiết, metadata 300 chiến lược, nội dung 3 Báo Cáo Chuyên Đề, 8 Hồ Sơ Nghiên Cứu, công thức LaTeX và mã nguồn mẫu) **được phân phối công khai hoàn toàn trên hạ tầng tĩnh Netlify CDN**.
- Cơ chế khóa bài viết chuyên sâu và form tải PDF thuần túy là lớp giao diện người dùng (Client-side Gatekeeping) kết hợp backend quản lý thành viên thủ công.

---
*Báo cáo được tổng hợp tự động và trích xuất nguyên bản từ mã nguồn triển khai thực tế.*
