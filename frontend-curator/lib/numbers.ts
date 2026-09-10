import {
  api,
} from "@/lib/api";

import type {
  PublicNumbersResponse,
  PublicNumbersSearchParams,
} from "@/types/numbers";

/* =========================================================
   SEARCH VALIDATED NUMBERS
========================================================= */

export async function searchValidatedNumbers(
  params: PublicNumbersSearchParams,
): Promise<PublicNumbersResponse> {

  const searchParams =
    new URLSearchParams();

  searchParams.set(
    "user_id",
    params.user_id,
  );

  searchParams.set(
    "limit",
    String(
      params.limit ?? 20,
    ),
  );

  searchParams.set(
    "offset",
    String(
      params.offset ?? 0,
    ),
  );

  if (
    params.query
    && params.query.trim()
  ) {

    searchParams.set(
      "query",
      params.query.trim(),
    );

  }

  if (params.universe_id) {

    searchParams.set(
      "universe_id",
      params.universe_id,
    );

  }

  if (
    params.entity_type
    && params.entity_id
  ) {

    searchParams.set(
      "entity_type",
      params.entity_type,
    );

    searchParams.set(
      "entity_id",
      params.entity_id,
    );

  }

  if (params.metric_type) {

    searchParams.set(
      "metric_type",
      params.metric_type,
    );

  }

  if (params.zone) {

    searchParams.set(
      "zone",
      params.zone,
    );

  }

  if (params.period) {

    searchParams.set(
      "period",
      params.period,
    );

  }

  return api.get(
    (
      "/numbers/public?"
      + searchParams.toString()
    ),
  ) as Promise<PublicNumbersResponse>;
}
