/* =========================================================
   ENTITIES
========================================================= */

export type Topic = {

  id_topic: string;

  label: string;

};

export type Company = {

  id_company: string;

  name: string;

  media_logo_rectangle_id?: string | null;

};

export type Solution = {

  id_solution: string;

  name: string;

  id_company?: string;

  company_name?: string;

  media_logo_rectangle_id?: string | null;

};

export type Concept = {

  id_concept: string;

  label: string;

};


/* =========================================================
   BADGES
========================================================= */

export type WatchBadgeType =
  | "topic"
  | "company"
  | "solution"
  | "universe"
  | "concept";

export type WatchBadge = {

  id?: string;

  label: string;

  type: WatchBadgeType;

};


/* =========================================================
   ITEM (WATCH)
========================================================= */

export type WatchItem = {

  id: string;

  title: string;

  excerpt?: string | null;

  published_at?: string | null;

  source_title?: string;

  source_url?: string;

  id_primary_company?: string | null;

  primary_company_logo?: string | null;

  topics?: Topic[];

  companies?: Company[];

  solutions?: Solution[];

  concepts?: Concept[];

  badges?: WatchBadge[];

};


/* =========================================================
   CONTENT (DRAWER)
========================================================= */

export type Content = {

  id_content: string;

  title: string;

  title_en?: string;

  excerpt?: string | null;

  excerpt_en?: string | null;

  content_body?: string;

  signal_analytique?: string;

  mecanique_expliquee?: string;

  enjeu_strategique?: string;

  point_de_friction?: string;

  chiffres?: string[];

  acteurs_cites?: string[];

  citations?: string[];

  source_title?: string;

  source_url?: string;

  published_at?: string | null;

  id_primary_company?: string;

  primary_company_logo?: string | null;

  companies?: Company[];

  solutions?: Solution[];

  topics?: Topic[];

  universes?: {

    id_universe: string;

    label: string;

  }[];

  concepts?: Concept[];

  badges?: WatchBadge[];

};


/* =========================================================
   RESPONSE
========================================================= */

export type WatchResponse = {

  items: WatchItem[];

  count: number;

};
