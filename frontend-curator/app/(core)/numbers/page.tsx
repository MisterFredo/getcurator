"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

import NumberCard from "@/components/numbers/NumberCard";
import NumbersSelectionPanel from "@/components/numbers/NumbersSelectionPanel";
import NumbersHeader from "@/components/numbers/NumbersHeader";

/* ========================================================= */

type NumberItem = {
  id: string;
  context_title?: string;
  TYPE?: string;
  [key: string]: any;
};

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function NumbersPage() {
  const LIMIT = 100;

  const [items, setItems] = useState<NumberItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");

  // 🔥 UNIVERS
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverse, setSelectedUniverse] = useState<string>("");

  // 🔥 SELECTION
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  /* =========================================================
     LOAD
  ========================================================= */

  async function load(q?: string) {
    const finalQuery = (q ?? query)?.trim();

    setLoading(true);

    try {
      const params = new URLSearchParams();

      params.append("limit", String(LIMIT));

      if (finalQuery) params.append("q", finalQuery);
      if (selectedUniverse) params.append("universe_id", selectedUniverse);

      const res = await api.get(`/curator/numbers?${params.toString()}`);

      setItems(res?.items ?? []);
    } catch (e) {
      console.error("❌ Numbers load error", e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  /* =========================================================
     LOAD UNIVERS
  ========================================================= */

  async function loadUniverses() {
    try {
      const res = await api.get("/universe/list");
      setUniverses(res?.universes || []);
    } catch (e) {
      console.error("❌ universe load error", e);
    }
  }

  useEffect(() => {
    load();
    loadUniverses();
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

  /* ========================================================= */

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

      {/* LEFT */}
      <div className="xl:col-span-2 space-y-8">

        {/* HEADER */}
        <NumbersHeader
          query={query}
          setQuery={setQuery}
          onSearch={(q) => load(q)}
        />

        {/* 🔥 UNIVERSE FILTER */}
        <div className="flex gap-2 items-center">

          <select
            value={selectedUniverse}
            onChange={(e) => {
              setSelectedUniverse(e.target.value);
            }}
            className="border p-2 text-sm rounded"
          >
            <option value="">Tous les univers</option>
            {universes.map((u) => (
              <option key={u.id_universe} value={u.id_universe}>
                {u.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => load()}
            className="bg-black text-white px-3 py-2 text-sm rounded"
          >
            Appliquer
          </button>

        </div>

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
        {!loading && items.length === 0 && (
          <p className="text-sm text-gray-400">
            Aucun chiffre disponible.
          </p>
        )}

        {/* CONTENT */}
        {!loading &&
          grouped.map(([title, groupItems]) => (

            <section key={title} className="space-y-3">

              {/* TITLE */}
              <div className="flex items-center justify-between">

                <div className="text-sm font-semibold text-gray-800">
                  {title}
                </div>

                <div className="text-xs text-gray-400">
                  {groupItems.length} chiffres
                </div>

              </div>

              {/* GRID CARDS */}
              <div className="
                grid
                grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5
                gap-3
              ">

                {groupItems.map((item) => {

                  const selected = selectedIds.includes(item.id);

                  return (
                    <NumberCard
                      key={item.id}
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
