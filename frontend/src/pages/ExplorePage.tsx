import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getTopicClusters } from "../api/client";
import EmptyState from "../components/EmptyState";
import { recordPaperClick } from "../lib/interactions";
import type { TopicCluster } from "../types";

const POPULAR_TAGS = [
  "machine learning",
  "computer vision",
  "natural language processing",
  "reinforcement learning",
  "deep learning",
];

export default function ExplorePage() {
  const [params, setParams] = useSearchParams();
  const tag = params.get("tag") ?? "";
  const [input, setInput] = useState(tag);
  const [clusters, setClusters] = useState<TopicCluster[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tag) return;
    setLoading(true);
    setError(null);
    getTopicClusters(tag)
      .then(setClusters)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [tag]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) setParams({ tag: input.trim() });
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl text-brand-900">Explore topics</h1>
      <p className="mt-2 text-muted">
        Find papers by similar tags and browse them grouped by tag
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter a topic, e.g. learning or vision…"
          className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand-400"
        />
        <button
          type="submit"
          className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Explore
        </button>
      </form>

      <div className="mt-4 flex flex-wrap gap-2">
        {POPULAR_TAGS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              setInput(t);
              setParams({ tag: t });
            }}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-700"
          >
            {t}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="mt-8 space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-100" />
          ))}
        </div>
      )}

      {!loading && tag && clusters.length === 0 && !error && (
        <div className="mt-8">
          <EmptyState
            title="No clusters found"
            description={`No papers with tags matching "${tag}" in your corpus.`}
          />
        </div>
      )}

      {!loading && clusters.length > 0 && (
        <div className="mt-8 space-y-4">
          <p className="text-sm text-muted">
            {clusters.length} matching tag{clusters.length !== 1 && "s"} for &ldquo;{tag}&rdquo;
          </p>
          {clusters.map((c) => (
            <div
              key={c.tag}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-slate-900">{c.tag}</h3>
                <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
                  {c.count} papers
                </span>
              </div>
              {c.papers.length > 0 && (
                <ul className="mt-3 space-y-1 text-sm">
                  {c.papers.map((paper) => (
                    <li key={paper.id} className="truncate">
                      <Link
                        to={`/papers/${paper.id}`}
                        onClick={() => recordPaperClick(paper.id)}
                        className="text-slate-600 hover:text-brand-600 hover:underline"
                      >
                        · {paper.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {!tag && !loading && (
        <div className="mt-8">
          <EmptyState
            title="Pick a topic"
            description="Enter a tag or click one of the suggestions above."
          />
        </div>
      )}

      <p className="mt-8 text-center">
        <Link to="/" className="text-sm text-brand-600 hover:underline">
          ← Back to search
        </Link>
      </p>
    </div>
  );
}
