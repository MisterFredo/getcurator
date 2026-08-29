"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  searchAdminDigests,
} from "@/lib/digest";

import type {
  AdminDigestSearchFilters,
  DigestHistoryItem,
} from "@/types/digest";

import DigestFilters from "@/components/digest/DigestFilters";
import DigestList from "@/components/digest/AdminDigestList";
import DigestPagination from "@/components/digest/DigestPagination";


/* =========================================================
   CONFIGURATION
========================================================= */

const DEFAULT_LIMIT = 50;

const SEARCH_DELAY_MS = 350;


/* =========================================================
   COMPONENT
========================================================= */

export default function DigestPage() {

  const [
    digests,
    setDigests,
  ] = useState<
    DigestHistoryItem[]
  >([]);

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    filters,
    setFilters,
  ] = useState<
    AdminDigestSearchFilters
  >({

    query: "",

    audience:
      undefined,

    status:
      undefined,

    period_start:
      undefined,

    period_end:
      undefined,

    limit:
      DEFAULT_LIMIT,

    offset:
      0,

  });

  const [
    debouncedQuery,
    setDebouncedQuery,
  ] = useState("");

  const requestIdRef =
    useRef(0);


  /* =========================================================
     DEBOUNCE SEARCH
  ========================================================= */

  useEffect(() => {

    const timeoutId =
      window.setTimeout(
        () => {

          setDebouncedQuery(
            filters.query?.trim()
            ?? "",
          );

        },
        SEARCH_DELAY_MS,
      );

    return () => {

      window.clearTimeout(
        timeoutId,
      );

    };

  }, [
    filters.query,
  ]);


  /* =========================================================
     LOAD
  ========================================================= */

  const load =
    useCallback(
      async () => {

        const requestId =
          requestIdRef.current + 1;

        requestIdRef.current =
          requestId;

        setLoading(
          true,
        );

        setError(
          null,
        );

        try {

          const result =
            await searchAdminDigests({

              query:
                debouncedQuery
                || undefined,

              audience:
                filters.audience,

              status:
                filters.status,

              campaign_id:
                filters.campaign_id,

              period_start:
                filters.period_start,

              period_end:
                filters.period_end,

              limit:
                filters.limit
                ?? DEFAULT_LIMIT,

              offset:
                filters.offset
                ?? 0,

            });

          if (
            requestId
            !== requestIdRef.current
          ) {

            return;

          }

          const currentOffset =
            filters.offset
            ?? 0;

          const currentLimit =
            filters.limit
            ?? DEFAULT_LIMIT;

          /*
           * When the last item of the current page
           * has been deleted, return to the previous
           * available page.
           */

          if (
            result.items.length === 0
            && result.total > 0
            && currentOffset >= result.total
          ) {

            setFilters(
              (
                current,
              ) => ({

                ...current,

                offset:
                  Math.max(
                    0,
                    currentOffset
                    - currentLimit,
                  ),

              }),
            );

            return;

          }

          setDigests(
            result.items,
          );

          setTotal(
            result.total,
          );

        } catch (loadError) {

          if (
            requestId
            !== requestIdRef.current
          ) {

            return;

          }

          console.error(
            "Unable to load Digests",
            loadError,
          );

          setError(
            "Unable to load Digests.",
          );

        } finally {

          if (
            requestId
            === requestIdRef.current
          ) {

            setLoading(
              false,
            );

          }

        }

      },
      [
        debouncedQuery,
        filters.audience,
        filters.status,
        filters.campaign_id,
        filters.period_start,
        filters.period_end,
        filters.limit,
        filters.offset,
      ],
    );


  /* =========================================================
     INITIAL LOAD + FILTER CHANGES
  ========================================================= */

  useEffect(() => {

    load();

  }, [
    load,
  ]);


  /* =========================================================
     FILTER CHANGE
  ========================================================= */

  function handleFiltersChange(
    nextFilters: AdminDigestSearchFilters,
  ) {

    setFilters(
      nextFilters,
    );

  }


  /* =========================================================
     PAGINATION
  ========================================================= */

  function handlePageChange(
    offset: number,
  ) {

    setFilters(
      (
        current,
      ) => ({

        ...current,

        offset,

      }),
    );

    window.scrollTo({

      top: 0,

      behavior:
        "smooth",

    });

  }


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="space-y-6">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div
        className="
          flex
          flex-col
          gap-3
          sm:flex-row
          sm:items-end
          sm:justify-between
        "
      >

        <div>

          <h1
            className="
              text-2xl
              font-bold
              text-gray-900
            "
          >
            Digests
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-gray-500
            "
          >
            Search, generate, preview, send and manage
            individual Digests.
          </p>

        </div>

        {!loading && (

          <div
            className="
              text-sm
              text-gray-500
            "
          >

            <span
              className="
                font-semibold
                text-gray-900
              "
            >
              {total}
            </span>

            {" "}

            {total === 1
              ? "Digest"
              : "Digests"}

          </div>

        )}

      </div>


      {/* =================================================== */}
      {/* FILTERS */}
      {/* =================================================== */}

      <DigestFilters

        filters={
          filters
        }

        onChange={
          handleFiltersChange
        }

      />


      {/* =================================================== */}
      {/* ERROR */}
      {/* =================================================== */}

      {error && (

        <div
          className="
            flex
            items-center
            justify-between
            gap-4
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-4
            py-3
          "
        >

          <span
            className="
              text-sm
              text-red-700
            "
          >
            {error}
          </span>

          <button
            type="button"
            onClick={
              load
            }
            className="
              rounded-md
              border
              border-red-200
              bg-white
              px-3
              py-1.5
              text-sm
              font-medium
              text-red-700
              transition
              hover:bg-red-100
            "
          >
            Retry
          </button>

        </div>

      )}


      {/* =================================================== */}
      {/* DIGESTS */}
      {/* =================================================== */}

      <AdminDigestList

        digests={
          digests
        }

        loading={
          loading
        }

        onChanged={
          load
        }

      />


      {/* =================================================== */}
      {/* PAGINATION */}
      {/* =================================================== */}

      <DigestPagination

        total={
          total
        }

        limit={
          filters.limit
          ?? DEFAULT_LIMIT
        }

        offset={
          filters.offset
          ?? 0
        }

        loading={
          loading
        }

        onChange={
          handlePageChange
        }

      />

    </div>

  );

}
