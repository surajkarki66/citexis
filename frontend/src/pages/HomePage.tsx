import { useState } from "react";
import { searchPapers } from "../api/client";
import EmptyState from "../components/EmptyState";
import FilterPanel from "../components/FilterPanel";
import PaperCard from "../components/PaperCard";
import SearchBar from "../components/SearchBar";
import type { SearchFilters, SearchResponse } from "../types";

const SUGGESTIONS = [
  "vision transformer",
  "reinforcement learning",
  "computer vision",
  "natural language processing",
];

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(q: string = query) {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchPapers({ query: q.trim(), filters, top_k: 10 });
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {/* Hero */}
      <section className="border-b border-slate-200 bg-gradient-to-b from-brand-50/60 to-surface px-4 py-16 sm:py-24">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="font-serif text-4xl tracking-tight text-brand-900 sm:text-5xl">
            Discover research papers
          </h1>
          <p className="mt-4 text-lg text-muted">
            Hybrid semantic + keyword search across your indexed corpus
          </p>
          <div className="mt-8">
            <SearchBar
              value={query}
              onChange={setQuery}
              onSubmit={() => runSearch()}
              loading={loading}
            />
          </div>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => {
                  setQuery(s);
                  runSearch(s);
                }}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 transition-colors hover:border-brand-300 hover:text-brand-700"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="grid gap-8 lg:grid-cols-[240px_1fr]">
          <FilterPanel filters={filters} onChange={setFilters} />

          <div>
            {error && (
              <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {loading && (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="h-36 animate-pulse rounded-xl bg-slate-100"
                  />
                ))}
              </div>
            )}

            {!loading && results && results.total > 0 && (
              <>
                <p className="mb-4 text-sm text-muted">
                  {results.total} result{results.total !== 1 && "s"} for &ldquo;
                  {results.query}&rdquo;
                </p>
                <div className="space-y-4">
                  {results.results.map((r, index) => (
                    <PaperCard
                      key={r.paper.id}
                      paper={r.paper}
                      rank={index + 1}
                      score={r.score}
                    />
                  ))}
                </div>
              </>
            )}

            {!loading && results && results.total === 0 && (
              <EmptyState
                title="No papers found"
                description="Try a different query or adjust your filters."
              />
            )}

            {!loading && !results && !error && (
              <EmptyState
                title="Start searching"
                description="Enter a query above to find papers in your indexed corpus."
              />
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
