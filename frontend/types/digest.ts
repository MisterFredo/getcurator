// frontend/types/digest.ts

/* =========================================================
   CONTENT
========================================================= */

export type DigestContentItem = {
  id: string;

  /* ===============================
     CONTENT TYPE
  =============================== */

  content_type?:
    | "news"
    | "analysis";

  /* ===============================
     CONTENT
  =============================== */

  title: string;

  excerpt?: string;

  published_at?: string;

  url?: string;

  /* ===============================
     VISUALS
  =============================== */

  media_id?: string | null;

  primary_company_logo?: string | null;

  /* ===============================
     ENTITIES
  =============================== */

  companies?: {
    id_company: string;

    name: string;

    is_partner?: boolean;
  }[];

  solutions?: {
    id_solution: string;

    name: string;
  }[];

  topics?: {
    id_topic?: string;

    label?: string;

    LABEL?: string;
  }[];

  /* ===============================
     OPTIONAL UI
  =============================== */

  styles?: string[];
};

/* =========================================================
   EDITORIAL FLOW
========================================================= */

export type DigestEditorialItem = {
  id: string;

  type:
    | "content";
};
