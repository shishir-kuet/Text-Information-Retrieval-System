import { useEffect, useState } from "react"
import { BookOpen, RefreshCw } from "lucide-react"
import { api } from "../lib/api"
import { useAuth } from "../lib/auth"
import type { BooksResponse, SearchLogsResponse } from "../lib/types"
import { Button } from "../components/ui/button"

export default function Admin() {
  const { token, user } = useAuth()
  const [books, setBooks] = useState<BooksResponse | null>(null)
  const [logs, setLogs] = useState<SearchLogsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [syncStatus, setSyncStatus] = useState<string | null>(null)
  const [indexStatus, setIndexStatus] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [building, setBuilding] = useState(false)

  const [fullRebuild, setFullRebuild] = useState(false)
  const [booksPage, setBooksPage] = useState(1)
  const booksPerPage = 10

  const loadAll = async () => {
    if (!token) return
    try {
      const [bookData, logData] = await Promise.all([
        api.adminBooks(token),
        api.adminSearchLogs(token, 8, 0),
      ])
      setBooks(bookData)
      setLogs(logData)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  useEffect(() => {
    loadAll()
  }, [token])

  const bookItems = books?.items ?? []
  const totalBooks = books?.count ?? bookItems.length

  const totalBookPages = Math.max(1, Math.ceil(bookItems.length / booksPerPage))
  const safeBooksPage = Math.min(Math.max(1, booksPage), totalBookPages)
  const pagedBooks = bookItems.slice((safeBooksPage - 1) * booksPerPage, safeBooksPage * booksPerPage)

  useEffect(() => {
    if (booksPage !== safeBooksPage) {
      setBooksPage(safeBooksPage)
    }
  }, [booksPage, safeBooksPage])

  if (!token) {
    return <div className="text-white/70">Admin login required.</div>
  }

  if (user?.role !== "admin") {
    return <div className="text-white/70">Admin access required.</div>
  }

  const handleSync = async () => {
    if (!token) return
    setSyncStatus("Syncing books from library...")
    setError(null)
    try {
      setSyncing(true)
      const response = await api.adminSyncBooks(token)
      const payload = response as { total_books?: number; new_books?: number; updated_books?: number }
      setSyncStatus(
        `Sync completed (${payload.new_books ?? 0} new, ${payload.updated_books ?? 0} updated, ${payload.total_books ?? 0} total)`,
      )
      await loadAll()
    } catch (err) {
      setError((err as Error).message)
      setSyncStatus(null)
    } finally {
      setSyncing(false)
    }
  }

  const handleBuild = async () => {
    if (!token) return
    setIndexStatus("Building index...")
    setError(null)
    try {
      setBuilding(true)
      const response = await api.adminBuildIndex(token, fullRebuild)
      const payload = response as {
        indexed_books?: number
        skipped?: boolean
        message?: string
        job_id?: string
      }
      if (payload.message) {
        setIndexStatus(payload.message)
      } else if (payload.skipped) {
        setIndexStatus("Index build skipped")
      } else if (typeof payload.indexed_books === "number") {
        setIndexStatus(`Index completed (${payload.indexed_books} books)`)
      } else {
        setIndexStatus("Index completed")
      }
      await loadAll()
    } catch (err) {
      setError((err as Error).message)
      setIndexStatus(null)
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/80 p-6">
        <div className="flex items-center gap-3">
          <RefreshCw className="h-5 w-5" />
          <h1 className="text-2xl font-semibold">Admin Console</h1>
        </div>
        <p className="mt-2 text-sm text-white/60">Sync library content, rebuild the local index, and review search activity.</p>
      </div>

      {error && <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <h2 className="text-lg font-semibold">Sync & Index</h2>
            <div className="mt-4 space-y-3">
              <div className="text-sm text-white/70">
                Pull the latest book metadata from the library system, then build or update the local search index.
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-white/60">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={fullRebuild} onChange={(event) => setFullRebuild(event.target.checked)} />
                  Full rebuild
                </label>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button type="button" variant="outline" onClick={handleSync} disabled={syncing}>
                  {syncing ? "Syncing..." : "Sync Books"}
                </Button>
                <Button type="button" onClick={handleBuild} disabled={building}>
                  {building ? "Building..." : "Build Index"}
                </Button>
              </div>
              {syncStatus && <div className="text-xs text-white/70">{syncStatus}</div>}
              {indexStatus && <div className="text-xs text-white/70">{indexStatus}</div>}
            </div>
          </div>

          <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <h2 className="text-lg font-semibold">Search Logs</h2>
            <div className="mt-4 space-y-3 text-sm text-white/70">
              {(logs?.items ?? []).map((log) => (
                <div key={log.log_id} className="rounded-xl border border-white/10 bg-black/20 p-3">
                  <div className="font-semibold text-white">{log.query_text}</div>
                  <div className="text-xs text-white/60">
                    {log.total_results} results · {log.latency_ms} ms · {log.created_at}
                  </div>
                </div>
              ))}
              {(logs?.items ?? []).length === 0 && <div className="text-xs text-white/60">No recent search logs.</div>}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold">
              <BookOpen className="h-4 w-4" />
              Synced Books
            </div>
            <div className="mt-1 text-xs text-white/60">Total books: {totalBooks}</div>
            <div className="mt-4 space-y-3 text-sm text-white/70">
              {pagedBooks.map((book) => (
                <div key={book.book_id} className="card-hover rounded-xl border border-white/10 bg-black/20 p-3">
                  <div className="font-semibold text-white">{book.title}</div>
                  <div className="text-xs text-white/60">{book.domain ?? "Library"} · {book.status}</div>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
              <Button
                type="button"
                variant="outline"
                className="h-9"
                onClick={() => setBooksPage((p) => Math.max(1, p - 1))}
                disabled={safeBooksPage <= 1}
              >
                Prev
              </Button>
              <div className="text-xs text-white/60">Page {safeBooksPage} of {totalBookPages}</div>
              <Button
                type="button"
                variant="outline"
                className="h-9"
                onClick={() => setBooksPage((p) => Math.min(totalBookPages, p + 1))}
                disabled={safeBooksPage >= totalBookPages}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
