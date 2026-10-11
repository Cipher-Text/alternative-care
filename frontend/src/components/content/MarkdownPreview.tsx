'use client'

import ReactMarkdown, { type Components } from 'react-markdown'

// Minimal styling through `components`; raw HTML in the source is not rendered (react-markdown default).
const components: Components = {
  h1: (p) => <h2 className="mt-6 mb-3 text-2xl font-bold" {...p} />,
  h2: (p) => <h2 className="mt-6 mb-3 text-xl font-bold" {...p} />,
  h3: (p) => <h3 className="mt-5 mb-2 text-lg font-semibold" {...p} />,
  h4: (p) => <h4 className="mt-4 mb-2 font-semibold" {...p} />,
  p: (p) => <p className="mb-3 leading-relaxed" {...p} />,
  ul: (p) => <ul className="mb-3 list-disc space-y-1 pl-6" {...p} />,
  ol: (p) => <ol className="mb-3 list-decimal space-y-1 pl-6" {...p} />,
  blockquote: (p) => (
    <blockquote className="mb-3 border-l-4 border-slate-300 pl-4 italic text-muted-foreground dark:border-slate-600" {...p} />
  ),
  a: (p) => <a className="text-primary underline" target="_blank" rel="noopener noreferrer nofollow" {...p} />,
  code: (p) => <code className="rounded bg-muted px-1 py-0.5 text-sm" {...p} />,
  hr: () => <hr className="my-6 border-slate-200 dark:border-slate-700" />,
}

export function MarkdownPreview({ source }: { source: string }) {
  return <ReactMarkdown components={components}>{source}</ReactMarkdown>
}
