"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  ContentFilters,
  ContentSearchResponse,
} from "@/types/content";

/* ========================================================= */

type Props = {
  filters: ContentFilters;
  page: number;
  pageSize?: number;
};

/* ========================================================= */

function cleanFilters(
  filters: ContentFilters,
) {

  return {

    search:
      filters.search || null,

    company_id:
      filters.company_id || null,

    solution_id:
      filters.solution_id || null,

    topic_id:
      filters.topic_id || null,

    concept_id:
      filters.concept_id || null,

    source_id:
      filters.source_id || null,

    date_from:
      filters.date_from || null,

    date_to:
      filters.date_to || null,

    only_numbers:
      filters.only_numbers,

  };

}

/* ========================================================= */

export function useContentSearch({
  filters,
  page,
  pageSize = 100,
}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    result,
    setResult,
  ] = useState<ContentSearchResponse>({
    contents: [],

    total_results: 0,

    total_pages: 1,

    page: 1,

    page_size: pageSize,

    has_next: false,

    has_previous: false,
  });

  /* ======================================================= */

  const search = useCallback(

    async () => {

      try {

        setLoading(true);

        const res =
          await api.post(
            "/content/search",
            {
              filters: cleanFilters(filters),

              page,

              page_size: pageSize,
            }
          );

        setResult({
          contents:
            res.contents || [],

          total_results:
            res.total_results || 0,

          total_pages:
            res.total_pages || 1,

          page:
            res.page || 1,

          page_size:
            res.page_size || pageSize,

          has_next:
            res.has_next || false,

          has_previous:
            res.has_previous || false,
        });

      } catch (e) {

        console.error(
          "Erreur search contents",
          e,
        );

      } finally {

        setLoading(false);

      }

    },

    [
      filters,
      page,
      pageSize,
    ]

  );

  /* ======================================================= */

  useEffect(() => {

    search();

  }, [search]);

  /* ======================================================= */

  return {

    loading,

    refresh: search,

    ...result,

  };

}
