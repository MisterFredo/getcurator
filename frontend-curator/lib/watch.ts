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
      row.id_content,

    title:
      row.title,

    title_en:
      row.title_en,

    excerpt:
      row.excerpt,

    excerpt_en:
      row.excerpt_en,

    content_body:
      row.content_body,

    signal_analytique:
      row.signal_analytique,

    mecanique_expliquee:
      row.mecanique_expliquee,

    enjeu_strategique:
      row.enjeu_strategique,

    point_de_friction:
      row.point_de_friction,

    chiffres:
      row.chiffres ?? [],

    source_title:
      row.source_title,

    source_url:
      row.source_url,

    published_at:
      row.published_at,

    id_primary_company:
      row.id_primary_company,

    companies:
      row.companies ?? [],

    topics:
      row.topics ?? [],

    solutions:
      row.solutions ?? [],

    universes:
      row.universes ?? [],

    concepts:
      row.concepts ?? [],

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
