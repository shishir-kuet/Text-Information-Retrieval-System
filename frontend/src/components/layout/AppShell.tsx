import { Link, NavLink, Outlet, useNavigate } from "react-router-dom"
import { BookOpen, LogOut, Shield } from "lucide-react"
import { Button } from "../ui/button"
import { useAuth } from "../../lib/auth"

const navItems = [
  { to: "/", label: "Home" },
  { to: "/results", label: "Search" },
  { to: "/history", label: "History" },
  { to: "/admin", label: "Admin" },
]

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-white">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 right-0 h-80 w-80 rounded-full bg-[var(--color-accent)]/20 blur-[140px]" />
        <div className="absolute bottom-0 left-0 h-96 w-96 rounded-full bg-[var(--color-accent-2)]/15 blur-[160px]" />
      </div>

      <header className="relative z-10 border-b border-white/10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
          <Link to="/" className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent)] shadow-lg">
              <BookOpen className="h-6 w-6" />
            </div>
            <div>
              <div className="text-lg font-bold">TIRS</div>
              <div className="text-xs text-white/70">Information Retrieval System</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-full border px-3 py-1.5 text-sm font-semibold transition ${
                    isActive
                      ? "border-white/35 bg-white/10 text-white"
                      : "border-transparent text-white/60 hover:border-white/50 hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/80 md:flex">
                  <Shield className="h-3.5 w-3.5" />
                  {user.name || user.email}
                </div>
                <Button variant="ghost" onClick={() => logout()}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => navigate("/login")}>
                  Login
                </Button>
                <Button onClick={() => navigate("/register")}>
                  Get Started
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl px-6 py-12">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-white/10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 text-xs text-white/60">
          <div>© 2026 Text Information Retrieval System</div>
        </div>
      </footer>
    </div>
  )
}
