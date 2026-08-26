import { api } from "@/lib/api";

import type {
  WatchItem,
  Content,
  WatchResponse,
  WatchFiltersResponse,
} from "@/types/watch";

/* ========================================================= */

type WatchParams = {

  user_id: string;

  limit?: number;

  offset?: number;

  period_start?: string | null;

  period_end?: string | null;

  universe_id?: string | null;

  company_id?: string | null;

  solution_id?: string | null;

  topic_id?: string | null;

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

    id_primary_company:
      row.id_primary_company,

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


/* =========================================================
   PARAMS
========================================================= */

function appendWatchParams(
  query: URLSearchParams,
  params: WatchParams,
) {

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

  if (params.period_start) {

    query.append(
      "period_start",
      params.period_start,
    );

  }

  if (params.period_end) {

    query.append(
      "period_end",
      params.period_end,
    );

  }

  if (params.universe_id) {

    query.append(
      "universe_id",
      params.universe_id,
    );

  }

  if (params.company_id) {

    query.append(
      "company_id",
      params.company_id,
    );

  }

  if (params.solution_id) {

    query.append(
      "solution_id",
      params.solution_id,
    );

  }

  if (params.topic_id) {

    query.append(
      "topic_id",
      params.topic_id,
    );

  }

}


/* =========================================================
   LATEST
========================================================= */

export async function watchLatest(
  params: WatchParams,
): Promise<WatchResponse> {

  const query =
    new URLSearchParams();

  appendWatchParams(
    query,
    params,
  );

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

  appendWatchParams(
    query,
    params,
  );

  query.append(
    "query",
    params.query,
  );

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

  return res as Content;

}
