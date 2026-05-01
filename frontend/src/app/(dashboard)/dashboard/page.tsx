'use client'

import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useOverviewStats, useFinancialAnalytics, usePatientAnalytics } from '@/lib/hooks/useDashboard'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { RevenueChart } from '@/components/dashboard/RevenueChart'
import { PatientDemographicsChart } from '@/components/dashboard/PatientDemographicsChart'
import { AgeDistributionChart } from '@/components/dashboard/AgeDistributionChart'
import { RevenueByMethodChart } from '@/components/dashboard/RevenueByMethodChart'
import { DateRangePicker } from '@/components/dashboard/DateRangePicker'
import {
  Users,
  Calendar,
  DollarSign,
  FileText,
  TrendingUp,
  Activity,
  Loader2,
} from 'lucide-react'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)
  const [dateRange, setDateRange] = useState<{
    date_from?: string
    date_to?: string
  }>({})

  const { data: overview, isLoading: overviewLoading } = useOverviewStats(dateRange)
  const { data: financial, isLoading: financialLoading } = useFinancialAnalytics(dateRange)
  const { data: patients, isLoading: patientsLoading } = usePatientAnalytics(dateRange)

  const handleDateRangeChange = (dateFrom?: string, dateTo?: string) => {
    setDateRange({
      date_from: dateFrom,
      date_to: dateTo,
    })
  }

  if (overviewLoading || financialLoading || patientsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back, {user?.full_name}!</p>
        </div>
        <DateRangePicker onRangeChange={handleDateRangeChange} />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Patients"
          value={overview?.total_patients || 0}
          description={`${overview?.new_patients_this_month || 0} new this month`}
          icon={Users}
        />
        <StatsCard
          title="Today's Appointments"
          value={overview?.appointments_today || 0}
          description={`${overview?.upcoming_appointments || 0} upcoming`}
          icon={Calendar}
        />
        <StatsCard
          title="This Month Revenue"
          value={`৳${(overview?.revenue_this_month || 0).toLocaleString()}`}
          description="Total collected"
          icon={DollarSign}
        />
        <StatsCard
          title="Pending Payments"
          value={`৳${(overview?.pending_payments || 0).toLocaleString()}`}
          description="Outstanding amount"
          icon={TrendingUp}
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Visits"
          value={overview?.total_visits || 0}
          description={`${overview?.visits_this_month || 0} this month`}
          icon={Activity}
        />
        <StatsCard
          title="Active Patients"
          value={overview?.active_patients || 0}
          description="Visited in last 30 days"
          icon={Users}
        />
        <StatsCard
          title="Prescriptions"
          value={overview?.total_prescriptions || 0}
          description={`${overview?.prescriptions_this_month || 0} this month`}
          icon={FileText}
        />
        <StatsCard
          title="Total Revenue"
          value={`৳${(overview?.total_revenue || 0).toLocaleString()}`}
          description="All time"
          icon={DollarSign}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {financial?.daily_revenue && financial.daily_revenue.length > 0 && (
          <RevenueChart data={financial.daily_revenue} />
        )}
        {financial?.revenue_by_method && (
          <RevenueByMethodChart data={financial.revenue_by_method} />
        )}
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {patients?.demographics && (
          <PatientDemographicsChart data={patients.demographics} />
        )}
        {patients?.age_distribution && (
          <AgeDistributionChart data={patients.age_distribution} />
        )}
      </div>
    </div>
  )
}
