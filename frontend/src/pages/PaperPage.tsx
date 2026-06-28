import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deletePaper,
  getCitationDois,
  getPaper,
  getSavedPaperIds,
  recordInteraction,
  recordPaperView,
  unsavePaper,
} from "../api/client";
import EmptyState from "../components/EmptyState";
import PaperCard from "../components/PaperCard";
import PaperRating from "../components/PaperRating";
import { useAuth } from "../context/AuthContext";
import type { Paper } from "../types";

export default function PaperPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [citations, setCitations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saveBusy, setSaveBusy] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);

    const savedPromise = user ? getSavedPaperIds() : Promise.resolve([] as string[]);

    Promise.all([getPaper(id), getCitationDois(id), savedPromise])
      .then(([p, dois, savedIds]) => {
        setPaper(p);
        setCitations(dois);
        setSaved(savedIds.includes(id));

        if (user) {
          recordPaperView(id).catch(() => undefined);
        }
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      )
      .finally(() => setLoading(false));
  }, [id, user]);

  async function toggleSave() {
    if (!id || saveBusy) return;
    if (!user) {
      navigate("/login", { state: { from: `/papers/${id}` } });
      return;
    }

    setSaveBusy(true);
    setSaveError(null);

    try {
      if (saved) {
        await unsavePaper(id);
        setSaved(false);
      } else {
        await recordInteraction({
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

  async function handleDelete() {
    if (!id || deleteBusy) return;

    if (
      !window.confirm(
        "Delete this paper from MongoDB, Elasticsearch, and Pinecone? This cannot be undone."
      )
    ) {
      return;
    }

    setDeleteBusy(true);
    setDeleteError(null);

    try {
      await deletePaper(id);
      navigate("/");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete paper");
    } finally {
      setDeleteBusy(false);
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
          {paper.year && (
            <span className="text-slate-600">{paper.year}</span>
          )}
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
          {user ? (
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
          ) : (
            <Link
              to={`/login`}
              state={{ from: `/papers/${id}` }}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:border-brand-300 hover:text-brand-700"
            >
              Sign in to save
            </Link>
          )}

          {saveError && (
            <span className="text-xs text-red-600">{saveError}</span>
          )}

          {isAdmin && (
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleteBusy}
              className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60"
            >
              Delete paper
            </button>
          )}

          {deleteError && (
            <span className="text-xs text-red-600">{deleteError}</span>
          )}
        </div>

        <div className="mt-3">
          {id && user && <PaperRating paperId={id} />}
          {id && !user && (
            <p className="text-sm text-muted">
              <Link to="/login" state={{ from: `/papers/${id}` }} className="text-brand-600 hover:underline">
                Sign in
              </Link>{" "}
              to rate this paper.
            </p>
          )}
        </div>

        {id && (
          <div className="mt-3">
            <Link
              to={`/papers/${id}/related`}
              className="text-sm text-brand-600 hover:underline"
            >
              View all related papers →
            </Link>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
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
            <p className="mt-3 leading-relaxed text-slate-700">
              {paper.abstract}
            </p>
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
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 className="font-serif text-2xl text-slate-900">
              Related papers
            </h2>

            {id && (
              <Link
                to={`/papers/${id}/related`}
                className="text-sm text-brand-600 hover:underline"
              >
                View all related →
              </Link>
            )}
          </div>

          <div className="mt-4 space-y-4">
            {paper.recommendations.map((rec, index) => (
              <PaperCard
                key={rec.paper.id}
                paper={rec.paper}
                rank={index + 1}
                score={rec.score}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
