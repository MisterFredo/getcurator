"use client";

import { useDrawer } from "@/contexts/DrawerContext";

/* ========================================================= */

type NumberItem = {
  id_number: string;
  label?: string;
  value?: number;
  unit?: string;
  scale?: string;
  zone?: string;
  period?: string;
};

type NumberType = {
  type: string;
  numbers: NumberItem[];
};

type NumberCategory = {
  category: string;
  types: NumberType[];
};

type Props = {
  numbers: NumberCategory[];
  entityId: string;
  entityType: "company" | "solution" | "topic";
};

/* ========================================================= */

function formatValue(n: NumberItem) {
  if (n.value === undefined || n.value === null) return "";

  const scaleMap: any = {
    millions: "M",
    billion: "Md",
    billions: "Md",
  };

  const scale = scaleMap[n.scale || ""] || "";
  const unit = n.unit || "";

  return [n.value, scale, unit]
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

  // 🔥 FIX CRITIQUE
  if (!Array.isArray(numbers) || numbers.length === 0) return null;

  return (
    <section className="space-y-3">
      <h2 className="text-xs font-semibold uppercase text-gray-400">
        Chiffres clés
      </h2>

      <div className="grid grid-cols-2 gap-3">
        {numbers.map((cat) =>
          cat.types.map((t) =>
            t.numbers.map((n) => (
              <div
                key={n.id_number}
                className="p-3 border rounded"
              >
                {(n.zone || n.period) && (
                  <div className="text-[10px] text-gray-400 mb-1">
                    {[n.zone, n.period]
                      .filter(Boolean)
                      .join(" — ")}
                  </div>
                )}

                <div className="text-sm font-semibold text-gray-900">
                  {formatValue(n)}
                </div>

                {n.label && (
                  <div className="text-xs text-gray-500 mt-1">
                    {n.label}
                  </div>
                )}
              </div>
            ))
          )
        )}
      </div>

      <button
        onClick={() =>
          openRightDrawer("numbers", entityId, "silent", {
            entityType,
          })
        }
        className="text-xs text-gray-400 hover:text-black"
      >
        Voir tous les chiffres →
      </button>
    </section>
  );
}
