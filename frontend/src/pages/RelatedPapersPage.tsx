import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getRelatedPapers } from "../api/client";
import EmptyState from "../components/EmptyState";
import PaperCard from "../components/PaperCard";
import type { PaperRecommendation } from "../types";

export default function RelatedPapersPage() {
  const { id } = useParams<{ id: string }>();
  const [items, setItems] = useState<PaperRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    setLoading(true);

    getRelatedPapers(id)
      .then((data) => setItems(data.items))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      )
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <Link
        to={id ? `/papers/${id}` : "/"}
        className="text-sm text-brand-600 hover:underline"
      >
        ← Back to paper
      </Link>

      <h1 className="mt-6 font-serif text-3xl text-brand-900">
        Related papers
      </h1>

      <p className="mt-2 text-sm text-muted">
        Full recommendation list ranked by semantic, citation, and collaborative signals.
      </p>

      {/* Error state */}
      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="mt-8 space-y-4">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-xl bg-slate-100"
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && items.length === 0 && (
        <div className="mt-8">
          <EmptyState
            title="No related papers"
            description="Try another paper in your corpus."
          />
        </div>
      )}

      {/* Results */}
      {!loading && items.length > 0 && (
        <div className="mt-8 space-y-4">
          {items.map((rec, index) => (
            <PaperCard
              key={rec.paper.id}
              paper={rec.paper}
              rank={index + 1}
              score={rec.score}
            />
          ))}
        </div>
      )}
    </div>
  );
}