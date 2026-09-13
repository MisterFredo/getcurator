/* =========================================================
   ENTITY
========================================================= */

export type PublicNumberEntityType =
  | "company"
  | "topic"
  | "solution";


export type PublicNumberEntity = {

  entity_type:
    PublicNumberEntityType;

  entity_id: string;

  entity_label: string;

};


/* =========================================================
   CONTENT
========================================================= */

export type PublicNumberContent = {

  id: string;

  title: string | null;

  excerpt: string | null;

};


/* =========================================================
   NUMBER
========================================================= */

export type PublicNumber = {

  id_number: string;

  id_content: string;

  label: string;

  metric_type: string;

  value: number | null;

  value_min: number | null;

  value_max: number | null;

  unit: string;

  scale: string;

  zone: string;

  period_label: string;

  value_status: string;

  confidence: number;

  published_at: string | null;

  content:
    PublicNumberContent;

  entities:
    PublicNumberEntity[];

};


/* =========================================================
   PAGINATION
========================================================= */

export type PublicNumbersPagination = {

  total: number;

  limit: number;

  offset: number;

  has_more: boolean;

};


/* =========================================================
   SEARCH RESPONSE
========================================================= */

export type PublicNumbersResponse = {

  status: string;

  items: PublicNumber[];

  pagination:
    PublicNumbersPagination;

};


/* =========================================================
   SEARCH PARAMETERS
========================================================= */

export type PublicNumbersSearchParams = {

  user_id: string;

  query?: string | null;

  universe_id?: string | null;

  entity_type?:
    | PublicNumberEntityType
    | null;

  entity_id?: string | null;

  company_id?: string | null;

  solution_id?: string | null;

  topic_id?: string | null;

  metric_type?: string | null;

  zone?: string | null;

  period?: string | null;

  limit?: number;

  offset?: number;

};


/* =========================================================
   FILTER OPTION
========================================================= */

export type PublicNumberFilterOption = {

  value: string;

  label: string;

  count: number;

};


/* =========================================================
   FILTERS
========================================================= */

export type PublicNumberFilters = {

  metric_types:
    PublicNumberFilterOption[];

  zones:
    PublicNumberFilterOption[];

  companies:
    PublicNumberFilterOption[];

  solutions:
    PublicNumberFilterOption[];

  topics:
    PublicNumberFilterOption[];

};


/* =========================================================
   FILTERS RESPONSE
========================================================= */

export type PublicNumberFiltersResponse = {

  status: string;

  filters:
    PublicNumberFilters;

};


/* =========================================================
   FILTER PARAMETERS
========================================================= */

export type PublicNumberFiltersParams = {

  user_id: string;

  universe_id?: string | null;

  query?: string | null;

};
