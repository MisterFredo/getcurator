// frontend/types/digest.ts

/* =========================================================
   CONTENT
========================================================= */

export type DigestContentItem = {
  id: string;


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

    media_logo_rectangle_id?: string;
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

  universes?: {
    id_universe?: string;

    label?: string;
  }[];

  concepts?: {
    id_concept?: string;

    label?: string;
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
