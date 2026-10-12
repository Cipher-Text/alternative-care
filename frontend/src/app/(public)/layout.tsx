import type { ReactNode } from 'react'
import { PublicHeader } from '@/components/public/PublicHeader'
import { PublicFooter } from '@/components/public/PublicFooter'

import { isDirectoryLaunched } from '@/lib/api/publicDirectory'

export default async function PublicSiteLayout({ children }: { children: ReactNode }) {
  const directoryLaunched = await isDirectoryLaunched().catch(() => false)
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <PublicHeader directoryLaunched={directoryLaunched} />
      <main className="flex-1">{children}</main>
      <PublicFooter directoryLaunched={directoryLaunched} />
    </div>
  )
}
