# KIỂM TOÁN THUẬT TOÁN & LOGIC VẬN HÀNH: PHÒNG MÔ PHỎNG (SIMULATOR AUDIT)

> **Nguồn trích xuất:** https://stategy.netlify.app/mo-phong và các bundle mã nguồn `HomeStitch-DfsUMINs.js`, `SauOStitch-B2mI6w5e.js`, `Vault-fzGslyIq.js`.  
> **Thời gian phân tích:** Ngày 22–23/11/2026.  
> **Mục tiêu:** Bóc tách toàn bộ tham số đầu vào, công thức tính toán, mô phỏng Monte Carlo ngẫu nhiên và quy trình định lượng phía client.

---

## 1. TỔNG QUAN KIẾN TRÚC PHÒNG MÔ PHỎNG

Phòng Mô Phỏng (Simulator) tại Strategy Audit được thiết kế gồm hai phân hệ chính:
1. **Phân hệ Tự Rà Soát Quy Tắc ("Sáu Ô" - SauOStitch):** Bộ công cụ 6 câu hỏi tương tác giúp nhà giao dịch chuyển hóa trực giác định tính thành bộ quy tắc khách quan có thể lập trình.
2. **Phân hệ Kiểm Chứng Ngẫu Nhiên (4 Cảnh Mô Phỏng - HomeStitch Demo):** Thực thi đối chiếu hiệu suất của một phiếu hệ thống mẫu với **300 lần vào lệnh ngẫu nhiên (Monte Carlo Bootstrap)** trên dữ liệu nến H1 XAUUSD thật 15 năm (2004–2018) nhằm phát hiện bẫy ngẫu nhiên.

---

## 2. PHÂN HỆ 1: QUY TRÌNH TỰ RÀ SOÁT 6 CÂU HỎI ("SÁU Ô")

Phân hệ này thu thập 6 trường dữ liệu cốt lõi cấu thành một hệ thống giao dịch hoàn chỉnh:

| Câu Hỏi (Ô) | Nội Dung Định Lượng | Ý Nghĩa Trong Lập Trình Hệ Thống | Các Lựa Chọn Có Sẵn |
| :--- | :--- | :--- | :--- |
| **Ô 1: Bối Cảnh Thị Trường** | *"Bạn thường vào lệnh trong tình huống nào?"* | Xác định chế độ thị trường (Market Regime) để áp dụng thuật toán phù hợp. | 1. Giá chạy quá đà rồi có dấu hiệu quay lại (Mean Reversion).<br>2. Giá phá qua một mức quan trọng (Breakout).<br>3. Giá đang chạy một chiều rõ ràng, tôi đi theo (Trend Following).<br>4. Xuất hiện một mẫu nến tôi nhận ra (Candlestick Pattern).<br>5. Giá chạm một vùng tôi đã đánh dấu sẵn (Key Level / Supply Demand).<br>6. Tôi cũng chưa rõ — tùy lúc (Discretionary). |
| **Ô 2: Tín Hiệu Kích Hoạt** | *"Bạn nhìn thấy gì thì bấm vào lệnh?"* | Định nghĩa chính xác điều kiện logic kích hoạt (Trigger Rule) tại giá đóng cửa nến, triệt tiêu tính chủ quan. | Ví dụ chuẩn hóa: *"Khi giá vượt lên khỏi mức cao nhất của bốn tiếng đầu tuần"* hoặc *"RSI 14 cắt lên 30 & Giá trên EMA 200"*. |
| **Ô 3: Quy Tắc Thoát Lệnh** | *"Bạn đóng lệnh khi nào — lúc lỗ và lúc lời?"* | Cố định tỷ lệ Lời:Lỗ (Risk:Reward Ratio) và quy tắc cắt lỗ độc lập với cảm xúc. | Ví dụ chuẩn hóa: *"Lỗ thì cắt khi âm 20 giá (2 ATR). Lời thì chốt khi được 60 giá (3 R)"*. |
| **Ô 4: Thời Gian Nắm Giữ** | *"Một lệnh của bạn thường mở bao lâu rồi đóng?"* | Ước tính chu kỳ nắm giữ để áp dụng chi phí swap và giới hạn nến tối đa (Time-stop). | Vài phút (Scalp), vài tiếng (Intraday), qua đêm, hoặc đa ngày/tuần (Swing). |
| **Ô 5: Khung Giờ & Bộ Lọc** | *"Bạn hay vào lệnh lúc nào? Có lúc nào bạn tự cấm mình vào không?"* | Thiết lập bộ lọc phiên giao dịch (Session Filter) và bộ lọc tin tức (News Filter). | Ví dụ: *"Hay vào buổi tối lúc thị trường Mỹ mở. Đứng ngoài trước tin CPI/FOMC 30 phút"*. |
| **Ô 6: Tần Suất Giao Dịch** | *"Một tuần bạn vào khoảng bao nhiêu lệnh?"* | Đánh giá độ lớn mẫu giao dịch (Sample Size) sau 1 năm hoặc 10 năm để áp dụng Luật số lớn. | Khoảng 5 đến 7 lệnh/tuần (tương đương 250–350 lệnh/năm, thỏa mãn điều kiện thống kê). |

