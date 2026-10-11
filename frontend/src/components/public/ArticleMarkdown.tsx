import ReactMarkdown, { type Components } from 'react-markdown'

/** Raw HTML is never enabled (react-markdown ignores it by default); do not add rehype-raw. */
const components: Components = {
  h1: (p) => <h2 className="mt-8 mb-3 text-2xl font-bold text-gray-900 dark:text-white" {...strip(p)} />,
  h2: (p) => <h2 className="mt-8 mb-3 text-2xl font-bold text-gray-900 dark:text-white" {...strip(p)} />,
  h3: (p) => <h3 className="mt-6 mb-2 text-xl font-semibold text-gray-900 dark:text-white" {...strip(p)} />,
  h4: (p) => <h4 className="mt-5 mb-2 text-lg font-semibold text-gray-900 dark:text-white" {...strip(p)} />,
  p: (p) => <p className="my-4 leading-7 text-gray-700 dark:text-gray-300" {...strip(p)} />,
  ul: (p) => <ul className="my-4 list-disc space-y-1 pl-6 text-gray-700 dark:text-gray-300" {...strip(p)} />,
  ol: (p) => <ol className="my-4 list-decimal space-y-1 pl-6 text-gray-700 dark:text-gray-300" {...strip(p)} />,
  li: (p) => <li className="leading-7" {...strip(p)} />,
  blockquote: (p) => (
    <blockquote className="my-4 border-l-4 border-emerald-500 pl-4 italic text-gray-600 dark:text-gray-400" {...strip(p)} />
  ),
  hr: () => <hr className="my-8 border-gray-200 dark:border-slate-800" />,
  strong: (p) => <strong className="font-semibold text-gray-900 dark:text-white" {...strip(p)} />,
  code: (p) => <code className="rounded bg-gray-100 px-1 py-0.5 text-sm dark:bg-slate-800" {...strip(p)} />,
  pre: (p) => <pre className="my-4 overflow-x-auto rounded-lg bg-gray-100 p-4 text-sm dark:bg-slate-800" {...strip(p)} />,
  table: (p) => (
    <div className="my-4 overflow-x-auto">
      <table className="w-full border-collapse text-sm" {...strip(p)} />
    </div>
  ),
  th: (p) => (
    <th className="border border-gray-200 bg-gray-50 px-3 py-2 text-start font-semibold dark:border-slate-700 dark:bg-slate-800" {...strip(p)} />
  ),
  td: (p) => <td className="border border-gray-200 px-3 py-2 dark:border-slate-700" {...strip(p)} />,
  img: ({ src, alt }) =>
    typeof src === 'string' ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={src} alt={alt ?? ''} loading="lazy" className="my-4 h-auto max-w-full rounded-lg" />
    ) : null,
  a: ({ href, children }) => {
    const external = typeof href === 'string' && /^(https?:)?\/\//i.test(href)
    const safe = typeof href === 'string' && !/^\s*(javascript|data|vbscript):/i.test(href)
    if (!safe) return <>{children}</>
    return (
      <a
        href={href}
        className="text-emerald-700 underline underline-offset-2 hover:text-emerald-600 dark:text-emerald-400"
        {...(external ? { target: '_blank', rel: 'noopener noreferrer nofollow' } : {})}
      >
        {children}
      </a>
    )
  },
}

// Drop react-markdown's `node` prop so it is not spread onto DOM elements.
function strip<T extends { node?: unknown }>(props: T): Omit<T, 'node'> {
  const { node: _node, ...rest } = props
  void _node
  return rest
}

export function ArticleMarkdown({ source }: { source: string }) {
  return <ReactMarkdown components={components}>{source}</ReactMarkdown>
}
