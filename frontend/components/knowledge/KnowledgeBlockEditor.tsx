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

  KnowledgeEntitySummary,

  KnowledgeBlockType,

} from "@/types/knowledge";

/* ========================================================= */

const BLOCK_LABELS: Record<
  KnowledgeBlockType,
  string
> = {

  signal_analytique:
    "Analytical Signal",

  mecanique_expliquee:
    "Mechanics",

  enjeu_strategique:
    "Strategic Implications",

  point_de_friction:
    "Structural Frictions",

  chiffres:
    "Key Numbers",

};

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  knowledge: KnowledgeEntity;

  selectedBlock: KnowledgeBlockType;

  onReload: () => void;

};

/* ========================================================= */

export default function KnowledgeBlockEditor({

  entity,

  knowledge,

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

      knowledge[
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

        entity_type:
          entity.entity_type,

        entity_id:
          entity.entity_id,

        block_type:
          selectedBlock,

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

    <div className="flex flex-1 flex-col overflow-hidden">

      <div className="flex items-center justify-between border-b px-6 py-4">

        <div>

          <div className="text-lg font-semibold">

            {

              BLOCK_LABELS[
                selectedBlock
              ]

            }

          </div>

          <div className="mt-1 text-sm text-gray-500">

            Last updated{" "}

            {

              new Date(

                knowledge[
                  selectedBlock
                ].updated_at,

              ).toLocaleString()

            }

          </div>

        </div>

        <div className="text-sm text-gray-500">

          Version{" "}

          {

            knowledge[
              selectedBlock
            ].version

          }

        </div>

      </div>

      <div className="flex-1 overflow-hidden p-6">

        <textarea

          value={content}

          onChange={(e) =>

            setContent(
              e.target.value,
            )

          }

          className="
            h-full
            w-full
            rounded-lg
            border
            p-4
            font-mono
            text-sm
            resize-none
          "

        />

      </div>

    </div>

  );

}