### Thang Đo Độ Rõ Của Quy Tắc (Clarity Scoring Engine)
Ứng dụng đánh giá mức độ hoàn thiện của hệ thống theo 3 cấp độ:
- **Cấp độ 1:** *"Bạn mới mô tả được một phần cách giao dịch"* (thiếu điểm cắt lỗ/chốt lời rõ ràng hoặc điểm vào còn mơ hồ).
- **Cấp độ 2:** *"Bạn đã làm rõ một số quy tắc"* (có điểm vào và ra nhưng thiếu bộ lọc giờ hoặc giới hạn rủi ro).
- **Cấp độ 3:** *"Bạn đã mô tả phần lớn quy tắc"* (đủ điều kiện logic để máy biên dịch thành thuật toán backtest độc lập).
> **Lưu ý minh bạch của hệ thống:** Giao diện nhấn mạnh: *"Đây chỉ là mức độ rõ của câu trả lời, không phải điểm chất lượng hay kết quả kiểm định phương pháp. Bài tự rà soát chưa xác nhận lợi thế hoặc kết quả giao dịch trong tương lai."*

---

## 3. PHÂN HỆ 2: BỐC TÁCH LOGIC PHIẾU HỆ THỐNG MẪU SỐ 1

Trong mã nguồn `HomeStitch-DfsUMINs.js`, ứng dụng nhúng sẵn toàn bộ dữ liệu thật của **Phiếu Hệ Thống Mẫu Số 1**:
- **Mã định danh máy chạy:** `may_chay SHA-256 1ABF7335…9015`.
- **Ngày xuất dữ liệu:** `20/11/2026`.
- **Tài sản & Khung thời gian:** `XAUUSD` khung `H1`.
- **Khoảng dữ liệu In-Sample:** Tháng `06/2004` đến tháng `11/2018` (15 năm).
- **Ghi chú dữ liệu:** *"Phần dữ liệu để chạy thử (backtest) của khung H1 vàng; từ 01/01/2019 trở đi là phần Kiểm chứng (OOS), không nằm trong 133 lệnh này."*

### 3.1. Đặc Tả Quy Tắc Của Phiếu Mẫu:
```text
Mua XAUUSD khung H1 khi:
  1. RSI(14) cắt lên mức 30.
  2. Giá đóng cửa nằm trên đường EMA(200).
Thoát lệnh:
  - Cắt lỗ (Stop Loss): 2 lần ATR(14).
  - Chốt lời (Take Profit): 3 R (tỉ lệ R:R = 1:1.5 so với khoảng cách cắt lỗ).
  - Giới hạn thời gian (Time Stop): Giữ tối đa 200 nến H1.
  - Chi phí giao dịch: 0,02% giá trị mỗi chiều vào - ra.
```

### 3.2. Kết Quả Thống Kê 133 Lệnh Của Phiếu Mẫu:
- **Tổng số lệnh phát sinh ($N$):** **133 lệnh**.
- **Số lệnh thắng:** **43 lệnh** (chiếm tỉ lệ thắng **$P_{win} = 32,3%$**).
- **Số lệnh thua:** **90 lệnh** (chiếm tỉ lệ thua **$P_{loss} = 67,7%$**).
- **Tổng lợi nhuận tích lũy:** **$+25,92	ext{ R}$**.
- **Lợi nhuận trung bình mỗi lệnh TRƯỚC phí ($R_{trước}$):** **$+0,271	ext{ R}$**.
- **Lợi nhuận trung bình mỗi lệnh SAU phí ($R_{sau}$):** **$+0,195	ext{ R}$**.
- **Chi phí ma sát bình quân mỗi lệnh:**
  $$\Delta R_{\text{fee}} = 0,271 - 0,195 = 0,076\text{ R}$$
  *(Phí giao dịch đã bào mòn mất $\frac{0,076}{0,271} \approx 28,04\%$ tổng biên lợi nhuận của hệ thống).*

