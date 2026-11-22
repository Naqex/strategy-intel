import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const vault = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../raw/vault_data.json'), 'utf8'));
const index = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../raw/thu_vien_index.json'), 'utf8'));

let md = `# BÁO CÁO TOÀN DIỆN: PHƯƠNG PHÁP LUẬN KIỂM ĐỊNH & TOÀN VĂN TÀI LIỆU NGHIÊN CỨU (STRATEGY AUDIT)

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
- **Khung thời gian (Timeframes):** Bao phủ đa khung từ ngắn đến dài: \`M15\`, \`M30\`, \`H1\`, \`H4\`, \`D1\`.
- **Định dạng & Toàn vẹn dữ liệu:** Lưu trữ theo định dạng cột Parquet chuẩn hóa múi giờ UTC, thuật toán phát hiện khoảng trống giá (Gap Detection), lọc nhiễu tick và kiểm tra Hash toàn vẹn (ví dụ: máy chạy SHA-256 \`1ABF7335…9015\`).

### 1.2. Chi Phí Ma Sát Giao Dịch Thực Tế (Friction Costs)
Mọi kết quả kiểm chứng **bắt buộc phải trừ chi phí ma sát thực tế** trước khi đưa ra kết luận:
1. **Phí hoa hồng (Commission):** Mặc định tính **0,02% mỗi chiều** (tương đương **$7 / standard lot** hai chiều vào-ra).
2. **Chênh lệch giá mua - bán (Spread):** Cố định tối thiểu **30 points (3 pips)** trong điều kiện thanh khoản bình thường; nới rộng theo các khung giờ chuyển phiên.
3. **Trượt giá thực thi (Slippage):** Mô phỏng trượt giá thực tế dựa trên độ sâu sổ lệnh giới hạn (Limit Order Book) và mất cân bằng dòng lệnh (OFI), đặc biệt trong các khung giờ thanh khoản mỏng hoặc tin tức mạnh.
4. **Phí qua đêm (Swap / Overnight Financing):** Hệ thống kiểm định KHÔNG tính phí swap qua đêm thả nổi (không áp dụng bảng swap thả nổi hay triple-swap thứ Tư); chi phí ma sát được chuẩn hóa qua hoa hồng cố định 0,02%/chiều và spread tối thiểu 30 points.

> [!WARNING] AUDIT_WARNING: MÂU THUẪN TOÁN HỌC TRONG MÔ HÌNH PHÍ HOA HỒNG (COMMISSION MATH CONTRADICTION)
> Báo cáo của tác giả ghi: *"Phí hoa hồng (Commission): Mặc định tính 0,02% mỗi chiều (tương đương $7 / standard lot hai chiều vào-ra)"*.
> **Phát hiện kiểm toán độc lập:**
> - Hợp đồng tiêu chuẩn (Standard Lot) của Vàng giao ngay (XAUUSD) có quy mô 100 troy ounces.
> - Tại mức giá vàng thời điểm hiện tại (~$2.650/oz), giá trị danh nghĩa 1 lot = 100 oz × $2.650 = $265.000.
> - Mức phí 0,02%/chiều tương ứng: $265.000 × 0,0002 = **$53/chiều**, tức **$106/lot hai chiều khứ hồi** (Roundturn).
> - Con số $106/lot chênh lệch gấp **15,1 lần** so với con số "$7 / standard lot" được tác giả công bố kèm theo. Mức phí $7/lot thực tế chỉ tương đương **0,00132%/chiều** (hoặc chỉ đạt 0,02% nếu giá vàng ở mức $175/oz cách đây 30 năm).
> - Toàn bộ kết quả kiểm định cần được đọc với lưu ý về sự không nhất quán giữa công thức phần trăm danh nghĩa và chi phí đô-la thực tế này.

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
| **\`edge_vs_null\`** | ① Hơn vào lệnh ngẫu nhiên? | So sánh phân phối lợi nhuận trung bình mỗi lệnh (R/lệnh trước phí) với **300 lần vào lệnh ngẫu nhiên (Monte Carlo)** cùng số lệnh và cùng cách thoát lệnh. Hệ thống phải vượt qua ngưỡng bách phân vị **95%** ($p < 0.05$). | Bác bỏ giả thuyết vô hiệu ($H_0$), chứng minh có lợi thế thống kê thực chất (Alpha) thay vì may rủi. |
| **\`ben_tham_so\`** | ② Đổi tham số ±30% còn lãi? | Thử nghiệm biến thiên các thông số chỉ báo/điều kiện (ví dụ: chu kỳ RSI, EMA, ngưỡng kích hoạt) trong biên độ $\pm 30\%$. Toàn bộ vùng lân cận phải duy trì có lãi. | Chống bẫy khớp đường cong (Curve-Fitting) và hiện tượng tối ưu hóa quá mức (Overfitting). |
| **\`song_sot_oos\`** | ③ Qua kỳ chấm 1 (2019–2023)? | Hệ thống duy trì lợi nhuận dương và đường vốn ổn định trên dữ liệu Out-of-Sample 5 năm mà thuật toán chưa từng nhìn thấy. | Kiểm tra khả năng tổng quát hóa (Generalization) khi thị trường thay đổi chu kỳ biến động. |
| **\`chiu_phi\`** | ④ Đã trừ phí? | Lợi nhuận ròng sau khi trừ đầy đủ phí hoa hồng 0,02%/chiều, spread $\ge 3$ pips và trượt giá vẫn phải dương. | Loại bỏ các chiến lược tần suất cao bị chi phí giao dịch hai chiều bào mòn hết lợi thế. |
| **\`kha_thi\`** | ⑤ Đủ $\ge 100$ lệnh? | Tổng số lượng lệnh phát sinh trong chuỗi kiểm định phải đạt tối thiểu từ **100 lệnh** trở lên (khuyến nghị $\ge 300$ lệnh). | Đảm bảo độ tin cậy của Luật số lớn (Law of Large Numbers), tránh kết luận vội vã trên mẫu nhỏ. |

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
`;

