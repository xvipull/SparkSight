export const number = new Intl.NumberFormat('en-IN')
export function inr(value: number, compact = true): string { if (!Number.isFinite(value)) return '—'; const absolute = Math.abs(value); if (!compact) return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value); if (absolute >= 10_000_000) return `₹${(value / 10_000_000).toFixed(2)} Cr`; if (absolute >= 100_000) return `₹${(value / 100_000).toFixed(1)} L`; if (absolute >= 1_000) return `₹${(value / 1_000).toFixed(1)} K`; return `₹${value.toFixed(0)}` }
export function metric(value: number, suffix = ''): string { return `${number.format(value)}${suffix}` }
export function n(row: Record<string, string | number | null>, key: string): number { return Number(row[key] ?? 0) }
export function s(row: Record<string, string | number | null>, key: string): string { return String(row[key] ?? 'Unknown') }
