'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
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
  const t = useTranslations('chartsUi')
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
      <SelectTrigger aria-label={t('dateRange')} className="w-[180px]">
        <SelectValue placeholder={t('selectPeriod')} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="today">{t('today')}</SelectItem>
        <SelectItem value="week">{t('last7')}</SelectItem>
        <SelectItem value="month">{t('last30')}</SelectItem>
        <SelectItem value="3months">{t('last3m')}</SelectItem>
        <SelectItem value="year">{t('lastYear')}</SelectItem>
        <SelectItem value="all">{t('allTime')}</SelectItem>
      </SelectContent>
    </Select>
  )
}
