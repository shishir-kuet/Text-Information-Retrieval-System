import { useEffect, useRef, useState } from "react"
import { Copy, Trash2 } from "lucide-react"
import { api } from "../lib/api"
import type { HistoryResponse } from "../lib/types"
import { Button } from "../components/ui/button"
import { useAuth } from "../lib/auth"

export default function History() {
  const { token } = useAuth()
  const [data, setData] = useState<HistoryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [popupMessage, setPopupMessage] = useState<string | null>(null)
  const popupTimer = useRef<number | null>(null)

  const load = async () => {
    if (!token) return
    try {
      const response = await api.history(token)
      setData(response)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  useEffect(() => {
    load()
  }, [token])

  const deleteItem = async (logId: number) => {
    if (!token) return
    await api.deleteHistory(token, logId)
    await load()
  }

  const clearAll = async () => {
    if (!token) return
    await api.clearHistory(token)
    await load()
  }

  const copyOnly = async (queryText: string) => {
    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard unavailable")
      }
      await navigator.clipboard.writeText(queryText)
      setPopupMessage("Copied Text")
      if (popupTimer.current) {
        window.clearTimeout(popupTimer.current)
      }
      popupTimer.current = window.setTimeout(() => {
        setPopupMessage(null)
        popupTimer.current = null
      }, 2000)
    } catch (err) {
      setError((err as Error).message || "Could not copy to clipboard.")
    }
  }

  if (!token) {
    return <div className="text-white/70">Login required to see your history.</div>
  }

  return (
    <div className="space-y-6">
      {popupMessage && (
        <div className="fixed right-6 top-6 z-50 rounded-2xl border border-white/15 bg-[var(--color-surface)]/90 px-4 py-3 text-sm text-white shadow-xl">
          {popupMessage}
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Search History</h1>
          <p className="text-sm text-white/60">Your recent searches.</p>
        </div>
        <Button variant="outline" onClick={clearAll}>Clear all</Button>
      </div>

      {error && <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>}

      <div className="grid gap-4">
        {data?.items.map((item) => (
          <div key={item.log_id} className="rounded-2xl border border-white/10 bg-[var(--color-surface)]/70 p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-white/60">{item.created_at}</div>
                <div className="text-lg font-semibold text-white">{item.query_text}</div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={() => copyOnly(item.query_text)}
                  title="Copy"
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button variant="ghost" onClick={() => deleteItem(item.log_id)} title="Delete">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div className="mt-3 text-xs text-white/60">{item.total_results} results</div>
          </div>
        ))}
      </div>
    </div>
  )
}
