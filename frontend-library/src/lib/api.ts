const API_BASE = import.meta.env.VITE_LIBRARY_API_BASE_URL ?? "http://127.0.0.1:5100"

async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  })
  const payload = await response.json()
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "Request failed")
  }
  return payload.data as T
}

async function requestForm<T>(path: string, formData: FormData, method = "POST"): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    body: formData,
  })
  const payload = await response.json()
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "Request failed")
  }
  return payload.data as T
}

export type LibraryBook = {
  book_id: number
  title: string
  author?: string | null
  year?: number | null
  status: string
  num_pages?: number | null
  file_size_mb?: number | null
}

export type LibraryPage = {
  page_id: string
  book_id: number
  page_number: number
  display_page_number: string
  text_content: string
}

export const libraryApi = {
  listBooks: () => requestJson<{ count: number; items: LibraryBook[] }>("/api/library/books"),
  uploadBook: (file: File, title: string, author: string, year?: string) => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("title", title)
    formData.append("author", author)
    if (year) formData.append("year", year)
    return requestForm<LibraryBook>("/api/library/books/upload", formData)
  },
  processBook: (bookId: number) => requestJson<{ book_id: number; num_pages: number; status: string }>(`/api/library/books/${bookId}/process`, { method: "POST" }),
  listPages: (bookId: number) => requestJson<{ count: number; items: LibraryPage[] }>(`/api/library/books/${bookId}/pages`),
}
