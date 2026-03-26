import type { ReactNode } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import { AppShell } from "./components/layout/AppShell"
import Home from "./pages/Home"
import Results from "./pages/Results"
import PageDetail from "./pages/PageDetail"
import Login from "./pages/Login"
import Register from "./pages/Register"
import History from "./pages/History"
import Admin from "./pages/Admin"
import NotFound from "./pages/NotFound"
import { useAuth } from "./lib/auth"

function RequireAuth({ children }: { children: ReactNode }) {
  const { token, loading } = useAuth()
  if (loading) {
    return <div className="text-white/70">Loading...</div>
  }
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="/results" element={<Results />} />
        <Route path="/page/:pageId" element={<PageDetail />} />
        <Route path="/history" element={<RequireAuth><History /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><Admin /></RequireAuth>} />
      </Route>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
