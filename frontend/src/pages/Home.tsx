import { useState } from "react"
import { ArrowRight, Database, Search, Shield, Zap } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { motion } from "motion/react"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Select } from "../components/ui/select"

export default function Home() {
  const navigate = useNavigate()
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState("5")



  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault()
    if (query.trim()) {
      navigate(`/results?q=${encodeURIComponent(query)}&k=${topK}`)
    }
  }


  return (
    <div className="space-y-16">
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr]"
      >
        <div className="space-y-6">
          <h1 className="text-4xl font-semibold leading-tight sm:text-5xl lg:text-6xl">
            Text Information<br />
            <span className="text-[var(--color-accent)]">Retrieval System</span>
          </h1>
          <p className="max-w-xl text-base text-white/70 sm:text-lg">
            Find the right page in seconds. Search by a line or paragraph, open the original PDF for accuracy, and
            save your recent searches when you sign in.
          </p>
          <div className="flex flex-wrap gap-4">
            <Button onClick={() => navigate("/results")}>Start searching</Button>
            <Button variant="outline" onClick={() => navigate("/admin")}>Admin Tools</Button>
          </div>
        </div>
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.1 }}
        className="rounded-3xl border border-[var(--color-accent)]/30 bg-[var(--color-surface)]/80 p-8 shadow-2xl"
      >
        <form onSubmit={handleSearch} className="space-y-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/60" />
            <Input
              type="text"
              placeholder="Search for a line, sentence, or paragraph..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-14 pl-12 text-base"
            />
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-white">Top Results:</span>
              <Select
                value={topK}
                onChange={setTopK}
                options={[
                  { label: "5", value: "5" },
                  { label: "10", value: "10" },
                  { label: "15", value: "15" },
                  { label: "20", value: "20" },
                ]}
              />
            </div>
            <Button type="submit" className="ml-auto">
              <Search className="mr-2 h-4 w-4" />
              Search
            </Button>
          </div>
        </form>
      </motion.section>

      <motion.section
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <h2 className="text-3xl font-semibold">
          Why Choose <span className="text-[var(--color-accent)]">TIRS</span>?
        </h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {[
            {
              title: "Lightning Fast",
              description:
                "Get results quickly, even when your library is large.",
              icon: Zap,
              color: "bg-[var(--color-accent)]",
            },
            {
              title: "Smart Results",
              description:
                "Open the most relevant pages first and preview the original PDF any time.",
              icon: Database,
              color: "bg-[var(--color-accent-2)]",
            },
            {
              title: "Secure & Private",
              description:
                "Sign in to access downloads and keep your activity private.",
              icon: Shield,
              color: "bg-[var(--color-accent)]",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-white/10 bg-[var(--color-surface)]/70 p-6 shadow-lg"
            >
              <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-xl ${feature.color}`}>
                <feature.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
              <p className="mt-3 text-sm text-white/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </motion.section>

      <section className="rounded-3xl border border-white/10 bg-[var(--color-surface)]/70 p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-2xl font-semibold text-white">Ready to dive in?</h3>
            <p className="mt-2 max-w-xl text-sm text-white/70">
              Create an account to save your history and download books.
            </p>
          </div>
          <Button onClick={() => navigate("/register")}>
            Get Started
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </section>
    </div>
  )
}