---

## 4. PHÂN HỆ 3: THUẬT TOÁN ĐỐI CHIẾU NGẪU NHIÊN MONTE CARLO (BOOTSTRAPPING NULL TEST)

Đây là hòn đá tảng trong phương pháp luận của Strategy Audit: **Đường vốn tăng trưởng không chứng minh được hệ thống có lợi thế thực.**

> [!WARNING] AUDIT_WARNING: MẢNG 300 LẦN MÔ PHỎNG MONTE CARLO LÀ DỮ LIỆU TĨNH NHÚNG SẴN (STATIC CACHED SIMULATION)
> Giao diện "Phòng Mô Phỏng" giới thiệu tính năng "300 lần vào lệnh ngẫu nhiên (Monte Carlo Bootstrap) trên nến H1 XAUUSD thật 15 năm (2004–2018)".
> **Phát hiện kiểm toán độc lập trong bundle `HomeStitch-DfsUMINs.js`:**
> - Phía client KHÔNG thực thi thuật toán Bootstrap tái tạo ngẫu nhiên hay sinh phân phối Monte Carlo thời gian thực khi người dùng tương tác.
> - Toàn bộ 300 kết quả mô phỏng (tỷ lệ thắng, EV/R, chuỗi lỗ liên tiếp) đã được tính toán từ trước và nhúng cứng vào mã nguồn dưới dạng mảng hằng số tĩnh (`display_cached_simulation`).
> - Giao diện chỉ hiển thị lại mảng dữ liệu mẫu đã lưu trữ sẵn của Phiếu Hệ Thống Mẫu Số 1, không đại diện cho một cỗ máy mô phỏng động tính toán theo tham số người dùng nhập vào.

### 4.1. Quy Trình Giả Lập Vô Hiệu ($H_0$ Simulation)
1. Giữ nguyên toàn bộ cấu trúc thị trường XAUUSD H1 trong cùng kỳ 2004–2018.
2. Giữ nguyên số lượng lệnh ($N = 133$) và toàn bộ quy tắc quản trị rủi ro / thoát lệnh (SL 2 ATR, TP 3 R, time-stop 200 nến).
3. Thay thế điều kiện vào lệnh (RSI & EMA) bằng cơ chế **vào lệnh ngẫu nhiên hoàn toàn (Random Entry)** lặp lại **300 lần độc lập**.
4. Ghi nhận phân phối lợi nhuận trung bình mỗi lệnh trước phí của 300 kịch bản ngẫu nhiên:
   $$\mathcal{D}_{random} = \{R_{1}, R_{2}, \dots, R_{300}\}$$

### 4.2. Số Liệu Phân Phối Của 300 Kịch Bản Ngẫu Nhiên:
- **Giá trị nhỏ nhất ($R_{min}$):** $-0,298\text{ R}$/lệnh.
- **Giá trị lớn nhất ($R_{max}$):** $+0,474\text{ R}$/lệnh.
- **Giá trị trung bình ($mu_{random}$):** $+0,039\text{ R}$/lệnh.
- **Giá trị trung vị ($Median_{random}$):** $+0,023\text{ R}$/lệnh.
- **Ngưỡng ý nghĩa thống kê tiêu chuẩn (Alpha level 5%):**
  $$\text{Bách phân vị thứ } 95\% \quad (P_{95}) = +0,286\text{ R}$$
- **Vị trí của Phiếu Mẫu trên biểu đồ phân phối:**
  $$R_{\text{phiếu}} = +0,271\text{ R} \implies \text{Percentile} = 93\%$$

### 4.3. Kết Luận Máy Chạy (Automated Verdict Logic):
- **Điều kiện Pass:** Để được xác nhận có lợi thế thống kê (Edge), hệ thống bắt buộc phải nằm ngoài vùng ngẫu nhiên ở độ tin cậy $95\%$:
  $$\text{Percentile} \ge 95\% \quad (p < 0.05)$$
