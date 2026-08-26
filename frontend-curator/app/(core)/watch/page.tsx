"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useUser,
} from "@/hooks/useUser";

import {
  getWatchFilters,
  watchLatest,
  watchSearch,
} from "@/lib/watch";

import WatchHeader
  from "@/components/watch/WatchHeader";

import WatchList
  from "@/components/watch/WatchList";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import {
  useWorkspace,
} from "@/contexts/WorkspaceContext";

import type {
  WatchFilterOption,
  WatchFiltersResponse,
  WatchItem,
} from "@/types/watch";

/* =========================================================
   TYPES
========================================================= */

export type WatchPeriod =
  | "7d"
  | "30d"
  | "3m"
  | "12m"
  | "all";


type PeriodRange = {

  period_start: string | null;

  period_end: string | null;

};

/* =========================================================
   CONSTANTS
========================================================= */

const WATCH_LIMIT = 20;

const EMPTY_FILTERS: WatchFiltersResponse = {

  universes: [],

  companies: [],

  solutions: [],

  topics: [],

};

/* =========================================================
   PERIOD
========================================================= */

function getPeriodRange(
  period: WatchPeriod,
): PeriodRange {

  if (period === "all") {

    return {

      period_start: null,

      period_end: null,

    };

  }

  const end =
    new Date();

  const start =
    new Date(end);

  if (period === "7d") {

    start.setUTCDate(
      start.getUTCDate() - 7,
    );

  }

  if (period === "30d") {

    start.setUTCDate(
      start.getUTCDate() - 30,
    );

  }

  if (period === "3m") {

    start.setUTCMonth(
      start.getUTCMonth() - 3,
    );

  }

  if (period === "12m") {

    start.setUTCFullYear(
      start.getUTCFullYear() - 1,
    );

  }

  return {

    period_start:
      start.toISOString(),

    period_end:
      end.toISOString(),

  };

}

/* =========================================================
   COMPONENT
========================================================= */

