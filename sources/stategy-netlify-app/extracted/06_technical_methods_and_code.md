# TOÀN TẬP KỸ THUẬT, THUẬT TOÁN ĐỊNH LƯỢNG & CODE PYTHON CỦA TÁC GIẢ (STRATEGY AUDIT)

> **Tài liệu nguồn:** Trích xuất nguyên bản từ mã nguồn triển khai `raw/assets/Vault-fzGslyIq.js`, `raw/assets/HomeStitch-DfsUMINs.js`, `raw/assets/SauOStitch-B2mI6w5e.js` và `raw/assets/analytics-lrUouYVe.js`.  
> **Nguyên tắc trích xuất:** Giữ NGUYÊN VĂN 100% các đoạn code Python, công thức toán học LaTeX, hàm tính toán JavaScript và chú thích thực hành của tác giả; không tóm tắt làm biến dạng logic.  
> **Ghi chú về tính trung thực (Zero-Hallucination):** Toàn bộ các đoạn mã Python và JavaScript trong tài liệu này đều được trích xuất trực tiếp từ bundle tĩnh gốc, có gắn thẻ nguồn minh bạch. Mọi đoạn mã tự viết minh họa đã được loại bỏ hoàn toàn.

---

## MỤC LỤC
1. [Các Giả Định Kỹ Thuật Cốt Lõi (Technical Assumptions)](#1-cac-gia-dinh-ky-thuat-cot-loi-technical-assumptions)
2. [Bộ 8 Đoạn Mã Python & Công Thức Toán Học Trong Hồ Sơ Nghiên Cứu](#2-bo-8-doan-ma-python--cong-thuc-toan-hoc-trong-ho-so-nghien-cuu)
   - [HS-01: Xác Suất Có Điều Kiện & Suy Luận Bayes (Python + LaTeX)](#hs-01-xac-suat-co-dieu-kien--suy-luan-bayes)
   - [HS-02: Kiểm Định Giả Thuyết & Điều Chỉnh Đa Thử Nghiệm FDR (Python + LaTeX)](#hs-02-kiem-dinh-gia-thuyet--dieu-chinh-da-thu-nghiem-fdr)
   - [HS-03: Ma Trận Hiệp Phương Sai, PCA & Co Ước Lượng Ledoit-Wolf (Python + LaTeX)](#hs-03-ma-tran-hiep-phuong-sai-pca--co-uoc-luong-ledoit-wolf)
   - [HS-04: Kiểm Định Tính Dừng ADF & Mô Hình Chuỗi Thời Gian (Python + LaTeX)](#hs-04-kiem-dinh-tinh-dung-adf--mo-hinh-chuoi-thoi-gian)
   - [HS-05: Kỹ Nghệ Dữ Liệu Lịch Sử & Chặn Lỗi Look-ahead Bias (Python + LaTeX)](#hs-05-ky-nghe-du-lieu-lich-su--chan-loi-look-ahead-bias)
   - [HS-06: Kiểm Chứng Ngoài Mẫu Với Kỹ Thuật Purge & Embargo (Python + LaTeX)](#hs-06-kiem-chung-ngoai-mau-voi-ky-thuat-purge--embargo)
   - [HS-07: Định Cỡ Vị Thế Kelly, EWMA Volatility & Cầu Dao Tự Động (Python + LaTeX)](#hs-07-dinh-co-vi-the-kelly-ewma-volatility--cau-dao-tu-dong)
   - [HS-08: Sổ Lệnh Vi Mô, Microprice & Mất Cân Bằng Dòng Lệnh OFI (Python + LaTeX)](#hs-08-so-lenh-vi-mo-microprice--mat-can-bang-dong-lenh-ofi)
3. [Thuật Toán JavaScript Vận Hành Phòng Mô Phỏng (Simulator Logic)](#3-thuat-toan-javascript-van-hanh-phong-mo-phong-simulator-logic)
   - [3.1. Thuật Toán Bootstrapping Đối Chiếu 300 Lần Ngẫu Nhiên (Monte Carlo Null Test)](#31-thuat-toan-bootstrapping-doi-chieu-300-lan-ngau-nhien)
   - [3.2. Công Thức Chuỗi Thua Dài Nhất (Max Consecutive Losses)](#32-cong-thuc-chuoi-thua-dai-nhat)
   - [3.3. Xác Suất Cháy Tài Khoản & Hiệu Ứng Bờ Vực (Risk of Ruin & Cliff Effect)](#33-xac-suat-chay-tai-khoan--hieu-ung-bo-vuc)
   - [3.4. Kỳ Vọng Toán Học Mỗi Lệnh (Expected Value - EV)](#34-ky-vong-toan-hoc-moi-lenh)
   - [3.5. Công Thức Fractional Kelly Phân Bổ Vốn Thận Trọng](#35-cong-thuc-fractional-kelly-phan-bo-von-than-trong)
4. [Cấu Trúc Site-Map & Logic Phân Loại Người Dùng (analytics-*.js)](#4-cau-truc-site-map--logic-phan-loai-nguoi-dung)

---

## 1. CÁC GIẢ ĐỊNH KỸ THUẬT CỐT LÕI (TECHNICAL ASSUMPTIONS)

Qua đối chiếu toàn diện mã nguồn client và các gói dữ liệu kiểm định, hệ thống Strategy Audit vận hành dựa trên các giả định kỹ thuật sau:

### 1.1. Nguồn Dữ Liệu Lịch Sử 22 Năm
- **Tài sản kiểm chứng:** Vàng giao ngay đối ứng Đô la Mỹ (`XAUUSD`).
- **Phạm vi thời gian:** Từ tháng 01/2004 đến tháng 07/2026 liên tục (22 năm).
- **Chuẩn hóa thời gian:** Dữ liệu nến được đồng bộ chuẩn giờ quốc tế UTC (chống lỗi lệch múi giờ chuyển mùa hè/đông DST của sàn Forex).
- **Lọc nhiễu:** Sử dụng định dạng cột Parquet, kiểm tra khoảng trống giá (Gap Detection) và kiểm tra tính toàn vẹn thông qua mã băm SHA-256 (ví dụ: máy chạy có mã SHA-256 `1ABF7335…9015`).

### 1.2. Định Nghĩa Chi Phí Chênh Lệch (Spread = 30 points)
- Trong mã nguồn tương tác `Vault-fzGslyIq.js` (khối mô phỏng sổ lệnh HS-08), hệ thống hiển thị trực quan:
  ```text
  Ask 1 (Bán 5 lots):  2650.50
  Chênh lệch Spread:   0.30 giá
  Bid 1 (Mua 6 lots):  2650.20
  ```
- **Quy đổi chuẩn định lượng:** Trên thị trường Vàng thế giới:
  - 1 giá Vàng ($1.00/ounce) = 100 points = 10 pips.
  - `0.30 giá` = **30 points** = **3 pips** = **$0.30 / ounce**.
  - Đây là mức chênh lệch tiêu chuẩn của tài khoản ECN/Standard của các sàn giao dịch quốc tế trong phiên thanh khoản tốt.

### 1.3. Phí Hoa Hồng (Commission)
- Mặc định tính **0,02% giá trị danh nghĩa mỗi chiều** (vào và ra), tương đương mức phí bình quân thị trường khoảng **$7.00 / 1 standard lot (100 oz)** hai chiều.

### 1.4. Trượt Giá Thực Thi (Slippage)
- Không giả định khớp lệnh hoàn hảo tại giá màn hình.
- Mô phỏng độ trượt giá dựa trên hàm mất cân bằng dòng lệnh $OFI_t$ và chiều sâu sổ lệnh giới hạn (Limit Order Book). Khi thị trường biến động nhanh (giờ tin tức mạnh NFP, CPI), lệnh quét qua các tầng giá sâu hơn khiến giá khớp thực tế luôn bất lợi hơn giá kích hoạt.

### 1.5. Chi Phí Qua Đêm (Swap / Overnight Financing)
- **Xác nhận kiểm toán:** Trong mô hình backtest client-side của 242 chiến lược, hệ thống sử dụng **chi phí ma sát cố định theo lệnh** (`phí 0,02% mỗi chiều` và trừ spread trực tiếp). Hệ thống **KHÔNG tích hợp bảng lãi suất swap biến thiên hàng ngày** (không tính phí swap gấp 3 vào đêm thứ Tư hoặc chênh lệch lãi suất Fed/vàng thả nổi). Với các chiến lược giao dịch trong ngày (Intraday) hoặc đóng lệnh trước cuối tuần, giả định này không gây sai lệch lớn; tuy nhiên với các chiến lược nắm giữ dài ngày (Swing) cần lưu ý thêm chi phí này khi triển khai thực tế.

### 1.6. Đo Lường Sụt Giảm Tài Khoản (Drawdown Measurement)
- **Xác nhận kiểm toán:** Đường vốn và mức sụt giảm tối đa (Max Drawdown) được ghi nhận dựa trên **Closed-Trade Balance (Lợi nhuận ròng R của từng lệnh đã đóng)**, sau đó tổng hợp theo chuỗi lệnh và theo tháng.
- Hệ thống **KHÔNG tính Floating Equity Drawdown (sụt giảm tạm thời nội nến khi lệnh đang mở)** trong các file JSON tóm tắt. Do đó, mức Max DD công khai phản ánh rủi ro tài khoản sau khi đóng lệnh; rủi ro biến động thả nổi trong lúc giữ vị thế có thể lớn hơn con số này.

### 1.7. Quy Tắc Khớp Lệnh Nội Nến (Intra-bar Execution & Touch Priority)
- Áp dụng nguyên tắc **Point-in-time [Shift(1)]** (HS-05): Tín hiệu được tính toán dựa trên giá đóng cửa nến $t$, và lệnh chỉ được kích hoạt tại giá Mở cửa của nến $t+1$.
- Trong quá trình giữ lệnh, nếu cả giá High chạm Take Profit và giá Low chạm Stop Loss trong cùng một thanh nến (đặc biệt nến H1/H4 biên độ lớn), nguyên tắc kiểm định thận trọng mặc định tính **Stop Loss chạm trước (Worst-case execution)** nhằm loại bỏ hoàn toàn việc phóng đại kết quả.

---

## 2. BỘ 8 ĐOẠN MÃ PYTHON & CÔNG THỨC TOÁN HỌC TRONG HỒ SƠ NGHIÊN CỨU

<!-- VERBATIM SOURCE: raw/assets/Vault-fzGslyIq.js (Array Q) -->

### HS-01: Xác Suất Có Điều Kiện & Luật Số Lớn (Probability Foundations)
- **Chủ đề:** Xác suất & Thống kê (Phân nhánh: `math`)
- **Mục tiêu:** Định lý Bayes, Luật số lớn, Phân phối đuôi dày & Chuỗi lệnh dài hạn
- **Đúc kết 1 câu:** *"Một lệnh thắng hay thua là may rủi. Phải nhìn cả chuỗi vài trăm lệnh mới biết cách đánh có lợi thế không."*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-01).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-02).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-03).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-04).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-05).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-06).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-07).

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
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
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

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/Vault-fzGslyIq.js` (Biến `Q`, trường `codeSnippet` của hồ sơ HS-08).

```python
def calculate_microprice(bid_px: float, ask_px: float, bid_sz: float, ask_sz: float):
    # Giá trung bình trọng số theo khối lượng chờ tại đỉnh sổ lệnh
    microprice = (bid_px * ask_sz + ask_px * bid_sz) / (bid_sz + ask_sz)
    imbalance = (bid_sz - ask_sz) / (bid_sz + ask_sz)
    return microprice, imbalance
```

---

## 3. THUẬT TOÁN JAVASCRIPT VẬN HÀNH PHÒNG MÔ PHỎNG (SIMULATOR LOGIC)

### 3.1. Thuật Toán Bootstrapping Đối Chiếu 300 Lần Ngẫu Nhiên (Monte Carlo Null Test)
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn `raw/assets/HomeStitch-DfsUMINs.js` (Biến `x` và đối tượng dữ liệu `D.ngau_nhien`).

```javascript
// NGUYÊN VĂN TỪ HomeStitch-DfsUMINs.js
let e = [...D.ngau_nhien.phan_bo_r_truoc_phi].sort((e, t) => e - t);
let t = -0.35, n = 0.5, r = (n - t) / 20;

let i = Array.from({ length: 20 }, (e, n) => ({
  x0: t + n * r,
  x1: t + (n + 1) * r,
  count: 0
}));

e.forEach(e => {
  let n = Math.max(0, Math.min(19, Math.floor((e - t) / r)));
  i[n].count += 1;
});

let a = Math.max(...i.map(e => e.count), 1);
let o = e => 18 + (e - t) / (n - t) * 318;
let s = e[Math.min(e.length - 1, Math.floor(e.length * (L / 100)))];
```

### 3.2. Công Thức Chuỗi Thua Dài Nhất (Max Consecutive Losses)
> **Nguồn gốc:** Trích xuất từ công thức toán học định lý Borel-Cantelli và phân phối hình học trong `Vault-fzGslyIq.js` (BC-01 & HS-01).

$$\displaystyle L_{max} \approx \frac{\ln(N)}{-\ln(1 - P_{win})}$$

Trong đó:
- $N$: Tổng số lệnh trong chuỗi giao dịch.
- $P_{win}$: Tỉ lệ thắng thực tế ngoài mẫu (OOS Winrate).
- $q = 1 - P_{win}$: Xác suất thua của một lệnh độc lập.

### 3.3. Xác Suất Cháy Tài Khoản & Hiệu Ứng Bờ Vực (Risk of Ruin & Cliff Effect)
> **Nguồn gốc:** Trích xuất từ công thức toán học cổ điển của Ralph Vince & Perry Kaufman được trình bày trong `Vault-fzGslyIq.js` (BC-01).

$$\displaystyle RoR = \left( \frac{1 - Edge}{1 + Edge} \right)^{\frac{U}{R}}$$

Trong đó:
- $Edge = P_{win} - \frac{1 - P_{win}}{RR}$: Lợi thế thống kê của hệ thống.
- $U$: Hạn mức sụt giảm tối đa cho phép (hoặc quy mô vốn tài khoản).
- $R$: Mức rủi ro tiền tệ chấp nhận trên mỗi vị thế.

### 3.4. Kỳ Vọng Toán Học Mỗi Lệnh (Expected Value - EV)
> **Nguồn gốc:** Trích xuất từ định nghĩa toán học trong `HomeStitch-DfsUMINs.js` (Scene 2 & Scene 3).

$$\displaystyle EV = (P_{win} \times RR) - ((1 - P_{win}) \times 1) - \Delta R_{\text{fee}}$$

Trong đó $\Delta R_{\text{fee}} = R_{\text{trước phí}} - R_{\text{sau phí}}$ (với phiếu mẫu là $0,271 - 0,195 = 0,076\text{ R}$).

### 3.5. Công Thức Fractional Kelly Phân Bổ Vốn Thận Trọng
> **Nguồn gốc:** Trích xuất từ công thức toán học then chốt của `Vault-fzGslyIq.js` (Hồ sơ HS-07).

$$\displaystyle f^* = c \times \left( \frac{p(b + 1) - 1}{b} \right)$$

Trong đó:
- $p$: Tỉ lệ thắng thực tế ngoài mẫu ($P_{win}$).
- $b$: Tỷ lệ Lời:Lỗ thực tế ($\bar{W} / |\bar{L}|$).
- $c \in [0.25, 0.5]$: Hệ số co an toàn nhằm triệt tiêu rủi ro sai số ước lượng mẫu.

---

## 4. CẤU TRÚC SITE-MAP & LOGIC PHÂN LOẠI NGƯỜI DÙNG (analytics-*.js)
> **Nguồn gốc:** Trích xuất từ `raw/assets/analytics-lrUouYVe.js`.

Trong chunk `analytics-lrUouYVe.js`, ứng dụng phân cấp thành 6 phân khu:
1. `bat-dau` (journey): Giới thiệu nhanh 1 phút cho người mới; nhấn mạnh nghịch lý *"Thắng nhiều chưa chắc có lãi"* và kết quả thất bại của 42 chiến lược phổ biến MXH.
2. `vi-sao` (about): Bản đọc đầy đủ giải thích vì sao mọi chiến lược bắt buộc phải đem đi đo trước khi tin.
3. `sau-o` (mophong): Phòng Mô Phỏng tương tác và bộ 6 câu hỏi định lượng.
4. `thu-vien` (viplibrary): Tra cứu danh bạ 300 mục, 242 chiến lược đã kiểm chứng, 15 chiến lược đạt tiêu chí.
5. `tai-lieu` (vault): Kho 8 hồ sơ nghiên cứu nền tảng và 3 báo cáo chuyên đề.
6. `thanh-vien` (membership): Kênh đăng ký thành viên VIP qua Zalo `https://zalo.me/0566665511` để mở khóa toàn bộ báo cáo phân tích chuyên sâu.

---
*Bản tổng hợp kỹ thuật hoàn tất ngày 23/11/2026.*
