import { useEffect, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { ExternalLink, Search } from "lucide-react"
import { api } from "../lib/api"
import type { SearchResponse } from "../lib/types"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Select } from "../components/ui/select"
import { Badge } from "../components/ui/badge"
import { useAuth } from "../lib/auth"

export default function Results() {
  const { token } = useAuth()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get("q") ?? "")
  const [topK, setTopK] = useState(params.get("k") ?? "5")
  const [data, setData] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const topKNum = useMemo(() => Number(topK || 5), [topK])

  const runSearch = async (nextQuery: string, nextTopK: number) => {
    if (!nextQuery.trim()) {
      setError("Type a query to search.")
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await api.search(nextQuery, nextTopK, token ?? undefined)
      setData(response)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const currentQuery = params.get("q")
    const currentTopK = Number(params.get("k") ?? 5)
    if (currentQuery) {
      runSearch(currentQuery, currentTopK)
    }
  }, [params])

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    // Update URL and let the effect trigger the actual request.
    // This avoids double requests (submit + params change).
    setParams({ q: query, k: topK })
  }

  return (
    <div className="space-y-8">

      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">Search</h1>
        <p className="max-w-2xl text-sm text-white/70">
          Paste a line, sentence, or a longer excerpt. Open a result to read the full page and preview the original PDF.
        </p>
      </div>

      <div className="rounded-3xl border border-white/10 bg-[var(--color-surface)]/80 p-6 md:p-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/60" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search for a line, sentence, or paragraph..."
              className="h-12 pl-12"
            />
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <div className="text-sm font-semibold text-white/80">Top results</div>
              <Select
                value={topK}
                onChange={setTopK}
                options={[
                  { label: "5", value: "5" },
                  { label: "10", value: "10" },
                  { label: "15", value: "15" },
                  { label: "20", value: "20" },
                ]}
              />
            </div>

            <Button type="submit" className="h-12 sm:ml-auto">
              <Search className="mr-2 h-4 w-4" />
              Search
            </Button>
          </div>
        </form>
      </div>

      {loading && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
          Searching…
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {!loading && !error && !data && (
        <div className="rounded-3xl border border-white/10 bg-[var(--color-surface)]/50 p-8">
          <div className="flex flex-col items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">
              <Search className="h-5 w-5 text-white/70" />
            </div>
            <div className="text-lg font-semibold">Start a search</div>
            <div className="max-w-2xl text-sm text-white/70">
              Use the search box above, then open a result to see the full page text and preview the corresponding PDF page.
            </div>
          </div>
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-lg font-semibold">Results</div>
              <div className="text-sm text-white/60">
                {data.count} results for “{data.query}”
              </div>
            </div>
            <Button variant="outline" className="h-11" onClick={() => runSearch(data.query, topKNum)}>
              Refresh
            </Button>
          </div>

          {data.results.length === 0 ? (
            <div className="rounded-3xl border border-white/10 bg-[var(--color-surface)]/50 p-8">
              <div className="text-lg font-semibold">No matches found</div>
              <div className="mt-2 text-sm text-white/70">
                Try a different excerpt or include a few more unique keywords.
              </div>
            </div>
          ) : (
            <div className="grid gap-4">
              {data.results.map((result) => (
                <div
                  key={result.page_id}
                  className="rounded-2xl border border-white/10 bg-[var(--color-surface)]/70 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="text-sm text-white/60">{result.title}</div>
                      <div className="mt-1 text-lg font-semibold">Page {result.page_number}</div>
                    </div>
                    <Badge>Top match</Badge>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-3">
                    <Link to={`/page/${result.page_id}`}>
                      <Button variant="outline" className="h-10">
                        Open details
                      </Button>
                    </Link>
                    <a href={`${api.baseUrl}/api/page/${result.page_id}/pdf`} target="_blank" rel="noreferrer">
                      <Button variant="ghost" className="h-10">
                        Open Page
                        <ExternalLink className="ml-2 h-4 w-4" />
                      </Button>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