export default function WatchPage() {

  const {
    user,
  } = useUser();

  const {
    openRightDrawer,
  } = useDrawer();

  const {
    selectedContentItems,
    toggleContent,
  } = useWorkspace();

  /* =======================================================
     CONTENT STATE
  ======================================================= */

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    loadingMore,
    setLoadingMore,
  ] = useState(false);

  /* =======================================================
     FILTER OPTIONS
  ======================================================= */

  const [
    filterOptions,
    setFilterOptions,
  ] = useState<WatchFiltersResponse>(
    EMPTY_FILTERS,
  );

  const [
    filtersLoading,
    setFiltersLoading,
  ] = useState(true);

  /* =======================================================
     ACTIVE FILTERS
  ======================================================= */

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    period,
    setPeriod,
  ] = useState<WatchPeriod>(
    "30d",
  );

  const [
    selectedUniverse,
    setSelectedUniverse,
  ] = useState<string | null>(
    null,
  );

  const [
    selectedCompany,
    setSelectedCompany,
  ] = useState<string | null>(
    null,
  );

  const [
    selectedSolution,
    setSelectedSolution,
  ] = useState<string | null>(
    null,
  );

  const [
    selectedTopic,
    setSelectedTopic,
  ] = useState<string | null>(
    null,
  );

  /* =======================================================
     REQUEST PROTECTION
  ======================================================= */

  const contentRequestId =
    useRef(0);

  const filtersRequestId =
    useRef(0);

  /* =======================================================
     PERIOD RANGE
  ======================================================= */

  const periodRange =
    getPeriodRange(
      period,
    );

  /* =======================================================
     LOAD FILTER OPTIONS
  ======================================================= */

  useEffect(() => {

    if (!user) {

      return;

    }

    const requestId =
      ++filtersRequestId.current;

    async function loadFilters() {

      setFiltersLoading(
        true,
      );

      try {

        const res =
          await getWatchFilters({

            user_id:
              user!.user_id,

            period_start:
              periodRange.period_start,

            period_end:
              periodRange.period_end,

          });

        if (
          requestId !==
          filtersRequestId.current
        ) {

          return;

        }

        setFilterOptions(
          res,
        );

      } catch (error) {

        console.error(
          "❌ Watch filters load error:",
          error,
        );

        if (
          requestId ===
          filtersRequestId.current
        ) {

          setFilterOptions(
            EMPTY_FILTERS,
          );

        }

      } finally {

        if (
          requestId ===
          filtersRequestId.current
        ) {

          setFiltersLoading(
            false,
          );

        }

      }

    }

    loadFilters();

  }, [
    user,
    period,
  ]);

  /* =======================================================
     LOAD CONTENTS
  ======================================================= */

  useEffect(() => {

    if (!user) {

      return;

    }

    const requestId =
      ++contentRequestId.current;

    async function loadContents() {

      setLoading(
        true,
      );

      try {

        const params = {

          user_id:
            user!.user_id,

          limit:
            WATCH_LIMIT,

          offset:
            0,

          period_start:
            periodRange.period_start,

          period_end:
            periodRange.period_end,

          universe_id:
            selectedUniverse,

          company_id:
            selectedCompany,

          solution_id:
            selectedSolution,

          topic_id:
            selectedTopic,

        };

        const res =
          query.trim()

            ? await watchSearch({

                ...params,

                query:
                  query.trim(),

              })

            : await watchLatest(
                params,
              );

        if (
          requestId !==
          contentRequestId.current
        ) {

          return;

        }

        setItems(
          res.items,
        );

        setTotal(
          res.count,
        );

      } catch (error) {

        console.error(
          "❌ Watch contents load error:",
          error,
        );

        if (
          requestId ===
          contentRequestId.current
        ) {

          setItems(
            [],
          );

          setTotal(
            0,
          );

        }

      } finally {

        if (
          requestId ===
          contentRequestId.current
        ) {

          setLoading(
            false,
          );

        }

      }

    }

    loadContents();

  }, [
    user,
    query,
    period,
    selectedUniverse,
    selectedCompany,
    selectedSolution,
    selectedTopic,
  ]);

  /* =======================================================
     SEARCH
  ======================================================= */

  function handleSearch(
    value: string,
  ) {

    setQuery(
      value.trim(),
    );

  }

  /* =======================================================
     LOAD MORE
  ======================================================= */

  async function handleLoadMore() {

    if (
      !user
      || loading
      || loadingMore
      || items.length >= total
    ) {

      return;

    }

    setLoadingMore(
      true,
    );

    try {

      const params = {

        user_id:
          user.user_id,

        limit:
          WATCH_LIMIT,

        offset:
          items.length,

        period_start:
          periodRange.period_start,

        period_end:
          periodRange.period_end,

        universe_id:
          selectedUniverse,

        company_id:
          selectedCompany,

        solution_id:
          selectedSolution,

        topic_id:
          selectedTopic,

      };

      const res =
        query.trim()

          ? await watchSearch({

              ...params,

              query:
                query.trim(),

            })

          : await watchLatest(
              params,
            );

      setItems(
        current => [

          ...current,

          ...res.items.filter(

            nextItem =>
              !current.some(

                currentItem =>
                  currentItem.id ===
                  nextItem.id,

              ),

          ),

        ],
      );

      setTotal(
        res.count,
      );

    } catch (error) {

      console.error(
        "❌ Watch load more error:",
        error,
      );

    } finally {

      setLoadingMore(
        false,
      );

    }

  }

  /* =======================================================
     CLEAR FILTERS
  ======================================================= */

  function clearFilters() {

    setQuery(
      "",
    );

    setPeriod(
      "30d",
    );

    setSelectedUniverse(
      null,
    );

    setSelectedCompany(
      null,
    );

    setSelectedSolution(
      null,
    );

    setSelectedTopic(
      null,
    );

  }

  /* =======================================================
     OPEN DRAWER
  ======================================================= */

  function openContent(
    item: WatchItem,
  ) {

    openRightDrawer(
      "content",
      item.id,
    );

  }

  /* =======================================================
     WORKSPACE
  ======================================================= */

  const selectedIds =
    selectedContentItems.map(
      item => item.id,
    );

  function toggleSelect(
    item: WatchItem,
  ) {

    toggleContent(
      item,
    );

  }

  /* =======================================================
     FILTER HELPERS
  ======================================================= */

  function findOption(
    options: WatchFilterOption[],
    id: string | null,
  ) {

    if (!id) {

      return null;

    }

    return (
      options.find(
        option =>
          option.id === id,
      )
      ?? null
    );

  }

  const selectedCompanyOption =
    findOption(
      filterOptions.companies,
      selectedCompany,
    );

  const selectedSolutionOption =
    findOption(
      filterOptions.solutions,
      selectedSolution,
    );

  const selectedTopicOption =
    findOption(
      filterOptions.topics,
      selectedTopic,
    );

  const selectedUniverseOption =
    findOption(
      filterOptions.universes,
      selectedUniverse,
    );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div
      className="
        space-y-8
      "
    >

      <WatchHeader

        query={
          query
        }

        onSearch={
          handleSearch
        }

        period={
          period
        }

        onSelectPeriod={
          setPeriod
        }

        universes={
          filterOptions.universes
        }

        companies={
          filterOptions.companies
        }

        solutions={
          filterOptions.solutions
        }

        topics={
          filterOptions.topics
        }

        selectedUniverse={
          selectedUniverse
        }

        selectedCompany={
          selectedCompany
        }

        selectedSolution={
          selectedSolution
        }

        selectedTopic={
          selectedTopic
        }

        selectedUniverseOption={
          selectedUniverseOption
        }

        selectedCompanyOption={
          selectedCompanyOption
        }

        selectedSolutionOption={
          selectedSolutionOption
        }

        selectedTopicOption={
          selectedTopicOption
        }

        onSelectUniverse={
          setSelectedUniverse
        }

        onSelectCompany={
          setSelectedCompany
        }

        onSelectSolution={
          setSelectedSolution
        }

        onSelectTopic={
          setSelectedTopic
        }

        onClearFilters={
          clearFilters
        }

        loading={
          loading
        }

        filtersLoading={
          filtersLoading
        }

      />

      <WatchList

        title="Results"

        total={
          total
        }

        items={
          items
        }

        loading={
          loading
        }

        hasMore={
          !loadingMore
          && items.length < total
        }

        onLoadMore={
          handleLoadMore
        }

        onSelect={
          openContent
        }

        selectedIds={
          selectedIds
        }

        onToggleSelect={
          toggleSelect
        }

      />

      {loadingMore && (

        <div
          className="
            text-center
            text-xs
            text-gray-400
          "
        >
          Loading more contents...
        </div>

      )}

    </div>

  );

}
