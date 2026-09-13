import {
  api,
} from "@/lib/api";

import type {
  PublicNumberFiltersParams,
  PublicNumberFiltersResponse,
  PublicNumbersResponse,
  PublicNumbersSearchParams,
} from "@/types/numbers";


/* =========================================================
   ADD OPTIONAL PARAMETER
========================================================= */

function addOptionalParameter(
  searchParams: URLSearchParams,
  key: string,
  value?: string | null,
) {

  const normalizedValue = (
    value
    || ""
  ).trim();

  if (!normalizedValue) {
    return;
  }

  searchParams.set(
    key,
    normalizedValue,
  );

}


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
      params.limit
      ?? 50,
    ),
  );

  searchParams.set(
    "offset",
    String(
      params.offset
      ?? 0,
    ),
  );

  addOptionalParameter(
    searchParams,
    "query",
    params.query,
  );

  addOptionalParameter(
    searchParams,
    "universe_id",
    params.universe_id,
  );

  addOptionalParameter(
    searchParams,
    "entity_type",
    params.entity_type,
  );

  addOptionalParameter(
    searchParams,
    "entity_id",
    params.entity_id,
  );

  addOptionalParameter(
    searchParams,
    "company_id",
    params.company_id,
  );

  addOptionalParameter(
    searchParams,
    "solution_id",
    params.solution_id,
  );

  addOptionalParameter(
    searchParams,
    "topic_id",
    params.topic_id,
  );

  addOptionalParameter(
    searchParams,
    "metric_type",
    params.metric_type,
  );

  addOptionalParameter(
    searchParams,
    "zone",
    params.zone,
  );

  addOptionalParameter(
    searchParams,
    "period",
    params.period,
  );

  return api.get(
    (
      "/numbers/public?"
      + searchParams.toString()
    ),
  ) as Promise<PublicNumbersResponse>;

}


/* =========================================================
   GET VALIDATED NUMBER FILTERS
========================================================= */

export async function getValidatedNumberFilters(
  params: PublicNumberFiltersParams,
): Promise<PublicNumberFiltersResponse> {

  const searchParams =
    new URLSearchParams();

  searchParams.set(
    "user_id",
    params.user_id,
  );

  addOptionalParameter(
    searchParams,
    "universe_id",
    params.universe_id,
  );

  addOptionalParameter(
    searchParams,
    "query",
    params.query,
  );

  return api.get(
    (
      "/numbers/public/filters?"
      + searchParams.toString()
    ),
  ) as Promise<PublicNumberFiltersResponse>;

}
