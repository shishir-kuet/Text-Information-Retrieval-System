import { useEffect, useRef, useState } from "react"
import { useLocation, useParams } from "react-router-dom"
import { Copy, Download, ExternalLink, Sparkles } from "lucide-react"
import { api } from "../lib/api"
import type { PageInfo, PageSummary } from "../lib/types"
import { Button } from "../components/ui/button"
import { useAuth } from "../lib/auth"

export default function PageDetail() {
  const { pageId } = useParams()
  const location = useLocation()
  const { token } = useAuth()
  const [page, setPage] = useState<PageInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<PageSummary | null>(null)
  const [isSummarizing, setIsSummarizing] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [popupMessage, setPopupMessage] = useState<string | null>(null)
  const popupTimer = useRef<number | null>(null)

  useEffect(() => {
    const load = async () => {
      if (!pageId) return
      try {
        const pageData = await api.page(pageId)
        setPage(pageData)
        setSummary(null)
        setSummaryError(null)
        setPopupMessage(null)
      } catch (err) {
        setError((err as Error).message)
      }
    }
    load()
  }, [pageId])

  useEffect(() => {
    return () => {
      if (popupTimer.current) {
        window.clearTimeout(popupTimer.current)
        popupTimer.current = null
      }
    }
  }, [])

  const handleSummarize = async () => {
    if (!pageId || isSummarizing) return
    setSummaryError(null)
    setIsSummarizing(true)
    try {
      const summaryData = await api.pageSummary(pageId, 3)
      setSummary(summaryData)
    } catch (err) {
      setSummaryError((err as Error).message)
    } finally {
      setIsSummarizing(false)
    }
  }

  const handleCopySummary = async () => {
    const textToCopy = (summary?.summary || "").trim()
    if (!textToCopy) return

    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard unavailable")
      }
      await navigator.clipboard.writeText(textToCopy)
      setPopupMessage("Copied Text")
      if (popupTimer.current) {
        window.clearTimeout(popupTimer.current)
      }
      popupTimer.current = window.setTimeout(() => {
        setPopupMessage(null)
        popupTimer.current = null
      }, 2000)
    } catch (err) {
      setSummaryError((err as Error).message || "Could not copy to clipboard.")
    }
  }

  if (!pageId) {
    return <div className="text-white/70">Missing page id.</div>
  }

  if (error) {
    return <div className="text-white/70">{error}</div>
  }

  if (!page) {
    return <div className="text-white/70">Loading page...</div>
  }

  const searchQuery = new URLSearchParams(location.search).get("q")?.trim() || ""
  const openPageUrl = searchQuery
    ? `${api.baseUrl}/api/page/${page.page_id}/pdf?q=${encodeURIComponent(searchQuery)}`
    : `${api.baseUrl}/api/page/${page.page_id}/pdf`

  const downloadUrl = token
    ? `${api.baseUrl}/api/book/${page.book_id}/download?token=${encodeURIComponent(token)}`
    : null

  return (
    <div className="space-y-6">
      {popupMessage && (
        <div className="fixed right-6 top-6 z-50 rounded-2xl border border-white/15 bg-[var(--color-surface)]/90 px-4 py-3 text-sm text-white shadow-xl">
          {popupMessage}
        </div>
      )}
      <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/80 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm text-white/60">{page.book.title}</div>
            <div className="text-2xl font-semibold">Page {page.display_page_number}</div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => window.open(openPageUrl, "_blank")}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Page
            </Button>
            <Button variant="outline" onClick={handleSummarize} disabled={isSummarizing}>
              <Sparkles className="mr-2 h-4 w-4" />
              {isSummarizing ? "Summarizing..." : "Summarize Page"}
            </Button>
            <Button
              variant="ghost"
              disabled={!downloadUrl}
              onClick={() => downloadUrl && window.open(downloadUrl, "_blank")}
            >
              <Download className="mr-2 h-4 w-4" />
              Download Book
            </Button>
          </div>
        </div>

        <div className="card-hover mt-6 rounded-2xl border border-white/10 bg-black/20 p-5">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-white/90">Page Summary</div>
            {summary && (
              <Button variant="ghost" onClick={handleCopySummary} title="Copy">
                <Copy className="h-4 w-4" />
              </Button>
            )}
          </div>
          {!summary && !summaryError && (
            <div className="mt-3 text-sm text-white/60">
              Click "Summarize Page" to generate a quick summary of this page.
            </div>
          )}
          {summaryError && <div className="mt-3 text-sm text-red-300">{summaryError}</div>}
          {summary && (
            <>
              <div className="mt-3 text-sm leading-7 text-white/80">{summary.summary || "No content to summarize."}</div>
              <div className="mt-2 text-xs text-white/50">
                {summary.sentence_count} sentence summary from {summary.source_sentence_count} source sentences
              </div>
            </>
          )}
        </div>

        <div className="card-hover mt-6 rounded-2xl border border-white/10 bg-black/20 p-5">
          <div className="text-sm text-white/90">About This Book</div>
          <div className="mt-4 space-y-2 text-sm text-white/60">
            <div>
              Book Title: <span className="font-semibold">{page.book.title || "-"}</span>
            </div>
            <div>
              Author: <span className="font-semibold">{page.book.author || "-"}</span>
            </div>
            <div>
              Publication Year: <span className="font-semibold">{page.book.year ?? "-"}</span>
            </div>
            <div>
              Domain: <span className="font-semibold">{page.book.domain || "-"}</span>
            </div>
            <div>
              Total Pages: <span className="font-semibold">{page.book.num_pages ?? "-"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