- **Thực tế:** Phiếu mẫu đạt **$93\%$** ($p = 0.07 > 0.05$).
- **Kết luận:** **"Không khác vào lệnh ngẫu nhiên"** (Verdict badge: Amber/Warning).
- **Bài học định lượng:** Mặc dù đường vốn trông rất đẹp ($+25,92\text{ R}$ qua 133 lệnh), nhưng một người tung đồng xu ngẫu nhiên 133 lần với cùng cách quản lý vốn vẫn có tới $7\%$ xác suất đạt kết quả tương đương hoặc tốt hơn. Do đó, hệ thống không vượt qua được bài kiểm định giả thuyết.

---

## 5. CÁC CÔNG THỨC TOÁN HỌC VẬN HÀNH PHÒNG MÔ PHỎNG & VAULT

### 5.1. Kỳ Vọng Toán Học Mỗi Lệnh (Expected Value - EV)
$$EV = (P_{win} \times RR) - ((1 - P_{win}) \times 1) - \text{Friction}$$
*Nếu $EV \le 0$, chiến lược chắc chắn lỗ vốn về mặt dài hạn bất kể kỹ năng tâm lý.*

### 5.2. Ước Tính Chuỗi Thua Dài Nhất (Max Consecutive Losses)
Dựa trên phân phối hình học và Luật số lớn, trong một chuỗi $N$ lệnh giao dịch với xác suất thua mỗi lệnh là $q = 1 - P_{win}$, kỳ vọng độ dài chuỗi thua liên tiếp lớn nhất được tính theo công thức:
$$L_{max} \approx \frac{\ln(N)}{\ln(1 / q)} = \frac{\ln(N)}{-\ln(1 - P_{win})}$$
*Ví dụ thực tế:*
- Với $P_{win} = 55\%$ ($q = 0.45$), trong $N = 1.000$ lệnh:
  $$L_{max} \approx \frac{\ln(1000)}{-\ln(0.45)} = \frac{6.9077}{0.7985} \approx 8,65 \implies \text{Chắc chắn xuất hiện chuỗi thua liên tiếp từ 8 đến 11 lệnh.}$$
- Với $P_{win} = 32,3\%$ ($q = 0.677$) của Phiếu mẫu số 1:
  $$L_{max} \approx \frac{\ln(133)}{-\ln(0.677)} = \frac{4.890}{0.390} \approx 12,5 \implies \text{Xuất hiện chuỗi thua 12–15 lệnh liên tiếp.}$$

### 5.3. Xác Suất Cháy Tài Khoản & Hiệu Ứng Bờ Vực (Risk of Ruin & Cliff Effect)
Theo công thức cổ điển của Ralph Vince và Perry Kaufman:
$$RoR = \left( \frac{1 - Edge}{1 + Edge} \right)^{\frac{U}{R}}$$
Trong đó:
- $Edge$: Lợi thế thống kê của hệ thống ($Edge = P_{win} - \frac{1 - P_{win}}{RR}$).
- $U$: Hạn mức sụt giảm tối đa cho phép (hoặc vốn tài khoản).
- $R$: Rủi ro tiền tệ trên mỗi lệnh giao dịch.

> **Hiện tượng Bờ Vực (The Cliff Effect):**
> Khi rủi ro mỗi lệnh $R$ được duy trì ở mức nhỏ ($1\% - 2\%$ tài khoản), giá trị số mũ $\frac{U}{R}$ rất lớn, khiến $RoR \approx 0\%$. Tuy nhiên, khi tăng $R$ lên $5\% - 10\%$, đồ thị RoR không tăng tuyến tính mà **vọt dựng đứng lên tiệm cận $100\%$**. Chỉ cần một chuỗi thua tự nhiên $L_{max}$ xuất hiện theo luật số lớn, toàn bộ tài khoản sẽ bị quét sạch.

### 5.4. Công Thức Định Cỡ Vị Thế Kelly Thận Trọng (Fractional Kelly Criterion - HS-07)
Để tránh sụt giảm tài khoản nghiêm trọng do tham số ước lượng không hoàn hảo, hệ thống khuyến nghị sử dụng phân số Kelly thận trọng:
$$f^* = c \times \left( \frac{p(b + 1) - 1}{b} \right)$$
Trong đó:
- $p$: Tỉ lệ thắng thực tế ngoài mẫu (OOS Winrate).
- $b$: Tỷ lệ Lời:Lỗ thực tế ($b = \frac{\bar{W}}{|\bar{L}|}$).
- $c$: Hệ số co an toàn ($c = 0.25$ đến $0.5$, tức Quarter Kelly hoặc Half Kelly).

---
*Tài liệu kiểm toán logic Phòng Mô Phỏng hoàn thành ngày 23/11/2026.*
