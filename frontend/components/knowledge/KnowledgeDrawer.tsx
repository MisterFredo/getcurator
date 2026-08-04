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
import KnowledgeActions from "./KnowledgeActions";
import KnowledgeTabs from "./KnowledgeTabs";
import KnowledgeBlockEditor from "./KnowledgeBlockEditor";

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

    try {

      setLoading(
        true,
      );

      const res =
        await getKnowledge(

          entity.entity_type,

          entity.entity_id,

        );

      setKnowledge(
        res,
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

    return null;

  }

  if (!knowledge) {

    return null;

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

        knowledge={knowledge}

        entity={entity}

        selectedBlock={selectedBlock}

        onReload={loadKnowledge}

      />

      <KnowledgeActions

        entity={entity}

        onReload={loadKnowledge}

      />

    </div>

  );

}
