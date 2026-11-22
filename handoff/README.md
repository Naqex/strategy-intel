# CLEANROOM HANDOFF STAGING AREA

> **Mục đích:** Vùng đệm bàn giao các hồ sơ chiến lược đã qua kiểm toán cho đội ngũ Quant nghiên cứu nội bộ (`Naqex`).

## NGUYÊN TẮC BẢO VỆ HOLDOUT:
1. Mọi tệp tin đặt trong thư mục này **TUYỆT ĐỐI KHÔNG CHỨA DỮ LIỆU KẾT QUẢ/PnL CỦA GIAI ĐOẠN HOLDOUT NGOÀI MẪU KỲ 2**.
2. Toàn bộ dữ liệu bàn giao phải được làm sạch bằng script `python scripts/common/holdout_sanitizer.py`.
3. Chỉ bàn giao các chiến lược có logic rõ ràng (`REPLICABLE_FROM_PUBLIC` hoặc `CONCEPT_ONLY_NEEDS_SLTP_DESIGN`), cấm tuyệt đối mọi biến thể Grid/Martingale.
