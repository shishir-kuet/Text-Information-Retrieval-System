import { useEffect, useMemo, useState } from "react"
import { BookOpen, Upload } from "lucide-react"
import { api } from "../lib/api"
import { useAuth } from "../lib/auth"
import type { BooksResponse, DomainListResponse } from "../lib/types"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Select } from "../components/ui/select"

export default function Admin() {
  const { token, user } = useAuth()
  const [books, setBooks] = useState<BooksResponse | null>(null)
  const [domains, setDomains] = useState<DomainListResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)
  const [processStatus, setProcessStatus] = useState<string | null>(null)
  const [indexStatus, setIndexStatus] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [building, setBuilding] = useState(false)

  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadDomain, setUploadDomain] = useState("")
  const [uploadTitle, setUploadTitle] = useState("")
  const [uploadAuthor, setUploadAuthor] = useState("")
  const [uploadYear, setUploadYear] = useState("")

  const [fullRebuild, setFullRebuild] = useState(false)
  const [waitMode, setWaitMode] = useState(true)
  const [booksPage, setBooksPage] = useState(1)
  const booksPerPage = 10

  const loadAll = async () => {
    if (!token) return
    try {
      const [bookData, domainData] = await Promise.all([
        api.adminBooks(token),
        api.adminDomains(token),
      ])
      setBooks(bookData)
      setDomains(domainData)
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

  const domainOptions = useMemo(() => {
    const items = domains?.items ?? []
    return items.map((domain) => ({ label: domain, value: domain }))
  }, [domains])

  const domainSelectOptions = useMemo(() => {
    return [{ label: "Select domain", value: "" }, ...domainOptions]
  }, [domainOptions])

  if (!token) {
    return <div className="text-white/70">Admin login required.</div>
  }

  if (user?.role !== "admin") {
    return <div className="text-white/70">Admin access required.</div>
  }

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!token) return
    if (!uploadFile || !uploadDomain || !uploadTitle.trim() || !uploadAuthor.trim()) {
      setError("File, domain, title, and author are required.")
      return
    }
    const formData = new FormData()
    formData.append("file", uploadFile)
    formData.append("domain", uploadDomain)
    formData.append("title", uploadTitle.trim())
    formData.append("author", uploadAuthor.trim())
    if (uploadYear.trim()) {
      formData.append("year", uploadYear.trim())
    }
    setUploadStatus("Uploading...")
    setError(null)
    try {
      setUploading(true)
      await api.adminUpload(token, formData)
      setUploadStatus("Upload success")
      await loadAll()
      setUploadFile(null)
      setUploadTitle("")
      setUploadAuthor("")
      setUploadYear("")
    } catch (err) {
      setError((err as Error).message)
      setUploadStatus(null)
    } finally {
      setUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!token) return
    setProcessStatus("Processing...")
    setError(null)
    try {
      setProcessing(true)
      const response = await api.adminProcessUploaded(token, waitMode)
      const payload = response as {
        processed_count?: number
        total_uploaded?: number
        errors?: Array<{ book_id: number; error: string }>
        message?: string
        job_id?: string
      }
      if (payload.errors && payload.errors.length > 0) {
        const failedIds = payload.errors.map((item) => item.book_id).join(", ")
        setError(`Some books failed to process: ${failedIds}`)
      }
      if (payload.message) {
        setProcessStatus(payload.message)
      } else if (typeof payload.processed_count === "number" && typeof payload.total_uploaded === "number") {
        setProcessStatus(`Process completed (${payload.processed_count}/${payload.total_uploaded})`)
      } else {
        setProcessStatus("Process completed")
      }
      await loadAll()
    } catch (err) {
      setError((err as Error).message)
      setProcessStatus(null)
    } finally {
      setProcessing(false)
    }
  }

  const handleBuild = async () => {
    if (!token) return
    setIndexStatus("Building index...")
    setProcessStatus(null)
    setError(null)
    try {
      setBuilding(true)
      const response = await api.adminBuildIndex(token, fullRebuild, waitMode)
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
          <Upload className="h-5 w-5" />
          <h1 className="text-2xl font-semibold">Admin Console</h1>
        </div>
        <p className="mt-2 text-sm text-white/60">Upload books, process pages, and rebuild search indexes.</p>
      </div>

      {error && <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <form onSubmit={handleUpload} className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <h2 className="text-lg font-semibold">Upload a book</h2>
            <div className="mt-4 space-y-3">
              <Input
                type="file"
                name="file"
                accept="application/pdf"
                required
                onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
              />
              <Select
                value={uploadDomain}
                onChange={setUploadDomain}
                options={domainSelectOptions}
                className="h-12"
              />
              {domainOptions.length === 0 && (
                <div className="text-xs text-white/60">No domains found in the books folder yet.</div>
              )}
              <Input
                type="text"
                name="title"
                placeholder="Title"
                value={uploadTitle}
                onChange={(event) => setUploadTitle(event.target.value)}
                required
              />
              <Input
                type="text"
                name="author"
                placeholder="Author"
                value={uploadAuthor}
                onChange={(event) => setUploadAuthor(event.target.value)}
                required
              />
              <Input
                type="number"
                name="year"
                placeholder="Year (optional)"
                value={uploadYear}
                onChange={(event) => setUploadYear(event.target.value)}
              />
              <Button type="submit" disabled={uploading}>
                {uploading ? "Uploading..." : "Upload"}
              </Button>
              {uploadStatus && <div className="text-xs text-white/70">{uploadStatus}</div>}
            </div>
          </form>

          <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <h2 className="text-lg font-semibold">Process & Index</h2>
            <div className="mt-4 space-y-3">
              <div className="text-sm text-white/70">
                Process all uploaded books in realtime, then build the index from processed books.
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-white/60">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={waitMode}
                    onChange={(event) => setWaitMode(event.target.checked)}
                  />
                  Wait for completion (realtime)
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={fullRebuild} onChange={(event) => setFullRebuild(event.target.checked)} />
                  Full rebuild
                </label>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button type="button" variant="outline" onClick={handleProcess} disabled={processing || !waitMode}>
                  {processing ? "Processing..." : "Process Book"}
                </Button>
                <Button type="button" onClick={handleBuild} disabled={building || !waitMode}>
                  {building ? "Building..." : "Build Index"}
                </Button>
              </div>
              {processStatus && <div className="text-xs text-white/70">{processStatus}</div>}
              {indexStatus && <div className="text-xs text-white/70">{indexStatus}</div>}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-hover rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-6">
            <div className="flex items-center gap-2 text-lg font-semibold">
              <BookOpen className="h-4 w-4" />
              Books
            </div>
            <div className="mt-1 text-xs text-white/60">Total books: {totalBooks}</div>
            <div className="mt-4 space-y-3 text-sm text-white/70">
              {pagedBooks.map((book) => (
                <div key={book.book_id} className="card-hover rounded-xl border border-white/10 bg-black/20 p-3">
                  <div className="font-semibold text-white">{book.title}</div>
                  <div className="text-xs text-white/60">{book.domain} · {book.status}</div>
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
