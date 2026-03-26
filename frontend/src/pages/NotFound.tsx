import { Link } from "react-router-dom"

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-white">Page not found</h1>
      <p className="text-sm text-white/70">The page you requested does not exist.</p>
      <Link to="/" className="text-sm font-semibold text-[var(--color-accent)]">
        Go back home
      </Link>
    </div>
  )
}
