export const dynamic = "force-dynamic";

import HomeClient from "./HomeClient";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/* =========================================================
   SAFE FETCH
========================================================= */
async function safeFetch<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    throw new Error(`Fetch error: ${url}`);
  }

  return res.json();
}

/* =========================================================
   PAGE — HOME RATECARD
========================================================= */
export default async function HomePage() {
  /* -------------------------------------------------------
     NEWS — FLUX PUBLIC RATECARD
  ------------------------------------------------------- */
  const newsRaw = await safeFetch<{ news: any[] }>(
    `${API_BASE}/news/list`
  );

  const news = newsRaw.news.map((n) => ({
    id: n.ID_NEWS,
    title: n.TITLE,
    excerpt: n.EXCERPT ?? null,

    visual_rect_id: n.VISUAL_RECT_ID ?? null,
    published_at: n.PUBLISHED_AT,

    // 🔑 STRUCTURE ÉDITORIALE — OBLIGATOIRE
    news_kind: n.NEWS_KIND as "NEWS" | "BRIEF",

    company: n.ID_COMPANY
      ? {
          id_company: n.ID_COMPANY,
          name: n.COMPANY_NAME,
          media_logo_rectangle_id:
            n.MEDIA_LOGO_RECTANGLE_ID ?? null,
          is_partner: n.IS_PARTNER === true,
        }
      : undefined,
  }));

  /* -------------------------------------------------------
     ANALYSES — FLUX PUBLIC (TEASING)
     ⚠️ API PUBLIQUE UNIQUEMENT
     see: backend/api/public/routes.py
  ------------------------------------------------------- */
  let analyses: any[] = [];

  try {
    const analysesRaw = await safeFetch<{ items: any[] }>(
      `${API_BASE}/public/analysis/list`
    );

    analyses = analysesRaw.items.map((a) => ({
      id: a.id,
      title: a.title,
      excerpt: a.excerpt ?? null,
      published_at: a.published_at,
      topics: a.topics ?? [],
      key_metrics: a.key_metrics ?? [],
      event: a.event,
    }));
  } catch (e) {
    // ⚠️ Non bloquant : la home doit rester fonctionnelle
    console.error("Analyses fetch failed", e);
  }

  /* -------------------------------------------------------
     RENDER
  ------------------------------------------------------- */
  return (
    <HomeClient
      news={news}
      analyses={analyses}
    />
  );
}
