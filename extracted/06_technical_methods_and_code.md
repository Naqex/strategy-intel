# TOÀN TẬP KỸ THUẬT, THUẬT TOÁN ĐỊNH LƯỢNG & CODE PYTHON CỦA TÁC GIẢ (STRATEGY AUDIT)

> **Tài liệu nguồn:** Trích xuất nguyên bản từ mã nguồn triển khai `Vault-fzGslyIq.js`, `HomeStitch-DfsUMINs.js`, `SauOStitch-B2mI6w5e.js` và `analytics-lrUouYVe.js`.  
> **Nguyên tắc trích xuất:** Giữ NGUYÊN VĂN 100% các đoạn code Python, công thức toán học LaTeX, hàm tính toán JavaScript và chú thích thực hành của tác giả; không tóm tắt làm biến dạng logic.

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

### HS-01: Xác Suất Có Điều Kiện & Suy Luận Bayes
- **Mã hồ sơ:** `HS-01` | **Phân nhánh:** `math` (Xác suất & Thống kê)
- **Mục tiêu:** Định lý Bayes, Luật số lớn, Phân phối đuôi dày & Chuỗi lệnh dài hạn.
- **Tóm tắt cốt lõi:** *"Một lệnh thắng hay thua là may rủi. Phải nhìn cả chuỗi vài trăm lệnh mới biết cách đánh có lợi thế không."*

#### Công Thức Toán Học:
$$\displaystyle P(A|B) = \frac{P(B|A) P(A)}{P(B)} \quad ; \quad \lim_{n \to \infty} \frac{1}{n} \sum_{i=1}^n X_i = \mathbb{E}[X]$$

> **Giải thích công thức:** Định lý Bayes cập nhật xác suất có lợi thế thực của hệ thống khi có thêm dữ liệu lệnh mới. Luật số lớn đảm bảo kết quả chỉ phản ánh đúng năng lực khi quy mô mẫu đủ lớn.

#### Ứng Dụng Thực Hành:
Cập nhật niềm tin về tỉ lệ thắng thực tế bằng phân phối Beta tiền nghiệm và hợp lý nhị thức (Binomial Likelihood).

#### Đoạn Mã Python Gốc:
```python
import numpy as np
from scipy import stats

# Mô phỏng cập nhật Bayes cho tỉ lệ thắng (Winrate) của hệ thống
# Phân phối tiền nghiệm (Prior): Beta(2, 2)
prior_alpha, prior_beta = 2, 2

# Dữ liệu thực nghiệm qua 100 lệnh: 58 lệnh thắng, 42 lệnh thua
wins, losses = 58, 42
post_alpha = prior_alpha + wins
post_beta = prior_beta + losses

# Phân phối hậu nghiệm (Posterior)
post = stats.beta(post_alpha, post_beta)
ci_95 = post.interval(0.95)
print(f"Ước lượng tỉ lệ thắng trung bình: {post.mean():.3f}")
print(f"Khoảng tin cậy 95%: [{ci_95[0]:.3f}, {ci_95[1]:.3f}]")
```

---

### HS-02: Kiểm Định Giả Thuyết & Điều Chỉnh Đa Thử Nghiệm FDR
- **Mã hồ sơ:** `HS-02` | **Phân nhánh:** `math` (Xác suất & Thống kê)
- **Mục tiêu:** Kiểm định H0, Hiệu chỉnh Benjamini-Hochberg & Bẫy thử nghiệm hàng loạt.
- **Tóm tắt cốt lõi:** *"Thử đủ nhiều cách thì kiểu gì cũng có một cách trông rất đẹp nhờ ăn may. Hồ sơ này chỉ cách loại những cái đẹp nhờ may."*

#### Công Thức Toán Học:
$$\displaystyle P(k \ge 1) = 1 - (1 - \alpha)^m \quad ; \quad P_{(i)} \le \frac{i}{m} Q$$

