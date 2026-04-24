import { useEffect, useState, type FormEvent } from "react"
import { libraryApi, type LibraryBook, type LibraryPage } from "./lib/api"
import "./index.css"

export default function App() {
  const [books, setBooks] = useState<LibraryBook[]>([])
  const [selectedBook, setSelectedBook] = useState<LibraryBook | null>(null)
  const [pages, setPages] = useState<LibraryPage[]>([])
  const [message, setMessage] = useState<string>("")
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState("")
  const [author, setAuthor] = useState("")
  const [year, setYear] = useState("")

  const refreshBooks = async () => {
    const data = await libraryApi.listBooks()
    setBooks(data.items)
    if (!selectedBook && data.items.length > 0) {
      setSelectedBook(data.items[0])
    }
  }

  useEffect(() => {
    refreshBooks().catch((err) => setMessage((err as Error).message))
  }, [])

  useEffect(() => {
    if (!selectedBook) return
    libraryApi.listPages(selectedBook.book_id)
      .then((data) => setPages(data.items))
      .catch((err) => setMessage((err as Error).message))
  }, [selectedBook])

  const handleUpload = async (event: FormEvent) => {
    event.preventDefault()
    if (!file || !title.trim() || !author.trim()) {
      setMessage("File, title, and author are required.")
      return
    }
    setMessage("Uploading book...")
    try {
      await libraryApi.uploadBook(file, title.trim(), author.trim(), year.trim() || undefined)
      setMessage("Upload complete.")
      setFile(null)
      setTitle("")
      setAuthor("")
      setYear("")
      await refreshBooks()
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  const handleProcess = async (bookId: number) => {
    setMessage(`Processing book ${bookId}...`)
    try {
      await libraryApi.processBook(bookId)
      setMessage("Processing complete.")
      await refreshBooks()
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Library System</p>
          <h1>Book upload and extraction</h1>
          <p className="lead">Manage uploaded PDFs, process pages, and inspect extracted text.</p>
        </div>
      </header>

      <section className="panel">
        <h2>Upload book</h2>
        <form onSubmit={handleUpload} className="form">
          <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input placeholder="Author" value={author} onChange={(e) => setAuthor(e.target.value)} />
          <input placeholder="Year (optional)" value={year} onChange={(e) => setYear(e.target.value)} />
          <button type="submit">Upload</button>
        </form>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Uploaded books</h2>
          <div className="stack">
            {books.map((book) => (
              <button
                key={book.book_id}
                type="button"
                className={`book ${selectedBook?.book_id === book.book_id ? "active" : ""}`}
                onClick={() => setSelectedBook(book)}
              >
                <strong>{book.title}</strong>
                <span>{book.status} · {book.num_pages ?? "?"} pages</span>
                <span className="muted">{book.author ?? "Unknown author"}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Processing</h2>
          {selectedBook ? (
            <div className="stack">
              <div className="book-details">
                <strong>{selectedBook.title}</strong>
                <span>Status: {selectedBook.status}</span>
                <button type="button" onClick={() => handleProcess(selectedBook.book_id)}>Process / Reprocess</button>
              </div>
              <div>
                <h3>Extracted pages</h3>
                <div className="stack">
                  {pages.map((page) => (
                    <details key={page.page_id}>
                      <summary>Page {page.page_number}</summary>
                      <pre>{page.text_content}</pre>
                    </details>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="muted">No book selected.</p>
          )}
        </div>
      </section>

      {message ? <div className="toast">{message}</div> : null}
    </div>
  )
}
