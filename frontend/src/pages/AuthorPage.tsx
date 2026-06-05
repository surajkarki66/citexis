import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getAuthorPapers } from "../api/client";
import EmptyState from "../components/EmptyState";
import type { AuthorPaper } from "../types";

export default function AuthorPage() {
  const { name } = useParams<{ name: string }>();
  const authorName = name ? decodeURIComponent(name) : "";
  const [papers, setPapers] = useState<AuthorPaper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authorName) return;
    setLoading(true);
    getAuthorPapers(authorName)
      .then(setPapers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [authorName]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm text-brand-600 hover:underline">
        ← Back to search
      </Link>

      <h1 className="mt-6 font-serif text-3xl text-brand-900">{authorName}</h1>
      <p className="mt-1 text-muted">Papers in your indexed corpus</p>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-8 space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {!loading && papers.length === 0 && !error && (
        <div className="mt-8">
          <EmptyState
            title="No papers found"
            description="This author name must match exactly as stored in MongoDB."
          />
        </div>
      )}

      {!loading && papers.length > 0 && (
        <ul className="mt-8 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
          {papers.map((p) => (
            <li key={p.id}>
              <Link
                to={`/papers/${p.id}`}
                className="flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-brand-50/50"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 line-clamp-1">{p.title}</p>
                  <p className="mt-0.5 text-sm text-muted">
                    {[p.year, p.venue].filter(Boolean).join(" · ")}
                  </p>
                </div>
                <span className="shrink-0 text-brand-600">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
