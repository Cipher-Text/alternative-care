'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { NavLinks } from '@/components/layout/Sidebar'

/**
 * Navigation for screens below the `md` breakpoint, where the sidebar is hidden: a hamburger
 * button in the header that opens a slide-over drawer with the same links. Built on Radix
 * Dialog so focus is trapped, Esc closes it, and it is announced to screen readers.
 */
export function MobileNav() {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  // Close after navigating (the layout persists across route changes).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOpen(false)
  }, [pathname])

  return (
    <DialogPrimitive.Root open={open} onOpenChange={setOpen}>
      <DialogPrimitive.Trigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden h-11 w-11"
          aria-label="Open navigation menu"
        >
          <Menu className="h-6 w-6" />
        </Button>
      </DialogPrimitive.Trigger>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 md:hidden" />
        <DialogPrimitive.Content
          aria-describedby={undefined}
          className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col bg-white shadow-xl dark:bg-slate-900 md:hidden"
        >
          <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-gray-200 px-4 dark:border-slate-700">
            <DialogPrimitive.Title className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
              AltCare
            </DialogPrimitive.Title>
            <DialogPrimitive.Close asChild>
              <Button variant="ghost" size="icon" className="h-11 w-11" aria-label="Close navigation menu">
                <X className="h-5 w-5" />
              </Button>
            </DialogPrimitive.Close>
          </div>
          <div className="flex flex-1 flex-col overflow-y-auto">
            <NavLinks onNavigate={() => setOpen(false)} />
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
