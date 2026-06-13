import { useState } from "react";
import { Link } from "react-router-dom";
import { importDoiSync, importOpenAlexSync, importPaperSync, searchArxiv } from "../api/client";
import EmptyState from "../components/EmptyState";
import { mergeImportResults, parseDoiList } from "../lib/import";
import type { ArxivSearchResponse, ImportResult, ManualPaperInput } from "../types";

const EMPTY_MANUAL_PAPER: ManualPaperInput = {
  title: "",
  authors: "",
  abstract: "",
  doi: "",
  year: "",
  venue: "",
  tags: "",
};

const ARXIV_SUGGESTIONS = [
  "object detection",
  "transformer",
  "large language model",
  "reinforcement learning",
];

const OPENALEX_SUGGESTIONS = [
  "machine learning",
  "computer vision",
  "transformer models",
  "climate change",
];

function ImportSummary({ result }: { result: ImportResult }) {
  const total = result.imported + result.skipped + result.failed;
  if (total === 0) return null;

  return (
    <section className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="font-serif text-xl text-slate-900">Import summary</h2>
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        <span className="rounded-full bg-green-50 px-3 py-1 font-medium text-green-700">
          {result.imported} imported
        </span>
        <span className="rounded-full bg-amber-50 px-3 py-1 font-medium text-amber-700">
          {result.skipped} skipped
        </span>
        <span className="rounded-full bg-red-50 px-3 py-1 font-medium text-red-700">
          {result.failed} failed
        </span>
      </div>

      {result.paper_ids.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted">
            Imported papers
          </h3>
          <ul className="mt-3 space-y-2">
            {result.paper_ids.map((id) => (
              <li key={id}>
                <Link to={`/papers/${id}`} className="text-sm text-brand-600 hover:underline">
                  View paper {id}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.skipped_items.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted">Skipped</h3>
          <p className="mt-2 text-sm text-slate-600">
            Already in the corpus: {result.skipped_items.join(", ")}
          </p>
        </div>
      )}

      {result.failed_items.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted">Failed</h3>
          <ul className="mt-2 space-y-2 text-sm text-red-700">
            {result.failed_reasons.length > 0
              ? result.failed_reasons.map((reason) => <li key={reason}>{reason}</li>)
              : result.failed_items.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
    </section>
  );
}

export default function ImportPage() {
  const [doiText, setDoiText] = useState("");
  const [openAlexQuery, setOpenAlexQuery] = useState("machine learning");
  const [openAlexLimit, setOpenAlexLimit] = useState(10);
  const [enrich, setEnrich] = useState(true);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [manualPaper, setManualPaper] = useState<ManualPaperInput>(EMPTY_MANUAL_PAPER);
  const [arxivQuery, setArxivQuery] = useState("object detection");
  const [arxivLimit, setArxivLimit] = useState(10);
  const [arxivSearching, setArxivSearching] = useState(false);
  const [arxivResults, setArxivResults] = useState<ArxivSearchResponse | null>(null);
  const [copyMessage, setCopyMessage] = useState<string | null>(null);

  async function handleDoiImport(e: React.FormEvent) {
    e.preventDefault();
    const dois = parseDoiList(doiText);
    if (dois.length === 0) {
      setError("Enter at least one DOI.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const results: ImportResult[] = [];
    try {
      for (let i = 0; i < dois.length; i += 1) {
        setProgress(`Importing DOI ${i + 1} of ${dois.length}…`);
        results.push(await importDoiSync(dois[i], enrich));
      }
      setResult(mergeImportResults(results));
    } catch (err) {
      setError(err instanceof Error ? err.message : "DOI import failed");
      if (results.length > 0) {
        setResult(mergeImportResults(results));
      }
    } finally {
      setProgress(null);
      setLoading(false);
    }
  }

  async function handleOpenAlexImport(e: React.FormEvent) {
    e.preventDefault();
    if (!openAlexQuery.trim()) {
      setError("Enter a search query.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress("Fetching from OpenAlex and indexing papers…");

    try {
      const data = await importOpenAlexSync(openAlexQuery.trim(), openAlexLimit, enrich);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OpenAlex import failed");
    } finally {
      setProgress(null);
      setLoading(false);
    }
  }

  async function handleArxivSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!arxivQuery.trim()) {
      setError("Enter an arXiv search query.");
      return;
    }

    setArxivSearching(true);
    setError(null);
    setCopyMessage(null);
    setArxivResults(null);

    try {
      const data = await searchArxiv(arxivQuery.trim(), arxivLimit);
      setArxivResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "arXiv search failed");
    } finally {
      setArxivSearching(false);
    }
  }

  async function handleImportArxivDois() {
    if (!arxivResults || arxivResults.dois.length === 0) {
      setError("No DOIs to import from the current arXiv results.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const results: ImportResult[] = [];
    try {
      for (let i = 0; i < arxivResults.dois.length; i += 1) {
        setProgress(`Importing arXiv DOI ${i + 1} of ${arxivResults.dois.length}…`);
        results.push(await importDoiSync(arxivResults.dois[i], enrich));
      }
      setResult(mergeImportResults(results));
    } catch (err) {
      setError(err instanceof Error ? err.message : "DOI import failed");
      if (results.length > 0) {
        setResult(mergeImportResults(results));
      }
    } finally {
      setProgress(null);
      setLoading(false);
    }
  }

  function handleCopyArxivDois() {
    if (!arxivResults || arxivResults.dois.length === 0) {
      setError("No DOIs to copy from the current arXiv results.");
      return;
    }

    const text = arxivResults.dois.join("\n");
    void navigator.clipboard.writeText(text).then(() => {
      setCopyMessage(`Copied ${arxivResults.dois.length} DOI(s) to clipboard.`);
      setError(null);
    });
  }

  function handleFillDoiImport() {
    if (!arxivResults || arxivResults.dois.length === 0) {
      setError("No DOIs to add from the current arXiv results.");
      return;
    }

    setDoiText(arxivResults.dois.join("\n"));
    setCopyMessage("DOIs added to the import-by-DOI field.");
    setError(null);
  }

  async function handleManualIngest(e: React.FormEvent) {
    e.preventDefault();
    if (!manualPaper.title.trim()) {
      setError("Title is required for manual ingest.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setProgress("Ingesting and indexing paper…");

    try {
      const data = await importPaperSync(manualPaper, enrich);
      setResult(data);
      if (data.imported > 0) {
        setManualPaper(EMPTY_MANUAL_PAPER);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Manual ingest failed");
    } finally {
      setProgress(null);
      setLoading(false);
    }
  }

  function updateManualField(field: keyof ManualPaperInput, value: string) {
    setManualPaper((current) => ({ ...current, [field]: value }));
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="font-serif text-3xl text-brand-900">Import papers</h1>
      <p className="mt-3 max-w-2xl text-muted">
        Add papers by DOI, OpenAlex search, arXiv DOI extraction, or manual entry. Imports run
        synchronously and index immediately.
      </p>

      <label className="mt-6 flex items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={enrich}
          onChange={(e) => setEnrich(e.target.checked)}
          className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
        />
        Enrich with CORE full-text URLs when available
      </label>

      {copyMessage && (
        <div className="mt-6 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          {copyMessage}
        </div>
      )}

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {progress && (
        <div className="mt-6 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
          {progress}
        </div>
      )}

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-xl text-slate-900">Import by DOI</h2>
          <p className="mt-2 text-sm text-muted">
            One or more DOIs, separated by new lines or commas.
          </p>
          <form onSubmit={handleDoiImport} className="mt-4 space-y-4">
            <textarea
              value={doiText}
              onChange={(e) => setDoiText(e.target.value)}
              rows={6}
              placeholder={"10.1038/nature12345\nhttps://doi.org/10.1145/example"}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Import DOIs
            </button>
          </form>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-xl text-slate-900">Import from OpenAlex</h2>
          <p className="mt-2 text-sm text-muted">
            Search OpenAlex and import up to 50 papers sorted by citations.
          </p>
          <form onSubmit={handleOpenAlexImport} className="mt-4 space-y-4">
            <input
              type="text"
              value={openAlexQuery}
              onChange={(e) => setOpenAlexQuery(e.target.value)}
              placeholder="machine learning"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
            />
            <div>
              <label className="text-sm text-slate-700">
                Limit: {openAlexLimit}
              </label>
              <input
                type="range"
                min={1}
                max={50}
                value={openAlexLimit}
                onChange={(e) => setOpenAlexLimit(Number(e.target.value))}
                className="mt-2 w-full accent-brand-600"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {OPENALEX_SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setOpenAlexQuery(s)}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-700"
                >
                  {s}
                </button>
              ))}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              Import from OpenAlex
            </button>
          </form>
        </section>
      </div>

      <section className="mt-10 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-serif text-xl text-slate-900">Extract DOIs from arXiv</h2>
        <p className="mt-2 text-sm text-muted">
          Search arXiv and list DOIs from matching papers. Not every arXiv preprint has a DOI.
        </p>
        <form onSubmit={handleArxivSearch} className="mt-4 space-y-4">
          <input
            type="text"
            value={arxivQuery}
            onChange={(e) => setArxivQuery(e.target.value)}
            placeholder="object detection"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
          <div>
            <label className="text-sm text-slate-700">Papers to fetch: {arxivLimit}</label>
            <input
              type="range"
              min={1}
              max={50}
              value={arxivLimit}
              onChange={(e) => setArxivLimit(Number(e.target.value))}
              className="mt-2 w-full accent-brand-600"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {ARXIV_SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setArxivQuery(s)}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-700"
              >
                {s}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={loading || arxivSearching}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {arxivSearching ? "Searching arXiv…" : "Search arXiv"}
          </button>
        </form>

        {arxivResults && (
          <div className="mt-6 border-t border-slate-100 pt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-slate-700">
                Found {arxivResults.total_results.toLocaleString()} matches. Showing{" "}
                {arxivResults.returned} paper{arxivResults.returned === 1 ? "" : "s"} with{" "}
                {arxivResults.doi_count} DOI{arxivResults.doi_count === 1 ? "" : "s"}.
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleCopyArxivDois}
                  disabled={arxivResults.dois.length === 0}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  Copy DOIs
                </button>
                <button
                  type="button"
                  onClick={handleFillDoiImport}
                  disabled={arxivResults.dois.length === 0}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  Add to DOI import
                </button>
                <button
                  type="button"
                  onClick={handleImportArxivDois}
                  disabled={loading || arxivResults.dois.length === 0}
                  className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  Import DOIs
                </button>
              </div>
            </div>

            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-muted">
                  <tr>
                    <th className="px-4 py-3 font-medium">Title</th>
                    <th className="px-4 py-3 font-medium">arXiv ID</th>
                    <th className="px-4 py-3 font-medium">DOI</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {arxivResults.papers.map((paper) => (
                    <tr key={paper.arxiv_id ?? paper.title}>
                      <td className="px-4 py-3 text-slate-800">{paper.title}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {paper.arxiv_id ? (
                          <a
                            href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-600 hover:underline"
                          >
                            {paper.arxiv_id}
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-slate-600">
                        {paper.doi ? (
                          <a
                            href={`https://doi.org/${paper.doi}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-600 hover:underline"
                          >
                            {paper.doi}
                          </a>
                        ) : (
                          <span className="text-muted">No DOI</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      <section className="mt-10 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-serif text-xl text-slate-900">Manual paper ingest</h2>
        <p className="mt-2 text-sm text-muted">
          Add a custom paper directly to the corpus.
        </p>
        <form onSubmit={handleManualIngest} className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="sm:col-span-2 block text-sm">
            <span className="text-slate-700">Title *</span>
            <input
              value={manualPaper.title}
              onChange={(e) => updateManualField("title", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="sm:col-span-2 block text-sm">
            <span className="text-slate-700">Authors (comma-separated)</span>
            <input
              value={manualPaper.authors}
              onChange={(e) => updateManualField("authors", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="sm:col-span-2 block text-sm">
            <span className="text-slate-700">Abstract</span>
            <textarea
              value={manualPaper.abstract}
              onChange={(e) => updateManualField("abstract", e.target.value)}
              rows={4}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-700">DOI</span>
            <input
              value={manualPaper.doi}
              onChange={(e) => updateManualField("doi", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-700">Year</span>
            <input
              value={manualPaper.year}
              onChange={(e) => updateManualField("year", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-700">Venue</span>
            <input
              value={manualPaper.venue}
              onChange={(e) => updateManualField("venue", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="text-slate-700">Tags (comma-separated)</span>
            <input
              value={manualPaper.tags}
              onChange={(e) => updateManualField("tags", e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </label>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-60"
            >
              Ingest paper
            </button>
          </div>
        </form>
      </section>

      {result ? (
        <ImportSummary result={result} />
      ) : !loading ? (
        <div className="mt-10">
          <EmptyState
            title="No imports yet"
            description="Use the forms above to add papers to the corpus."
          />
        </div>
      ) : null}
    </div>
  );
}
