// frontend/app/(admin)/admin/knowledge/page.tsx

"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import KnowledgeHeader from "@/components/knowledge/KnowledgeHeader";
import KnowledgeDashboard from "@/components/knowledge/KnowledgeDashboard";
import KnowledgeToolbar from "@/components/knowledge/KnowledgeToolbar";
import KnowledgeExplorer from "@/components/knowledge/KnowledgeExplorer";

import {
  buildKnowledge,
  getKnowledgeDashboard,
  getKnowledgeExplorer,
} from "@/lib/knowledge";

import type {
  KnowledgeDashboard as Dashboard,
  KnowledgeExplorer as Explorer,
  KnowledgeEntitySummary,
} from "@/types/knowledge";


/* ========================================================= */

export default function KnowledgePage() {

  const [
    dashboard,
    setDashboard,
  ] =
    useState<Dashboard | null>(
      null,
    );

  const [
    explorer,
    setExplorer,
  ] =
    useState<Explorer | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);


  /* =======================================================
     SEARCH
  ======================================================= */

  const [
    searchQuery,
    setSearchQuery,
  ] =
    useState("");


  const filteredEntities =
    useMemo(
      () => {

        if (!explorer) {

          return [];

        }

        const normalizedQuery =
          searchQuery
            .trim()
            .toLocaleLowerCase();

        if (!normalizedQuery) {

          return explorer.entities;

        }

        return explorer.entities.filter(
          entity =>
            entity.name
              .toLocaleLowerCase()
              .includes(
                normalizedQuery,
              ),
        );

      },
      [
        explorer,
        searchQuery,
      ],
    );


  /* =======================================================
     MULTI SELECTION
  ======================================================= */

  const [
    selectedKeys,
    setSelectedKeys,
  ] =
    useState<string[]>(
      [],
    );


  /* =======================================================
     MULTI BUILD
  ======================================================= */

  const [
    multiBuilding,
    setMultiBuilding,
  ] =
    useState(false);

  const [
    currentBuild,
    setCurrentBuild,
  ] =
    useState<{
      index: number;
      total: number;
      name: string;
    } | null>(
      null,
    );


  /* =======================================================
     ENTITY KEY
  ======================================================= */

  function getEntityKey(
    entity: KnowledgeEntitySummary,
  ) {

    return (
      `${entity.entity_type}:${entity.entity_id}`
    );

  }


  /* =======================================================
     LOAD
  ======================================================= */

  async function load() {

    try {

      const [
        dashboardResult,
        explorerResult,
      ] = await Promise.all([

        getKnowledgeDashboard(),

        getKnowledgeExplorer(),

      ]);

      setDashboard(
        dashboardResult,
      );

      setExplorer(
        explorerResult,
      );

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Unable to load Knowledge Cockpit.",
      );

    } finally {

      setLoading(
        false,
      );

    }

  }


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {

    load();

  }, []);


  /* =======================================================
     TOGGLE ENTITY
  ======================================================= */

  function handleToggleEntity(
    entity: KnowledgeEntitySummary,
  ) {

    if (multiBuilding) {

      return;

    }

    const key =
      getEntityKey(
        entity,
      );

    setSelectedKeys(
      current => {

        if (
          current.includes(
            key,
          )
        ) {

          return current.filter(
            item =>
              item !== key,
          );

        }

        return [
          ...current,
          key,
        ];

      },
    );

  }


  /* =======================================================
     SET SELECTION
  ======================================================= */

  function handleSetSelection(
    entities: KnowledgeEntitySummary[],
  ) {

    if (multiBuilding) {

      return;

    }

    setSelectedKeys(
      entities.map(
        getEntityKey,
      ),
    );

  }


  /* =======================================================
     MULTI AUTO CONTINUE
  ======================================================= */

  async function handleMultiBuild() {

    if (
      multiBuilding
      ||
      !explorer
      ||
      selectedKeys.length === 0
    ) {

      return;

    }

    /*
     * Freeze the selected entities before starting.
     *
     * The loop below is intentionally sequential.
     * Do NOT replace it with Promise.all().
     */

    const selectedEntities =
      explorer.entities.filter(
        entity =>
          selectedKeys.includes(
            getEntityKey(
              entity,
            ),
          ),
      );

    if (
      selectedEntities.length === 0
    ) {

      return;

    }

    setMultiBuilding(
      true,
    );

    let failed = 0;

    try {

      for (
        let index = 0;
        index < selectedEntities.length;
        index += 1
      ) {

        const entity =
          selectedEntities[index];

        setCurrentBuild({

          index:
            index + 1,

          total:
            selectedEntities.length,

          name:
            entity.name,

        });

        try {

          /*
           * IMPORTANT:
           *
           * await guarantees that the complete
           * AutoContinue of this entity finishes
           * before the next entity starts.
           */

          await buildKnowledge({

            entity_type:
              entity.entity_type,

            entity_id:
              entity.entity_id,

            auto_continue:
              true,

          });

        } catch (error) {

          failed += 1;

          console.error(
            "Knowledge multi build failed:",
            entity.entity_type,
            entity.entity_id,
            error,
          );

          /*
           * Do not stop the complete run.
           * Continue with the next entity.
           */

        }

      }

      await load();

      setSelectedKeys(
        [],
      );

      if (failed > 0) {

        alert(
          `${selectedEntities.length - failed} completed · ${failed} failed`,
        );

      }

    } finally {

      setCurrentBuild(
        null,
      );

      setMultiBuilding(
        false,
      );

    }

  }


  /* =======================================================
     RENDER
  ======================================================= */

  if (loading) {

    return (

      <div>

        Loading...

      </div>

    );

  }


  return (

    <div className="space-y-8">

      <KnowledgeHeader />


      {/* ================================================= */}
      {/* SEARCH */}
      {/* ================================================= */}

      <div className="rounded-xl border bg-white p-4">

        <label
          htmlFor="knowledge-search"
          className="mb-2 block text-sm font-medium text-gray-700"
        >
          Search by name
        </label>

        <div className="flex items-center gap-3">

          <input
            id="knowledge-search"
            type="search"
            value={searchQuery}
            disabled={multiBuilding}
            onChange={event =>
              setSearchQuery(
                event.target.value,
              )
            }
            placeholder="Company, solution or topic..."
            className="w-full max-w-xl rounded-lg border px-3 py-2 text-sm outline-none focus:border-ratecard-blue disabled:bg-gray-100"
          />

          {searchQuery && (

            <button
              type="button"
              disabled={multiBuilding}
              onClick={() =>
                setSearchQuery("")
              }
              className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Clear
            </button>

          )}

          <span className="text-sm text-gray-500">

            {filteredEntities.length} result
            {filteredEntities.length !== 1
              ? "s"
              : ""}

          </span>

        </div>

      </div>


      {/* ================================================= */}
      {/* DASHBOARD */}
      {/* ================================================= */}

      {dashboard && (

        <KnowledgeDashboard
          dashboard={dashboard}
        />

      )}


      {/* ================================================= */}
      {/* TOOLBAR */}
      {/* ================================================= */}

      <KnowledgeToolbar />


      {/* ================================================= */}
      {/* EXPLORER */}
      {/* ================================================= */}

      {explorer && (

        <KnowledgeExplorer

          entities={
            filteredEntities
          }

          selectedKeys={
            selectedKeys
          }

          multiBuilding={
            multiBuilding
          }

          currentBuild={
            currentBuild
          }

          onToggleEntity={
            handleToggleEntity
          }

          onSetSelection={
            handleSetSelection
          }

          onMultiBuild={
            handleMultiBuild
          }

        />

      )}

    </div>

  );

}
