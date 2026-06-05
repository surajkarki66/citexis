export interface PaperSummary {
  id: string;
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  abstract_snippet: string | null;
}

export interface SearchFilters {
  year_min?: number | null;
  year_max?: number | null;
  tags?: string[];
  venue?: string | null;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  top_k?: number;
}

export interface SearchResult {
  paper: PaperSummary;
  score: number;
  source: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface Author {
  name: string;
  affiliation: string | null;
  orcid: string | null;
}

export interface PaperRecommendation {
  paper: PaperSummary;
  reason: string;
  score: number;
}

export interface Paper {
  id: string;
  doi: string | null;
  title: string;
  authors: Author[];
  abstract: string;
  year: number | null;
  venue: string | null;
  citations: string[];
  cited_by_count: number;
  tags: string[];
  full_text_url: string | null;
  embedding_status: string;
  recommendations: PaperRecommendation[];
}

export interface TopicCluster {
  venue: string;
  count: number;
  sample_titles: string[];
}

export interface AuthorPaper {
  id: string;
  title: string;
  year: number | null;
  venue: string | null;
}
