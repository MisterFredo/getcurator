"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  api,
} from "@/lib/api";

import {
  EMPTY_CONTENT_FILTERS,
  type ContentFilters,
} from "@/types/content";

import type {
  CompanyOption,
} from "@/types/company";

import type {
  SolutionOption,
} from "@/types/solution";

import type {
  TopicOption,
} from "@/types/topic";

import type {
  ConceptOption,
} from "@/types/concept";

import type {
  SourceOption,
} from "@/types/source";

import {
  useContentSearch,
} from "@/hooks/useContentSearch";

import ContentFiltersPanel from "@/components/admin/content/ContentFilters";
import ContentTable from "@/components/admin/content/ContentTable";
import ContentPagination from "@/components/admin/content/ContentPagination";

/* ========================================================= */

export default function ContentPage() {

  const [
    filters,
    setFilters,
  ] = useState<ContentFilters>(
    EMPTY_CONTENT_FILTERS,
  );

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    selectedIds,
    setSelectedIds,
  ] = useState<string[]>([]);

  const [
    bulkLoading,
    setBulkLoading,
  ] = useState(false);

  const [
    companies,
    setCompanies,
  ] = useState<CompanyOption[]>([]);

  const [
    solutions,
    setSolutions,
  ] = useState<SolutionOption[]>([]);

  const [
    topics,
    setTopics,
  ] = useState<TopicOption[]>([]);

  const [
    concepts,
    setConcepts,
  ] = useState<ConceptOption[]>([]);

  const [
    sources,
    setSources,
  ] = useState<SourceOption[]>([]);

  /* =======================================================
     SEARCH
  ======================================================= */

  const {
    contents,
    loading,
    total_results,
    total_pages,
    refresh,
  } = useContentSearch({
    filters,
    page,
    pageSize: 100,
  });

  /* =======================================================
     LOOKUPS
  ======================================================= */

  useEffect(() => {

    async function loadLookups() {

      try {

        const [
          companiesRes,
          solutionsRes,
          topicsRes,
          conceptsRes,
          sourcesRes,
        ] = await Promise.all([

          api.get(
            "/company/list",
          ),

          api.get(
            "/solution/list",
          ),

          api.get(
            "/topic/list",
          ),

          api.get(
            "/concept/list",
          ),

          api.get(
            "/source/list",
          ),

        ]);

        setCompanies(
          companiesRes.companies || [],
        );

        setSolutions(
          solutionsRes.solutions || [],
        );

        setTopics(
          topicsRes.topics || [],
        );

        setConcepts(
          conceptsRes.concepts || [],
        );

        setSources(
          sourcesRes.sources || [],
        );

      } catch (e) {

        console.error(
          "Unable to load lookups",
          e,
        );

      }

    }

    loadLookups();

  }, []);

  /* =======================================================
     FILTERS
  ======================================================= */

  function handleFiltersChange(
    next: ContentFilters,
  ) {

    setPage(1);

    setSelectedIds([]);

    setFilters(next);

  }

  /* =======================================================
     BULK READY
  ======================================================= */

  async function handleBulkReady() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      setBulkLoading(true);

      await api.post(
        "/content/bulk/ready",
        {
          ids: selectedIds,
        },
      );

      setSelectedIds([]);

      await refresh();

    } catch (e) {

      console.error(
        "Bulk ready error",
        e,
      );

      alert(
        "Unable to mark contents as ready.",
      );

    } finally {

      setBulkLoading(false);

    }

  }

  /* =======================================================
     BULK PUBLISH
  ======================================================= */

  async function handleBulkPublish() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      setBulkLoading(true);

      const result =
        await api.post(
          "/content/bulk/publish",
          {
            ids: selectedIds,
          },
        );

      setSelectedIds([]);

      await refresh();

      if (
        result.skipped > 0
      ) {

        alert(
          `${result.updated} published, ${result.skipped} skipped.`,
        );

      }

    } catch (e) {

      console.error(
        "Bulk publish error",
        e,
      );

      alert(
        "Unable to publish contents.",
      );

    } finally {

      setBulkLoading(false);

    }

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-8">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold">
            Contents
          </h1>

          <p className="text-gray-500 mt-1">
            Browse, search and edit contents.
          </p>

        </div>

        <Link
          href="/admin/content/create"
          className="
            bg-ratecard-blue
            text-white
            px-4
            py-2
            rounded
          "
        >
          New content
        </Link>

      </div>

      {/* =================================================== */}
      {/* FILTERS */}
      {/* =================================================== */}

      <ContentFiltersPanel

        filters={filters}

        onChange={
          handleFiltersChange
        }

        companies={companies}

        solutions={solutions}

        topics={topics}

        concepts={concepts}

        sources={sources}

        onReset={() => {

          setPage(1);

          setSelectedIds([]);

          setFilters(
            EMPTY_CONTENT_FILTERS,
          );

        }}

      />

      {/* =================================================== */}
      {/* RESULTS */}
      {/* =================================================== */}

      <div className="space-y-4">

        <div className="flex items-center justify-between">

          <div>

            <h2 className="text-xl font-semibold">
              Results
            </h2>

            <p className="text-sm text-gray-500">

              {total_results} contents found

            </p>

          </div>

          {/* =============================================== */}
          {/* BULK ACTIONS */}
          {/* =============================================== */}

          {selectedIds.length > 0 && (

            <div className="flex items-center gap-3">

              <span className="text-sm text-gray-500">

                {selectedIds.length} selected

              </span>

              <button
                type="button"
                onClick={
                  handleBulkReady
                }
                disabled={
                  bulkLoading
                }
                className="
                  px-4
                  py-2
                  border
                  rounded
                  bg-white
                  hover:bg-gray-50
                  disabled:opacity-50
                "
              >
                Mark as ready
              </button>

              <button
                type="button"
                onClick={
                  handleBulkPublish
                }
                disabled={
                  bulkLoading
                }
                className="
                  px-4
                  py-2
                  rounded
                  bg-ratecard-blue
                  text-white
                  disabled:opacity-50
                "
              >
                Publish
              </button>

            </div>

          )}

        </div>

        {/* ================================================= */}
        {/* TABLE */}
        {/* ================================================= */}

        <ContentTable

          contents={contents}

          loading={loading}

          selectedIds={
            selectedIds
          }

          onSelectionChange={
            setSelectedIds
          }

        />

        {/* ================================================= */}
        {/* PAGINATION */}
        {/* ================================================= */}

        <ContentPagination

          page={page}

          totalPages={
            total_pages
          }

          totalResults={
            total_results
          }

          onPageChange={(
            nextPage,
          ) => {

            setSelectedIds([]);

            setPage(
              nextPage,
            );

          }}

        />

      </div>

    </div>

  );

}
