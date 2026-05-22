'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { useOverviewStats, useFinancialAnalytics, usePatientAnalytics } from '@/lib/hooks/useDashboard'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { RevenueChart } from '@/components/dashboard/RevenueChart'
import { PatientDemographicsChart } from '@/components/dashboard/PatientDemographicsChart'
import { AgeDistributionChart } from '@/components/dashboard/AgeDistributionChart'
import { RevenueByMethodChart } from '@/components/dashboard/RevenueByMethodChart'
import { DateRangePicker } from '@/components/dashboard/DateRangePicker'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Users,
  Calendar,
  DollarSign,
  FileText,
  TrendingUp,
  Activity,
  Loader2,
  UserPlus,
  FilePlus,
} from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
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

  // Note: Trend calculations would come from backend in production
  // For now, we show static metrics without trends

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Welcome back, {user?.full_name}!
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DateRangePicker onRangeChange={handleDateRangeChange} />
        </div>
      </div>

      {/* Quick Actions */}
      <Card className="border-2 border-dashed border-gray-200 dark:border-gray-700 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950 dark:to-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-gray-900 dark:text-white">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 hover:border-indigo-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/patients/new')}
            >
              <UserPlus className="h-5 w-5 mb-2 text-indigo-600 dark:text-indigo-400" />
              <span className="font-medium text-sm">New Patient</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-green-50 dark:hover:bg-green-950 hover:border-green-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/appointments/new')}
            >
              <Calendar className="h-5 w-5 mb-2 text-green-600 dark:text-green-400" />
              <span className="font-medium text-sm">Schedule</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-purple-50 dark:hover:bg-purple-950 hover:border-purple-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/prescriptions/new')}
            >
              <FilePlus className="h-5 w-5 mb-2 text-purple-600 dark:text-purple-400" />
              <span className="font-medium text-sm">Prescription</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-blue-50 dark:hover:bg-blue-950 hover:border-blue-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/payments')}
            >
              <DollarSign className="h-5 w-5 mb-2 text-blue-600 dark:text-blue-400" />
              <span className="font-medium text-sm">Payment</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Key Metrics
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
            title="Monthly Revenue"
            value={`৳${(overview?.revenue_this_month || 0).toLocaleString()}`}
            description="Collected this month"
            icon={DollarSign}
          />
          <StatsCard
            title="Active Patients"
            value={overview?.active_patients || 0}
            description="Visited in last 30 days"
            icon={Activity}
          />
          <StatsCard
            title="Prescriptions"
            value={overview?.prescriptions_this_month || 0}
            description="Issued this month"
            icon={FileText}
          />
          <StatsCard
            title="Pending Payments"
            value={`৳${(overview?.pending_payments || 0).toLocaleString()}`}
            description="Outstanding amount"
            icon={TrendingUp}
            className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-800"
          />
        </div>
      </div>

      {/* Analytics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Analytics
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {financial?.daily_revenue && financial.daily_revenue.length > 0 ? (
            <RevenueChart data={financial.daily_revenue} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">Revenue Trend</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>No revenue data available</p>
                  <p className="text-xs mt-1">Start accepting payments to see trends</p>
                </div>
              </CardContent>
            </Card>
          )}

          {financial?.revenue_by_method ? (
            <RevenueByMethodChart data={financial.revenue_by_method} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">Revenue by Payment Method</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <DollarSign className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>No payment data available</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Patient Insights */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Patient Insights
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {patients?.demographics ? (
            <PatientDemographicsChart data={patients.demographics} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">Patient Demographics</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <Users className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>No patient data available</p>
                </div>
              </CardContent>
            </Card>
          )}

          {patients?.age_distribution ? (
            <AgeDistributionChart data={patients.age_distribution} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">Age Distribution</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>No age data available</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
