import {
  api,
} from "@/lib/api";

import type {
  TouchResearchBrief,
  TouchSearchResponse,
  TouchSearchResult,
} from "@/types/touch";


/* =========================================================
   TYPES
========================================================= */

export type TouchSearchResponseMode =
  | "full"
  | "analysis"
  | "consolidation";


/* =========================================================
   SEARCH
========================================================= */

export async function searchTouchContents(
  brief: TouchResearchBrief,
  responseMode: TouchSearchResponseMode = "full",
): Promise<TouchSearchResult> {

  const params =
    new URLSearchParams();

  params.set(
    "response_mode",
    responseMode,
  );

  const response:
    TouchSearchResponse =
      await api.post(
        `/touch/search?${params.toString()}`,
        brief,
      );

  return response.search;

}
