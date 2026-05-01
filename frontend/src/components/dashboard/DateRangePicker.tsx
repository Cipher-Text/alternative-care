'use client'

import { useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { subDays, subMonths, format } from 'date-fns'

export type DateRangePreset = 'today' | 'week' | 'month' | '3months' | 'year' | 'all'

interface DateRangePickerProps {
  onRangeChange: (dateFrom?: string, dateTo?: string) => void
}

export function DateRangePicker({ onRangeChange }: DateRangePickerProps) {
  const [preset, setPreset] = useState<DateRangePreset>('month')

  const handlePresetChange = (value: DateRangePreset) => {
    setPreset(value)

    const today = new Date()
    const formatStr = 'yyyy-MM-dd'

    switch (value) {
      case 'today':
        onRangeChange(format(today, formatStr), format(today, formatStr))
        break
      case 'week':
        onRangeChange(format(subDays(today, 7), formatStr), format(today, formatStr))
        break
      case 'month':
        onRangeChange(format(subMonths(today, 1), formatStr), format(today, formatStr))
        break
      case '3months':
        onRangeChange(format(subMonths(today, 3), formatStr), format(today, formatStr))
        break
      case 'year':
        onRangeChange(format(subMonths(today, 12), formatStr), format(today, formatStr))
        break
      case 'all':
        onRangeChange(undefined, undefined)
        break
    }
  }

  return (
    <Select value={preset} onValueChange={handlePresetChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select period" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="today">Today</SelectItem>
        <SelectItem value="week">Last 7 Days</SelectItem>
        <SelectItem value="month">Last 30 Days</SelectItem>
        <SelectItem value="3months">Last 3 Months</SelectItem>
        <SelectItem value="year">Last Year</SelectItem>
        <SelectItem value="all">All Time</SelectItem>
      </SelectContent>
    </Select>
  )
}
