/* =========================================================
   BADGES (UI LAYER)
========================================================= */

export type FeedBadgeType =
  | "topic"
  | "company"
  | "solution"
  | "news_type"
  | "universe"
  | "concept"; // 🔥 ajout propre

export type FeedBadge = {
  id?: string;
  label: string;
  type: FeedBadgeType;
};


/* =========================================================
   ENTITIES
========================================================= */

export type Topic = {
  id_topic: string;
  label: string;

  axis?: string;

  nb_analyses?: number;
  delta_30d?: number;
};

export type Company = {
  id_company: string;
  name: string;

  media_logo_rectangle_id?: string | null;

  logo_type?: "company";

  is_partner?: boolean;

  nb_analyses?: number;
  delta_30d?: number;
};

export type Solution = {
  id_solution: string;
  name: string;

  id_company?: string;
  company_name?: string;

  media_logo_rectangle_id?: string | null;

  logo_type?: "solution" | "company";

  is_partner?: boolean;

  nb_analyses?: number;
  delta_30d?: number;
};

/* =========================================================
   🔥 NEW — CONCEPT (ALIGNÉ BACKEND)
========================================================= */

export type Concept = {
  id_concept: string;
  title: string;
};


/* =========================================================
   ITEM (ALIGNÉ SEARCH BACKEND)
========================================================= */

export type FeedItem = {
  id: string;

  type: "news" | "analysis";

  title: string;
  excerpt?: string | null;
  published_at?: string | null;

  universes?: {
    id_universe: string;
    label: string;
  }[];

  topics?: Topic[];
  companies?: Company[];
  solutions?: Solution[];

  // 🔥 NEW
  concepts?: Concept[];

  news_type?: string | null;

  has_visual?: boolean;
  media_id?: string | null;

  badges?: FeedBadge[];
};


/* =========================================================
   META
========================================================= */

export type MetaItem = {
  id: string;
  label: string;
  count: number;
};

export type FeedMetaResponse = {
  topics: MetaItem[];
  companies: MetaItem[];
  solutions: MetaItem[];
  news_types: MetaItem[];
};


/* =========================================================
   RESPONSE
========================================================= */

export type FeedResponse = {
  items: FeedItem[];
  count: number;
};
