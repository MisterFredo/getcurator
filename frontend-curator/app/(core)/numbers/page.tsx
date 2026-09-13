"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import {
  getValidatedNumberFilters,
  searchValidatedNumbers,
} from "@/lib/numbers";

import {
  useUser,
} from "@/hooks/useUser";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import NumbersExplorerFilters from "@/components/numbers/explorer/NumbersExplorerFilters";
import NumbersExplorerPagination from "@/components/numbers/explorer/NumbersExplorerPagination";
import NumbersExplorerTable from "@/components/numbers/explorer/NumbersExplorerTable";

import type {
  NumbersExplorerFilterState,
} from "@/components/numbers/explorer/NumbersExplorerFilters";

import type {
  PublicNumber,
  PublicNumberFilters,
  PublicNumbersPagination,
} from "@/types/numbers";


/* ============================================================
   TYPES
============================================================ */

type Universe = {

  id_universe: string;

  label: string;

};


/* ============================================================
   CONFIG
============================================================ */

const PAGE_SIZE = 50;

const INITIAL_FILTER_STATE:
  NumbersExplorerFilterState = {

    universeId: "",

    metricType: "",

    year: "",

    zone: "",

    valueStatus: "",

  };

const INITIAL_PAGINATION:
  PublicNumbersPagination = {

    total: 0,

    limit: PAGE_SIZE,

    offset: 0,

    has_more: false,

  };


/* ============================================================
   PAGE
============================================================ */

