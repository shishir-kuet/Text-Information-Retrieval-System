import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../lib/auth"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"

export default function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register(name, email, password)
      navigate("/")
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="card-hover mx-auto w-full max-w-md rounded-3xl border border-white/10 bg-[var(--color-surface)]/80 p-8">
        <h1 className="text-2xl font-semibold text-white">Create your account</h1>
        <p className="mt-2 text-sm text-white/60">Get access to downloads and saved search history.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Input
            placeholder="Full name"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <Input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">{error}</div>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating account..." : "Register"}
          </Button>
        </form>
      </div>
    </div>
  )
}
