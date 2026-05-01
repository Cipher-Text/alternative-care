export function apiUrl(path: string): string {
  const base = process.env.E2E_API_URL || 'http://localhost:8000/api/v1'
  return `${base}${path}`
}
