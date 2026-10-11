'use client'

import { useTranslations } from 'next-intl'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useCan } from '@/lib/auth/permissions'
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

  useEffect(() => {
    if (user && !user.tenant_id && (user.role === 'admin' || user.role === 'operator')) {
      router.replace('/admin/dashboard')
    }
  }, [router, user])

  if (user && !user.tenant_id && (user.role === 'admin' || user.role === 'operator')) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    )
  }

  return <TenantDashboardContent userName={user?.full_name} />
}

function TenantDashboardContent({ userName }: { userName?: string }) {
  const tp = useTranslations('pages')
  const t = useTranslations('homeUi')
  const router = useRouter()
  const can = useCan()
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
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
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
            {tp('dashboardTitle')}
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {tp('dashboardWelcome', { name: userName ?? '' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <DateRangePicker onRangeChange={handleDateRangeChange} />
        </div>
      </div>

      {/* Quick Actions */}
      <Card className="border-2 border-dashed border-gray-200 dark:border-gray-700 bg-gradient-to-br from-emerald-50 to-white dark:from-emerald-950 dark:to-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-gray-900 dark:text-white">{t('quickActions')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {can.writeClinical && (
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-emerald-50 dark:hover:bg-emerald-950 hover:border-emerald-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/patients/new')}
            >
              <UserPlus className="h-5 w-5 mb-2 text-emerald-600 dark:text-emerald-400" />
              <span className="font-medium text-sm">{t('newPatient')}</span>
            </Button>
            )}
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-green-50 dark:hover:bg-green-950 hover:border-green-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/appointments/new')}
            >
              <Calendar className="h-5 w-5 mb-2 text-green-600 dark:text-green-400" />
              <span className="font-medium text-sm">{t('schedule')}</span>
            </Button>
            {can.writeClinical && (
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-purple-50 dark:hover:bg-purple-950 hover:border-purple-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/prescriptions/new')}
            >
              <FilePlus className="h-5 w-5 mb-2 text-purple-600 dark:text-purple-400" />
              <span className="font-medium text-sm">{t('prescription')}</span>
            </Button>
            )}
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 hover:bg-blue-50 dark:hover:bg-blue-950 hover:border-blue-300 text-gray-700 dark:text-gray-200"
              onClick={() => router.push('/payments')}
            >
              <DollarSign className="h-5 w-5 mb-2 text-blue-600 dark:text-blue-400" />
              <span className="font-medium text-sm">{t('payment')}</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('keyMetrics')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatsCard
            title={t('totalPatients')}
            value={overview?.total_patients || 0}
            description={t('newThisMonth', { count: overview?.new_patients_this_month || 0 })}
            icon={Users}
          />
          <StatsCard
            title={t('todaysAppointments')}
            value={overview?.appointments_today || 0}
            description={t('upcoming', { count: overview?.upcoming_appointments || 0 })}
            icon={Calendar}
          />
          <StatsCard
            title={t('monthlyRevenue')}
            value={`৳${(overview?.revenue_this_month || 0).toLocaleString()}`}
            description={t('collectedThisMonth')}
            icon={DollarSign}
          />
          <StatsCard
            title={t('activePatients')}
            value={overview?.active_patients || 0}
            description={t('visitedLast30')}
            icon={Activity}
          />
          <StatsCard
            title={t('prescriptions')}
            value={overview?.prescriptions_this_month || 0}
            description={t('issuedThisMonth')}
            icon={FileText}
          />
          <StatsCard
            title={t('pendingPayments')}
            value={`৳${(overview?.pending_payments || 0).toLocaleString()}`}
            description={t('outstandingAmount')}
            icon={TrendingUp}
            className="border-orange-200 bg-orange-50 dark:bg-orange-950 dark:border-orange-800"
          />
        </div>
      </div>

      {/* Analytics */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('analytics')}
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {financial?.daily_revenue && financial.daily_revenue.length > 0 ? (
            <RevenueChart data={financial.daily_revenue} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">{t('revenueTrend')}</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>{t('noRevenueData')}</p>
                  <p className="text-xs mt-1">{t('noRevenueHint')}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {financial?.revenue_by_method ? (
            <RevenueByMethodChart data={financial.revenue_by_method} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">{t('revenueByMethod')}</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <DollarSign className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>{t('noPaymentData')}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Patient Insights */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('patientInsights')}
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {patients?.demographics ? (
            <PatientDemographicsChart data={patients.demographics} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">{t('patientDemographics')}</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <Users className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>{t('noPatientData')}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {patients?.age_distribution ? (
            <AgeDistributionChart data={patients.age_distribution} />
          ) : (
            <Card className="bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-gray-900 dark:text-white">{t('ageDistribution')}</CardTitle>
              </CardHeader>
              <CardContent className="h-[300px] flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <Activity className="h-12 w-12 mx-auto mb-2 opacity-20" />
                  <p>{t('noAgeData')}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
