"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import EntityDrawerLayout from "@/components/drawers/EntityDrawerLayout";
import DrawerHeader from "@/components/drawers/DrawerHeader";

/* =========================================================
   TYPES
========================================================= */

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

/* ========================================================= */

type Props = {
  id: string;
  entityType?: "company" | "topic" | "solution";
  onClose: () => void;
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

export default function NumberDrawer({
  id,
  entityType,
  onClose,
}: Props) {
  const [data, setData] = useState<NumberCategory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        if (!entityType) {
          setData([]);
          setLoading(false);
          return;
        }

        setLoading(true);

        const res = await api.get(
          `/numbers/entity?entity_type=${entityType}&entity_id=${id}`
        );

        setData(res.items ?? []);
      } catch (e) {
        console.error("❌ Numbers drawer load error", e);
        setData([]);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, entityType]);

  return (
    <EntityDrawerLayout onClose={onClose}>

      {/* HEADER */}
      <DrawerHeader
        title="Chiffres"
        variant="topic"
        onClose={onClose}
      />

      {/* CONTENT */}
      <div className="px-6 py-6 space-y-10">

        {loading ? (
          <p className="text-sm text-gray-400">
            Chargement...
          </p>
        ) : data.length === 0 ? (
          <p className="text-sm text-gray-400">
            Aucun chiffre disponible.
          </p>
        ) : (
          data.map((category) => (
            <section key={category.category} className="space-y-4">

              {/* CATEGORY */}
              <h2 className="text-xs font-semibold uppercase text-gray-400">
                {category.category}
              </h2>

              {category.types.map((type) => (
                <div key={type.type} className="space-y-3">

                  {/* TYPE */}
                  <div className="text-xs text-gray-500">
                    {type.type}
                  </div>

                  {/* GRID NUMBERS */}
                  <div className="grid grid-cols-2 gap-3">
                    {type.numbers.map((n) => (
                      <div
                        key={n.id_number}
                        className="p-3 border rounded"
                      >
                        {/* CONTEXTE */}
                        {(n.zone || n.period) && (
                          <div className="text-[10px] text-gray-400 mb-1">
                            {[n.zone, n.period]
                              .filter(Boolean)
                              .join(" — ")}
                          </div>
                        )}

                        {/* VALUE */}
                        <div className="text-sm font-semibold text-gray-900">
                          {formatValue(n)}
                        </div>

                        {/* LABEL */}
                        {n.label && (
                          <div className="text-xs text-gray-500 mt-1">
                            {n.label}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                </div>
              ))}
            </section>
          ))
        )}

      </div>

    </EntityDrawerLayout>
  );
}
