'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { PatientDemographics } from '@/types/dashboard'

interface PatientDemographicsChartProps {
  data: PatientDemographics
}

const COLORS = {
  male: '#3b82f6',
  female: '#ec4899',
  other: '#8b5cf6',
}

export function PatientDemographicsChart({ data }: PatientDemographicsChartProps) {
  const chartData = [
    { name: 'Male', value: data.male, color: COLORS.male },
    { name: 'Female', value: data.female, color: COLORS.female },
    { name: 'Other', value: data.other, color: COLORS.other },
  ].filter((item) => item.value > 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Demographics</CardTitle>
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
                `${name}: ${((percent || 0) * 100).toFixed(0)}%`
              }
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
