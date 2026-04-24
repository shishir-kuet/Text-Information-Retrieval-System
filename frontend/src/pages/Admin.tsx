import { useEffect, useState } from "react"
import { Activity, AlertTriangle, BarChart3, BookOpen, Clock3, Database, RefreshCw, Search, ShieldAlert, Users } from "lucide-react"
import { api } from "../lib/api"
import { useAuth } from "../lib/auth"
import type { AdminIndexStats, BooksResponse } from "../lib/types"
import { Button } from "../components/ui/button"

export default function Admin() {
  const { token, user } = useAuth()
  const [books, setBooks] = useState<BooksResponse | null>(null)
  const [stats, setStats] = useState<AdminIndexStats | null>(null)
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
      const [bookData, statsData] = await Promise.all([
        api.adminBooks(token),
        api.adminIndexStats(token),
      ])
      setBooks(bookData)
      setStats(statsData)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  useEffect(() => {
    loadAll()
  }, [token])

  const bookItems = books?.items ?? []
  const totalBooks = books?.count ?? bookItems.length
  const dashboardStats = stats

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

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[
              { label: "Total searches", value: dashboardStats?.total_search_logs ?? 0, icon: Search },
              { label: "Avg latency (ms)", value: dashboardStats?.average_latency_ms ?? 0, icon: Clock3 },
              { label: "Zero-result searches", value: dashboardStats?.zero_result_searches ?? 0, icon: ShieldAlert },
              { label: "Success rate", value: `${dashboardStats?.success_rate ?? 0}%`, icon: Activity },
              { label: "Zero-result rate", value: `${dashboardStats?.zero_result_rate ?? 0}%`, icon: AlertTriangle },
              { label: "Unique queries", value: dashboardStats?.unique_queries ?? 0, icon: Database },
              { label: "Total users", value: dashboardStats?.total_users ?? 0, icon: Users },
            ].map((metric) => (
              <div key={metric.label} className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-5">
                <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-white/50">
                  <metric.icon className="h-4 w-4" />
                  {metric.label}
                </div>
                <div className="mt-3 text-2xl font-semibold text-white">{metric.value}</div>
              </div>
            ))}
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

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <BarChart3 className="h-4 w-4" />
            Search Volume
          </div>
          <div className="mt-4 space-y-4">
            {(dashboardStats?.recent_search_activity ?? []).map((item) => {
              const maxSearches = Math.max(1, ...(dashboardStats?.recent_search_activity ?? []).map((entry) => entry.searches))
              const width = `${Math.max(6, Math.round((item.searches / maxSearches) * 100))}%`
              return (
                <div key={item.date} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-white/60">
                    <span>{item.date}</span>
                    <span>{item.searches} searches</span>
                  </div>
                  <div className="h-3 rounded-full bg-white/10">
                    <div className="h-3 rounded-full bg-[var(--color-accent)] transition-all duration-300" style={{ width }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-7">
          <h2 className="text-lg font-semibold">Search Quality Overview</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs uppercase tracking-wide text-white/50">Index status</div>
              <div className="mt-2 text-base text-white/80">
                {dashboardStats?.index_available ? "Local search index is available" : "Local search index is missing"}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs uppercase tracking-wide text-white/50">Semantic index</div>
              <div className="mt-2 text-base text-white/80">
                {dashboardStats?.semantic_index_available ? "Semantic index is available" : "Semantic index is missing"}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs uppercase tracking-wide text-white/50">Synced books</div>
              <div className="mt-2 text-base text-white/80">{dashboardStats?.synced_books ?? 0} synced books</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs uppercase tracking-wide text-white/50">Last build</div>
              <div className="mt-2 text-base text-white/80">{dashboardStats?.build_date ?? "Not built yet"}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4 sm:col-span-2">
              <div className="text-xs uppercase tracking-wide text-white/50">Sync health</div>
              <div className="mt-3 grid gap-3 grid-cols-2">
                {[
                  { label: "Processed", value: dashboardStats?.synced_books_by_status?.processed ?? 0 },
                  { label: "Uploaded", value: dashboardStats?.synced_books_by_status?.uploaded ?? 0 },
                  { label: "Indexed", value: dashboardStats?.synced_books_by_status?.indexed ?? 0 },
                  { label: "Other", value: dashboardStats?.synced_books_by_status?.other ?? 0 },
                ].map((item) => (
                  <div key={item.label} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <div className="text-[11px] uppercase tracking-wide text-white/45">{item.label}</div>
                    <div className="mt-1 text-xl font-semibold text-white">{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