> **Giải thích công thức:** Xác suất xuất hiện ít nhất một phát hiện sai tăng bùng nổ khi thử nghiệm $m$ biến thể. Thủ tục Benjamini-Hochberg kiểm soát tỉ lệ phát hiện sai (FDR) ở mức $Q$.

#### Ứng Dụng Thực Hành:
Xây dựng bài kiểm tra hoán vị (Permutation Test) 10.000 lần xáo trộn thứ tự lệnh để đo giá trị p-value thực tế.

#### Đoạn Mã Python Gốc:
```python
# Kiểm tra bẫy thử nghiệm đa biến (Multiple Testing)
from scipy import stats
from statsmodels.stats.multitest import multipletests
import numpy as np

rng = np.random.default_rng(42)
# Giả sử thử nghiệm 50 biến thể chỉ báo ngẫu nhiên không có lợi thế thực
p_values = [stats.ttest_1samp(rng.normal(0, 1, 100), 0).pvalue for _ in range(50)]

# Hiệu chỉnh kiểm soát tỉ lệ phát hiện sai Benjamini-Hochberg (FDR)
rejected, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method="fdr_bh")
print(f"Chưa hiệu chỉnh p < 0.05: {sum(p < 0.05 for p in p_values)}")
print(f"Sau hiệu chỉnh Benjamini-Hochberg: {sum(rejected)}")
```

---

### HS-03: Ma Trận Hiệp Phương Sai, PCA & Co Ước Lượng Ledoit-Wolf
- **Mã hồ sơ:** `HS-03` | **Phân nhánh:** `math` (Xác suất & Thống kê)
- **Mục tiêu:** Ma trận hiệp phương sai, Phân tích thành phần chính PCA & Co ước lượng Ledoit-Wolf.
- **Tóm tắt cốt lõi:** *"Nhiều chiến lược trông khác nhau nhưng thật ra cùng lên cùng xuống. Gộp lại không giảm rủi ro như mình tưởng."*

#### Công Thức Toán Học:
$$\displaystyle \Sigma = \mathbb{E}[(X - \mu)(X - \mu)^T] \quad ; \quad \Sigma^* = \alpha F + (1-\alpha)\Sigma$$

> **Giải thích công thức:** Phân tích ma trận tương quan bóc tách các chiến lược tưởng như độc lập nhưng cùng chịu rủi ro chung từ một nhân tố tiềm ẩn (Latent Factor).

#### Ứng Dụng Thực Hành:
Phân rã chuỗi lợi nhuận của danh mục nhiều chiến lược để tìm xem có bao nhiêu nguồn lợi thế thực sự độc lập.

#### Đoạn Mã Python Gốc:
```python
import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.decomposition import PCA

# Giả lập ma trận lợi nhuận 5 chiến lược qua 250 phiên
rng = np.random.default_rng(42)
returns = rng.normal(0, 0.01, (250, 5))

# Co ước lượng Ledoit-Wolf để làm sạch nhiễu ma trận hiệp phương sai
lw = LedoitWolf().fit(returns)
clean_cov = lw.covariance_

# Phân tích thành phần chính PCA
pca = PCA().fit(returns)
explained_first = pca.explained_variance_ratio_[0]
print(f"Nhân tố lớn nhất giải thích: {explained_first:.2f} tổng biến động")
```

---

### HS-04: Kiểm Định Tính Dừng ADF & Mô Hình Chuỗi Thời Gian
- **Mã hồ sơ:** `HS-04` | **Phân nhánh:** `math` (Xác suất & Thống kê)
- **Mục tiêu:** Kiểm định tính dừng ADF, Cụm biến động GARCH, Ornstein-Uhlenbeck & Hiệu ứng lịch.
- **Tóm tắt cốt lõi:** *"Giá có lúc chạy một chiều, có lúc quay về. Hồ sơ này chỉ cách đo xem một nhịp lặp lại là thật hay chỉ trùng hợp."*

