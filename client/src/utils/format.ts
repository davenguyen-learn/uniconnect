/**
 * Format số ngày Công tác xã hội (CTXH):
 * - Nếu không có phần thập phân (1, 2, 4...), không hiển thị ".0".
 * - Nếu có phần thập phân (1.5, 2.25...), hiển thị gọn gàng, tự động bỏ số 0 thừa ở cuối.
 */
export function formatCtxh(val: number | string | null | undefined): string {
  if (val == null || val === '') return '0';
  const num = typeof val === 'number' ? val : Number(val);
  if (isNaN(num)) return '0';
  return Number.isInteger(num) ? num.toString() : parseFloat(num.toFixed(1)).toString();
}
