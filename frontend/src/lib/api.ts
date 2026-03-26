import type {
  ApiResponse,
  AdminIndexStats,
  AuthResponse,
  AuthUser,
  BooksResponse,
  HistoryResponse,
  IndexStats,
  JobsResponse,
  PageInfo,
  PdfPreview,
  SearchLogsResponse,
  SearchResponse,
} from "./types"

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000"

function buildHeaders(token?: string, extra?: HeadersInit) {
  const headers = new Headers(extra)

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  return headers
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: buildHeaders(token, {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    }),
  })

  const payload = (await response.json()) as ApiResponse<T>
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "Request failed")
  }

  return payload.data
}

async function requestForm<T>(
  path: string,
  body: FormData,
  token?: string,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body,
    headers: buildHeaders(token),
  })

  const payload = (await response.json()) as ApiResponse<T>
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "Request failed")
  }

  return payload.data
}

export const api = {
  baseUrl: API_BASE,
  health: () => requestJson<{ status: string; timestamp: string }>("/api/health"),
  stats: () => requestJson<IndexStats>("/api/stats"),
  search: (query: string, topK: number, token?: string) =>
    requestJson<SearchResponse>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    }, token),
  page: (pageId: string) => requestJson<PageInfo>(`/api/page/${pageId}`),
  pagePreview: (pageId: string) =>
    requestJson<PdfPreview>(`/api/page/${pageId}/pdf-preview`),
  login: (email: string, password: string) =>
    requestJson<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string) =>
    requestJson<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),
  me: (token: string) => requestJson<AuthUser>("/api/auth/me", {}, token),
  logout: (token: string) =>
    requestJson<{ logged_out: boolean; user_id: number }>("/api/auth/logout", { method: "POST" }, token),
  history: (token: string, limit = 50) =>
    requestJson<HistoryResponse>(`/api/history?limit=${limit}`, {}, token),
  deleteHistory: (token: string, logId: number) =>
    requestJson<{ deleted: number }>(`/api/history/${logId}`, { method: "DELETE" }, token),
  clearHistory: (token: string) =>
    requestJson<{ deleted: number }>("/api/history", { method: "DELETE" }, token),
  adminUpload: (token: string, data: FormData) => requestForm<Record<string, unknown>>("/api/admin/upload", data, token),
  adminProcessBook: (token: string, bookId: number, wait = false) =>
    requestJson<Record<string, unknown>>(`/api/admin/process-book/${bookId}?wait=${wait ? 1 : 0}`, { method: "POST" }, token),
  adminProcessUploaded: (token: string, wait = false) =>
    requestJson<Record<string, unknown>>(`/api/admin/process-books?wait=${wait ? 1 : 0}`, { method: "POST" }, token),
  adminBuildIndex: (token: string, full = false, wait = false) =>
    requestJson<Record<string, unknown>>(`/api/admin/index/build?full=${full ? 1 : 0}&wait=${wait ? 1 : 0}`, { method: "POST" }, token),
  adminIndexStats: (token: string) => requestJson<AdminIndexStats>("/api/admin/index/stats", {}, token),
  adminBooks: (token: string, limit = 200) =>
    requestJson<BooksResponse>(`/api/admin/books?limit=${limit}`, {}, token),
  adminSearchLogs: (token: string, limit = 100, skip = 0) =>
    requestJson<SearchLogsResponse>(`/api/admin/logs/search?limit=${limit}&skip=${skip}`, {}, token),
  adminJobs: (token: string, limit = 50, status?: string) => {
    const query = status ? `?limit=${limit}&status=${status}` : `?limit=${limit}`
    return requestJson<JobsResponse>(`/api/admin/jobs${query}`, {}, token)
  },
  adminJob: (token: string, jobId: string) => requestJson<Record<string, unknown>>(`/api/admin/jobs/${jobId}`, {}, token),
}
