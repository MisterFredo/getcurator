"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

import NumbersSelectionPanel from "@/components/numbers/NumbersSelectionPanel";
import NumbersHeader from "@/components/numbers/NumbersHeader";

/* ========================================================= */

type NumberItem = {
  id: string;
  label?: string;
  value?: number;
  unit?: string;

  zone?: string;
  period?: string;
  actor?: string;

  context_title?: string;
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
        `/curator/numbers?limit=${LIMIT}${
          finalQuery
            ? `&q=${encodeURIComponent(finalQuery)}`
            : ""
        }`
      );

      setItems(res?.items ?? []);
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
    const id = item.id;

    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );

    setIsPanelOpen(true);
  }

  /* =========================================================
     GROUP BY CONTENT
  ========================================================= */

  function groupByContent(items: NumberItem[]) {
    const map: Record<string, NumberItem[]> = {};

    items.forEach((item) => {
      const key = item.context_title || "Autres";

      if (!map[key]) map[key] = [];
      map[key].push(item);
    });

    return Object.entries(map);
  }

  const grouped = groupByContent(items);

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
          grouped.map(([title, groupItems]) => (

            <section key={title} className="space-y-4">

              {/* 🔹 CONTENT TITLE */}
              <div className="text-sm font-semibold text-gray-800">
                {title}
              </div>

              {/* 🔹 NUMBERS LIST */}
              <div className="space-y-2">

                {groupItems.map((item) => {

                  const selected = selectedIds.includes(item.id);

                  return (
                    <div
                      key={item.id}
                      onClick={() => toggleSelect(item)}
                      className={`
                        border rounded p-3 cursor-pointer
                        ${selected ? "border-blue-500 bg-blue-50" : "hover:bg-gray-50"}
                      `}
                    >

                      <div className="text-sm font-medium">
                        {item.label}
                      </div>

                      <div className="text-xs text-gray-500">
                        {item.value} {item.unit} • {item.zone} • {item.period}
                      </div>

                      {item.actor && (
                        <div className="text-xs text-gray-400">
                          {item.actor}
                        </div>
                      )}

                    </div>
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
