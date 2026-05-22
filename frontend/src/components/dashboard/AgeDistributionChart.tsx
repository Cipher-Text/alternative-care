'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { AgeGroupDistribution } from '@/types/dashboard'

interface AgeDistributionChartProps {
  data: AgeGroupDistribution
}

export function AgeDistributionChart({ data }: AgeDistributionChartProps) {
  const chartData = [
    { ageGroup: '0-18', count: data.age_0_18, label: 'Children' },
    { ageGroup: '19-35', count: data.age_19_35, label: 'Young Adults' },
    { ageGroup: '36-50', count: data.age_36_50, label: 'Adults' },
    { ageGroup: '51-65', count: data.age_51_65, label: 'Middle Age' },
    { ageGroup: '66+', count: data.age_66_plus, label: 'Seniors' },
  ]

  const total = chartData.reduce((sum, item) => sum + item.count, 0)

  if (total === 0) {
    return null
  }

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
            Age Distribution
          </CardTitle>
          <div className="text-right">
            <p className="text-xs text-gray-600 dark:text-gray-400">Total</p>
            <p className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
              {total}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
            <XAxis
              dataKey="ageGroup"
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
            />
            <Tooltip
              formatter={(value, name, props) => [
                `${value} patients`,
                props.payload.label
              ]}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
              labelStyle={{ color: '#6b7280' }}
            />
            <Bar
              dataKey="count"
              fill="#6366f1"
              radius={[8, 8, 0, 0]}
              maxBarSize={60}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
