---
name: web-source-ingestor
description: Safely crawls, intercepts, and stores raw HTML/JSON text payloads from target web sources into sources/<source_id>/raw/ while strictly blocking all binary/executable downloads.
---

# Web Source Ingestor Skill

## Mục đích
Thu thập an toàn toàn bộ dữ liệu công khai từ nguồn web mục tiêu (trang danh bạ EA, kho backtest, tài liệu định lượng) và lưu trữ nguyên bản vào `sources/<source-name>/raw/`.

## Quy tắc thực thi
1. **Kiểm tra cấu trúc nguồn:**
   - Dùng Browser Subagent hoặc HTTP fetch kiểm tra xem trang sử dụng HTML tĩnh (SSR), Next.js data bundle (`__NEXT_DATA__`), hay REST/GraphQL JSON APIs.
2. **Quy tắc Air-Gap & Binary Filter:**
   - Nếu phát hiện nút tải file hoặc link trỏ tới đuôi `.ex4`, `.ex5`, `.mq4`, `.mq5`, `.zip`, `.rar`, `.exe`, `.msi`, `.dll`: **TUYỆT ĐỐI KHÔNG BẤM VÀ KHÔNG GỬI REQUEST TẢI VỀ**.
   - Chỉ thu thập văn bản mô tả, bảng số liệu, đường link Myfxbook/MQL5 tín hiệu, và các metadata công khai.
3. **Lưu trữ nguyên vẹn:**
   - Lưu trữ toàn bộ payload thô vào `sources/<source-name>/raw/`.
   - Lưu trữ các tệp HTML/JSON kèm định danh rõ ràng, không chỉnh sửa nội dung trước khi lưu.
