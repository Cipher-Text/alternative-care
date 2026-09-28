import Link from 'next/link'

const columns = [
  {
    title: 'Directory',
    links: [
      { name: 'Medicines', href: '/knowledge/medicines' },
      { name: 'Symptoms', href: '/knowledge/symptoms' },
      { name: 'Institutions', href: '/institutions' },
    ],
  },
  {
    title: 'Product',
    links: [
      { name: 'For Practitioners', href: '/for-practitioners' },
      { name: 'Pricing', href: '/pricing' },
      { name: 'Sign In', href: '/login' },
    ],
  },
  {
    title: 'Company',
    links: [{ name: 'About', href: '/about' }],
  },
]

export function PublicFooter() {
  return (
    <footer className="border-t border-gray-200 dark:border-slate-800 bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 md:col-span-1">
            <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              AltCare
            </span>
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
              Practice management and a public knowledge directory for Homeopathy, Ayurveda,
              Unani, and Herbal medicine practitioners.
            </p>
          </div>

          {columns.map((column) => (
            <div key={column.title}>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                {column.title}
              </h3>
              <ul className="mt-3 space-y-2">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 pt-6 border-t border-gray-200 dark:border-slate-800 text-sm text-gray-500 dark:text-gray-400">
          © {new Date().getFullYear()} AltCare. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
