// frontend/app/(admin)/admin/knowledge/page.tsx

"use client";

import {
  useEffect,
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
        dashboard,
        explorer,
      ] = await Promise.all([

        getKnowledgeDashboard(),

        getKnowledgeExplorer(),

      ]);

      setDashboard(
        dashboard,
      );

      setExplorer(
        explorer,
      );

    } catch (e) {

      console.error(e);

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

        } catch (e) {

          failed += 1;

          console.error(
            "Knowledge multi build failed:",
            entity.entity_type,
            entity.entity_id,
            e,
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

      {

        dashboard && (

          <KnowledgeDashboard

            dashboard={
              dashboard
            }

          />

        )

      }

      <KnowledgeToolbar />

      {

        explorer && (

          <KnowledgeExplorer

            entities={
              explorer.entities
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

        )

      }

    </div>

  );

}
