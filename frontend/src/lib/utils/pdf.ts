import { toast } from 'react-hot-toast'

/**
 * Show a server-rendered PDF in a new tab (the user can print or save it from there).
 *
 * The document endpoints need the Authorization header, so a plain link cannot be used: the PDF
 * is fetched as a Blob and shown through an object URL. The tab is opened synchronously, inside
 * the click handler, so browsers do not treat it as a blocked popup; if one is blocked anyway the
 * file is downloaded instead.
 */
export async function openPdf(fetchBlob: () => Promise<Blob>, filename: string): Promise<void> {
  const tab = window.open('', '_blank')
  try {
    const blob = await fetchBlob()
    const url = URL.createObjectURL(blob)
    if (tab) {
      tab.location.href = url
    } else {
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (error) {
    tab?.close()
    toast.error(await pdfErrorMessage(error))
  }
}

/** Error responses to a Blob request arrive as a Blob; unwrap the API's `detail` message. */
async function pdfErrorMessage(error: unknown): Promise<string> {
  const fallback = 'Could not load the PDF'
  const data = (error as { response?: { data?: unknown } })?.response?.data
  if (data instanceof Blob) {
    try {
      const detail = JSON.parse(await data.text())?.detail
      if (typeof detail === 'string') return detail
      if (detail && typeof detail.message === 'string') return detail.message
    } catch {
      // not JSON — fall through
    }
  }
  return error instanceof Error && error.message ? error.message : fallback
}
