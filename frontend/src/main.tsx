import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BarChart3, Boxes, CalendarDays, ChevronDown, DollarSign, Package, TrendingUp } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getDashboard, type DashboardQuery } from './api'
import type { DashboardData } from './types'
import './styles.css'

const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const compactMoney = (value: number) => value >= 1000 ? `$${(value / 1000).toFixed(1)}k` : `$${value}`
const colors = ['#6366f1', '#22c55e', '#f59e0b', '#ec4899', '#06b6d4', '#8b5cf6']

function MultiSelect({ label, values, selected, onChange }: { label: string; values: string[]; selected: string[]; onChange: (values: string[]) => void }) {
  return <label className="filter"><span>{label}</span><select multiple value={selected} onChange={event => onChange([...event.target.selectedOptions].map(o => o.value))} aria-label={label}>
    {values.map(value => <option key={value} value={value}>{value}</option>)}
  </select><ChevronDown size={15} /></label>
}

function App() {
  const [data, setData] = useState<DashboardData>()
  const [error, setError] = useState('')
  const [query, setQuery] = useState<DashboardQuery>({ regions: [], categories: [] })
  const load = async () => { try { setError(''); setData(await getDashboard(query)) } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load data') } }
  useEffect(() => { load() }, [query.start_date, query.end_date, query.regions.join(','), query.categories.join(',')])
  const update = (partial: Partial<DashboardQuery>) => setQuery(current => ({ ...current, ...partial }))
  if (error) return <main className="state"><h1>SparkSight</h1><p>{error}</p><button onClick={load}>Try again</button></main>
  if (!data) return <main className="state"><Activity className="animate-pulse" size={34}/><p>Running SparkSight analytics…</p></main>
  const cards = [
    ['Total Revenue', money.format(data.kpis.revenue), DollarSign, 'Processed sales'],
    ['Net Profit', money.format(data.kpis.profit), TrendingUp, `${data.kpis.profit_margin}% margin`],
    ['Orders', data.kpis.orders.toLocaleString(), BarChart3, `${money.format(data.kpis.average_order_value)} avg. order`],
    ['Units Sold', data.kpis.units_sold.toLocaleString(), Package, 'Across selected transactions'],
  ] as const
  return <div className="shell">
    <aside><div className="brand"><span className="brand-mark"><Boxes size={21}/></span><span>SparkSight</span></div><nav><a className="active"><BarChart3 size={18}/> Overview</a><a><TrendingUp size={18}/> Sales performance</a><a><Package size={18}/> Products</a></nav><div className="spark-note"><Activity size={18}/><div><strong>Apache Spark</strong><small>Processing active</small></div></div></aside>
    <main className="content"><header><div><p className="eyebrow">DISTRIBUTED SALES ANALYTICS</p><h1>Sales overview</h1><p className="subtitle">Live metrics calculated from your Spark data pipeline.</p></div><div className="date-range"><CalendarDays size={17}/>{data.filters.min_date} — {data.filters.max_date}</div></header>
      <section className="filters"><label className="filter"><span>From</span><input type="date" min={data.filters.min_date} max={data.filters.max_date} value={query.start_date ?? ''} onChange={e => update({ start_date: e.target.value || undefined })}/></label><label className="filter"><span>To</span><input type="date" min={data.filters.min_date} max={data.filters.max_date} value={query.end_date ?? ''} onChange={e => update({ end_date: e.target.value || undefined })}/></label><MultiSelect label="Regions" values={data.filters.regions} selected={query.regions} onChange={regions => update({ regions })}/><MultiSelect label="Categories" values={data.filters.categories} selected={query.categories} onChange={categories => update({ categories })}/><button className="clear" onClick={() => setQuery({ regions: [], categories: [] })}>Clear filters</button></section>
      <section className="cards">{cards.map(([label, value, Icon, note]) => <article className="card" key={label}><div className="card-icon"><Icon size={19}/></div><p>{label}</p><h2>{value}</h2><small>{note}</small></article>)}</section>
      <section className="grid primary"><article className="panel span-2"><div className="panel-title"><div><h2>Revenue trend</h2><p>Monthly revenue and profit</p></div><span>USD</span></div><ResponsiveContainer width="100%" height={300}><LineChart data={data.revenue_trend} margin={{left: 4, right: 14}}><CartesianGrid vertical={false} stroke="#e7eaf1"/><XAxis dataKey="period" tickLine={false} axisLine={false}/><YAxis tickFormatter={compactMoney} tickLine={false} axisLine={false}/><Tooltip formatter={(v: number) => money.format(v)}/><Legend/><Line type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={3} dot={false}/><Line type="monotone" dataKey="profit" stroke="#22c55e" strokeWidth={3} dot={false}/></LineChart></ResponsiveContainer></article>
      <article className="panel"><div className="panel-title"><div><h2>Revenue by category</h2><p>Share of sales</p></div></div><ResponsiveContainer width="100%" height={300}><PieChart><Pie data={data.category_performance} dataKey="revenue" nameKey="name" innerRadius={67} outerRadius={105} paddingAngle={3}>{data.category_performance.map((_, i) => <Cell key={i} fill={colors[i]}/>)}</Pie><Tooltip formatter={(v: number) => money.format(v)}/><Legend/></PieChart></ResponsiveContainer></article></section>
      <section className="grid"><article className="panel"><div className="panel-title"><div><h2>Regional performance</h2><p>Revenue by market</p></div></div><ResponsiveContainer width="100%" height={260}><BarChart data={data.regional_performance} layout="vertical" margin={{left: 20}}><XAxis type="number" tickFormatter={compactMoney} hide/><YAxis type="category" dataKey="name" width={55} tickLine={false} axisLine={false}/><Tooltip formatter={(v: number) => money.format(v)}/><Bar dataKey="revenue" fill="#6366f1" radius={[0,5,5,0]}/></BarChart></ResponsiveContainer></article><article className="panel"><div className="panel-title"><div><h2>Top products</h2><p>Highest-grossing items</p></div></div><div className="rankings">{data.top_products.map((item, index) => <div className="ranking" key={item.name}><b>{String(index + 1).padStart(2, '0')}</b><span>{item.name}<small>{item.orders} orders</small></span><strong>{money.format(item.revenue)}</strong></div>)}</div></article></section>
      <section className="panel table-panel"><div className="panel-title"><div><h2>Recent transactions</h2><p>Latest processed sales records</p></div><span>{data.transactions.length} shown</span></div><div className="table-wrap"><table><thead><tr><th>Order</th><th>Customer</th><th>Product</th><th>Region</th><th>Revenue</th><th>Profit</th></tr></thead><tbody>{data.transactions.map(t => <tr key={t.order_id}><td><b>{t.order_id}</b><small>{t.order_date}</small></td><td>{t.customer}</td><td>{t.product}<small>{t.category} · {t.quantity} units</small></td><td><span className="tag">{t.region}</span></td><td>{money.format(t.revenue)}</td><td className={t.profit >= 0 ? 'positive' : 'negative'}>{money.format(t.profit)}</td></tr>)}</tbody></table></div></section>
    </main></div>
}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
