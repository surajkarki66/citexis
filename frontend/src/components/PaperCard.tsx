import { Link } from "react-router-dom";
import { recordPaperClickSafe } from "../lib/interactions";
import type { PaperSummary } from "../types";

interface PaperCardProps {
  paper: PaperSummary;
  rank?: number;
  score?: number;
  reasonLabel?: string;
  trackClick?: boolean;
}

export default function PaperCard({
  paper,
  rank,
  score,
  reasonLabel,
  trackClick = true,
}: PaperCardProps) {
  const rankTitle =
    score !== undefined
      ? `Rank ${rank}. Internal fusion score: ${score.toFixed(4)}.`
      : rank !== undefined
        ? `Rank ${rank}`
        : undefined;

  return (
    <article className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-brand-200 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <Link
          to={`/papers/${paper.id}`}
          className="min-w-0 flex-1"
          onClick={() => {
            if (trackClick) recordPaperClickSafe(paper.id);
          }}
        >
          <h3 className="font-serif text-lg leading-snug text-slate-900 group-hover:text-brand-700 transition-colors line-clamp-2">
            {paper.title}
          </h3>
        </Link>
        {rank !== undefined || reasonLabel ? (
          <div className="flex shrink-0 flex-col items-end gap-1">
            {rank !== undefined && (
              <span
                className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700"
                title={rankTitle}
              >
                #{rank}
              </span>
            )}
            {reasonLabel && (
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                {reasonLabel}
              </span>
            )}
          </div>
        ) : null}
      </div>
      <p className="mt-2 text-sm text-muted">
        {paper.authors.slice(0, 4).map((a, i) => (
          <span key={a}>
            {i > 0 && ", "}
            <Link
              to={`/authors/${encodeURIComponent(a)}`}
              className="hover:text-brand-600 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {a}
            </Link>
          </span>
        ))}
        {paper.authors.length > 4 && ` +${paper.authors.length - 4} more`}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {paper.year && <span>{paper.year}</span>}
        {paper.venue && (
          <>
            <span className="text-slate-300">·</span>
            <span className="truncate max-w-[200px]">{paper.venue}</span>
          </>
        )}
      </div>
      {paper.abstract_snippet && (
        <p className="mt-3 text-sm leading-relaxed text-slate-600 line-clamp-2">
          {paper.abstract_snippet}
        </p>
      )}
    </article>
  );
}
