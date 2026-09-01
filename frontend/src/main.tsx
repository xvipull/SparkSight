import { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BarChart3, CircleDollarSign, Package, Percent, RotateCcw, ShoppingBag, TrendingDown, TrendingUp, Users } from 'lucide-react'
import { loadDashboard, loadFilterOptions } from './api'
import { ChartCard } from './components/ChartCard'
import { ErrorState } from './components/ErrorState'
import { Header } from './components/Header'
import { DashboardSkeleton } from './components/LoadingSkeleton'
import { MetricCard } from './components/MetricCard'
import { Sidebar } from './components/Sidebar'
import { PipelinePage } from './components/PipelinePage'
import { FilterBar } from './components/FilterBar'
import { ProductsPage } from './components/ProductsPage'
import { CustomersPage } from './components/CustomersPage'
import { RegionsPage } from './components/RegionsPage'
import { CategoryChart, ChannelChart, RegionChart, RevenueChart, SegmentChart, StatusChart } from './components/charts'
import { TopProductsTable } from './components/TopProductsTable'
import { inr, metric, s } from './lib/format'
import type { DashboardData, FilterOptions, GlobalFilters } from './types'
import './styles.css'
import './polish.css'

function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [page, setPage] = useState('overview')
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [filters, setFilters] = useState<GlobalFilters>({ start_date: '', end_date: '', region: '', category: '', customer_segment: '', sales_channel: '' })
  const refresh = async () => { setRefreshing(true); setError(false); try { setData(await loadDashboard(filters)) } catch { setError(true) } finally { setRefreshing(false) } }
  useEffect(() => { void loadFilterOptions().then(setOptions) }, [])
  useEffect(() => { void refresh() }, [filters.start_date, filters.end_date, filters.region, filters.category, filters.customer_segment, filters.sales_channel])
  useEffect(() => { const updatePage = () => setPage(window.location.hash.slice(1) || 'overview'); updatePage(); window.addEventListener('hashchange', updatePage); return () => window.removeEventListener('hashchange', updatePage) }, [])
  const range = useMemo(() => { if (!data?.monthlySales.length) return 'All available data'; const months = data.monthlySales.map(row => s(row, 'year_month')); return `${months[0]} — ${months[months.length - 1]}` }, [data])
  if (error && !data) return <ErrorState retry={() => void refresh()}/>
  return <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}><Sidebar collapsed={collapsed} toggle={() => setCollapsed(value => !value)} activePage={page}/><main className="main">{page === 'data-pipeline' ? <PipelinePage/> : <><Header range={range} refreshing={refreshing} refresh={() => void refresh()} title={page === 'products' ? 'Product Performance' : page === 'customers' ? 'Customer Intelligence' : page === 'regions' ? 'Regional Performance' : 'Sales Analytics'} subtitle={page === 'products' ? 'Product-level revenue and profitability intelligence' : page === 'customers' ? 'Customer performance and segment intelligence powered by Spark' : page === 'regions' ? 'Regional sales, order volume, and margin intelligence' : undefined}/><FilterBar options={options} filters={filters} update={(key, value) => setFilters(current => ({ ...current, [key]: value }))} clear={() => setFilters({ start_date: '', end_date: '', region: '', category: '', customer_segment: '', sales_channel: '' })}/>{page === 'products' ? <ProductsPage filters={filters}/> : page === 'customers' ? <CustomersPage filters={filters}/> : page === 'regions' ? <RegionsPage filters={filters}/> : !data ? <DashboardSkeleton/> : <><section className="metrics" id="overview"><MetricCard icon={CircleDollarSign} label="Total Revenue" value={inr(data.overview.totalRevenue)} detail="Gross sales processed"/><MetricCard icon={TrendingUp} label="Total Profit" value={inr(data.overview.totalProfit)} detail={`${data.overview.profitMargin.toFixed(1)}% net margin`} tone="green"/><MetricCard icon={ShoppingBag} label="Total Orders" value={metric(data.overview.totalOrders)} detail="Validated transactions"/><MetricCard icon={BarChart3} label="Average Order Value" value={inr(data.overview.averageOrderValue)} detail="Revenue per transaction" tone="amber"/><MetricCard icon={Users} label="Customers" value={metric(data.overview.totalCustomers)} detail="Distinct customer accounts"/><MetricCard icon={Package} label="Units Sold" value={metric(data.overview.unitsSold)} detail="Across all channels"/><MetricCard icon={Percent} label="Profit Margin" value={`${data.overview.profitMargin.toFixed(1)}%`} detail="Revenue-weighted margin" tone="green"/><MetricCard icon={RotateCcw} label="Return Rate" value={`${data.overview.returnRate.toFixed(1)}%`} detail="Returned transactions" tone="red"/></section>
  <section className="chart-grid feature" id="sales-trends"><ChartCard title="Revenue Trend" description="Monthly revenue and profit performance" className="revenue-card"><RevenueChart sales={data.monthlySales} profit={data.monthlyProfit}/></ChartCard><ChartCard title="Sales by Category" description="Revenue contribution"><CategoryChart data={data.categories}/></ChartCard></section>
  <section className="chart-grid"><ChartCard title="Revenue by Region" description="Regional revenue distribution" id="regions"><RegionChart data={data.regions}/></ChartCard><ChartCard title="Top Products" description="Ranked by net revenue" id="products"><TopProductsTable products={data.products}/></ChartCard></section>
  <section className="chart-grid"><ChartCard title="Customer Segments" description="Revenue by customer profile" id="customers"><SegmentChart data={data.segments}/></ChartCard><ChartCard title="Sales Channels" description="Channel contribution to revenue"><ChannelChart data={data.channels}/></ChartCard></section>
  <section className="chart-grid final-row"><ChartCard title="Order Status Distribution" description="Completed, returned, and cancelled"><StatusChart data={data.orderStatus}/></ChartCard><ChartCard title="Profit vs Revenue" description="Performance comparison across time"><RevenueChart sales={data.monthlySales} profit={data.monthlyProfit}/></ChartCard></section></>}</>}</main></div>
}
createRoot(document.getElementById('root')!).render(<App />)
