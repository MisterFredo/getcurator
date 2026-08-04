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
  KnowledgeEntityType,
  KnowledgeBlockType,
} from "@/types/knowledge";

import KnowledgeSummary from "./KnowledgeSummary";
import KnowledgeActions from "./KnowledgeActions";
import KnowledgeTabs from "./KnowledgeTabs";
import KnowledgeBlockEditor from "./KnowledgeBlockEditor";

/* ========================================================= */

type Props = {

  entityId: string;

  entityType: KnowledgeEntityType;

  onClose: () => void;

};

/* ========================================================= */

export default function KnowledgeDrawer({

  entityId,

  entityType,

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

      const entity =
        await getKnowledge(

          entityType,

          entityId,

        );

      setKnowledge(
        entity,
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

    entityId,

    entityType,

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

    <div className="flex h-full flex-col">

      <KnowledgeSummary

        knowledge={knowledge}

        onClose={onClose}

      />

      <KnowledgeActions

        entityId={entityId}

        entityType={entityType}

        onReload={loadKnowledge}

      />

      <KnowledgeTabs

        selectedBlock={selectedBlock}

        onChange={setSelectedBlock}

      />

      <KnowledgeBlockEditor

        knowledge={knowledge}

        selectedBlock={selectedBlock}

        entityId={entityId}

        entityType={entityType}

        onReload={loadKnowledge}

      />

    </div>

  );

}
