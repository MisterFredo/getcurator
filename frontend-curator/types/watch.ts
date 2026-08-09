/* =========================================================
   REUSE FEED ENTITIES
========================================================= */

import type {
  Topic,
  Company,
  Solution,
  Concept,
} from "./feed";

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
   ITEM (WATCH LIST)
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

export type WatchContent = {

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

  source_title?: string;

  source_url?: string;

  published_at?: string | null;

  id_primary_company?: string;

  companies?: Company[];

  solutions?: Solution[];

  topics?: Topic[];

  universes?: {

    id_universe: string;

    label: string;

  }[];

  concepts?: Concept[];

};


/* =========================================================
   RESPONSE
========================================================= */

export type WatchResponse = {

  items: WatchItem[];

  count: number;

};
