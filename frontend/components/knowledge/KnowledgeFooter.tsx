// frontend/components/knowledge/KnowledgeFooter.tsx

"use client";

import {
  useState,
} from "react";

import {
  buildKnowledge,
  updateKnowledge,
} from "@/lib/knowledge";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  onReload: () => Promise<void>;

  onSave?: () => Promise<void>;

  saving?: boolean;

};

/* ========================================================= */

export default function KnowledgeFooter({

  entity,

  onReload,

  onSave,

  saving = false,

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

  /* =======================================================
     BUILD
  ======================================================= */

  async function handleBuild() {

    setBuilding(
      true,
    );

    try {

      await buildKnowledge({

        entity_type:
          entity.entity_type,

        entity_id:
          entity.entity_id,

      });

      await onReload();

    } finally {

      setBuilding(
        false,
      );

    }

  }

  /* =======================================================
     UPDATE
  ======================================================= */

  async function handleUpdate() {

    setUpdating(
      true,
    );

    try {

      await updateKnowledge({

        entity_type:
          entity.entity_type,

        entity_id:
          entity.entity_id,

      });

      await onReload();

    } finally {

      setUpdating(
        false,
      );

    }

  }

  /* =======================================================
     SAVE
  ======================================================= */

  async function handleSave() {

    if (!onSave) {
      return;
    }

    await onSave();

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="flex items-center justify-between border-t bg-white px-6 py-4">

      <div className="flex gap-3">

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

      <button

        onClick={handleSave}

        disabled={!onSave || saving}

        className="rounded bg-ratecard-blue px-5 py-2 text-white disabled:opacity-50"

      >

        {

          saving

            ? "Saving..."

            : "Save"

        }

      </button>

    </div>

  );

}
