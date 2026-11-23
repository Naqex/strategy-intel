# Hộp thư nạp chiến lược ngoài (`strategy-intel/inbox/`)

Đây là khu vực riêng để bạn bỏ mọi nguồn chiến lược, bot, tài liệu sưu tầm từ bên ngoài (tách biệt **Air-Gap** khỏi `TradingWorkspace` và được `.gitignore` tự động bỏ qua nên **không bao giờ đẩy file nhị phân/nặng lên GitHub**).

## Chia theo 4 ngăn (bên trong mỗi ngăn tạo thư mục con theo tên nguồn thoải mái)

1. **`01-open-source-code/`** *(Ưu tiên số 1 — hiệu quả cao nhất)*
   - Bỏ file mã nguồn đọc được: `.mq5`, `.mq4`, `.pine` (TradingView), `.py` (GitHub / QuantConnect / MQL5 CodeBase).
   - Ví dụ: `01-open-source-code/mql5-codebase/`, `01-open-source-code/github-quant/`, `01-open-source-code/tradingview-pine/`.
   - Máy sẽ tự đọc code, kiểm tra cờ đỏ (Martingale/Grid/DLL/WebRequest/thiếu SL) rồi chuyển thẳng các mã sạch sang kiểm định M1 Bid/Ask.

2. **`02-trade-logs-csv/`**
   - Bỏ file `.csv` / `.html` lịch sử giao dịch công khai (MQL5 Live Signals, Myfxbook, Darwinex).
   - Máy sẽ tự chạy phễu DNA (Pass 8–9): bắt cờ nhồi lệnh ẩn, tính margin `1:30`, định giá lại theo phí & swap 3× FTMO.

3. **`03-papers-and-notes/`**
   - Bỏ file `.pdf`, `.md`, `.txt`, ảnh chụp luật giao dịch từ SSRN, Quantpedia, Reddit, diễn đàn Trung / Nga / Anh.
   - Máy sẽ trích xuất giả thuyết toán học rõ ràng để lập protocol kiểm định trắng.

4. **`04-quarantine-setfiles/`** *(Khu vực cách ly — vd: `eafree.net`, gói tải diễn đàn)*
   - Bạn có thể chuyển `eafree.net` và các gói tương tự vào đây theo từng thư mục nguồn: `04-quarantine-setfiles/eafree.net/`, `04-quarantine-setfiles/forum-ru/`, v.v.
   - **Quy tắc an toàn cứng:** Bộ quét **chỉ đọc văn bản thuần (`.set`, `.txt`, `.md`)** để trích xuất tham số/ý tưởng công khai và tự gắn cờ bẫy (`Martingale`, `Grid`, `HFT`, `Rollover 23:00–01:00`). Mọi file nhị phân (`.ex4`, `.ex5`, `.exe`, `.dll`, `.rar`, `.zip`) bị **cách ly (`QUARANTINED_NO_EXEC`) — tuyệt đối không giải nén, không chạy, không dịch ngược trái phép**.

## Cách dùng

Sau khi bỏ file mới vào bất kỳ ngăn nào, chỉ cần nhắn agent: **"quét inbox đi"** (hoặc chạy trực tiếp):

```powershell
$py = 'D:\ANNAM\TradingWorkspace\.runtime\quant-audit-v24\Scripts\python.exe'
& $py D:\ANNAM\TradingWorkspace\tooling\ai-engines\inbox_intake_scanner.py --defender
```
