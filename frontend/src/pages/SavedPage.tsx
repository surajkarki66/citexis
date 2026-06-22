import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getSavedPapers, unsavePaper } from "../api/client";
import EmptyState from "../components/EmptyState";
import { getUserId } from "../lib/userId";
import type { Paper } from "../types";

export default function SavedPage() {
  const userId = getUserId();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function loadSaved() {
    setLoading(true);
    setError(null);
    try {
      setPapers(await getSavedPapers(userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load saved papers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSaved();
  }, [userId]);

  async function handleUnsave(paperId: string) {
    setBusyId(paperId);
    try {
      await unsavePaper(userId, paperId);
      setPapers((current) => current.filter((paper) => paper.id !== paperId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove save");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl text-brand-900">Saved papers</h1>
      <p className="mt-2 text-sm text-muted">Papers you saved in this browser.</p>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-8 space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {!loading && papers.length === 0 && !error && (
        <div className="mt-8">
          <EmptyState
            title="No saved papers"
            description="Open a paper and click Save paper to bookmark it here."
          />
        </div>
      )}

      {!loading && papers.length > 0 && (
        <ul className="mt-8 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
          {papers.map((paper) => (
            <li key={paper.id} className="flex items-center justify-between gap-4 px-5 py-4">
              <Link to={`/papers/${paper.id}`} className="min-w-0 flex-1 hover:text-brand-700">
                <p className="font-medium text-slate-900 line-clamp-2">{paper.title}</p>
                <p className="mt-1 text-sm text-muted">
                  {[paper.year, paper.venue].filter(Boolean).join(" · ")}
                </p>
              </Link>
              <button
                type="button"
                disabled={busyId === paper.id}
                onClick={() => handleUnsave(paper.id)}
                className="shrink-0 rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:border-red-200 hover:text-red-700 disabled:opacity-60"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