#### Công Thức Toán Học:
$$\displaystyle \Delta y_t = \alpha + \beta t + \gamma y_{t-1} + \sum_{i=1}^p \delta_i \Delta y_{t-i} + \varepsilon_t$$

> **Giải thích công thức:** Kiểm định Augmented Dickey-Fuller (ADF) xác định một chuỗi chênh lệch giá có tính dừng (Stationary) và hồi quy trung bình (Mean-reverting) hay không.

#### Ứng Dụng Thực Hành:
Kiểm định tính dừng của chuỗi chênh lệch giá giữa hai phiên giao dịch để kiểm tra hiệu ứng phục hồi trung bình.

#### Đoạn Mã Python Gốc:
```python
import numpy as np
from statsmodels.tsa.stattools import adfuller

# Tạo chuỗi giả lập quá trình hồi quy trung bình Ornstein-Uhlenbeck
rng = np.random.default_rng(42)
spread_series = np.zeros(500)
theta, mu, sigma = 0.15, 0.0, 0.5
for t in range(1, 500):
    spread_series[t] = spread_series[t-1] + theta * (mu - spread_series[t-1]) + sigma * rng.normal()

# Kiểm định nghiệm đơn vị Augmented Dickey-Fuller
adf_stat, p_val, _, _, _, _ = adfuller(spread_series)
print(f"ADF Statistic: {adf_stat:.3f} | p-value: {p_val:.4f}")
```

---

### HS-05: Kỹ Nghệ Dữ Liệu Lịch Sử & Chặn Lỗi Look-ahead Bias
- **Mã hồ sơ:** `HS-05` | **Phân nhánh:** `systems` (Dữ liệu & Hệ thống)
- **Mục tiêu:** Look-ahead Bias, Survivorship Bias, Đồng bộ múi giờ UTC, Gap Detection & Point-in-time.
- **Tóm tắt cốt lõi:** *"Chạy thử trên quá khứ rất dễ vô tình dùng thông tin mà lúc đó chưa có, làm kết quả đẹp giả."*

#### Công Thức Toán Học:
$$\displaystyle \mathcal{I}_t = \sigma(X_s : s \le t) \quad ; \quad S_t \in \mathcal{I}_{t-1}$$

> **Giải thích công thức:** Mọi quyết định vào lệnh tại thời điểm $t$ chỉ được phép sử dụng thông tin đã đóng nến thuộc tập thông tin quá khứ $\mathcal{I}_{t-1}$, triệt tiêu Look-ahead Bias.

#### Ứng Dụng Thực Hành:
Xây dựng đường ống nạp dữ liệu nến chuẩn hóa bằng Polars, tự động phát hiện khoảng trống thời gian và kiểm tra rò rỉ dữ liệu tương lai.

#### Đoạn Mã Python Gốc:
```python
import polars as pl

# Chuẩn bị dữ liệu và dịch chuyển tín hiệu để đảm bảo không rò rỉ tương lai
bars = pl.DataFrame({
    "timestamp": ["2026-01-01 00:00:00", "2026-01-01 01:00:00", "2026-01-01 02:00:00"],
    "close": [2650.0, 2655.0, 2648.0],
    "raw_signal": [0, 1, -1]
})

# Luôn dịch tín hiệu 1 bước để chặn Look-ahead Bias
bars = bars.with_columns(
    pl.col("raw_signal").shift(1).alias("executable_signal")
)
print(bars)
```

---

### HS-06: Kiểm Chứng Ngoài Mẫu Với Kỹ Thuật Purge & Embargo
- **Mã hồ sơ:** `HS-06` | **Phân nhánh:** `systems` (Dữ liệu & Hệ thống)
- **Mục tiêu:** Tách dữ liệu chỉnh luật / chấm thi, Purge & Embargo, Kiểm tra độ bền ngoài mẫu.
- **Tóm tắt cốt lõi:** *"Đặt quy tắc trên một đoạn dữ liệu rồi chấm trên đoạn khác chưa từng nhìn, giống như học một đề rồi thi một đề khác."*

