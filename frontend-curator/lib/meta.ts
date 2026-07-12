// frontend-curator/lib/meta.ts

import { api } from "@/lib/api";
import type { FeedMetaResponse, MetaItem } from "@/types/feed";

/* ========================================================= */

function safeArray(value: any): MetaItem[] {
  if (!Array.isArray(value)) return [];

  return value
    .map((v) => ({
      id: String(v?.id ?? ""),
      label: String(v?.label ?? ""),
      count: Number(v?.count ?? 0),
    }))
    .filter((v) => v.id && v.label); // 🔥 évite lignes cassées
}

/* ========================================================= */

export async function getFeedMeta(): Promise<FeedMetaResponse> {
  try {
    const res = await api.get("/curator/meta");

    const data = res?.data ?? res;

    // 🔒 sécurité structure globale
    if (!data || typeof data !== "object") {
      console.warn("⚠️ getFeedMeta: invalid response", data);
      return {
        topics: [],
        companies: [],
        solutions: [],
      };
    }

    return {
      topics: safeArray(data.topics),
      companies: safeArray(data.companies),
      solutions: safeArray(data.solutions),
    };

  } catch (e) {
    console.error("❌ getFeedMeta error", e);

    return {
      topics: [],
      companies: [],
      solutions: [],
    };
  }
}
