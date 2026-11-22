# INTEL AIR-GAP & EXTRACTION GUARDRAILS

> **Phạm vi áp dụng:** Toàn bộ AI Agents, subagents, scripts và quy trình kiểm toán hoạt động bên trong kho lưu trữ `strategy-intel`.

---

## 4 NGUYÊN TẮC RÀNG BUỘC TUYỆT ĐỐI (NON-NEGOTIABLE)

### 1. NGUYÊN TẮC AIR-GAP (CÁCH LY HOÀN TOÀN)
- Mọi hoạt động I/O (đọc, ghi, tìm kiếm, tham chiếu, lập chỉ mục) **CHỈ ĐƯỢC PHÉP DIỄN RA BÊN TRONG THƯ MỤC** `d:/ANNAM/strategy-intel`.
- **TUYỆT ĐỐI KHÔNG** truy cập, đọc lén, tham chiếu, import hay ghi đè sang thư mục trading nội bộ `D:/ANNAM/TradingWorkspace` hay bất kỳ workspace cá nhân nào khác.
- Ngăn chặn mọi nguy cơ rò rỉ ý tưởng, code độc quyền hoặc làm ô nhiễm dữ liệu nội bộ.

### 2. NGUYÊN TẮC NO BINARY DOWNLOAD (CẤM NHẬP FILE THỰC THI/MÃ NGUỒN ĐÓNG)
- **TUYỆT ĐỐI KHÔNG** tải về, giải nén, thực thi hay phân tích động bất kỳ tệp tin nhị phân hay mã nguồn sau:
  - MetaTrader compiled EAs / Indicators: `.ex4`, `.ex5`.
  - MetaTrader source files không rõ nguồn gốc: `.mq4`, `.mq5`.
  - Windows Executables / Libraries / Installers: `.dll`, `.exe`, `.msi`, `.bat`, `.cmd`, `.ps1` từ web.
  - Tệp nén chứa binary: `.zip`, `.rar`, `.7z`, `.tar.gz`.
- **CHỈ ĐƯỢC THU THẬP:** Văn bản thuần (HTML, CSS), JSON APIs, HTTP network responses, ảnh minh họa metadata và các bài viết báo cáo công khai.

### 3. NGUYÊN TẮC ZERO HALLUCINATION (TRUNG THỰC SỐ LIỆU TUYỆT ĐỐI)
- Mọi bảng tổng hợp, chỉ số PnL, Winrate, Profit Factor, số lệnh trong `extracted/` **PHẢI** do script tự động đọc và trích xuất trực tiếp từ các file lưu trữ trong `raw/`.
- Nếu trang web gốc không công bố trường thông tin nào (ví dụ: không có SL/TP, không có drawdown), trường đó **BẮT BUỘC ĐIỀN CHUỖI:** `NOT_DISCLOSED`.
- **NGHIÊM CẤM:**
  - Tự suy diễn hoặc bịa ra tỷ lệ R:R, Winrate, Max DD.
  - Tự viết thêm code minh họa hoặc logic giả định mà tác giả không cung cấp.
  - Để xảy ra mâu thuẫn giữa các file báo cáo và file tóm tắt.

### 4. NGUYÊN TẮC CLEAN REPO (VỆ SINH KHO LƯU TRỮ)
- Mọi script kiểm tra nhanh, dò tìm cấu trúc DOM hoặc regex dùng một lần **PHẢI ĐƯỢC ĐẶT VÀ THỰC THI TRONG** `.scratch/`.
- Thư mục `.scratch/` được cấu hình bỏ qua trong `.gitignore` và không bao giờ được commit vào git.
- Thư mục gốc và thư mục con `sources/*/scripts/` chỉ chứa các script tái lập (reproducible pipeline) đã qua kiểm thử và hoạt động ổn định.

---
*Vi phạm bất kỳ nguyên tắc nào ở trên sẽ kích hoạt script `repo_hygiene_check.py` báo lỗi và từ chối xuất dữ liệu.*