for (const bc of vault.reports_bc) {
  md += `
### ${bc.code}: ${bc.title}
- **Chuyên mục:** ${bc.category}
- **Thời lượng:** ${bc.readTime}
- **Tóm tắt ngắn:** *${bc.desc}*

#### 1. Dẫn nhập
${bc.content.intro}

#### 2. Phân tích trọng tâm
${bc.content.body1}

${bc.content.body2}

${bc.content.body3}

#### 3. Sự thật cốt lõi (Core Truth)
> **${bc.content.truth}**

---
`;
}

md += `
## 3. TOÀN VĂN 8 HỒ SƠ NGHIÊN CỨU ĐỊNH LƯỢNG (QUANTITATIVE RESEARCH DOSSIERS)
`;

for (const hs of vault.dossiers_hs) {
  const summaryText = vault.summaries[hs.id] || '';
  md += `
### ${hs.docCode}: ${hs.title}
- **Chủ đề:** ${hs.categoryLabel} (Phân nhánh: \`${hs.track}\`)
- **Mục tiêu:** ${hs.subtitle}
- **Đúc kết 1 câu:** *"${summaryText}"*

#### 1. Công thức toán học then chốt (Key Mathematical Equation)
$$\\displaystyle ${hs.keyEquation}$$

> **Giải thích công thức:** ${hs.equationNote}

#### 2. Các khái niệm nền tảng (Core Concepts)
${hs.coreConcepts.map(c => `- ${c}`).join('\n')}

#### 3. Cầu nối kiểm định tại Strategy Audit (Audit Bridge)
${hs.auditBridge}

#### 4. Tài liệu học thuật tham khảo (Academic References)
${hs.books.map(b => `- **${b.name}** — *Tác giả:* ${b.author}. Ghi chú: ${b.note}`).join('\n')}

#### 5. Ứng dụng thực hành & Đoạn mã Python (Practice Note & Implementation)
${hs.practiceNote}

\`\`\`python
${hs.codeSnippet}
\`\`\`

---
`;
}

