'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { RevenueByMethod } from '@/types/dashboard'

interface RevenueByMethodChartProps {
  data: RevenueByMethod
}

const COLORS = {
  cash: '#10b981',
  bkash: '#f59e0b',
  other: '#6366f1',
}

export function RevenueByMethodChart({ data }: RevenueByMethodChartProps) {
  const chartData = [
    { name: 'Cash', value: data.cash, color: COLORS.cash },
    { name: 'bKash', value: data.bkash, color: COLORS.bkash },
    { name: 'Other', value: data.other, color: COLORS.other },
  ].filter((item) => item.value > 0)

  const total = data.cash + data.bkash + data.other

  if (total === 0) {
    return null
  }

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
          Revenue by Payment Method
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
              }
              outerRadius={90}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `৳${Number(value || 0).toLocaleString()}`}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="text-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">Total Revenue</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            ৳{total.toLocaleString()}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
