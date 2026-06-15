import { api } from "@/lib/api";
import type { FeedItem, FeedResponse } from "@/types/feed";

/* ========================================================= */

type Params = {
  query?: string;
  limit?: number;
  offset?: number;

  // 🔥 NEW
  content_type?: "NEWS" | "ANALYSIS";

  // 🔥 EXISTANT
  user_id?: string;
  universe_id?: string | null;

  // 🔥 NEW (FIX)
  feed_mode?:
    | "all"
    | "mine"
    | "keywords";
};

/* ========================================================= */

function mapItem(row: any): FeedItem {
  return {
    id: row.id,

    type: row.type,

    // 🔥 PRIMARY COMPANY
    id_primary_company:
      row.id_primary_company,

    primary_company_name:
      row.primary_company_name,

    primary_company_logo:
      row.primary_company_logo,

    title: row.title,
    title_en: row.title_en,

    excerpt: row.excerpt,
    excerpt_en: row.excerpt_en,

    // 🔥 NEW
    content_body:
      row.content_body,

    published_at:
      row.published_at,

    topics: row.topics,

    companies: row.companies,

    solutions: row.solutions,

    concepts: row.concepts,

    badges: row.badges,

    news_type:
      row.news_type,
  };
}

/* ========================================================= */
// SEARCH
/* ========================================================= */

export async function searchCurator(
  params: Params
): Promise<FeedResponse> {
  try {
    const query = new URLSearchParams();

    if (params.query) {
      query.append("q", params.query.trim());
    }

    query.append(
      "limit",
      String(params.limit ?? 20)
    );

    query.append(
      "offset",
      String(params.offset ?? 0)
    );

    // 🔥 CONTENT TYPE
    if (params.content_type) {
      query.append(
        "content_type",
        params.content_type
      );
    }

    // 🔥 USER
    if (params.user_id) {
      query.append(
        "user_id",
        params.user_id
      );
    }

    // 🔥 UNIVERSE
    if (params.universe_id) {
      query.append(
        "universe_id",
        params.universe_id
      );
    }

    // 🔥 NEW (FIX)
    if (params.feed_mode) {
      query.append(
        "feed_mode",
        params.feed_mode
      );
    }

    const res = await api.get(
      `/curator/search?${query.toString()}`
    );

    const data = res?.data ?? res;

    if (
      !data ||
      !Array.isArray(data.items)
    ) {
      return {
        items: [],
        count: 0,
      };
    }

    return {
      items: data.items.map(mapItem),
      count: data.count ?? 0,
    };

  } catch (e) {

    console.error(
      "❌ searchCurator error",
      e
    );

    return {
      items: [],
      count: 0,
    };
  }
}

/* ========================================================= */
// LATEST
/* ========================================================= */

export async function getLatestCurator(
  params?: Params
): Promise<FeedResponse> {
  try {
    const query = new URLSearchParams();

    query.append(
      "limit",
      String(params?.limit ?? 20)
    );

    query.append(
      "offset",
      String(params?.offset ?? 0)
    );

    // 🔥 CONTENT TYPE
    if (params?.content_type) {
      query.append(
        "content_type",
        params.content_type
      );
    }

    // 🔥 USER
    if (params?.user_id) {
      query.append(
        "user_id",
        params.user_id
      );
    }

    // 🔥 UNIVERSE
    if (params?.universe_id) {
      query.append(
        "universe_id",
        params.universe_id
      );
    }

    // 🔥 NEW (FIX)
    if (params?.feed_mode) {
      query.append(
        "feed_mode",
        params.feed_mode
      );
    }

    const res = await api.get(
      `/curator/latest?${query.toString()}`
    );

    const data = res?.data ?? res;

    if (
      !data ||
      !Array.isArray(data.items)
    ) {
      return {
        items: [],
        count: 0,
      };
    }

    return {
      items: data.items.map(mapItem),
      count: data.count ?? 0,
    };

  } catch (e) {

    console.error(
      "❌ latestCurator error",
      e
    );

    return {
      items: [],
      count: 0,
    };
  }
}
