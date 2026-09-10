/* =========================================================
   ENTITY
========================================================= */

export type PublicNumberEntity = {
  entity_type:
    | "company"
    | "topic"
    | "solution";

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

  content: PublicNumberContent;

  entities: PublicNumberEntity[];
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
   RESPONSE
========================================================= */

export type PublicNumbersResponse = {
  status: string;

  items: PublicNumber[];

  pagination: PublicNumbersPagination;
};

/* =========================================================
   SEARCH PARAMETERS
========================================================= */

export type PublicNumbersSearchParams = {
  user_id: string;

  query?: string | null;

  universe_id?: string | null;

  entity_type?:
    | "company"
    | "topic"
    | "solution"
    | null;

  entity_id?: string | null;

  metric_type?: string | null;

  zone?: string | null;
  period?: string | null;

  limit?: number;
  offset?: number;
};
