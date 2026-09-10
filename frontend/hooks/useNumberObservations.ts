"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import type {
  NumberModerationResponse,
  NumberModerationResult,
  NumberObservation,
  NumberObservationsResponse,
  NumberStatus,
} from "@/types/numbers";

/* =========================================================
   CONFIG
========================================================= */

const PAGE_SIZE = 100;

/* =========================================================
   HOOK
========================================================= */

export function useNumberObservations() {

  const [
    status,
    setStatusState,
  ] = useState<NumberStatus>(
    "REVIEW",
  );

  const [
    query,
    setQueryState,
  ] = useState("");

  const [
    offset,
    setOffset,
  ] = useState(0);

  const [
    items,
    setItems,
  ] = useState<NumberObservation[]>(
    [],
  );

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    counts,
    setCounts,
  ] = useState<Record<NumberStatus, number>>({
    ACCEPTED: 0,
    REVIEW: 0,
    REJECTED: 0,
  });

  const [
    selectedIds,
    setSelectedIds,
  ] = useState<Set<string>>(
    new Set(),
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    moderating,
    setModerating,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    lastModeration,
    setLastModeration,
  ] = useState<NumberModerationResult | null>(
    null,
  );

  /* =======================================================
     BUILD URL
  ======================================================= */

  const buildListUrl = useCallback(
    (
      requestedStatus: NumberStatus,
      requestedOffset: number,
      requestedLimit: number,
      requestedQuery?: string,
    ) => {

      const params =
        new URLSearchParams();

      params.set(
        "status",
        requestedStatus,
      );

      params.set(
        "limit",
        String(requestedLimit),
      );

      params.set(
        "offset",
        String(requestedOffset),
      );

      if (
        requestedQuery
        && requestedQuery.trim()
      ) {

        params.set(
          "query",
          requestedQuery.trim(),
        );

      }

      return (
        "/numbers/observations?"
        + params.toString()
      );

    },
    [],
  );

  /* =======================================================
     LOAD COUNTS
  ======================================================= */

  const loadCounts = useCallback(
    async () => {

      const statuses: NumberStatus[] = [
        "ACCEPTED",
        "REVIEW",
        "REJECTED",
      ];

      const responses =
        await Promise.all(
          statuses.map(
            async (
              requestedStatus,
            ) => {

              const response =
                await api.get(
                  buildListUrl(
                    requestedStatus,
                    0,
                    1,
                  ),
                ) as NumberObservationsResponse;

              return {
                status: requestedStatus,
                total: (
                  response.pagination.total
                ),
              };

            },
          ),
        );

      const nextCounts: Record<
        NumberStatus,
        number
      > = {
        ACCEPTED: 0,
        REVIEW: 0,
        REJECTED: 0,
      };

      for (
        const response
        of responses
      ) {

        nextCounts[
          response.status
        ] = response.total;

      }

      setCounts(
        nextCounts,
      );

    },
    [
      buildListUrl,
    ],
  );

  /* =======================================================
     LOAD ITEMS
  ======================================================= */

  const loadItems = useCallback(
    async () => {

      setLoading(true);
      setError(null);

      try {

        const response =
          await api.get(
            buildListUrl(
              status,
              offset,
              PAGE_SIZE,
              query,
            ),
          ) as NumberObservationsResponse;

        setItems(
          response.items,
        );

        setTotal(
          response.pagination.total,
        );

        setSelectedIds(
          new Set(),
        );

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load Number observations.",
        );

      } finally {

        setLoading(false);

      }

    },
    [
      buildListUrl,
      offset,
      query,
      status,
    ],
  );

  /* =======================================================
     FILTERS
  ======================================================= */

  const setStatus = useCallback(
    (
      nextStatus: NumberStatus,
    ) => {

      setStatusState(
        nextStatus,
      );

      setOffset(0);

      setSelectedIds(
        new Set(),
      );

      setLastModeration(
        null,
      );

    },
    [],
  );

  const setQuery = useCallback(
    (
      nextQuery: string,
    ) => {

      setQueryState(
        nextQuery,
      );

      setOffset(0);

      setSelectedIds(
        new Set(),
      );

    },
    [],
  );

  /* =======================================================
     SELECTION
  ======================================================= */

  const toggleSelection = useCallback(
    (
      idNumber: string,
    ) => {

      setSelectedIds(
        (current) => {

          const next =
            new Set(current);

          if (
            next.has(idNumber)
          ) {

            next.delete(
              idNumber,
            );

          } else {

            next.add(
              idNumber,
            );

          }

          return next;

        },
      );

    },
    [],
  );

  const selectAllPage = useCallback(
    () => {

      setSelectedIds(
        new Set(
          items.map(
            (item) =>
              item.id_number,
          ),
        ),
      );

    },
    [
      items,
    ],
  );

  const clearSelection = useCallback(
    () => {

      setSelectedIds(
        new Set(),
      );

    },
    [],
  );

  const allPageSelected =
    useMemo(
      () => {

        return (
          items.length > 0

          && items.every(
            (item) =>
              selectedIds.has(
                item.id_number,
              ),
          )
        );

      },
      [
        items,
        selectedIds,
      ],
    );

  /* =======================================================
     MODERATION
  ======================================================= */

  const applyDecision = useCallback(
    async (
      decision: NumberStatus,
    ) => {

      const ids =
        Array.from(
          selectedIds,
        );

      if (!ids.length) {
        return null;
      }

      setModerating(true);
      setError(null);

      try {

        const response =
          await api.post(
            "/numbers/observations/decisions",
            {
              ids,
              decision,
            },
          ) as NumberModerationResponse;

        setLastModeration(
          response.result,
        );

        await Promise.all([
          loadItems(),
          loadCounts(),
        ]);

        return response.result;

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to moderate Numbers.",
        );

        return null;

      } finally {

        setModerating(false);

      }

    },
    [
      loadCounts,
      loadItems,
      selectedIds,
    ],
  );

  /* =======================================================
     PAGINATION
  ======================================================= */

  const previousPage = useCallback(
    () => {

      setOffset(
        (current) =>
          Math.max(
            0,
            current - PAGE_SIZE,
          ),
      );

    },
    [],
  );

  const nextPage = useCallback(
    () => {

      setOffset(
        (current) =>
          current + PAGE_SIZE,
      );

    },
    [],
  );

  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(
    () => {

      loadItems();

    },
    [
      loadItems,
    ],
  );

  useEffect(
    () => {

      loadCounts().catch(
        () => {
          // The main list still remains usable
          // if one counter request fails.
        },
      );

    },
    [
      loadCounts,
    ],
  );

  return {
    status,
    query,
    offset,

    items,
    total,
    counts,

    selectedIds,
    selectedCount:
      selectedIds.size,

    allPageSelected,

    loading,
    moderating,
    error,
    lastModeration,

    pageSize: PAGE_SIZE,

    setStatus,
    setQuery,

    toggleSelection,
    selectAllPage,
    clearSelection,

    applyDecision,

    previousPage,
    nextPage,

    reload: async () => {

      await Promise.all([
        loadItems(),
        loadCounts(),
      ]);

    },
  };
}
