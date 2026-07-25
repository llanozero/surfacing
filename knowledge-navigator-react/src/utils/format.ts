/** 权重显示：保留两位小数 */
export function formatWeight(w: number): string {
  return w.toFixed(2)
}

/** ISO 时间 → YYYY-MM-DD HH:mm */
export function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
