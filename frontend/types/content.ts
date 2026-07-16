// frontend/types/content.ts

/* ========================================================= */

export type ContentFilters = {
  search: string;

  company_id: string;
  solution_id: string;
  topic_id: string;
  concept_id: string;
  source_id: string;

  date_from: string;
  date_to: string;

  only_numbers: boolean;
};

/* ========================================================= */

export const EMPTY_CONTENT_FILTERS: ContentFilters = {
  search: "",

  company_id: "",
  solution_id: "",
  topic_id: "",
  concept_id: "",
  source_id: "",

  date_from: "",
  date_to: "",

  only_numbers: false,
};

/* ========================================================= */

export type ContentRow = {
  id_content: string;

  title: string | null;

  source_title: string | null;

  source_date: string | null;

  published_at: string | null;
};

/* ========================================================= */

export type ContentSearchResponse = {
  contents: ContentRow[];

  total_results: number;

  page: number;

  page_size: number;

  total_pages: number;

  has_next: boolean;

  has_previous: boolean;
};
