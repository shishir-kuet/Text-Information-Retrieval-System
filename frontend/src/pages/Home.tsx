import { useState } from "react";
import { Search, BookOpen, Zap, Shield, Database, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router";
import { motion } from "motion/react";

const COLORS = {
  bg: "#393A3A",
  card: "#575959",
  orange: "#F89344",
  red: "#FF642F",
  text: "#F4F4F4",
};

export default function Home() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("5");

  const features = [
    {
      icon: Zap,
      title: "Lightning Fast",
      desc: "Get search results instantly. Our smart indexing system finds what you need in milliseconds, even across thousands of books.",
      accent: COLORS.orange,
    },
    {
      icon: Database,
      title: "Smart Results",
      desc: "The most relevant pages appear first, automatically ranked by how well they match your search. Find exactly what you're looking for.",
      accent: COLORS.red,
    },
    {
      icon: Shield,
      title: "Secure & Private",
      desc: "Your searches stay private. We protect your data with strong security, so you can search confidently.",
      accent: COLORS.orange,
    },
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/results?q=${encodeURIComponent(query)}&k=${topK}`);
    }
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: COLORS.bg, position: "relative", overflowX: "hidden" }}>

      {/* Background blobs */}
      <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
        <div style={{ position: "absolute", top: 80, left: 40, width: 384, height: 384, borderRadius: "50%", filter: "blur(80px)", opacity: 0.12, backgroundColor: COLORS.orange }} />
        <div style={{ position: "absolute", bottom: 80, right: 40, width: 320, height: 320, borderRadius: "50%", filter: "blur(80px)", opacity: 0.1, backgroundColor: COLORS.card }} />
      </div>

      {/* Header */}
      <header style={{ position: "relative", zIndex: 10, padding: "20px 40px" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, backgroundColor: COLORS.orange, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <BookOpen size={24} color="#fff" />
            </div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 22, lineHeight: 1 }}>TIRS</div>
              <div style={{ color: COLORS.text, fontSize: 11 }}>Text Information Retrieval</div>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} style={{ display: "flex", gap: 12 }}>
            <button
              onClick={() => navigate("/login")}
              style={{ padding: "8px 22px", borderRadius: 8, border: `1px solid ${COLORS.text}`, background: "transparent", color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 500 }}
            >
              Login
            </button>
            <button
              onClick={() => navigate("/register")}
              style={{ padding: "8px 22px", borderRadius: 8, backgroundColor: COLORS.orange, border: "none", color: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}
            >
              Get Started <ArrowRight size={14} />
            </button>
          </motion.div>
        </div>
      </header>

      {/* Main */}
      <main style={{ position: "relative", zIndex: 10, padding: "60px 40px 80px" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>

          {/* Hero */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} style={{ textAlign: "center", marginBottom: 56 }}>
            <h1 style={{ fontSize: "clamp(40px, 6vw, 72px)", fontWeight: 800, color: "#fff", lineHeight: 1.15, margin: 0 }}>
              Text Information<br />
              <span style={{ color: COLORS.orange }}>Retrieval System</span>
            </h1>
            <p style={{ marginTop: 24, fontSize: 18, color: COLORS.text, maxWidth: 560, marginLeft: "auto", marginRight: "auto", lineHeight: 1.7 }}>
              Search through thousands of indexed documents with lightning-fast precision.
            </p>
          </motion.div>


          {/* Search Card */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            style={{ maxWidth: 760, margin: "0 auto 80px" }}
          >
            <div style={{ backgroundColor: COLORS.card, borderRadius: 20, padding: 32, border: `2px solid ${COLORS.orange}`, boxShadow: "0 25px 50px rgba(0,0,0,0.35)" }}>
              <form onSubmit={handleSearch}>
                {/* Search Input */}
                <div style={{ position: "relative", marginBottom: 20 }}>
                  <Search size={18} color="#bbb" style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)" }} />
                  <input
                    type="text"
                    placeholder="Search books, topics, passages…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    style={{
                      width: "100%",
                      height: 60,
                      paddingLeft: 48,
                      paddingRight: 16,
                      backgroundColor: COLORS.bg,
                      border: `1px solid rgba(244,244,244,0.5)`,
                      borderRadius: 10,
                      color: "#fff",
                      fontSize: 16,
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                {/* Controls Row */}
                <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
                    <label style={{ color: "#fff", fontSize: 14, fontWeight: 500, whiteSpace: "nowrap" }}>Top Results:</label>
                    <div style={{ position: "relative" }}>
                      <select
                        value={topK}
                        onChange={(e) => setTopK(e.target.value)}
                        style={{
                          height: 44,
                          paddingLeft: 14,
                          paddingRight: 36,
                          backgroundColor: COLORS.bg,
                          border: `1px solid rgba(244,244,244,0.5)`,
                          borderRadius: 8,
                          color: "#fff",
                          fontSize: 14,
                          cursor: "pointer",
                          outline: "none",
                          appearance: "none",
                          WebkitAppearance: "none",
                        }}
                      >
                        <option value="5" style={{ backgroundColor: COLORS.card }}>5</option>
                        <option value="10" style={{ backgroundColor: COLORS.card }}>10</option>
                        <option value="15" style={{ backgroundColor: COLORS.card }}>15</option>
                        <option value="20" style={{ backgroundColor: COLORS.card }}>20</option>
                      </select>
                      <div style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", pointerEvents: "none", color: "#bbb", fontSize: 10 }}>▼</div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    style={{
                      height: 44,
                      paddingLeft: 28,
                      paddingRight: 28,
                      backgroundColor: COLORS.orange,
                      border: "none",
                      borderRadius: 8,
                      color: "#fff",
                      fontSize: 15,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <Search size={16} /> Search
                  </button>
                </div>
              </form>


            </div>
          </motion.div>

          {/* Features */}
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4 }}>
            <h2 style={{ textAlign: "center", fontSize: "clamp(28px, 4vw, 40px)", fontWeight: 800, color: "#fff", marginBottom: 48 }}>
              Why Choose <span style={{ color: COLORS.orange }}>TIRS</span>?
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 28, maxWidth: 1100, margin: "0 auto" }}>
              {features.map(({ icon: Icon, title, desc, accent }) => (
                <div
                  key={title}
                  style={{ backgroundColor: COLORS.card, borderRadius: 20, padding: 32, border: `2px solid ${accent}`, boxShadow: "0 4px 24px rgba(0,0,0,0.2)" }}
                >
                  <div style={{ width: 60, height: 60, borderRadius: 14, backgroundColor: accent, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20 }}>
                    <Icon size={28} color="#fff" />
                  </div>
                  <h3 style={{ color: "#fff", fontSize: 22, fontWeight: 700, marginBottom: 12 }}>{title}</h3>
                  <p style={{ color: COLORS.text, lineHeight: 1.7, fontSize: 15, margin: 0 }}>{desc}</p>
                </div>
              ))}
            </div>
          </motion.div>

        </div>
      </main>

      {/* Footer */}
      <footer style={{ position: "relative", zIndex: 10, borderTop: `1px solid ${COLORS.orange}`, padding: "28px 40px", textAlign: "center" }}>
        <p style={{ color: COLORS.text, fontSize: 13, margin: 0 }}>© 2026 Text Information Retrieval System</p>
      </footer>

    </div>
  );
}
