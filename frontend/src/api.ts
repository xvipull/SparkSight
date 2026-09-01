import type { DashboardData } from './types'

export type DashboardQuery = { start_date?: string; end_date?: string; regions: string[]; categories: string[] }
export async function getDashboard(query: DashboardQuery): Promise<DashboardData> {
  const params = new URLSearchParams()
  if (query.start_date) params.set('start_date', query.start_date)
  if (query.end_date) params.set('end_date', query.end_date)
  query.regions.forEach(value => params.append('regions', value))
  query.categories.forEach(value => params.append('categories', value))
  const response = await fetch(`/api/v1/dashboard?${params}`)
  if (!response.ok) throw new Error('SparkSight could not load analytics.')
  return response.json()
}
