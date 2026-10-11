'use client'

import { useState } from 'react'
import { Play } from 'lucide-react'
import { useTranslations } from 'next-intl'

/** Click-to-load YouTube embed: nothing third-party loads until the reader presses play. */
export function YouTubeFacade({ videoId, title }: { videoId: string; title: string }) {
  const t = useTranslations('publicContentUi')
  const [active, setActive] = useState(false)

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
      {active ? (
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0`}
          title={title || t('videoTitle')}
          className="absolute inset-0 h-full w-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          referrerPolicy="strict-origin-when-cross-origin"
        />
      ) : (
        <button
          type="button"
          onClick={() => setActive(true)}
          aria-label={`${t('playVideo')}: ${title}`}
          className="group absolute inset-0 h-full w-full"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover"
          />
          <span className="absolute inset-0 flex items-center justify-center bg-black/20 transition-colors group-hover:bg-black/30">
            <span className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-600 text-white shadow-lg">
              <Play className="h-7 w-7 translate-x-0.5" fill="currentColor" />
            </span>
          </span>
        </button>
      )}
    </div>
  )
}
