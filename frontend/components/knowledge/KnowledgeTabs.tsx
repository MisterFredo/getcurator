"use client";

import type {
  KnowledgeBlockType,
} from "@/types/knowledge";

type Props = {

  selectedBlock: KnowledgeBlockType;

  onChange: (
    block: KnowledgeBlockType,
  ) => void;

};

const BLOCKS = [

  {
    id: "signal_analytique",
    label: "Signal",
  },

  {
    id: "mecanique_expliquee",
    label: "Mechanics",
  },

  {
    id: "enjeu_strategique",
    label: "Strategic",
  },

  {
    id: "point_de_friction",
    label: "Friction",
  },

  {
    id: "chiffres",
    label: "Numbers",
  },

] as const;

export default function KnowledgeTabs({

  selectedBlock,

  onChange,

}: Props) {

  return (

    <div className="border-b bg-gray-50 px-6 py-3">

      <select

        value={selectedBlock}

        onChange={(e) =>

          onChange(

            e.target.value as KnowledgeBlockType,

          )

        }

        className="rounded border px-3 py-2"

      >

        {

          BLOCKS.map((block) => (

            <option

              key={block.id}

              value={block.id}

            >

              {block.label}

            </option>

          ))

        }

      </select>

    </div>

  );

}
