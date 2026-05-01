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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue by Payment Method</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) =>
                `${name}: ৳${value.toLocaleString()}`
              }
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `৳${Number(value || 0).toLocaleString()}`}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        <div className="text-center mt-4">
          <p className="text-sm text-muted-foreground">Total Revenue</p>
          <p className="text-2xl font-bold">৳{total.toLocaleString()}</p>
        </div>
      </CardContent>
    </Card>
  )
}