#### Công Thức Toán Học:
$$\displaystyle \text{SR}_{\text{deflated}} = \text{DSR}(\widehat{\text{SR}}, \{ \widehat{\text{SR}}_k \}, T, \gamma_3, \gamma_4)$$

> **Giải thích công thức:** Deflated Sharpe Ratio của Bailey & López de Prado hiệu chỉnh tỉ số Sharpe dựa trên số lần thử nghiệm, độ bất đối xứng và độ nhọn của phân phối lợi nhuận.

#### Ứng Dụng Thực Hành:
Tách chuỗi nến thành tập Huấn luyện (Train) và Chấm thi (Test) có khoảng đệm xóa nhạt (Purge & Embargo) để chống rò rỉ tương quan chuỗi.

#### Đoạn Mã Python Gốc:
```python
import numpy as np

def purge_embargo_split(n_samples: int, train_ratio: float = 0.7, embargo_pct: float = 0.01):
    split_idx = int(n_samples * train_ratio)
    embargo_len = int(n_samples * embargo_pct)
    
    train_idx = np.arange(0, split_idx)
    # Bỏ qua đoạn biên (Purge) và tạo vùng đệm (Embargo)
    test_idx = np.arange(split_idx + embargo_len, n_samples)
    return train_idx, test_idx

train_idx, test_idx = purge_embargo_split(1000)
print(f"Mẫu huấn luyện: {len(train_idx)} | Mẫu chấm thi: {len(test_idx)}")
```

---

### HS-07: Định Cỡ Vị Thế Kelly, EWMA Volatility & Cầu Dao Tự Động
- **Mã hồ sơ:** `HS-07` | **Phân nhánh:** `systems` (Dữ liệu & Hệ thống)
- **Mục tiêu:** Nguyên lý Kelly thận trọng, Điều chỉnh theo biến động EWMA & Ngắt mạch Kill Switch.
- **Tóm tắt cốt lõi:** *"Mỗi lệnh đánh bao nhiêu để chuỗi thua dài nhất, thứ chắc chắn sẽ đến, không làm cháy tài khoản."*

#### Công Thức Toán Học:
$$\displaystyle f^* = \frac{p(b+1) - 1}{b} \quad ; \quad \text{Size}_t = \min\left(f^* \cdot \frac{\sigma_{\text{target}}}{\sigma_t}, \text{Cap}\right)$$

> **Giải thích công thức:** Tiêu chuẩn Kelly tính toán tỉ lệ vốn tối ưu theo xác suất thắng $p$ và tỉ lệ lời/lỗ $b$. Tỉ lệ này được điều chỉnh nghịch đảo với độ biến động thực tế $\sigma_t$.

#### Ứng Dụng Thực Hành:
Xây dựng hàm tự động ngắt bot (Kill Switch) khi mức sụt giảm trong ngày hoặc chuỗi thua liên tiếp chạm ngưỡng giới hạn an toàn.

#### Đoạn Mã Python Gốc:
```python
def evaluate_kill_switch(consecutive_losses: int, max_allowed_losses: int, daily_dd: float, max_dd_limit: float):
    # Kích hoạt ngắt mạch khẩn cấp khi chạm ngưỡng tới hạn
    if consecutive_losses >= max_allowed_losses:
        return True, "DỪNG: Chuỗi thua chạm ngưỡng tới hạn"
    if daily_dd >= max_dd_limit:
        return True, "DỪNG: Sụt giảm chạm trần an toàn"
    return False, "AN TOÀN"

triggered, reason = evaluate_kill_switch(consecutive_losses=11, max_allowed_losses=10, daily_dd=0.04, max_dd_limit=0.05)
print(f"Trạng thái Kill-switch: {reason}")
```

