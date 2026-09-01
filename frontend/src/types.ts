export interface Metric { name: string; revenue: number; profit: number; orders: number }
export interface DashboardData {
  filters: { regions: string[]; categories: string[]; min_date: string; max_date: string }
  kpis: { revenue: number; profit: number; orders: number; units_sold: number; profit_margin: number; average_order_value: number }
  revenue_trend: { period: string; revenue: number; profit: number; orders: number }[]
  category_performance: Metric[]; regional_performance: Metric[]; top_products: Metric[]
  transactions: { order_id: string; order_date: string; region: string; category: string; product: string; customer: string; quantity: number; revenue: number; profit: number }[]
}