md += `
## 4. BÁO CÁO MINH BẠCH: CÁC KHU VỰC BỊ KHÓA THÀNH VIÊN & PHỄU THU THẬP (GATEKEEPING AUDIT)

Qua quá trình rà soát toàn bộ tài nguyên mạng và mã nguồn JavaScript của ứng dụng \`https://stategy.netlify.app/\`, Strategy Audit xác định các cơ chế giới hạn truy cập đối với người dùng công khai:

### 4.1. Nút "Tải Về Trọn Bộ Tài Liệu PDF" (Lead Capture Form)
- **Vị trí:** Xuất hiện tại giao diện Kho Nghiên Cứu (\`/vault\`).
- **Hành vi thực tế:** Không chứa liên kết direct download đến tệp \`.pdf\` công khai. Khi người dùng nhấp chuột, hệ thống kích hoạt modal form thu thập khách hàng tiềm năng:
  - Trường 1: Họ và tên (tối thiểu 2 ký tự).
  - Trường 2: Số điện thoại / Zalo (8–15 chữ số).
  - Trường 3: Địa chỉ Email (đúng định dạng RFC).
- **Mục đích:** Thu thập thông tin liên hệ để đội ngũ hỗ trợ gửi tài liệu thủ công qua kênh Zalo (\`https://zalo.me/0566665511\`) hoặc Email.

### 4.2. Báo Cáo Phân Tích Chuyên Sâu (Deep Dive Reports)
- **Vị trí:** Xuất hiện tại cửa sổ chi tiết (Modal) của từng chiến lược trong Thư viện (\`/vip\`).
- **Phần công khai:** Mọi người dùng đều xem được miễn phí:
  1. Tên, họ chiến lược, khung thời gian, nguồn gốc và mô tả ngắn quy tắc.
  2. Bảng trạng thái 5 tiêu chí cứng (\`edge_vs_null\`, \`ben_tham_so\`, \`song_sot_oos\`, \`chiu_phi\`, \`kha_thi\`).
  3. Bảng số liệu chi tiết 3 giai đoạn: In-Sample (2004–2018), Out-of-Sample Kỳ 1 (2019–2023) và Out-of-Sample Kỳ 2 (2024–2026), bao gồm số lệnh, winrate % và số năm dương.
- **Phần bị khóa:** Khối văn bản *"Báo Cáo Phân Tích Chuyên Sâu"* (chứa giải phẫu mã nguồn, bộ quy tắc vào/ra lệnh chi tiết từng nến, tham số tối ưu hóa và nhật ký lệnh) được bảo vệ bằng cơ chế xác thực \`x-passkey\` gửi về backend Netlify Functions / Google Apps Script (\`https://script.google.com/macros/s/AKfycbyH6xzJc9J4Dj8fKJi-Rp91tfeS0tZbLtjz0m26bON4kjLKFnMLjS8btAxo66CoPDCGbA/exec?action=article\`). Nếu không có passkey thành viên VIP, giao diện hiển thị lớp phủ mờ (opacity 60%, pointer-events-none) và hướng dẫn liên hệ Zalo để đăng ký thành viên.

### 4.3. Đánh Giá Khách Quan Về Mặt Kỹ Thuật
- Toàn bộ dữ liệu định lượng cốt lõi (242 file JSON chi tiết, metadata 300 chiến lược, nội dung 3 Báo Cáo Chuyên Đề, 8 Hồ Sơ Nghiên Cứu, công thức LaTeX và mã nguồn mẫu) **được phân phối công khai hoàn toàn trên hạ tầng tĩnh Netlify CDN**.
- Cơ chế khóa bài viết chuyên sâu và form tải PDF thuần túy là lớp giao diện người dùng (Client-side Gatekeeping) kết hợp backend quản lý thành viên thủ công.

---
*Báo cáo được tổng hợp tự động và trích xuất nguyên bản từ mã nguồn triển khai thực tế.*
`;

fs.writeFileSync(path.resolve(__dirname, '../extracted/01_methodology_and_reports.md'), md, 'utf8');
console.log('Successfully written 01_methodology_and_reports.md!');
