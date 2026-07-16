"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  ContentFilters,
  ContentRow,
} from "@/types/content";

/* ========================================================= */

type SearchResult = {
  contents: ContentRow[];

  total_results: number;

  total_pages: number;

  page: number;

  page_size: number;

  has_next: boolean;

  has_previous: boolean;
};

/* ========================================================= */

export function useContentSearch(

  filters: ContentFilters,

  page: number,

  pageSize = 100,

) {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    result,
    setResult,
  ] = useState<SearchResult>({
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
              filters,

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
