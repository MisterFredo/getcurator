"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

import NumberCard from "@/components/numbers/NumberCard";
import NumbersSelectionPanel from "@/components/numbers/NumbersSelectionPanel";
import NumbersHeader from "@/components/numbers/NumbersHeader";

/* ========================================================= */

type NumberItem = {
  ID_NUMBER: string;
  TYPE?: string;
  [key: string]: any;
};

/* ========================================================= */

export default function NumbersPage() {
  const LIMIT = 100;

  const [items, setItems] = useState<NumberItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");

  /* SELECTION */
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  /* =========================================================
     LOAD
  ========================================================= */

  async function load(q?: string) {
    const finalQuery = (q ?? query)?.trim();

    setLoading(true);

    try {
      const res = await api.get(
        `/numbers/feed?limit=${LIMIT}${
          finalQuery
            ? `&query=${encodeURIComponent(finalQuery)}`
            : ""
        }`
      );

      const data = res?.items ?? [];

      setItems(data);
    } catch (e) {
      console.error("❌ Numbers load error", e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(item: NumberItem) {
    const id = item.ID_NUMBER;

    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );

    setIsPanelOpen(true);
  }

  /* =========================================================
     GROUP BY TYPE
  ========================================================= */

  function groupByType(items: NumberItem[]) {
    const map: Record<string, NumberItem[]> = {};

    items.forEach((item) => {
      const key = item.TYPE ?? "Autres"; // ⚠️ seul fallback toléré ici

      if (!map[key]) map[key] = [];
      map[key].push(item);
    });

    // tri alphabétique des groupes
    return Object.fromEntries(
      Object.entries(map).sort(([a], [b]) =>
        a.localeCompare(b, "fr", { sensitivity: "base" })
      )
    );
  }

  const grouped = groupByType(items);

  const hasContent = items.length > 0;

  /* ========================================================= */

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

      {/* LEFT */}
      <div className="xl:col-span-2 space-y-10">

        {/* HEADER */}
        <NumbersHeader
          query={query}
          setQuery={setQuery}
          onSearch={(q) => load(q)}
        />

        {/* COUNT */}
        {!loading && (
          <div className="text-xs text-gray-400">
            {items.length} chiffres
          </div>
        )}

        {/* LOADING */}
        {loading && (
          <p className="text-sm text-gray-400">
            Chargement des chiffres...
          </p>
        )}

        {/* EMPTY */}
        {!loading && !hasContent && (
          <p className="text-sm text-gray-400">
            Aucun chiffre disponible.
          </p>
        )}

        {/* CONTENT */}
        {!loading && hasContent &&
          Object.entries(grouped).map(([type, groupItems]) => (
            <section key={type} className="space-y-4">

              <div className="flex items-center justify-between">
                <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {type}
                </h2>

                <span className="text-xs text-gray-300">
                  {groupItems.length}
                </span>
              </div>

              <div className="
                grid
                grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5
                gap-3
              ">
                {groupItems.map((item) => {
                  const selected = selectedIds.includes(item.ID_NUMBER);

                  return (
                    <NumberCard
                      key={item.ID_NUMBER}
                      item={item}
                      selected={selected}
                      onClick={() => toggleSelect(item)}
                    />
                  );
                })}
              </div>

            </section>
          ))}

      </div>

      {/* RIGHT PANEL */}
      {isPanelOpen && (
        <div className="xl:col-span-1 sticky top-6 h-[calc(100vh-120px)]">
          <NumbersSelectionPanel
            items={items}
            selectedIds={selectedIds}
            onClose={() => setIsPanelOpen(false)}
          />
        </div>
      )}

    </div>
  );
}
