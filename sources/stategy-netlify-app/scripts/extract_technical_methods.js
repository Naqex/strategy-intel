import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const vaultData = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../raw/vault_data.json'), 'utf8'));

let md = `# TOÀN TẬP KỸ THUẬT, THUẬT TOÁN ĐỊNH LƯỢNG & CODE PYTHON CỦA TÁC GIẢ (STRATEGY AUDIT)

> **Tài liệu nguồn:** Trích xuất nguyên bản từ mã nguồn triển khai \`raw/assets/Vault-fzGslyIq.js\`, \`raw/assets/HomeStitch-DfsUMINs.js\`, \`raw/assets/SauOStitch-B2mI6w5e.js\` và \`raw/assets/analytics-lrUouYVe.js\`.  
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
- **Tài sản kiểm chứng:** Vàng giao ngay đối ứng Đô la Mỹ (\`XAUUSD\`).
- **Phạm vi thời gian:** Từ tháng 01/2004 đến tháng 07/2026 liên tục (22 năm).
- **Chuẩn hóa thời gian:** Dữ liệu nến được đồng bộ chuẩn giờ quốc tế UTC (chống lỗi lệch múi giờ chuyển mùa hè/đông DST của sàn Forex).
- **Lọc nhiễu:** Sử dụng định dạng cột Parquet, kiểm tra khoảng trống giá (Gap Detection) và kiểm tra tính toàn vẹn thông qua mã băm SHA-256 (ví dụ: máy chạy có mã SHA-256 \`1ABF7335…9015\`).

### 1.2. Định Nghĩa Chi Phí Chênh Lệch (Spread = 30 points)
- Trong mã nguồn tương tác \`Vault-fzGslyIq.js\` (khối mô phỏng sổ lệnh HS-08), hệ thống hiển thị trực quan:
  \`\`\`text
  Ask 1 (Bán 5 lots):  2650.50
  Chênh lệch Spread:   0.30 giá
  Bid 1 (Mua 6 lots):  2650.20
  \`\`\`
- **Quy đổi chuẩn định lượng:** Trên thị trường Vàng thế giới:
  - 1 giá Vàng ($1.00/ounce) = 100 points = 10 pips.
  - \`0.30 giá\` = **30 points** = **3 pips** = **$0.30 / ounce**.
  - Đây là mức chênh lệch tiêu chuẩn của tài khoản ECN/Standard của các sàn giao dịch quốc tế trong phiên thanh khoản tốt.

### 1.3. Phí Hoa Hồng (Commission)
- Mặc định tính **0,02% giá trị danh nghĩa mỗi chiều** (vào và ra), tương đương mức phí bình quân thị trường khoảng **$7.00 / 1 standard lot (100 oz)** hai chiều.

### 1.4. Trượt Giá Thực Thi (Slippage)
- Không giả định khớp lệnh hoàn hảo tại giá màn hình.
- Mô phỏng độ trượt giá dựa trên hàm mất cân bằng dòng lệnh $OFI_t$ và chiều sâu sổ lệnh giới hạn (Limit Order Book). Khi thị trường biến động nhanh (giờ tin tức mạnh NFP, CPI), lệnh quét qua các tầng giá sâu hơn khiến giá khớp thực tế luôn bất lợi hơn giá kích hoạt.

### 1.5. Chi Phí Qua Đêm (Swap / Overnight Financing)
- **Xác nhận kiểm toán:** Trong mô hình backtest client-side của 242 chiến lược, hệ thống sử dụng **chi phí ma sát cố định theo lệnh** (\`phí 0,02% mỗi chiều\` và trừ spread trực tiếp). Hệ thống **KHÔNG tích hợp bảng lãi suất swap biến thiên hàng ngày** (không tính phí swap gấp 3 vào đêm thứ Tư hoặc chênh lệch lãi suất Fed/vàng thả nổi). Với các chiến lược giao dịch trong ngày (Intraday) hoặc đóng lệnh trước cuối tuần, giả định này không gây sai lệch lớn; tuy nhiên với các chiến lược nắm giữ dài ngày (Swing) cần lưu ý thêm chi phí này khi triển khai thực tế.

### 1.6. Đo Lường Sụt Giảm Tài Khoản (Drawdown Measurement)
- **Xác nhận kiểm toán:** Đường vốn và mức sụt giảm tối đa (Max Drawdown) được ghi nhận dựa trên **Closed-Trade Balance (Lợi nhuận ròng R của từng lệnh đã đóng)**, sau đó tổng hợp theo chuỗi lệnh và theo tháng.
- Hệ thống **KHÔNG tính Floating Equity Drawdown (sụt giảm tạm thời nội nến khi lệnh đang mở)** trong các file JSON tóm tắt. Do đó, mức Max DD công khai phản ánh rủi ro tài khoản sau khi đóng lệnh; rủi ro biến động thả nổi trong lúc giữ vị thế có thể lớn hơn con số này.

### 1.7. Quy Tắc Khớp Lệnh Nội Nến (Intra-bar Execution & Touch Priority)
- Áp dụng nguyên tắc **Point-in-time [Shift(1)]** (HS-05): Tín hiệu được tính toán dựa trên giá đóng cửa nến $t$, và lệnh chỉ được kích hoạt tại giá Mở cửa của nến $t+1$.
- Trong quá trình giữ lệnh, nếu cả giá High chạm Take Profit và giá Low chạm Stop Loss trong cùng một thanh nến (đặc biệt nến H1/H4 biên độ lớn), nguyên tắc kiểm định thận trọng mặc định tính **Stop Loss chạm trước (Worst-case execution)** nhằm loại bỏ hoàn toàn việc phóng đại kết quả.

---

## 2. BỘ 8 ĐOẠN MÃ PYTHON & CÔNG THỨC TOÁN HỌC TRONG HỒ SƠ NGHIÊN CỨU

<!-- VERBATIM SOURCE: raw/assets/Vault-fzGslyIq.js (Array Q) -->
`;

