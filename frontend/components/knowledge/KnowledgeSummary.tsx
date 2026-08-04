"use client";

import type {
  KnowledgeEntity,
} from "@/types/knowledge";

type Props = {

  knowledge: KnowledgeEntity;

  onClose: () => void;

};

export default function KnowledgeSummary({

  knowledge,

  onClose,

}: Props) {

  return (

    <div className="border-b bg-white px-6 py-4">

      <div className="flex items-start justify-between">

        <div>

          <h2 className="text-2xl font-semibold text-ratecard-blue">

            {knowledge.entity_id}

          </h2>

          <div className="mt-1 text-sm text-gray-500">

            {knowledge.entity_type}

          </div>

        </div>

        <button

          onClick={onClose}

          className="text-gray-400 hover:text-gray-700"

        >

          ✕

        </button>

      </div>

    </div>

  );

}