export default function NumbersPage() {

  /* ========================================================
     USER
  ======================================================== */

  const {
    user,
    loading: userLoading,
  } = useUser();

  const userId =
    user?.user_id
    || null;


  /* ========================================================
     DRAWER
  ======================================================== */

  const {
    openRightDrawer,
  } = useDrawer();


  /* ========================================================
     UNIVERSes
  ======================================================== */

  const [
    universes,
    setUniverses,
  ] = useState<Universe[]>([]);


  /* ========================================================
     SEARCH / FILTER STATE
  ======================================================== */

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    filterState,
    setFilterState,
  ] =
    useState<NumbersExplorerFilterState>(
      INITIAL_FILTER_STATE,
    );

  const [
    availableFilters,
    setAvailableFilters,
  ] =
    useState<PublicNumberFilters | null>(
      null,
    );


  /* ========================================================
     NUMBERS
  ======================================================== */

  const [
    items,
    setItems,
  ] = useState<PublicNumber[]>([]);

  const [
    pagination,
    setPagination,
  ] =
    useState<PublicNumbersPagination>(
      INITIAL_PAGINATION,
    );


  /* ========================================================
     UI STATE
  ======================================================== */

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    filtersLoading,
    setFiltersLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* ========================================================
     LOAD UNIVERSES
  ======================================================== */

  useEffect(() => {

    if (
      userLoading
      || !userId
    ) {

      return;

    }

    async function loadUniverses() {

      try {

        const response = await api.get(
          "/universe/list-for-user",
        );

        setUniverses(
          response?.universes
          || [],
        );

      } catch (loadError) {

        console.error(
          "Unable to load universes:",
          loadError,
        );

      }

    }

    loadUniverses();

  }, [
    userId,
    userLoading,
  ]);


  /* ========================================================
     LOAD AVAILABLE FILTERS
  ======================================================== */

  const loadAvailableFilters = useCallback(

    async ({
      searchQuery,
      universeId,
    }: {
      searchQuery: string;
      universeId: string;
    }) => {

      if (!userId) {

        return;

      }

      setFiltersLoading(
        true,
      );

      try {

        const response =
          await getValidatedNumberFilters({

            user_id:
              userId,

            query:
              searchQuery
              || undefined,

            universe_id:
              universeId
              || undefined,

          });

        setAvailableFilters(
          response.filters,
        );

      } catch (loadError) {

        console.error(
          "Unable to load Number filters:",
          loadError,
        );

        setAvailableFilters(
          null,
        );

      } finally {

        setFiltersLoading(
          false,
        );

      }

    },

    [
      userId,
    ],
  );


  /* ========================================================
     LOAD NUMBERS
  ======================================================== */

  const loadNumbers = useCallback(

    async ({
      searchQuery,
      filters,
      offset = 0,
    }: {
      searchQuery: string;
      filters:
        NumbersExplorerFilterState;
      offset?: number;
    }) => {

      if (!userId) {

        return;

      }

      setLoading(
        true,
      );

      setError(
        null,
      );

      try {

        const response =
          await searchValidatedNumbers({

            user_id:
              userId,

            query:
              searchQuery
              || undefined,

            universe_id:
              filters.universeId
              || undefined,

            metric_type:
              filters.metricType
              || undefined,

            year:
              filters.year
              || undefined,

            zone:
              filters.zone
              || undefined,

            value_status:
              filters.valueStatus
              || undefined,

            limit:
              PAGE_SIZE,

            offset,

          });

        setItems(
          response.items
          || [],
        );

        setPagination(
          response.pagination
          || {
            ...INITIAL_PAGINATION,
            offset,
          },
        );

      } catch (loadError) {

        console.error(
          "Unable to load validated Numbers:",
          loadError,
        );

        setItems([]);

        setPagination({
          ...INITIAL_PAGINATION,
          offset: 0,
        });

        setError(
          "Unable to load Numbers.",
        );

      } finally {

        setLoading(
          false,
        );

      }

    },

    [
      userId,
    ],
  );


  /* ========================================================
     INITIAL LOAD
  ======================================================== */

  useEffect(() => {

    if (
      userLoading
      || !userId
    ) {

      return;

    }

    loadNumbers({
      searchQuery: "",
      filters: INITIAL_FILTER_STATE,
      offset: 0,
    });

    loadAvailableFilters({
      searchQuery: "",
      universeId: "",
    });

  }, [
    loadAvailableFilters,
    loadNumbers,
    userId,
    userLoading,
  ]);


  /* ========================================================
     SEARCH
  ======================================================== */

  function handleSearch(
    nextQuery: string,
  ) {

    setQuery(
      nextQuery,
    );

    loadNumbers({
      searchQuery: nextQuery,
      filters: filterState,
      offset: 0,
    });

    loadAvailableFilters({
      searchQuery: nextQuery,
      universeId:
        filterState.universeId,
    });

  }


  /* ========================================================
     FILTER CHANGE
  ======================================================== */

  function handleFilterChange(
    nextFilters:
      NumbersExplorerFilterState,
  ) {

    const universeChanged =
      nextFilters.universeId
      !== filterState.universeId;

    setFilterState(
      nextFilters,
    );

    loadNumbers({
      searchQuery: query,
      filters: nextFilters,
      offset: 0,
    });

    if (universeChanged) {

      loadAvailableFilters({
        searchQuery: query,
        universeId:
          nextFilters.universeId,
      });

    }

  }


  /* ========================================================
     RESET
  ======================================================== */

  function handleReset() {

    setQuery("");

    setFilterState(
      INITIAL_FILTER_STATE,
    );

    loadNumbers({
      searchQuery: "",
      filters: INITIAL_FILTER_STATE,
      offset: 0,
    });

    loadAvailableFilters({
      searchQuery: "",
      universeId: "",
    });

  }


  /* ========================================================
     PREVIOUS PAGE
  ======================================================== */

  function handlePreviousPage() {

    if (loading) {

      return;

    }

    const previousOffset = Math.max(
      0,
      pagination.offset
      - pagination.limit,
    );

    loadNumbers({
      searchQuery: query,
      filters: filterState,
      offset: previousOffset,
    });

  }


  /* ========================================================
     NEXT PAGE
  ======================================================== */

  function handleNextPage() {

    if (
      loading
      || !pagination.has_more
    ) {

      return;

    }

    const nextOffset =
      pagination.offset
      + pagination.limit;

    loadNumbers({
      searchQuery: query,
      filters: filterState,
      offset: nextOffset,
    });

  }


  /* ========================================================
     OPEN CONTENT
  ======================================================== */

  function handleOpenContent(
    contentId: string,
  ) {

    openRightDrawer(
      "content",
      contentId,
      "silent",
    );

  }


  /* ========================================================
     PAGE STATE
  ======================================================== */

  const pageLoading =
    userLoading
    || loading;

  const controlsLoading =
    pageLoading
    || filtersLoading;


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div
      className="
        space-y-6
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header
        className="
          flex
          flex-col
          gap-2
          sm:flex-row
          sm:items-end
          sm:justify-between
        "
      >

        <div>

          <h1
            className="
              text-2xl
              font-semibold
              tracking-tight
              text-gray-900
            "
          >
            Numbers
          </h1>

          <p
            className="
              mt-1
              max-w-3xl
              text-sm
              leading-6
              text-gray-500
            "
          >
            Explore verified business metrics extracted from
            GetCurator&apos;s editorial intelligence.
          </p>

        </div>

        {!pageLoading
          && !error
          && (

            <div
              className="
                whitespace-nowrap
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
                {pagination.total}
              </span>
              {" validated Number"}
              {pagination.total !== 1
                ? "s"
                : ""}
            </div>

          )}

      </header>


      {/* ================================================= */}
      {/* FILTERS */}
      {/* ================================================= */}

      <NumbersExplorerFilters
        query={query}
        value={filterState}
        universes={universes}
        filters={availableFilters}
        loading={controlsLoading}
        onSearch={handleSearch}
        onChange={handleFilterChange}
        onReset={handleReset}
      />


      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (

        <div
          className="
            rounded-xl
            border
            border-red-100
            bg-red-50
            px-4
            py-3
            text-sm
            text-red-700
          "
        >
          {error}
        </div>

      )}


      {/* ================================================= */}
      {/* TABLE */}
      {/* ================================================= */}

      {!error && (

        <NumbersExplorerTable
          items={items}
          loading={pageLoading}
          onOpenContent={
            handleOpenContent
          }
        />

      )}


      {/* ================================================= */}
      {/* PAGINATION */}
      {/* ================================================= */}

      {!error
        && !pageLoading
        && (

          <NumbersExplorerPagination
            pagination={pagination}
            loading={loading}
            onPrevious={
              handlePreviousPage
            }
            onNext={
              handleNextPage
            }
          />

        )}

    </div>

  );

}
