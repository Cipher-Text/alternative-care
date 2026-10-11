'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import type { TrendData } from '@/types/dashboard'
import { parseISO } from 'date-fns'
import { useTranslations } from 'next-intl'
import { useDateFormat } from '@/lib/i18n/date'

interface RevenueChartProps {
  data: TrendData[]
  title?: string
}

export function RevenueChart({ data, title }: RevenueChartProps) {
  const t = useTranslations('chartsUi')
  const { fmt } = useDateFormat()
  const chartData = data.map((item) => ({
    date: fmt(parseISO(item.date), 'MMM dd'),
    revenue: item.value,
  }))

  const maxRevenue = Math.max(...chartData.map(d => d.revenue), 0)
  const totalRevenue = chartData.reduce((sum, d) => sum + d.revenue, 0)

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
            {title ?? t('revenueTrend')}
          </CardTitle>
          <div className="text-right">
            <p className="text-xs text-gray-600 dark:text-gray-400">{t('total')}</p>
            <p className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              ৳{totalRevenue.toLocaleString()}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#9ca3af"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `৳${value}`}
            />
            <Tooltip
              formatter={(value) => [`৳${Number(value).toLocaleString()}`, t('revenue')]}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
              labelStyle={{ color: '#6b7280' }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#6366f1"
              strokeWidth={3}
              fill="url(#colorRevenue)"
              dot={{ fill: '#6366f1', r: 4 }}
              activeDot={{ r: 6, fill: '#4f46e5' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
