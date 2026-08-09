// frontend-curator/types/watch.ts

/* =========================================================
   BADGES
========================================================= */

export type WatchBadge = {
  type:
    | "company"
    | "topic"
    | "solution"
    | "concept"
    | "universe";

  id?: string;

  label: string;
};

/* =========================================================
   ITEM
========================================================= */

export type WatchItem = {

  id: string;

  title: string;

  excerpt: string;

  published_at: string | null;

  source_title?: string;

  source_url?: string;

  primary_company_logo?: string | null;

  companies: any[];

  topics: any[];

  solutions: any[];

  concepts: any[];

  badges: WatchBadge[];

};

/* =========================================================
   RESPONSE
========================================================= */

export type WatchResponse = {

  items: WatchItem[];

  count: number;

};

/* =========================================================
   CONTENT (DRAWER)
========================================================= */

export type WatchContent = {

  id_content: string;

  title: string;

  title_en?: string;

  excerpt: string;

  excerpt_en?: string;

  content_body: string;

  signal_analytique?: string;

  mecanique_expliquee?: string;

  enjeu_strategique?: string;

  point_de_friction?: string;

  chiffres?: string[];

  source_title?: string;

  source_url?: string;

  published_at?: string | null;

  id_primary_company?: string;

  companies: any[];

  topics: any[];

  solutions: any[];

  universes: any[];

  concepts: any[];

};
