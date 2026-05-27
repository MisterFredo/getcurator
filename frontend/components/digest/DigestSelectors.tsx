// frontend/components/digest/DigestSelectors.tsx

"use client";

import DeliverySelector from "@/components/delivery/core/DeliverySelector";

import type {
  DigestContentItem,
  DigestNumberItem,
  DigestEditorialItem,
} from "@/types/digest";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  contents: DigestContentItem[];

  numbers: DigestNumberItem[];

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

  numbers,

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

  const numbersSelected =
    editorialOrder.filter(
      (i) =>
        i.type ===
        "number"
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

      </section>

      {/* NUMBERS */}

      <section className="space-y-2">

        <div className="flex items-center justify-between text-sm">

          <div className="flex items-center gap-2">

            <h2 className="font-semibold tracking-tight">
              Chiffres clés
            </h2>

            <span className="text-xs text-gray-400">
              {numbers.length} résultats
            </span>

          </div>

          <span className="text-xs font-medium text-gray-500">

            {numbersSelected} sélectionné
            {numbersSelected > 1
              ? "s"
              : ""}

          </span>

        </div>

        <DeliverySelector
          title=""

          items={numbers.map(
            (n) => ({
              ...n,

              label: `${n.label} · ${n.value ?? ""} ${n.unit ?? ""}${
                n.period
                  ? ` · ${n.period}`
                  : ""
              }`,
            })
          )}

          selectedIds={editorialOrder
            .filter(
              (i) =>
                i.type ===
                "number"
            )
            .map(
              (i) => i.id
            )}

          onChange={(ids) =>
            updateTypeSelection(
              ids,
              "number"
            )
          }

          labelKey="label"
        />

      </section>

    </div>
  );
}
