// KnowledgeDrawer.tsx

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
} from "@/types/knowledge";

type Props = {

  entityId: string;

  entityType: KnowledgeEntityType;

  onClose: () => void;

};

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

  useEffect(() => {

    async function load() {

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

    load();

  }, [

    entityId,

    entityType,

  ]);

  if (loading) {

    return null;

  }

  return (

    <div>

      Drawer

    </div>

  );

}
