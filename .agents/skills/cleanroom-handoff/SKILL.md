---
name: cleanroom-handoff
description: Packages validated external leads into catalog/master_leads.json, rejects toxic patterns into catalog/rejected_log.json, and sanitizes holdout data before staging in handoff/.
---

# Cleanroom Handoff Skill

## Mục đích
Sàng lọc các chiến lược/EA đạt tiêu chuẩn định lượng đưa vào danh mục chính `catalog/master_leads.json`, lưu vết các chiến lược rác/Grid/Martingale vào `catalog/rejected_log.json`, và chuẩn bị dữ liệu bàn giao an toàn cho đội ngũ Quant tại `handoff/`.

## Quy tắc thực thi
1. **Phân loại rủi ro nghiêm ngặt:**
   - Chiến lược có dấu hiệu Grid, Martingale, nhồi lệnh khi âm, hoặc không có Stop Loss: Gắn nhãn `REJECTED_TOXIC_RISK` và đẩy vào `catalog/rejected_log.json`.
   - Chiến lược có Stop Loss xác định, logic rõ ràng, có Myfxbook/MQL5 kiểm chứng: Đẩy vào `catalog/master_leads.json`.
2. **Khử nhiễm Holdout (Holdout Sanitization):**
   - Tuyệt đối không cho phép kết quả kiểm định của các năm `2025` và `2026` lọt vào thư mục `handoff/`.
   - Giai đoạn 2025–2026 được bảo lưu nghiêm ngặt làm tập Holdout kiểm tra mù cho hệ thống nội bộ.
   - Bắt buộc chạy script `holdout_sanitizer.py` kiểm tra 100% tệp trong `handoff/` trước khi xuất kho.
