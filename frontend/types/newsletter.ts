// frontend/types/newsletter.ts

/* =========================================================
   NEWS
========================================================= */

export type NewsletterNewsItem = {
  id: string;

  title: string;

  excerpt?: string;

  published_at: string;

  news_type?: string;

  news_kind?: string;

  visual_rect_id?: string | null;

  company_visual_rect_id?: string | null;

  company?: {
    id_company: string;

    name: string;

    is_partner: boolean;
  };

  topics?: {
    id_topic?: string;

    label?: string;

    LABEL?: string;
  }[];
};

/* =========================================================
   HEADER
========================================================= */

export type HeaderCompany = {
  id_company: string;

  name: string;

  media_logo_rectangle_id?: string | null;
};

export type HeaderConfig = {
  title: string;

  subtitle?: string;

  period?: string;

  headerCompany?: HeaderCompany;

  /* ===============================
     VARIANT
  =============================== */

  variant?: "media" | "consulting";

  /* ===============================
     TOP BAR
  =============================== */

  topBarEnabled?: boolean;

  topBarColor?: string;

  /* ===============================
     COLORS
  =============================== */

  periodColor?: string;

  /* ===============================
     EDITORIAL
  =============================== */

  introHtml?: string;

  /* ===============================
     EVENT
  =============================== */

  eventId?: string;

  /* ===============================
     HERO
  =============================== */

  showHero?: boolean;

  heroLink?: string;

  heroImageUrl?: string;

  /* ===============================
     LOGO
  =============================== */

  showLogo?: boolean;

  logoLink?: string;
};

/* =========================================================
   STATS
========================================================= */

export type TopicStat = {
  label: string;

  last_30_days: number;

  total: number;
};
