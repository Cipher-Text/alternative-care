'use client'

import { useTranslations } from 'next-intl'
import { useDirectoryListing, useDirectoryStats } from '@/lib/hooks/useDirectory'
import { ListingStatusCard } from '@/components/directory/ListingStatusCard'
import { DirectoryStatsCards } from '@/components/directory/DirectoryStatsCards'
import { ListingForm } from '@/components/directory/ListingForm'
import { RequestsInbox } from '@/components/directory/RequestsInbox'
import { useCan } from '@/lib/auth/permissions'

export default function DirectoryPage() {
  const t = useTranslations('directoryAdminUi')
  // The directory is doctor-only on the backend; receptionists and platform staff get nothing here
  const { can } = useCan()
  const isDoctor = can('directory.manage')
  const listing = useDirectoryListing(isDoctor)
  const stats = useDirectoryStats(isDoctor)

  if (!isDoctor) return null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('title')}</h1>
        <p className="mt-2 max-w-2xl text-gray-600 dark:text-gray-400">{t('subtitle')}</p>
      </div>

      {listing.isLoading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" aria-busy="true" />
      ) : listing.isError || !listing.data ? (
        <p role="alert" className="text-sm text-red-600">{t('loadFailed')}</p>
      ) : (
        <>
          <ListingStatusCard listing={listing.data} />
          {stats.data && <DirectoryStatsCards stats={stats.data} />}
          <ListingForm listing={listing.data} />
          <RequestsInbox />
        </>
      )}
    </div>
  )
}
