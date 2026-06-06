import type { ImportResult } from "../types";

export function normalizeDoi(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) return "";

  const withoutUrl = trimmed
    .replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "")
    .replace(/^doi:/i, "");

  return withoutUrl.trim();
}

export function parseDoiList(text: string): string[] {
  const seen = new Set<string>();
  const dois: string[] = [];

  for (const line of text.split(/\r?\n/)) {
    for (const part of line.split(/[,;]/)) {
      const doi = normalizeDoi(part);
      if (doi && !seen.has(doi)) {
        seen.add(doi);
        dois.push(doi);
      }
    }
  }

  return dois;
}

export function emptyImportResult(): ImportResult {
  return {
    status: "completed",
    imported: 0,
    skipped: 0,
    failed: 0,
    paper_ids: [],
    skipped_items: [],
    failed_items: [],
    failed_reasons: [],
  };
}

export function mergeImportResults(results: ImportResult[]): ImportResult {
  return results.reduce(
    (acc, result) => ({
      status: "completed",
      imported: acc.imported + result.imported,
      skipped: acc.skipped + result.skipped,
      failed: acc.failed + result.failed,
      paper_ids: [...acc.paper_ids, ...result.paper_ids],
      skipped_items: [...acc.skipped_items, ...result.skipped_items],
      failed_items: [...acc.failed_items, ...result.failed_items],
      failed_reasons: [...acc.failed_reasons, ...result.failed_reasons],
    }),
    emptyImportResult(),
  );
}
