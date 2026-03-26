export type ApiResponse<T> = {
  success: boolean
  message: string
  data: T
  details?: unknown
}

export type SearchResult = {
  book_id: number
  title: string
  page_id: string
  page_number: number
  score: number
  snippet: string
}

export type SearchResponse = {
  query: string
  count: number
  results: SearchResult[]
  latency_ms: number
}

export type PageInfo = {
  page_id: string
  book_id: number
  page_number: number
  display_page_number: string
  text_content: string
  snippet: string
  book: {
    book_id: number
    title: string
    domain: string
    author?: string | null
    year?: number | null
    num_pages?: number | null
  }
}

export type PdfPreview = {
  book_id: number
  page_number: number
  pdf_url: string
}

export type AuthUser = {
  user_id: number
  name: string
  email: string
  role: string
  created_at?: string
  updated_at?: string
}

export type AuthResponse = {
  token: string
  user: AuthUser
}

export type HistoryItem = {
  log_id: number
  user_id: number | null
  query_text: string
  normalized_query: string[]
  total_results: number
  top_results: Array<{ book_id: number; page_id: string; page_number: number; score: number }>
  latency_ms: number
  created_at: string
}

export type HistoryResponse = {
  count: number
  items: HistoryItem[]
}

export type BookItem = {
  book_id: number
  title: string
  domain: string
  status: string
  num_pages?: number
  file_size_mb?: number
  date_added?: string
  updated_at?: string
}

export type BooksResponse = {
  count: number
  items: BookItem[]
}

export type IndexStats = {
  total_books: number
  total_pages: number
  index: {
    available: boolean
    path: string
    size_bytes: number
    build_date: string | null
  }
}

export type AdminIndexStats = {
  index_available: boolean
  index_size_bytes: number
  build_date: string | null
  total_books: number
  total_pages: number
}

export type JobItem = {
  job_id: string
  job_type: string
  status: string
  created_at?: string
  updated_at?: string
  meta?: Record<string, unknown>
}

export type JobsResponse = {
  count: number
  items: JobItem[]
  limit: number
  status: string | null
}

export type SearchLogsResponse = {
  count: number
  items: Array<Record<string, unknown>>
  limit: number
  skip: number
}
