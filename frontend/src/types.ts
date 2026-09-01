export type AnalyticsRow = Record<string, string | number | null>
export interface Overview { totalRevenue: number; totalProfit: number; totalOrders: number; averageOrderValue: number; totalCustomers: number; unitsSold: number; profitMargin: number; returnRate: number }
export interface DashboardData { overview: Overview; monthlySales: AnalyticsRow[]; monthlyProfit: AnalyticsRow[]; categories: AnalyticsRow[]; regions: AnalyticsRow[]; products: AnalyticsRow[]; segments: AnalyticsRow[]; channels: AnalyticsRow[]; orderStatus: AnalyticsRow[] }
export interface PipelineStatus { status: string; records_processed: number; data_source: string; processing_engine: string; api: string; frontend: string }
