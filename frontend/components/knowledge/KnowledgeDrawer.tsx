"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getKnowledge,
} from "@/lib/knowledge";

import type {
  KnowledgeEntity,
  KnowledgeEntitySummary,
  KnowledgeBlockType,
} from "@/types/knowledge";

import KnowledgeSummary from "./KnowledgeSummary";
import KnowledgeTabs from "./KnowledgeTabs";
import KnowledgeBlockEditor from "./KnowledgeBlockEditor";
import KnowledgeFooter from "./KnowledgeFooter";

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  onClose: () => void;

};

/* ========================================================= */

export default function KnowledgeDrawer({

  entity,

  onClose,

}: Props) {

  const [
    knowledge,
    setKnowledge,
  ] =
    useState<KnowledgeEntity | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    selectedBlock,
    setSelectedBlock,
  ] =
    useState<KnowledgeBlockType>(
      "signal_analytique",
    );

  /* =======================================================
     LOAD
  ======================================================= */

  async function loadKnowledge() {

    setLoading(
      true,
    );

    try {

      const knowledge =
        await getKnowledge(

          entity.entity_type,

          entity.entity_id,

        );

      setKnowledge(
        knowledge,
      );

    } catch (e) {

      console.error(e);

      setKnowledge(
        null,
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  useEffect(() => {

    loadKnowledge();

  }, [

    entity.entity_id,

    entity.entity_type,

  ]);

  /* =======================================================
     RENDER
  ======================================================= */

  if (loading) {

    return (

      <div className="flex h-full items-center justify-center">

        Loading...

      </div>

    );

  }

  if (!knowledge) {

    return (

      <div className="flex h-full items-center justify-center">

        Unable to load Knowledge.

      </div>

    );

  }

  return (

    <div className="flex h-full flex-col bg-white">

      <KnowledgeSummary

        entity={entity}

        knowledge={knowledge}

        onClose={onClose}

      />

      <KnowledgeTabs

        selectedBlock={selectedBlock}

        onChange={setSelectedBlock}

      />

      <KnowledgeBlockEditor

        entity={entity}

        knowledge={knowledge}

        selectedBlock={selectedBlock}

        onReload={loadKnowledge}

      />

      <KnowledgeFooter

        entity={entity}

        onReload={loadKnowledge}

      />

    </div>

  );

}
