import { useEffect, useState } from "react";
import { getPaperRating, recordInteraction } from "../api/client";

interface PaperRatingProps {
  paperId: string;
  userId: string;
}

const STARS = [1, 2, 3, 4, 5] as const;

export default function PaperRating({ paperId, userId }: PaperRatingProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPaperRating(userId, paperId)
      .then((value) => setRating(value))
      .catch(() => undefined);
  }, [userId, paperId]);

  async function submit(value: number) {
    setBusy(true);
    setError(null);
    try {
      await recordInteraction({
        user_id: userId,
        paper_id: paperId,
        interaction_type: "rating",
        rating: value,
      });
      setRating(value);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to save rating";
      try {
        const parsed = JSON.parse(message) as { detail?: unknown };
        if (Array.isArray(parsed.detail)) {
          const first = parsed.detail[0] as { msg?: string };
          setError(first.msg ?? message);
        } else if (typeof parsed.detail === "string") {
          setError(parsed.detail);
        } else {
          setError(message);
        }
      } catch {
        setError(message);
      }
    } finally {
      setBusy(false);
    }
  }

  const active = hover ?? rating;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-slate-600">Your rating</span>
      <div
        className="flex items-center gap-0.5"
        onMouseLeave={() => setHover(null)}
        role="group"
        aria-label="Rate this paper from 1 to 5 stars"
      >
        {STARS.map((value) => {
          const filled = active !== null && value <= active;
          return (
            <button
              key={value}
              type="button"
              disabled={busy}
              onMouseEnter={() => setHover(value)}
              onClick={() => submit(value)}
              className="rounded p-0.5 text-xl leading-none transition-colors disabled:opacity-60"
              aria-label={`Rate ${value} out of 5`}
            >
              <span className={filled ? "text-amber-400" : "text-slate-300"}>★</span>
            </button>
          );
        })}
      </div>
      {rating !== null && (
        <span className="text-xs text-muted">{rating}/5</span>
      )}
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
