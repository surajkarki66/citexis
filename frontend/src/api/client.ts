import type {
  ArxivSearchResponse,
  AuthorPaper,
  BulkImportAccepted,
  ImportResult,
  ManualPaperInput,
  Paper,
  RecommendationResponse,
  SearchRequest,
  SearchResponse,
  TaskStatus,
  TopicCluster,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function searchPapers(body: SearchRequest): Promise<SearchResponse> {
  return request("/search", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getCorpusStats(): Promise<{ total_papers: number }> {
  return request("/papers/stats");
}

export function getPaper(id: string): Promise<Paper> {
  return request<Record<string, unknown>>(`/papers/${id}`).then((data) => ({
    ...(data as Paper),
    id: String(data.id ?? data._id ?? id),
  }));
}

export function getCitationDois(id: string): Promise<string[]> {
  return request(`/explore/papers/${id}/neighbors`);
}

export function getTopicClusters(tag: string): Promise<TopicCluster[]> {
  return request(`/explore/topics?tag=${encodeURIComponent(tag)}`);
}

export function getAuthorPapers(name: string): Promise<AuthorPaper[]> {
  return request(`/authors/${encodeURIComponent(name)}/papers`);
}

export function importDoiSync(doi: string, enrich = true): Promise<ImportResult> {
  const params = new URLSearchParams({ doi, enrich: String(enrich) });
  return request(`/papers/import/doi/sync?${params}`, { method: "POST" });
}

export function importDoisBulk(dois: string[], enrich = true): Promise<BulkImportAccepted> {
  return request("/papers/import/doi/bulk", {
    method: "POST",
    body: JSON.stringify({ dois, enrich }),
  });
}

export function importOpenAlexSync(
  query: string,
  limit: number,
  enrich = true,
): Promise<ImportResult> {
  const params = new URLSearchParams({
    query,
    limit: String(limit),
    enrich: String(enrich),
  });
  return request(`/papers/import/openalex/sync?${params}`, { method: "POST" });
}

export function importOpenAlexBulk(
  query: string,
  limit: number,
  enrich = true,
): Promise<BulkImportAccepted> {
  const params = new URLSearchParams({
    query,
    limit: String(limit),
    enrich: String(enrich),
  });
  return request(`/papers/import/openalex?${params}`, { method: "POST" });
}

export function searchArxiv(query: string, limit: number): Promise<ArxivSearchResponse> {
  const params = new URLSearchParams({
    query,
    limit: String(limit),
  });
  return request(`/papers/import/arxiv/search?${params}`);
}

export async function importJsonBulk(file: File): Promise<BulkImportAccepted> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE}/papers/import/json`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json() as Promise<BulkImportAccepted>;
}

export function getTaskStatus(taskId: string): Promise<TaskStatus> {
  return request(`/tasks/${encodeURIComponent(taskId)}`);
}

export async function pollImportTask(
  taskId: string,
  onProgress?: (state: string) => void,
): Promise<ImportResult> {
  for (;;) {
    const status = await getTaskStatus(taskId);
    onProgress?.(status.state);

    if (status.ready) {
      if (status.state === "SUCCESS" && status.result) {
        return status.result;
      }
      throw new Error(status.error || `Import task failed (${status.state})`);
    }

    await new Promise((resolve) => {
      setTimeout(resolve, 2000);
    });
  }
}

export type InteractionType = "view" | "save" | "click" | "rating";

export function recordInteraction(body: {
  user_id: string;
  paper_id: string;
  interaction_type: InteractionType;
  rating?: number;
}): Promise<{ id: string; status: string }> {
  return request("/interactions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getSavedPaperIds(userId: string): Promise<string[]> {
  return request<{ user_id: string; paper_ids: string[] }>(
    `/interactions/users/${encodeURIComponent(userId)}/saved`,
  ).then((data) => data.paper_ids);
}

export function getPaperRating(userId: string, paperId: string): Promise<number | null> {
  return request<{ user_id: string; paper_id: string; rating: number | null }>(
    `/interactions/users/${encodeURIComponent(userId)}/papers/${encodeURIComponent(paperId)}/rating`,
  ).then((data) => data.rating);
}

export function unsavePaper(userId: string, paperId: string): Promise<void> {
  return request(`/interactions/users/${encodeURIComponent(userId)}/saved/${encodeURIComponent(paperId)}`, {
    method: "DELETE",
  }).then(() => undefined);
}

export function deletePaper(paperId: string): Promise<{ status: string; paper_id: string }> {
  return request(`/papers/${encodeURIComponent(paperId)}`, { method: "DELETE" });
}

export function getRelatedPapers(paperId: string): Promise<RecommendationResponse> {
  return request(`/papers/${encodeURIComponent(paperId)}/related`);
}

function buildManualPaperBody(input: ManualPaperInput) {
  const authors = input.authors
    .split(",")
    .map((name) => name.trim())
    .filter(Boolean)
    .map((name) => ({ name }));

  const tags = input.tags
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  const year = input.year.trim() ? Number(input.year) : null;

  return {
    title: input.title.trim(),
    authors,
    abstract: input.abstract.trim(),
    doi: input.doi.trim() || null,
    year: Number.isFinite(year) ? year : null,
    venue: input.venue.trim() || null,
    tags,
  };
}

export function importPaperSync(input: ManualPaperInput, enrich = true): Promise<ImportResult> {
  const params = new URLSearchParams({ enrich: String(enrich) });
  return request(`/papers/sync?${params}`, {
    method: "POST",
    body: JSON.stringify(buildManualPaperBody(input)),
  });
}

export async function getSavedPapers(userId: string): Promise<Paper[]> {
  const ids = await getSavedPaperIds(userId);
  const results = await Promise.allSettled(ids.map((id) => getPaper(id)));
  return results
    .filter((result): result is PromiseFulfilledResult<Paper> => result.status === "fulfilled")
    .map((result) => result.value);
}
