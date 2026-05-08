"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import EntityDrawerLayout from "@/components/drawers/EntityDrawerLayout";
import DrawerHeader from "@/components/drawers/DrawerHeader";

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
  id: string;
  entityType?: "company" | "topic" | "solution";
  onClose: () => void;
};

/* ========================================================= */

function formatValue(n: NumberItem) {
  if (n.VALUE === undefined || n.VALUE === null) return "";

  const scaleMap: any = {
    millions: "M",
    billion: "Md",
    billions: "Md",
  };

  const scale = scaleMap[n.SCALE || ""] || "";
  const unit = n.UNIT || "";

  return [n.VALUE, scale, unit]
    .filter(Boolean)
    .join(" ");
}

/* ========================================================= */

export default function NumberDrawer({
  id,
  entityType,
  onClose,
}: Props) {
  const [data, setData] = useState<NumberItem[]>([]);
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

  /* =========================================================
     GROUP BY CATEGORY / TYPE (OPTIONNEL MAIS PROPRE)
  ========================================================= */

  const grouped: Record<string, Record<string, NumberItem[]>> = {};

  data.forEach((n) => {
    const cat = n.CATEGORY || "Autres";
    const type = n.TYPE || "Autres";

    if (!grouped[cat]) grouped[cat] = {};
    if (!grouped[cat][type]) grouped[cat][type] = [];

    grouped[cat][type].push(n);
  });

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <EntityDrawerLayout onClose={onClose}>

      <DrawerHeader
        title="Chiffres"
        variant="topic"
        onClose={onClose}
      />

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
          Object.entries(grouped).map(([category, types]) => (

            <section key={category} className="space-y-4">

              {/* CATEGORY */}
              <h2 className="text-xs font-semibold uppercase text-gray-400">
                {category}
              </h2>

              {Object.entries(types).map(([type, numbers]) => (

                <div key={type} className="space-y-3">

                  {/* TYPE */}
                  <div className="text-xs text-gray-500">
                    {type}
                  </div>

                  {/* GRID */}
                  <div className="grid grid-cols-2 gap-3">

                    {numbers.map((n) => (
                      <div
                        key={n.ID_NUMBER}
                        className="p-3 border rounded space-y-1"
                      >

                        {/* CONTEXTE */}
                        {(n.ZONE || n.PERIOD) && (
                          <div className="text-[10px] text-gray-400">
                            {[n.ZONE, n.PERIOD]
                              .filter(Boolean)
                              .join(" — ")}
                          </div>
                        )}

                        {/* VALUE */}
                        <div className="text-sm font-semibold text-gray-900">
                          {formatValue(n)}
                        </div>

                        {/* LABEL */}
                        {n.LABEL && (
                          <div className="text-xs text-gray-500">
                            {n.LABEL}
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