---

### HS-08: Sổ Lệnh Vi Mô, Microprice & Mất Cân Bằng Dòng Lệnh OFI
- **Mã hồ sơ:** `HS-08` | **Phân nhánh:** `systems` (Dữ liệu & Hệ thống)
- **Mục tiêu:** Sổ lệnh giới hạn (Limit Order Book), Chênh lệch giá Bid-Ask, Trượt giá & Thanh khoản.
- **Tóm tắt cốt lõi:** *"Giá bạn thấy chưa phải giá bạn khớp. Chênh lệch giá và trượt giá ăn mòn những lợi thế nhỏ."*

#### Công Thức Toán Học:
$$\displaystyle P_{\text{micro}} = \frac{P_{\text{bid}} Q_{\text{ask}} + P_{\text{ask}} Q_{\text{bid}}}{Q_{\text{bid}} + Q_{\text{ask}}} \quad ; \quad \text{OFI}_t = \Delta Q_{\text{bid}} - \Delta Q_{\text{ask}}$$

> **Giải thích công thức:** Giá khớp thực tế luôn chịu ảnh hưởng bởi độ dày sổ lệnh và chênh lệch mua-bán (spread). Bỏ qua chi phí này là nguyên nhân hàng đầu khiến chiến lược tần suất cao thất bại.

#### Ứng Dụng Thực Hành:
Tính toán giá trọng số khối lượng Microprice và mất cân bằng dòng lệnh (Order Flow Imbalance) từ dữ liệu sổ lệnh.

#### Đoạn Mã Python Gốc:
```python
def calculate_microprice(bid_px: float, ask_px: float, bid_sz: float, ask_sz: float):
    # Giá trung bình trọng số theo khối lượng chờ tại đỉnh sổ lệnh
    microprice = (bid_px * ask_sz + ask_px * bid_sz) / (bid_sz + ask_sz)
    imbalance = (bid_sz - ask_sz) / (bid_sz + ask_sz)
    return microprice, imbalance

micro_px, imb = calculate_microprice(bid_px=2650.20, ask_px=2650.50, bid_sz=6.0, ask_sz=4.0)
print(f"Microprice: {micro_px:.3f} | Imbalance: {imb:.2%}")
```

---

## 3. THUẬT TOÁN JAVASCRIPT VẬN HÀNH PHÒNG MÔ PHỎNG (SIMULATOR LOGIC)

Dưới đây là mã nguồn bóc tách trực tiếp từ các hàm tính toán của file `HomeStitch-DfsUMINs.js` và `Vault-fzGslyIq.js`:

### 3.1. Thuật Toán Bootstrapping Đối Chiếu 300 Lần Ngẫu Nhiên
Trích từ logic biểu đồ phân phối trong `HomeStitch-DfsUMINs.js`:
```javascript
// Dữ liệu phân bố 300 lần ngẫu nhiên: D.ngau_nhien.phan_bo_r_truoc_phi
let e = [...D.ngau_nhien.phan_bo_r_truoc_phi].sort((e, t) => e - t);
let t = -0.35, n = 0.5, r = (n - t) / 20;

// Chia 20 cột tần suất (Histogram Bins)
let bins = Array.from({ length: 20 }, (e, n) => ({
  x0: t + n * r,
  x1: t + (n + 1) * r,
  count: 0
}));

e.forEach(val => {
  let idx = Math.max(0, Math.min(19, Math.floor((val - t) / r)));
  bins[idx].count += 1;
});

// Điểm bách phân vị 95% (Ngưỡng p = 0.05)
let L = D.ngau_nhien.moc_can_vuot_phan_tram; // 95%
let p95Val = e[Math.min(e.length - 1, Math.floor(e.length * (L / 100)))];

// Hệ số so sánh: I = 93% (Hệ thống cao hơn 93% số lần ngẫu nhiên)
// Do 93% < 95% => Kết luận máy: "Không khác vào lệnh ngẫu nhiên"
let isPassed = D.ngau_nhien.he_thong_cao_hon_phan_tram >= L;
```

