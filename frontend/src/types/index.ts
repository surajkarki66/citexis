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

export interface TopicClusterPaper {
  id: string;
  title: string;
}

export interface TopicCluster {
  tag: string;
  count: number;
  papers: TopicClusterPaper[];
}

export interface AuthorPaper {
  id: string;
  title: string;
  year: number | null;
  venue: string | null;
}


export interface ArxivPaperResult {
  arxiv_id: string | null;
  title: string;
  authors: string[];
  doi: string | null;
  year: number | null;
}

export interface ArxivSearchResponse {
  query: string;
  arxiv_query: string;
  total_results: number;
  returned: number;
  doi_count: number;
  dois: string[];
  papers: ArxivPaperResult[];
}

export interface ImportResult {
  status: string;
  imported: number;
  skipped: number;
  failed: number;
  paper_ids: string[];
  skipped_items: string[];
  failed_items: string[];
  failed_reasons: string[];
}

export interface BulkImportAccepted {
  status: string;
  task_id: string;
  source: string;
  queued: number;
}

export interface TaskStatus {
  task_id: string;
  state: string;
  ready: boolean;
  result?: ImportResult;
  error?: string;
}

export interface RecommendationResponse {
  paper_id: string;
  items: PaperRecommendation[];
}

export interface ManualPaperInput {
  title: string;
  authors: string;
  abstract: string;
  doi: string;
  year: string;
  venue: string;
  tags: string;
}