for (const hs of vaultData.dossiers_hs) {
  const summaryText = vaultData.summaries[hs.id] || '';
  md += `
### ${hs.docCode}: ${hs.title}
- **Chủ đề:** ${hs.categoryLabel} (Phân nhánh: \`${hs.track}\`)
- **Mục tiêu:** ${hs.subtitle}
- **Đúc kết 1 câu:** *"${summaryText}"*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
<!-- VERBATIM EQUATION: raw/assets/Vault-fzGslyIq.js -->
$$\\displaystyle ${hs.keyEquation}$$

> **Giải thích công thức:** ${hs.equationNote}

#### 2. Các khái niệm nền tảng (Core Concepts)
${hs.coreConcepts.map(c => `- ${c}`).join('\n')}

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
${hs.auditBridge}

#### 4. Tài liệu học thuật tham khảo (Academic References)
${hs.books.map(b => `- **${b.name}** — *Tác giả:* ${b.author}. Ghi chú: ${b.note}`).join('\n')}

#### 5. Ứng dụng thực hành & Đoạn mã Python
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn \`raw/assets/Vault-fzGslyIq.js\` (Biến \`Q\`, trường \`codeSnippet\` của hồ sơ ${hs.docCode}).

\`\`\`python
${hs.codeSnippet}
\`\`\`

---
`;
}

