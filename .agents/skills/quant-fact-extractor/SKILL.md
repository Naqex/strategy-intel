---
name: quant-fact-extractor
description: Extracts structured quantitative facts and strategy rules from raw payloads into extracted/ using deterministic scripts without hallucination.
---

# Quant Fact Extractor Skill

## Mục đích
Phân tích và trích xuất dữ liệu định lượng có cấu trúc từ `sources/<source-name>/raw/` sang `sources/<source-name>/extracted/` bằng các script Python/Node xác định (deterministic).

## Quy tắc thực thi
1. **Zero-Hallucination:**
   - Tuyệt đối không tự suy diễn các trường thông tin mà web không cung cấp.
   - Trường nào không có dữ liệu bắt buộc điền: `NOT_DISCLOSED`.
   - Cấm tự tạo code minh họa hay giả định tỷ lệ R:R nếu tác giả không nêu rõ.
2. **Schema Validation:**
   - Định nghĩa Pydantic schema hoặc cấu trúc dữ liệu chặt chẽ cho đầu ra JSON/CSV.
   - Xác thực kiểu dữ liệu (bool, float, string) trước khi ghi ra tệp.
3. **Trích dẫn nguyên văn:**
   - Mọi trích đoạn quy tắc, lý do gắn nhãn rủi ro (Grid/Martingale) phải trích nguyên văn từ văn bản của trang web.
