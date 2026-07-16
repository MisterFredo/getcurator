"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

import {
  EMPTY_CONTENT_FILTERS,
  type ContentFilters,
} from "@/types/content";

import type { CompanyOption } from "@/types/company";
import type { SolutionOption } from "@/types/solution";
import type { TopicOption } from "@/types/topic";
import type { ConceptOption } from "@/types/concept";
import type { SourceOption } from "@/types/source";

import { useContentSearch } from "@/hooks/useContentSearch";

import ContentOperations from "@/components/admin/content/ContentOperations";
import ContentFiltersPanel from "@/components/admin/content/ContentFilters";
import ContentTable from "@/components/admin/content/ContentTable";
import ContentPagination from "@/components/admin/content/ContentPagination";

/* ========================================================= */

export default function ContentPage() {

  const [
    filters,
    setFilters,
  ] = useState<ContentFilters>(
    EMPTY_CONTENT_FILTERS
  );

  const [
    page,
    setPage,
  ] = useState(1);

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
  } = useContentSearch(...);

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

          api.get("/company/list"),

          api.get("/solution/list"),

          api.get("/topic/list"),

          api.get("/concept/list"),

          api.get("/source/list"),

        ]);

        setCompanies(
          companiesRes.companies || []
        );

        setSolutions(
          solutionsRes.solutions || []
        );

        setTopics(
          topicsRes.topics || []
        );

        setConcepts(
          conceptsRes.concepts || []
        );

        setSources(
          sourcesRes.sources || []
        );

      } catch (e) {

        console.error(
          "Erreur chargement lookups",
          e
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

    setFilters(next);

  }

  /* ======================================================= */

  return (

    <div className="space-y-6">

      <ContentOperations />

      <ContentFiltersPanel

        filters={filters}

        onChange={handleFiltersChange}

        companies={companies}

        solutions={solutions}

        topics={topics}

        concepts={concepts}

        sources={sources}

        onReset={() => {

          setPage(1);

          setFilters(
            EMPTY_CONTENT_FILTERS
          );

        }}

       />

      <ContentTable

        contents={contents}

        loading={loading}

      />

      <ContentPagination

        page={page}

        totalPages={
          total_pages
        }

        totalResults={
          total_results
        }

        onPageChange={
          setPage
        }

      />

    </div>

  );

}
