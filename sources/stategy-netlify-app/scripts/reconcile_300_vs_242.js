import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const indexPath = path.resolve(__dirname, '../raw/thu_vien_index.json');
const reportsDir = path.resolve(__dirname, '../raw/reports_json');
const outputPath = path.resolve(__dirname, '../extracted/07_missing_58_items.json');

const indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
const files = new Set(fs.readdirSync(reportsDir).map(f => f.replace('.json', '')));

const danhSach = indexData.danh_sach || [];
const missingItems = [];

// Specific mapping for 18 unverified items
const unverifiedClassification = {
  'BRK025': { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Vẽ trendline nội bộ chủ quan, điểm vẽ thay đổi tùy người giao dịch.' },
  'BRK027': { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Mô hình rounding/cổ chén vẽ tay cảm tính, không có quy tắc toán học xác định độ cong.' },
  'BRK028': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu lịch kinh tế & dấu thời gian công bố tin tức chính xác.' },
  'BRK036': { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Kênh song song vẽ tay chủ quan theo đỉnh đáy cảm tính.' },
  'REV012': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu bảng dữ liệu thời điểm công bố tin tức vĩ mô để đo độ giật nến.' },
  'REV032': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu nguồn cấp dữ liệu lịch sự kiện kinh tế lớn trước 2 giờ.' },
  'REV038': { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Quy tắc đếm 3 cú đẩy trong ngày mang tính diễn giải chủ quan.' },
  'SEA008': { category: 'NOT_A_STANDALONE_STRATEGY', reason: 'Bộ lọc thời gian phiên (tránh 11-14h VN), không phải quy tắc vào/thoát lệnh độc lập.' },
  'SEA010': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu chu kỳ các kỳ họp FOMC của Fed.' },
  'SEA018': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu lịch đáo hạn và chuyển kỳ hợp đồng tương lai vàng (Gold Futures Rollover).' },
  'SEA024': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu lịch kinh tế Fed rate decision và họp báo FOMC.' },
  'SEA026': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu lịch công bố chỉ số CPI Hoa Kỳ.' },
  'SEA027': { category: 'NOT_A_STANDALONE_STRATEGY', reason: 'Bộ lọc phiên nghỉ giao dịch ban đêm (0-5h sáng VN), không phải chiến lược độc lập.' },
  'SEA030': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu tin tức cuối tuần (địa chính trị, sự kiện vĩ mô).' },
  'VIR016': { category: 'NOT_A_STANDALONE_STRATEGY', reason: 'Quy tắc lọc khung giờ ICT Kill Zones, là bộ lọc phiên cần kết hợp mô hình kích hoạt.' },
  'VIR021': { category: 'MISSING_AUXILIARY_DATA', reason: 'Thiếu dữ liệu chuỗi giá liên thị trường (Chỉ số DXY và Bạc XAGUSD).' },
  'VIR023': { category: 'NOT_A_STANDALONE_STRATEGY', reason: 'Framework quản trị thói quen giao dịch 5-3-1, không phải thuật toán định lượng.' },
  'VIR028': { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Chiến lược kết hợp KAMA + Bollinger Bands cảm tính, chưa được tối ưu hóa tham số.' }
};

// Specific mapping for 40 merged items
const duplicateExactIds = new Set(['BRK020', 'BRK033', 'SEA019', 'VIR032', 'VIR046', 'VIR047']);
const untestedVariantIds = new Set(['REV029', 'REV018', 'REV021', 'REV023', 'REV024', 'REV036', 'BRK039']);

for (const item of danhSach) {
  if (!files.has(item.id)) {
    let lyDo = '';
    let mergeRelation = null;
    let unverifiedCat = null;
    let verdictClean = item.verdict;
    let qualityFlags = [];

    if (item.trang_thai === 'gop') {
      if (duplicateExactIds.has(item.id)) {
        mergeRelation = 'DUPLICATE_EXACT';
      } else if (untestedVariantIds.has(item.id)) {
        mergeRelation = 'UNTESTED_VARIANT';
      } else {
        mergeRelation = 'RELATED_VARIANT';
      }

      // Check special case REV029: DO NOT inherit CHẤT
      if (item.id === 'REV029') {
        verdictClean = 'CHUA_KIEM_DINH_BIEN_THE_NGUOC';
        qualityFlags.push('UNTESTED_REVERSE_VARIANT_CANNOT_INHERIT_CHAT');
        lyDo = 'Biến thể bán ngược chiều (Fade) không được thừa kế phán quyết CHẤT của SEA003. Bản thân chưa được kiểm định độc lập.';
      } else {
        lyDo = item.ghi_chu || `Bản đối xứng / gộp biến thể của chiến lược gốc ${item.goc}. Không chạy file backtest riêng rẽ.`;
      }
    } else if (item.trang_thai === 'chua_kiem_dinh') {
      const mapping = unverifiedClassification[item.id] || { category: 'DISCRETIONARY_NOT_FORMALIZED', reason: 'Chưa kiểm định: dựa trên quy tắc vẽ tay/cảm tính chủ quan.' };
      unverifiedCat = mapping.category;
      lyDo = mapping.reason;
      verdictClean = 'CHUA_KIEM_DINH';
    } else {
      lyDo = 'Không có file report JSON trên server Netlify tĩnh.';
    }

    missingItems.push({
      id: item.id,
      ten: item.ten,
      ho: item.ho,
      khung_thoi_gian: item.tf,
      trang_thai: item.trang_thai,
      verdict_goc: verdictClean,
      xep_hang: item.xep_hang ?? null,
      goc_tham_chieu: item.goc || null,
      merge_relation: mergeRelation,
      unverified_category: unverifiedCat,
      data_quality_flags: qualityFlags,
      ly_do_thieu_file_json: lyDo
    });
  }
}

const summary = {
  tong_muc_index: indexData.tong,
  da_chay_co_file_json: files.size,
  tong_so_muc_thieu: missingItems.length,
  phan_loai_thieu: {
    gop_bien_the_doi_xung: missingItems.filter(i => i.trang_thai === 'gop').length,
    chua_kiem_dinh: missingItems.filter(i => i.trang_thai === 'chua_kiem_dinh').length,
    phan_loai_chua_kiem_dinh: {
      MISSING_AUXILIARY_DATA: missingItems.filter(i => i.unverified_category === 'MISSING_AUXILIARY_DATA').length,
      NOT_A_STANDALONE_STRATEGY: missingItems.filter(i => i.unverified_category === 'NOT_A_STANDALONE_STRATEGY').length,
      DISCRETIONARY_NOT_FORMALIZED: missingItems.filter(i => i.unverified_category === 'DISCRETIONARY_NOT_FORMALIZED').length
    },
    phan_loai_gop: {
      DUPLICATE_EXACT: missingItems.filter(i => i.merge_relation === 'DUPLICATE_EXACT').length,
      RELATED_VARIANT: missingItems.filter(i => i.merge_relation === 'RELATED_VARIANT').length,
      UNTESTED_VARIANT: missingItems.filter(i => i.merge_relation === 'UNTESTED_VARIANT').length
    }
  },
  danh_sach_chi_tiet_58_muc: missingItems
};

fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2), 'utf8');
console.log(`Successfully generated ${outputPath} with ${missingItems.length} items.`);
console.log('Breakdown:', JSON.stringify(summary.phan_loai_thieu, null, 2));
