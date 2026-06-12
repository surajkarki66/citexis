import type {
  AuthorPaper,
  ImportResult,
  ManualPaperInput,
  Paper,
  RecommendationResponse,
  SearchRequest,
  SearchResponse,
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

export async function importPdfsSync(files: File[], enrich = true): Promise<ImportResult> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }

  const params = new URLSearchParams({ enrich: String(enrich) });
  const response = await fetch(`${API_BASE}/papers/import/pdf/sync?${params}`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json() as Promise<ImportResult>;
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
