import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCitationDois, getPaper, getSavedPaperIds, recordInteraction, unsavePaper } from "../api/client";
import EmptyState from "../components/EmptyState";
import PaperCard from "../components/PaperCard";
import { getUserId } from "../lib/userId";
import type { Paper } from "../types";

const REASON_LABELS: Record<string, string> = {
  "semantically similar": "Semantic",
  "cited together": "Citation",
  "readers also saved": "Collaborative",
};

export default function PaperPage() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [citations, setCitations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saveBusy, setSaveBusy] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    const userId = getUserId();
    Promise.all([getPaper(id), getCitationDois(id), getSavedPaperIds(userId)])
      .then(([p, dois, savedIds]) => {
        setPaper(p);
        setCitations(dois);
        setSaved(savedIds.includes(id));
        recordInteraction({
          user_id: userId,
          paper_id: id,
          interaction_type: "view",
        }).catch(() => undefined);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  async function toggleSave() {
    if (!id || saveBusy) return;
    const userId = getUserId();
    setSaveBusy(true);
    setSaveError(null);
    try {
      if (saved) {
        await unsavePaper(userId, id);
        setSaved(false);
      } else {
        await recordInteraction({
          user_id: userId,
          paper_id: id,
          interaction_type: "save",
        });
        setSaved(true);
      }
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to update save");
    } finally {
      setSaveBusy(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <div className="h-8 w-2/3 animate-pulse rounded bg-slate-100" />
        <div className="mt-4 h-4 w-1/3 animate-pulse rounded bg-slate-100" />
        <div className="mt-8 h-48 animate-pulse rounded-xl bg-slate-100" />
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <EmptyState title="Paper not found" description={error ?? undefined} />
        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-brand-600 hover:underline">
            ← Back to search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <Link to="/" className="text-sm text-brand-600 hover:underline">
        ← Back to search
      </Link>

      <article className="mt-6">
        <h1 className="font-serif text-3xl leading-tight text-slate-900 sm:text-4xl">
          {paper.title}
        </h1>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-muted">
          {paper.authors.map((a) => (
            <Link
              key={a.name}
              to={`/authors/${encodeURIComponent(a.name)}`}
              className="hover:text-brand-600 hover:underline"
            >
              {a.name}
            </Link>
          ))}
        </div>

        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          {paper.year && <span className="text-slate-600">{paper.year}</span>}
          {paper.venue && (
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600">
              {paper.venue}
            </span>
          )}
          {paper.doi && (
            <a
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 hover:underline"
            >
              doi:{paper.doi}
            </a>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={toggleSave}
            disabled={saveBusy}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60 ${
              saved
                ? "border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100"
                : "border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:text-brand-700"
            }`}
          >
            {saved ? "Saved" : "Save paper"}
          </button>
          {saveError && <span className="text-xs text-red-600">{saveError}</span>}
          <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
            {paper.cited_by_count.toLocaleString()} citations
          </span>
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              paper.embedding_status === "indexed"
                ? "bg-green-50 text-green-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {paper.embedding_status}
          </span>
          {paper.tags.slice(0, 5).map((tag) => (
            <Link
              key={tag}
              to={`/explore?tag=${encodeURIComponent(tag)}`}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 hover:bg-brand-50 hover:text-brand-700"
            >
              {tag}
            </Link>
          ))}
        </div>

        {paper.full_text_url && (
          <a
            href={paper.full_text_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Read full text →
          </a>
        )}

        {paper.abstract && (
          <section className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
              Abstract
            </h2>
            <p className="mt-3 leading-relaxed text-slate-700">{paper.abstract}</p>
          </section>
        )}

        {citations.length > 0 && (
          <section className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
              References ({citations.length})
            </h2>
            <ul className="mt-3 max-h-64 space-y-1 overflow-y-auto rounded-lg border border-slate-200 bg-white p-4 text-sm">
              {citations.map((doi) => (
                <li key={doi}>
                  <a
                    href={`https://doi.org/${doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-600 hover:underline"
                  >
                    {doi}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
      </article>

      {paper.recommendations.length > 0 && (
        <section className="mt-12">
          <h2 className="font-serif text-2xl text-slate-900">Related papers</h2>
          <div className="mt-4 space-y-4">
            {paper.recommendations.map((rec, index) => (
              <PaperCard
                key={rec.paper.id}
                paper={rec.paper}
                rank={index + 1}
                score={rec.score}
                reasonLabel={REASON_LABELS[rec.reason] ?? rec.reason}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
