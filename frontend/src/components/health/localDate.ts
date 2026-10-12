/** Today as YYYY-MM-DD in the user's own time zone. `toISOString()` is UTC, which is the previous day for
 * the first hours of a Bangladesh morning. */
export function localToday(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}
