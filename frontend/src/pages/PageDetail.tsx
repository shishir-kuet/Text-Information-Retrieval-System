import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { Download, ExternalLink } from "lucide-react"
import { api } from "../lib/api"
import type { PageInfo } from "../lib/types"
import { Button } from "../components/ui/button"
import { useAuth } from "../lib/auth"

export default function PageDetail() {
  const { pageId } = useParams()
  const { token } = useAuth()
  const [page, setPage] = useState<PageInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      if (!pageId) return
      try {
        const pageData = await api.page(pageId)
        setPage(pageData)
      } catch (err) {
        setError((err as Error).message)
      }
    }
    load()
  }, [pageId])

  if (!pageId) {
    return <div className="text-white/70">Missing page id.</div>
  }

  if (error) {
    return <div className="text-white/70">{error}</div>
  }

  if (!page) {
    return <div className="text-white/70">Loading page...</div>
  }

  const downloadUrl = token
    ? `${api.baseUrl}/api/book/${page.book_id}/download?token=${encodeURIComponent(token)}`
    : null

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-white/10 bg-[var(--color-surface)]/80 p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm text-white/60">{page.book.title}</div>
            <div className="text-2xl font-semibold">Page {page.display_page_number}</div>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => window.open(`${api.baseUrl}/api/page/${page.page_id}/pdf`, "_blank")}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Open Page
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

        <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-5">
        <div className="text-sm text-white/90">About This Book</div>
          <div className="mt-4 space-y-2 text-sm text-white/60">
            <div>Book Title: {page.book.title || "-"}</div>
            <div>Author: {page.book.author || "-"}</div>
            <div>Publication Year: {page.book.year ?? "-"}</div>
            <div>Domain: {page.book.domain || "-"}</div>
            <div>Total Pages: {page.book.num_pages ?? "-"}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
