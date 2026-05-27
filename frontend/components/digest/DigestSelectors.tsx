// frontend/components/digest/DigestSelectors.tsx

"use client";

import DeliverySelector from "@/components/delivery/core/DeliverySelector";

import type {
  DigestContentItem,
  DigestEditorialItem,
} from "@/types/digest";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  contents: DigestContentItem[];

  editorialOrder: DigestEditorialItem[];

  setEditorialOrder: React.Dispatch<
    React.SetStateAction<
      DigestEditorialItem[]
    >
  >;
};

/* =========================================================
   HELPERS
========================================================= */

function formatDate(
  date?: string
) {

  if (!date) {
    return "";
  }

  return new Date(
    date
  ).toLocaleDateString(
    "fr-FR"
  );
}

/* =========================================================
   COMPONENT
========================================================= */

export default function DigestSelectors({
  contents,

  editorialOrder,

  setEditorialOrder,
}: Props) {

  /* =======================================================
     UPDATE TYPE
  ======================================================= */

  function updateTypeSelection(
    ids: string[],

    type:
      DigestEditorialItem["type"]
  ) {

    setEditorialOrder(
      (prev) => {

        const prevSameType =
          prev.filter(
            (i) =>
              i.type ===
              type
          );

        const newItems =
          ids
            .filter(
              (id) =>
                !prevSameType.some(
                  (i) =>
                    i.id ===
                    id
                )
            )
            .map(
              (id) => ({
                id,
                type,
              })
            );

        const keptItems =
          prevSameType.filter(
            (i) =>
              ids.includes(
                i.id
              )
          );

        const others =
          prev.filter(
            (i) =>
              i.type !==
              type
          );

        return [
          ...others,
          ...keptItems,
          ...newItems,
        ];
      }
    );
  }

  /* =======================================================
     COUNTS
  ======================================================= */

  const contentsSelected =
    editorialOrder.filter(
      (i) =>
        i.type ===
        "content"
    ).length;

  /* =======================================================
     UI
  ======================================================= */

  return (

    <div className="space-y-5">

      {/* CONTENTS */}

      <section className="space-y-2">

        <div className="flex items-center justify-between text-sm">

          <div className="flex items-center gap-2">

            <h2 className="font-semibold tracking-tight">
              Contenus
            </h2>

            <span className="text-xs text-gray-400">
              {contents.length} résultats
            </span>

          </div>

          <span className="text-xs font-medium text-gray-500">

            {contentsSelected} sélectionné
            {contentsSelected > 1
              ? "s"
              : ""}

          </span>

        </div>

        {/* =================================================
           SELECTOR WRAPPER
        ================================================= */}

        <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">

          {/* HEADER */}

          <div className="px-3 py-2 border-b bg-gray-50 flex items-center justify-between">

            <div className="text-xs font-medium text-gray-600">
              Sélection des contenus
            </div>

            <div className="text-[11px] text-gray-400">
              Scroll indépendant
            </div>

          </div>

          {/* SCROLL AREA */}

          <div className="h-[72vh] overflow-y-auto p-2">

            <DeliverySelector
              title=""

              items={contents.map(
                (c) => ({
                  ...c,

                  label: `${c.title} · ${formatDate(
                    c.published_at
                  )}`,
                })
              )}

              selectedIds={editorialOrder
                .filter(
                  (i) =>
                    i.type ===
                    "content"
                )
                .map(
                  (i) => i.id
                )}

              onChange={(ids) =>
                updateTypeSelection(
                  ids,
                  "content"
                )
              }

              labelKey="label"
            />

          </div>

        </div>

      </section>

    </div>
  );
}
