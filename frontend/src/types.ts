export type AnalyticsRow = Record<string, string | number | null>
export interface Overview { totalRevenue: number; totalProfit: number; totalOrders: number; averageOrderValue: number; totalCustomers: number; unitsSold: number; profitMargin: number; returnRate: number }
export interface DashboardData { overview: Overview; monthlySales: AnalyticsRow[]; monthlyProfit: AnalyticsRow[]; categories: AnalyticsRow[]; regions: AnalyticsRow[]; products: AnalyticsRow[]; segments: AnalyticsRow[]; channels: AnalyticsRow[]; orderStatus: AnalyticsRow[] }
export interface PipelineStatus { status: string; records_processed: number; data_source: string; processing_engine: string; api: string; frontend: string }
export interface FilterOptions { regions: string[]; categories: string[]; customer_segments: string[]; sales_channels: string[]; min_date: string; max_date: string }
export interface GlobalFilters { start_date: string; end_date: string; region: string; category: string; customer_segment: string; sales_channel: string }
export interface ProductSummary { total_product_revenue: number; total_product_profit: number; units_sold: number; number_products: number; best_performing_category: string }
export interface ProductData { summary: ProductSummary; revenueProducts: AnalyticsRow[]; profitProducts: AnalyticsRow[]; categories: AnalyticsRow[]; tableProducts: AnalyticsRow[] }
export interface CustomerSummary { total_customers: number; average_revenue_per_customer: number; average_order_value: number; returning_customer_rate: number }
export interface CustomerData { summary: CustomerSummary; topCustomers: AnalyticsRow[]; segments: AnalyticsRow[] }
