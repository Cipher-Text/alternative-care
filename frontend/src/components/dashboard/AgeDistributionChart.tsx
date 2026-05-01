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
    { ageGroup: '0-18', count: data.age_0_18 },
    { ageGroup: '19-35', count: data.age_19_35 },
    { ageGroup: '36-50', count: data.age_36_50 },
    { ageGroup: '51-65', count: data.age_51_65 },
    { ageGroup: '66+', count: data.age_66_plus },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Age Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="ageGroup"
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
              }}
            />
            <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
