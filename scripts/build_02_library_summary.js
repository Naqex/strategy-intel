import fs from 'fs';
import path from 'path';

const index = JSON.parse(fs.readFileSync('raw/thu_vien_index.json', 'utf8'));
const reportsDir = 'raw/reports_json';

const summaryList = [];

for (const item of index.danh_sach) {
  // Only process 242 tested strategies
  if (item.trang_thai !== 'da_kiem_dinh') continue;

  const reportPath = path.join(reportsDir, `${item.id}.json`);
  let reportData = null;
  if (fs.existsSync(reportPath)) {
    reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  }

  const spec = reportData?.spec || {};
  const tc = reportData?.tieu_chi || {};
  const isData = reportData?.IS || {};
  const oosData = reportData?.OOS || {};
  const oos2Data = reportData?.OOS2 || {};

  summaryList.push({
    id: item.id,
    ten: item.ten || spec.ten || '',
    ho: item.ho || spec.ho || '',
    khung_thoi_gian: item.tf || spec.tf || '',
    quy_tac_mo_ta: spec.mo_ta || '',
    nguon_goc: spec.nguon || '',
    verdict_goc: item.verdict || reportData?.verdict || '',
    ket_qua_pass_fail: item.verdict === 'CHẤT' ? 'PASS (Đạt tiêu chí)' : (item.verdict === 'TÌNH HUỐNG' ? 'CONDITIONAL (Tình huống/Bối cảnh)' : 'FAIL (Không đạt)'),
    xep_hang: item.xep_hang ?? null,
    tin_cay: item.tin_cay || '',
    
    // 5 Tiêu chí kiểm định
    tieu_chi: {
      tieu_chi_1_hon_ngau_nhien: tc.edge_vs_null ?? null,
      tieu_chi_2_ben_tham_so: tc.ben_tham_so ?? null,
      tieu_chi_3_song_sot_oos1: tc.song_sot_oos ?? null,
      tieu_chi_4_da_tru_phi: tc.chiu_phi ?? null,
      tieu_chi_5_du_lon_mau_tren_100_lenh: tc.kha_thi ?? null,
      so_tieu_chi_dat: Object.values(tc).filter(Boolean).length
    },

    // Giai đoạn In-Sample (2004-2018)
    in_sample_2004_2018: {
      so_lenh: isData.n ?? null,
      winrate_pct: isData.wr ?? null,
      so_nam_duong: isData.years_pos ?? '',
      chi_tiet_nam: isData.nam_duong ?? {}
    },

    // Giai đoạn Out-of-Sample Kỳ 1 (2019-2023)
    out_of_sample_1_2019_2023: {
      so_lenh: oosData.n ?? item.oos_n ?? null,
      winrate_pct: oosData.wr ?? null,
      so_nam_duong: oosData.years_pos ?? item.oos_years ?? '',
      chi_tiet_nam: oosData.nam_duong ?? {}
    },

    // Giai đoạn Out-of-Sample Kỳ 2 (2024-2026)
    out_of_sample_2_2024_2026: {
      so_lenh: oos2Data.n ?? item.oos2_n ?? null,
      winrate_pct: oos2Data.wr ?? null,
      so_nam_duong: oos2Data.years_pos ?? item.oos2_years ?? '',
      trang_thai: oos2Data.status ?? item.oos2_status ?? '',
      chi_tiet_nam: oos2Data.nam_duong ?? {}
    }
  });
}

console.log(`Compiled summary for ${summaryList.length} strategies.`);

// Save JSON
fs.writeFileSync('extracted/02_library_242_summary.json', JSON.stringify({
  tong_quan: {
    tong_so_muc_danh_ba: index.tong,
    da_kiem_dinh: index.da_chay,
    ho_so_gop_bien_the: index.gop,
    chua_kiem_dinh: index.chua,
    phan_bo_verdict_da_chay: index.verdict_da_chay,
    ky_thi_lan_2: index.ky_thi_2
  },
  danh_sach_242_chien_luoc: summaryList
}, null, 2), 'utf8');

// Save CSV
const csvHeaders = [
  'Mã ID',
  'Tên Chiến Lược',
  'Họ Chiến Lược',
  'Khung Thời Gian',
  'Quy Tắc Vào/Thoát',
  'Nguồn Gốc',
  'Kết Luận (Verdict)',
  'Phân Loại Pass/Fail',
  'Xếp Hạng',
  'Tiêu Chí Đạt (x/5)',
  'Hơn Ngẫu Nhiên',
  'Bền Tham Số',
  'Sống Sót OOS1',
  'Đã Trừ Phí',
  'Đủ Mẫu (>=100)',
  'IS Lệnh',
  'IS Winrate (%)',
  'IS Năm Dương',
  'OOS1 Lệnh',
  'OOS1 Winrate (%)',
  'OOS1 Năm Dương',
  'OOS2 Lệnh',
  'OOS2 Winrate (%)',
  'OOS2 Năm Dương',
  'OOS2 Trạng Thái'
];

function escapeCsv(val) {
  if (val === null || val === undefined) return '';
  const str = String(val);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

const csvRows = [csvHeaders.join(',')];
for (const s of summaryList) {
  csvRows.push([
    escapeCsv(s.id),
    escapeCsv(s.ten),
    escapeCsv(s.ho),
    escapeCsv(s.khung_thoi_gian),
    escapeCsv(s.quy_tac_mo_ta),
    escapeCsv(s.nguon_goc),
    escapeCsv(s.verdict_goc),
    escapeCsv(s.ket_qua_pass_fail),
    escapeCsv(s.xep_hang),
    escapeCsv(`${s.tieu_chi.so_tieu_chi_dat}/5`),
    escapeCsv(s.tieu_chi.tieu_chi_1_hon_ngau_nhien ? 'ĐẠT' : 'KHÔNG'),
    escapeCsv(s.tieu_chi.tieu_chi_2_ben_tham_so ? 'ĐẠT' : 'KHÔNG'),
    escapeCsv(s.tieu_chi.tieu_chi_3_song_sot_oos1 ? 'ĐẠT' : 'KHÔNG'),
    escapeCsv(s.tieu_chi.tieu_chi_4_da_tru_phi ? 'ĐẠT' : 'KHÔNG'),
    escapeCsv(s.tieu_chi.tieu_chi_5_du_lon_mau_tren_100_lenh ? 'ĐẠT' : 'KHÔNG'),
    escapeCsv(s.in_sample_2004_2018.so_lenh),
    escapeCsv(s.in_sample_2004_2018.winrate_pct),
    escapeCsv(s.in_sample_2004_2018.so_nam_duong),
    escapeCsv(s.out_of_sample_1_2019_2023.so_lenh),
    escapeCsv(s.out_of_sample_1_2019_2023.winrate_pct),
    escapeCsv(s.out_of_sample_1_2019_2023.so_nam_duong),
    escapeCsv(s.out_of_sample_2_2024_2026.so_lenh),
    escapeCsv(s.out_of_sample_2_2024_2026.winrate_pct),
    escapeCsv(s.out_of_sample_2_2024_2026.so_nam_duong),
    escapeCsv(s.out_of_sample_2_2024_2026.trang_thai)
  ].join(','));
}

fs.writeFileSync('extracted/02_library_242_summary.csv', '\uFEFF' + csvRows.join('\n'), 'utf8');
console.log('Successfully written 02_library_242_summary.json and 02_library_242_summary.csv!');