### 3.2. Công Thức Chuỗi Thua Dài Nhất
```javascript
function calculateMaxConsecutiveLosses(nTrades, winRate) {
  const q = 1 - winRate;
  if (q <= 0) return 0;
  // L_max ≈ ln(N) / -ln(1 - P_win)
  return Math.round(Math.log(nTrades) / -Math.log(q));
}
// Ví dụ: N = 1000, Winrate = 0.55 => L_max ≈ 9 đến 11 lệnh
// Ví dụ: N = 133, Winrate = 0.323 => L_max ≈ 12 đến 15 lệnh
```

### 3.3. Xác Suất Cháy Tài Khoản & Hiệu Ứng Bờ Vực
```javascript
function calculateRiskOfRuin(winRate, riskReward, riskPerTradePct, capital = 100) {
  const edge = winRate - (1 - winRate) / riskReward;
  if (edge <= 0) return 1.0; // 100% Cháy nếu không có Edge
  const units = capital / riskPerTradePct;
  const base = (1 - edge) / (1 + edge);
  return Math.min(1.0, Math.pow(base, units));
}
// Khi riskPerTradePct = 1% => RoR ≈ 0%
// Khi riskPerTradePct vọt lên 5-10% => RoR tiệm cận 100% khi gặp chuỗi thua cực đại
```

### 3.4. Kỳ Vọng Toán Học Mỗi Lệnh
```javascript
function calculateEV(winRate, rewardRiskRatio, frictionPerTradeR = 0.076) {
  // EV = (P_win * RR) - ((1 - P_win) * 1) - Friction
  const grossEV = (winRate * rewardRiskRatio) - ((1 - winRate) * 1.0);
  const netEV = grossEV - frictionPerTradeR;
  return { grossEV, netEV };
}
```

### 3.5. Công Thức Fractional Kelly Phân Bổ Vốn Thận Trọng
```javascript
function calculateFractionalKelly(winRate, winLossRatio, safetyFactor = 0.25) {
  const p = winRate;
  const b = winLossRatio; // Lời trung bình / Lỗ trung bình
  const fullKelly = (p * (b + 1) - 1) / b;
  if (fullKelly <= 0) return 0;
  return fullKelly * safetyFactor; // Dùng 25% Kelly để chống sai số ước lượng mẫu
}
```

---

## 4. CẤU TRÚC SITE-MAP & LOGIC PHÂN LOẠI NGƯỜI DÙNG (analytics-*.js)

Trong chunk `analytics-lrUouYVe.js`, ứng dụng phân cấp thành 6 phân khu:
1. `bat-dau` (journey): Giới thiệu nhanh 1 phút cho người mới; nhấn mạnh nghịch lý *"Thắng nhiều chưa chắc có lãi"* và kết quả thất bại của 42 chiến lược phổ biến MXH.
2. `vi-sao` (about): Bản đọc đầy đủ giải thích vì sao mọi chiến lược bắt buộc phải đem đi đo trước khi tin.
3. `sau-o` (mophong): Phòng Mô Phỏng tương tác và bộ 6 câu hỏi định lượng.
4. `thu-vien` (viplibrary): Tra cứu danh bạ 300 mục, 242 chiến lược đã kiểm chứng, 15 chiến lược đạt tiêu chí.
5. `tai-lieu` (vault): Kho 8 hồ sơ nghiên cứu nền tảng và 3 báo cáo chuyên đề.
6. `thanh-vien` (membership): Kênh đăng ký thành viên VIP qua Zalo `https://zalo.me/0566665511` để mở khóa toàn bộ báo cáo phân tích chuyên sâu.

---
*Bản tổng hợp kỹ thuật hoàn tất ngày 23/11/2026.*
