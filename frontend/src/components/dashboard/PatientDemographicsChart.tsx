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

  const total = data.male + data.female + data.other

  if (total === 0) {
    return null
  }

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900 dark:text-white">
            Patient Demographics
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
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name}: ${((percent || 0) * 100).toFixed(0)}%`
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
              formatter={(value) => [`${value} patients`, '']}
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
      </CardContent>
    </Card>
  )
}
