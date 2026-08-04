"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  updateKnowledgeBlock,
} from "@/lib/knowledge";

import type {

  KnowledgeEntity,

  KnowledgeBlockType,

  KnowledgeEntityType,

} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  knowledge: KnowledgeEntity;

  entityId: string;

  entityType: KnowledgeEntityType;

  selectedBlock: KnowledgeBlockType;

  onReload: () => void;

};

/* ========================================================= */

export default function KnowledgeBlockEditor({

  knowledge,

  entityId,

  entityType,

  selectedBlock,

  onReload,

}: Props) {

  const [

    content,

    setContent,

  ] =
    useState("");

  const [

    saving,

    setSaving,

  ] =
    useState(false);

  /* =======================================================
     LOAD BLOCK
  ======================================================= */

  useEffect(() => {

    setContent(

      knowledge?.[
        selectedBlock
      ]?.content || ""

    );

  }, [

    knowledge,

    selectedBlock,

  ]);

  /* =======================================================
     SAVE
  ======================================================= */

  async function save() {

    setSaving(
      true,
    );

    try {

      await updateKnowledgeBlock({

        entity_type: entityType,

        entity_id: entityId,

        block_type: selectedBlock,

        content,

      });

      await onReload();

    } finally {

      setSaving(
        false,
      );

    }

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="flex flex-1 flex-col">

      <div className="flex items-center justify-between border-b px-6 py-4">

        <div className="font-semibold">

          {selectedBlock}

        </div>

        <div className="text-sm text-gray-500">

          Version {

            knowledge[
              selectedBlock
            ].version

          }

        </div>

      </div>

      <div className="flex-1 p-6">

        <textarea

          value={content}

          onChange={(e) =>

            setContent(
              e.target.value,
            )

          }

          className="h-full w-full rounded border p-4 font-mono text-sm"

        />

      </div>

      <div className="border-t bg-white px-6 py-4">

        <button

          onClick={save}

          disabled={saving}

          className="rounded bg-ratecard-blue px-5 py-2 text-white disabled:opacity-50"

        >

          {

            saving

              ? "Saving..."

              : "Save"

          }

        </button>

      </div>

    </div>

  );

}
