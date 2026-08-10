// frontend-curator/lib/watch.ts

import { api } from "@/lib/api";

import type {
  WatchItem,
  Content,
  WatchResponse,
} from "@/types/watch";

/* ========================================================= */

type WatchParams = {

  user_id: string;

  limit?: number;

  offset?: number;

  universe_id?: string | null;

};

type SearchParams = WatchParams & {

  query: string;

};

/* ========================================================= */

function mapItem(
  row: any,
): WatchItem {

  return {

    id: row.id,

    title: row.title,

    excerpt: row.excerpt,

    published_at:
      row.published_at,

    source_title:
      row.source_title,

    source_url:
      row.source_url,

    primary_company_logo:
      row.primary_company_logo,

    companies:
      row.companies ?? [],

    topics:
      row.topics ?? [],

    solutions:
      row.solutions ?? [],

    concepts:
      row.concepts ?? [],

    badges:
      row.badges ?? [],

  };

}

/* ========================================================= */

function mapContent(
  row: any,
): Content {

  return {

    id_content:
      row.ID_CONTENT,

    title:
      row.TITLE,

    title_en:
      row.TITLE_EN,

    excerpt:
      row.EXCERPT,

    excerpt_en:
      row.EXCERPT_EN,

    content_body:
      row.CONTENT_BODY,

    signal_analytique:
      row.SIGNAL_ANALYTIQUE,

    mecanique_expliquee:
      row.MECANIQUE_EXPLIQUEE,

    enjeu_strategique:
      row.ENJEU_STRATEGIQUE,

    point_de_friction:
      row.POINT_DE_FRICTION,

    chiffres:
      row.CHIFFRES ?? [],

    source_title:
      row.SOURCE_TITLE,

    source_url:
      row.SOURCE_URL,

    published_at:
      row.PUBLISHED_AT,

    id_primary_company:
      row.ID_PRIMARY_COMPANY,

    companies:
      row.COMPANIES ?? [],

    topics:
      row.TOPICS ?? [],

    solutions:
      row.SOLUTIONS ?? [],

    universes:
      row.UNIVERSES ?? [],

    concepts:
      row.CONCEPTS ?? [],

  };

}

/* =========================================================
   LATEST
========================================================= */

export async function watchLatest(
  params: WatchParams,
): Promise<WatchResponse> {

  const query =
    new URLSearchParams();

  query.append(
    "user_id",
    params.user_id,
  );

  query.append(
    "limit",
    String(
      params.limit ?? 20,
    ),
  );

  query.append(
    "offset",
    String(
      params.offset ?? 0,
    ),
  );

  if (params.universe_id) {

    query.append(
      "universe_id",
      params.universe_id,
    );

  }

  const res =
    await api.get(
      `/watch/latest?${query.toString()}`,
    );

  return {

    items:
      (res.items ?? []).map(
        mapItem,
      ),

    count:
      res.count ?? 0,

  };

}

/* =========================================================
   SEARCH
========================================================= */

export async function watchSearch(
  params: SearchParams,
): Promise<WatchResponse> {

  const query =
    new URLSearchParams();

  query.append(
    "user_id",
    params.user_id,
  );

  query.append(
    "query",
    params.query,
  );

  query.append(
    "limit",
    String(
      params.limit ?? 20,
    ),
  );

  query.append(
    "offset",
    String(
      params.offset ?? 0,
    ),
  );

  if (params.universe_id) {

    query.append(
      "universe_id",
      params.universe_id,
    );

  }

  const res =
    await api.get(
      `/watch/search?${query.toString()}`,
    );

  return {

    items:
      (res.items ?? []).map(
        mapItem,
      ),

    count:
      res.count ?? 0,

  };

}

/* =========================================================
   CONTENT
========================================================= */

export async function getContent(
  contentId: string,
  userId?: string,
): Promise<Content> {

  console.log("GET CONTENT", contentId, userId);

  const query =
    new URLSearchParams();

  if (userId) {

    query.append(
      "user_id",
      userId,
    );

  }

  const res =
    await api.get(
      `/watch/content/${contentId}?${query.toString()}`,
    );

  console.log("API RESPONSE", res);

  return mapContent(
    res,
  );

}
