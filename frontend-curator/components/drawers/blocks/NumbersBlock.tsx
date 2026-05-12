"use client";

import { useDrawer } from "@/contexts/DrawerContext";

/* ========================================================= */

type NumberItem = {
  ID_NUMBER: string;
  LABEL?: string;
  VALUE?: number;
  UNIT?: string;
  SCALE?: string;

  TYPE?: string;
  CATEGORY?: string;

  ZONE?: string;
  PERIOD?: string;
};

/* ========================================================= */

type Props = {
  numbers: NumberItem[];
  entityId: string;
  entityType: "company" | "solution" | "topic";
};

/* ========================================================= */

function formatValue(n: NumberItem) {

  if (
    n.VALUE === undefined ||
    n.VALUE === null
  ) {
    return "";
  }

  const scaleRaw = (
    n.SCALE || ""
  )
    .toString()
    .toLowerCase();

  const scaleMap: any = {

    thousand: "K",
    thousands: "K",

    million: "M",
    millions: "M",

    billion: "Md",
    billions: "Md",

    trillion: "T",
    trillions: "T",
  };

  const scale =
    scaleMap[scaleRaw] ||
    n.SCALE ||
    "";

  const unit = n.UNIT || "";

  return [
    n.VALUE,
    scale,
    unit,
  ]
    .filter(Boolean)
    .join(" ");
}

/* ========================================================= */

export default function NumbersBlock({
  numbers,
  entityId,
  entityType,
}: Props) {

  const { openRightDrawer } = useDrawer();

  if (
    !Array.isArray(numbers) ||
    numbers.length === 0
  ) {
    return null;
  }

  return (

    <section className="space-y-3">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <h2 className="
          text-xs
          font-semibold
          uppercase
          text-gray-400
        ">
          Chiffres clés
        </h2>

        <button
          onClick={() =>
            openRightDrawer(
              "numbers",
              entityId,
              "silent",
              {
                entityType,
              }
            )
          }
          className="
            text-xs
            text-gray-400
            hover:text-black
          "
        >
          Voir →
        </button>

      </div>

      {/* GRID */}

      <div className="
        grid
        grid-cols-2
        gap-3
      ">

        {numbers.map((n) => (

          <div
            key={n.ID_NUMBER}
            className="
              p-3
              border
              rounded
              space-y-1
            "
          >

            {/* CONTEXTE */}

            {(n.CATEGORY || n.TYPE) && (

              <div className="
                text-[10px]
                text-gray-400
                uppercase
              ">
                {[n.CATEGORY, n.TYPE]
                  .filter(Boolean)
                  .join(" • ")}
              </div>

            )}

            {/* VALUE */}

            <div className="
              text-sm
              font-semibold
              text-gray-900
            ">
              {formatValue(n)}
            </div>

            {/* LABEL */}

            {n.LABEL && (

              <div className="
                text-xs
                text-gray-500
              ">
                {n.LABEL}
              </div>

            )}

            {/* META */}

            {(n.ZONE || n.PERIOD) && (

              <div className="
                text-[10px]
                text-gray-400
              ">
                {[n.ZONE, n.PERIOD]
                  .filter(Boolean)
                  .join(" — ")}
              </div>

            )}

          </div>

        ))}

      </div>

    </section>

  );
}