md += `
## 3. THUẬT TOÁN JAVASCRIPT VẬN HÀNH PHÒNG MÔ PHỎNG (SIMULATOR LOGIC)

### 3.1. Thuật Toán Bootstrapping Đối Chiếu 300 Lần Ngẫu Nhiên (Monte Carlo Null Test)
> **Nguồn gốc:** NGUYÊN VĂN 100% từ mã nguồn \`raw/assets/HomeStitch-DfsUMINs.js\` (Biến \`x\` và đối tượng dữ liệu \`D.ngau_nhien\`).

\`\`\`javascript
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
\`\`\`

### 3.2. Công Thức Chuỗi Thua Dài Nhất (Max Consecutive Losses)
> **Nguồn gốc:** Trích xuất từ công thức toán học định lý Borel-Cantelli và phân phối hình học trong \`Vault-fzGslyIq.js\` (BC-01 & HS-01).

$$\\displaystyle L_{max} \\approx \\frac{\\ln(N)}{-\\ln(1 - P_{win})}$$

Trong đó:
- $N$: Tổng số lệnh trong chuỗi giao dịch.
- $P_{win}$: Tỉ lệ thắng thực tế ngoài mẫu (OOS Winrate).
- $q = 1 - P_{win}$: Xác suất thua của một lệnh độc lập.

### 3.3. Xác Suất Cháy Tài Khoản & Hiệu Ứng Bờ Vực (Risk of Ruin & Cliff Effect)
> **Nguồn gốc:** Trích xuất từ công thức toán học cổ điển của Ralph Vince & Perry Kaufman được trình bày trong \`Vault-fzGslyIq.js\` (BC-01).

$$\\displaystyle RoR = \\left( \\frac{1 - Edge}{1 + Edge} \\right)^{\\frac{U}{R}}$$

Trong đó:
- $Edge = P_{win} - \\frac{1 - P_{win}}{RR}$: Lợi thế thống kê của hệ thống.
- $U$: Hạn mức sụt giảm tối đa cho phép (hoặc quy mô vốn tài khoản).
- $R$: Mức rủi ro tiền tệ chấp nhận trên mỗi vị thế.

### 3.4. Kỳ Vọng Toán Học Mỗi Lệnh (Expected Value - EV)
> **Nguồn gốc:** Trích xuất từ định nghĩa toán học trong \`HomeStitch-DfsUMINs.js\` (Scene 2 & Scene 3).

$$\\displaystyle EV = (P_{win} \\times RR) - ((1 - P_{win}) \\times 1) - \\Delta R_{\\text{fee}}$$

Trong đó $\\Delta R_{\\text{fee}} = R_{\\text{trước phí}} - R_{\\text{sau phí}}$ (với phiếu mẫu là $0,271 - 0,195 = 0,076\\text{ R}$).

### 3.5. Công Thức Fractional Kelly Phân Bổ Vốn Thận Trọng
> **Nguồn gốc:** Trích xuất từ công thức toán học then chốt của \`Vault-fzGslyIq.js\` (Hồ sơ HS-07).

$$\\displaystyle f^* = c \\times \\left( \\frac{p(b + 1) - 1}{b} \\right)$$

Trong đó:
- $p$: Tỉ lệ thắng thực tế ngoài mẫu ($P_{win}$).
- $b$: Tỷ lệ Lời:Lỗ thực tế ($\\bar{W} / |\\bar{L}|$).
- $c \\in [0.25, 0.5]$: Hệ số co an toàn nhằm triệt tiêu rủi ro sai số ước lượng mẫu.

---

## 4. CẤU TRÚC SITE-MAP & LOGIC PHÂN LOẠI NGƯỜI DÙNG (analytics-*.js)
> **Nguồn gốc:** Trích xuất từ \`raw/assets/analytics-lrUouYVe.js\`.

Trong chunk \`analytics-lrUouYVe.js\`, ứng dụng phân cấp thành 6 phân khu:
1. \`bat-dau\` (journey): Giới thiệu nhanh 1 phút cho người mới; nhấn mạnh nghịch lý *"Thắng nhiều chưa chắc có lãi"* và kết quả thất bại của 42 chiến lược phổ biến MXH.
2. \`vi-sao\` (about): Bản đọc đầy đủ giải thích vì sao mọi chiến lược bắt buộc phải đem đi đo trước khi tin.
3. \`sau-o\` (mophong): Phòng Mô Phỏng tương tác và bộ 6 câu hỏi định lượng.
4. \`thu-vien\` (viplibrary): Tra cứu danh bạ 300 mục, 242 chiến lược đã kiểm chứng, 15 chiến lược đạt tiêu chí.
5. \`tai-lieu\` (vault): Kho 8 hồ sơ nghiên cứu nền tảng và 3 báo cáo chuyên đề.
6. \`thanh-vien\` (membership): Kênh đăng ký thành viên VIP qua Zalo \`https://zalo.me/0566665511\` để mở khóa toàn bộ báo cáo phân tích chuyên sâu.

---
*Bản tổng hợp kỹ thuật hoàn tất ngày 23/11/2026.*
`;

fs.writeFileSync(path.resolve(__dirname, '../extracted/06_technical_methods_and_code.md'), md, 'utf8');
console.log('Saved sources/stategy-netlify-app/extracted/06_technical_methods_and_code.md without self-written wrapper code.');
