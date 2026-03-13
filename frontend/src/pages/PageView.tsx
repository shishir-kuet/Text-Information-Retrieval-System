import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router";
import { ArrowLeft, ArrowRight, BookOpen, FileText, User, Calendar, Loader2, AlertCircle } from "lucide-react";
import { motion } from "motion/react";

const COLORS = {
  bg: "#393A3A",
  card: "#575959",
  orange: "#F89344",
  red: "#FF642F",
  text: "#F4F4F4",
};

export interface PageData {
  page_id: string;
  text_content: string;
  display_page_number: string;
  book_title: string;
  author: string;
  year: string;
  domain: string;
  page_number: number;
  prev_page_id: string | null;
  next_page_id: string | null;
}

const STOPWORDS = new Set([
  "the","a","an","is","in","of","to","and","or","for","with","on","at",
  "by","from","that","this","it","as","be","was","are","were","has","have",
  "not","but","what","which","who","if","then","than","so","no","up","do",
  "did","can","will","just","its","are","how","about",
]);

export function getHighlightTerms(query: string): string[] {
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w));
}

export function highlightPageText(text: string, terms: string[]): string {
  if (!terms.length) return text;
  const escaped = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  return text.replace(
    regex,
    `<mark style="background:${COLORS.orange};color:#fff;padding:1px 4px;border-radius:3px;font-weight:600">$1</mark>`
  );
}

export default function PageView() {
  const { pageId } = useParams<{ pageId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q") || "";

  const [page, setPage] = useState<PageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pageId) return;
    setLoading(true);
    setError(null);
    setPage(null);

    fetch(`/api/page/${pageId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        return res.json();
      })
      .then((data: PageData) => {
        setPage(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load page.");
        setLoading(false);
      });
  }, [pageId]);

  const terms = getHighlightTerms(query);

  function goToPage(id: string | null) {
    if (!id) return;
    navigate(`/page/${id}?q=${encodeURIComponent(query)}`);
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: COLORS.bg }}>

      {/* Header */}
      <header style={{ backgroundColor: COLORS.card, borderBottom: `3px solid ${COLORS.orange}` }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "20px 32px" }}>
          <button
            onClick={() => navigate(`/results?q=${encodeURIComponent(query)}`)}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              marginBottom: 18, padding: "8px 18px", borderRadius: 8,
              border: `1.5px solid ${COLORS.text}`, background: "transparent",
              color: "#fff", fontSize: 14, cursor: "pointer", fontWeight: 500,
            }}
          >
            <ArrowLeft size={15} /> Back to Results
          </button>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                <BookOpen size={28} color={COLORS.orange} />
                <h1 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: 0, lineHeight: 1.3 }}>
                  {loading ? "Loading…" : (page?.book_title ?? "Unknown Book")}
                </h1>
              </div>
              {page && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center" }}>
                  {page.author && (
                    <span style={{ display: "flex", alignItems: "center", gap: 6, color: COLORS.text, fontSize: 15 }}>
                      <User size={15} color={COLORS.orange} />
                      {page.author}
                    </span>
                  )}
                  {page.year && (
                    <span style={{ display: "flex", alignItems: "center", gap: 6, color: COLORS.text, fontSize: 15 }}>
                      <Calendar size={15} color={COLORS.orange} />
                      {page.year}
                    </span>
                  )}
                </div>
              )}
            </div>
            {page && (
              <span style={{
                display: "flex", alignItems: "center", gap: 6, flexShrink: 0,
                fontSize: 14, fontWeight: 700, padding: "6px 14px",
                borderRadius: 20, backgroundColor: COLORS.red, color: "#fff",
              }}>
                <FileText size={14} /> Page {page.display_page_number}
              </span>
            )}
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "36px 32px 72px" }}>

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", paddingTop: 80 }}>
            <Loader2 size={52} color={COLORS.orange} style={{ animation: "spin 1s linear infinite", margin: "0 auto 16px" }} />
            <p style={{ color: COLORS.text, fontSize: 17 }}>Loading page…</p>
            <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div style={{ textAlign: "center", paddingTop: 80 }}>
            <AlertCircle size={52} color={COLORS.red} style={{ margin: "0 auto 16px" }} />
            <h3 style={{ color: "#fff", fontSize: 22, fontWeight: 700, marginBottom: 10 }}>Page Not Found</h3>
            <p style={{ color: COLORS.text, fontSize: 15, maxWidth: 480, margin: "0 auto" }}>{error}</p>
          </div>
        )}

        {/* Page content */}
        {!loading && !error && page && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            {/* Highlighted terms bar */}
            {terms.length > 0 && (
              <div style={{
                display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8,
                marginBottom: 24, padding: "14px 18px",
                backgroundColor: COLORS.card, borderRadius: 12,
              }}>
                <span style={{ color: COLORS.text, fontSize: 14, fontWeight: 600, marginRight: 4 }}>
                  Highlighted terms:
                </span>
                {terms.map((term) => (
                  <span
                    key={term}
                    style={{
                      fontSize: 13, padding: "3px 12px", borderRadius: 20,
                      backgroundColor: COLORS.orange, color: "#fff", fontWeight: 600,
                    }}
                  >
                    {term}
                  </span>
                ))}
              </div>
            )}

            {/* Full page text */}
            <div style={{
              backgroundColor: COLORS.card,
              border: `2px solid ${COLORS.orange}`,
              borderRadius: 16,
              padding: "28px 32px",
              marginBottom: 32,
            }}>
              <div
                style={{
                  color: COLORS.text, fontSize: 16, lineHeight: 1.9,
                  whiteSpace: "pre-wrap", wordBreak: "break-word",
                }}
                dangerouslySetInnerHTML={{ __html: highlightPageText(page.text_content, terms) }}
              />
            </div>

            {/* Prev / Next navigation */}
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
              <button
                onClick={() => goToPage(page.prev_page_id)}
                disabled={!page.prev_page_id}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 22px", borderRadius: 10,
                  border: `1.5px solid ${page.prev_page_id ? COLORS.text : "#666"}`,
                  background: "transparent",
                  color: page.prev_page_id ? "#fff" : "#888",
                  fontSize: 15, fontWeight: 600,
                  cursor: page.prev_page_id ? "pointer" : "not-allowed",
                  transition: "border-color 0.2s",
                }}
              >
                <ArrowLeft size={16} /> Previous Page
              </button>

              <button
                onClick={() => goToPage(page.next_page_id)}
                disabled={!page.next_page_id}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 22px", borderRadius: 10,
                  border: `1.5px solid ${page.next_page_id ? COLORS.text : "#666"}`,
                  background: "transparent",
                  color: page.next_page_id ? "#fff" : "#888",
                  fontSize: 15, fontWeight: 600,
                  cursor: page.next_page_id ? "pointer" : "not-allowed",
                  transition: "border-color 0.2s",
                }}
              >
                Next Page <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

      </main>
    </div>
  );
}
