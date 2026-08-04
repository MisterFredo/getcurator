"use client";

import {
  useState,
} from "react";

import {
  buildKnowledge,
  updateKnowledge,
} from "@/lib/knowledge";

import type {
  KnowledgeEntityType,
} from "@/types/knowledge";

type Props = {

  entityId: string;

  entityType: KnowledgeEntityType;

  onReload: () => void;

};

export default function KnowledgeActions({

  entityId,

  entityType,

  onReload,

}: Props) {

  const [

    building,

    setBuilding,

  ] =
    useState(false);

  const [

    updating,

    setUpdating,

  ] =
    useState(false);

  async function handleBuild() {

    setBuilding(
      true,
    );

    try {

      await buildKnowledge({

        entity_type: entityType,

        entity_id: entityId,

      });

      await onReload();

    } finally {

      setBuilding(
        false,
      );

    }

  }

  async function handleUpdate() {

    setUpdating(
      true,
    );

    try {

      await updateKnowledge({

        entity_type: entityType,

        entity_id: entityId,

      });

      await onReload();

    } finally {

      setUpdating(
        false,
      );

    }

  }

  return (

    <div className="flex gap-3 border-b bg-white px-6 py-4">

      <button

        onClick={handleBuild}

        disabled={building}

        className="rounded bg-ratecard-green px-4 py-2 text-white disabled:opacity-50"

      >

        {

          building

            ? "Building..."

            : "Build"

        }

      </button>

      <button

        onClick={handleUpdate}

        disabled={updating}

        className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"

      >

        {

          updating

            ? "Updating..."

            : "Update"

        }

      </button>

    </div>

  );

}
