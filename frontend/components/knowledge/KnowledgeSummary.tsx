"use client";

import type {
  KnowledgeEntity,
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  knowledge: KnowledgeEntity;

  onClose: () => void;

};

/* ========================================================= */

export default function KnowledgeSummary({

  entity,

  knowledge,

  onClose,

}: Props) {

  let status = "⚪ Not built";

  if (
    entity.processed_contents >= entity.contents_count &&
    entity.contents_count > 0
  ) {

    status = "🟢 Ready";

  } else if (
    entity.processed_contents > 0
  ) {

    status = "🟡 Building";

  }

  return (

    <div className="border-b bg-white px-6 py-5">

      <div className="flex items-start justify-between">

        <div className="space-y-4">

          <div>

            <h2 className="text-2xl font-semibold text-ratecard-blue">

              {entity.name}

            </h2>

            <div className="mt-1 text-sm text-gray-500">

              {entity.entity_type}

            </div>

          </div>

          <div className="flex flex-wrap gap-6 text-sm">

            <div>

              <span className="font-semibold">

                {entity.contents_count}

              </span>

              {" "}contents

            </div>

            <div>

              <span className="font-semibold">

                {entity.users_count}

              </span>

              {" "}users

            </div>

            <div>

              <span className="font-semibold">

                {entity.experts_count}

              </span>

              {" "}experts

            </div>

          </div>

          <div className="flex flex-wrap gap-8 text-sm">

            <div>

              <span className="font-semibold">
                Status:
              </span>

              {" "}

              {status}

            </div>

            <div>

              <span className="font-semibold">
                Progress:
              </span>

              {" "}

              {entity.processed_contents}
              {" / "}
              {entity.contents_count}

            </div>

          </div>

          <div className="text-xs text-gray-500">

            Last update{" "}

            {

              entity.updated_at

                ? new Date(
                    entity.updated_at,
                  ).toLocaleString()

                : "Never"

            }

          </div>

        </div>

        <button

          onClick={onClose}

          className="rounded p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700"

        >

          ✕

        </button>

      </div>

    </div>

  );

}
