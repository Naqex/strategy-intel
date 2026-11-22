import fs from 'fs';
import path from 'path';

const indexPath = path.resolve('raw/thu_vien_index.json');
const reportsDir = path.resolve('raw/reports_json');
const outputPath = path.resolve('extracted/07_missing_58_items.json');

const indexData = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
const files = new Set(fs.readdirSync(reportsDir).map(f => f.replace('.json', '')));

const danhSach = indexData.danh_sach || [];
const missingItems = [];

for (const item of danhSach) {
  if (!files.has(item.id)) {
    let lyDo = '';
    if (item.trang_thai === 'gop') {
      lyDo = item.ghi_chu || `Bản đối xứng / gộp biến thể của chiến lược gốc ${item.goc}. Không chạy file backtest riêng rẽ.`;
    } else if (item.trang_thai === 'chua_kiem_dinh') {
      lyDo = item.ly_do || 'Chưa kiểm định: dựa trên quy tắc vẽ tay/cảm tính chủ quan, không thể thuật toán hoá khách quan bằng máy.';
    } else {
      lyDo = 'Không có file report JSON trên server Netlify tĩnh.';
    }

    missingItems.push({
      id: item.id,
      ten: item.ten,
      ho: item.ho,
      khung_thoi_gian: item.tf,
      trang_thai: item.trang_thai,
      verdict_goc: item.verdict,
      xep_hang: item.xep_hang ?? null,
      goc_tham_chieu: item.goc || null,
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
    chua_kiem_dinh_chu_quan: missingItems.filter(i => i.trang_thai === 'chua_kiem_dinh').length,
    khac: missingItems.filter(i => i.trang_thai !== 'gop' && i.trang_thai !== 'chua_kiem_dinh').length
  },
  danh_sach_chi_tiet_58_muc: missingItems
};

fs.writeFileSync(outputPath, JSON.stringify(summary, null, 2), 'utf8');
console.log(`Successfully generated ${outputPath} with ${missingItems.length} items.`);
console.log('Breakdown:', summary.phan_loai_thieu);
