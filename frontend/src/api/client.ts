import type {
  AuthorPaper,
  Paper,
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
  return request(`/papers/${id}`);
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

export function importDoiSync(doi: string): Promise<Record<string, unknown>> {
  return request(`/papers/import/doi/sync?doi=${encodeURIComponent(doi)}`, {
    method: "POST",
  });
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

export function unsavePaper(userId: string, paperId: string): Promise<void> {
  return request(`/interactions/users/${encodeURIComponent(userId)}/saved/${encodeURIComponent(paperId)}`, {
    method: "DELETE",
  }).then(() => undefined);
}
