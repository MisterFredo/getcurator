"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

import NumberCard from "@/components/numbers/NumberCard";
import NumbersSelectionPanel from "@/components/numbers/NumbersSelectionPanel";
import NumbersHeader from "@/components/numbers/NumbersHeader";

/* ========================================================= */

type Universe = {
  id_universe: string;
  label: string;
};

type Concept = {
  id_concept: string;
  title: string;
};

/* ========================================================= */

export default function NumbersPage() {
  const LIMIT = 100;

  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");

  /* 🔥 univers (comme feed) */
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [activeUniverse, setActiveUniverse] = useState<string | null>(null);

  /* 🔥 concepts (NEW) */
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [activeConcepts, setActiveConcepts] = useState<string[]>([]);

  /* selection */
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  /* =========================================================
     LOAD NUMBERS
  ========================================================= */

  async function load(q?: string) {
    const finalQuery = (q ?? query)?.trim();

    setLoading(true);

    try {
      const params = new URLSearchParams();

      params.append("limit", String(LIMIT));

      if (finalQuery) params.append("q", finalQuery);
      if (activeUniverse) params.append("universe_id", activeUniverse);

      if (activeConcepts.length > 0) {
        activeConcepts.forEach((c) =>
          params.append("concept_ids", c)
        );
      }

      // ✅ NEW ROUTE (curator)
      const res = finalQuery
        ? await api.get(`/curator/numbers?${params}`)
        : await api.get(`/curator/numbers/latest?${params}`);

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

  useEffect(() => {
    async function loadUniverses() {
      try {
        const res = await api.get("/universe/list-for-user");
        setUniverses(res?.universes || []);
      } catch (e) {
        console.error("❌ universe load error", e);
      }
    }

    loadUniverses();
  }, []);

  /* =========================================================
     LOAD CONCEPTS (NEW)
  ========================================================= */

  useEffect(() => {
    async function loadConcepts() {
      try {
        const res = await api.get("/curator/concepts");
        setConcepts(res?.items || []);
      } catch (e) {
        console.error("❌ concepts load error", e);
      }
    }

    loadConcepts();
  }, []);

  /* =========================================================
     RELOAD
  ========================================================= */

  useEffect(() => {
    load();
  }, [activeUniverse, activeConcepts]);

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(item: any) {
    const id = item.ID_NUMBER;

    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );

    setIsPanelOpen(true);
  }

  /* =========================================================
     CONCEPT TOGGLE
  ========================================================= */

  function toggleConcept(id: string) {
    setActiveConcepts((prev) =>
      prev.includes(id)
        ? prev.filter((c) => c !== id)
        : [...prev, id]
    );
  }

  /* =========================================================
     GROUP BY CONTENT
  ========================================================= */

  function groupByContent(items: any[]) {
    const map: Record<string, any[]> = {};

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
      <div className="xl:col-span-2 space-y-6">

        {/* HEADER */}
        <NumbersHeader
          query={query}
          setQuery={setQuery}
          onSearch={(q) => load(q)}
        />

        {/* =====================================================
            UNIVERS FILTER
        ===================================================== */}
        <div className="flex gap-2 flex-wrap">

          <button
            onClick={() => setActiveUniverse(null)}
            className={`px-3 py-1 text-xs rounded ${
              !activeUniverse
                ? "bg-black text-white"
                : "bg-gray-100"
            }`}
          >
            Tous
          </button>

          {universes.map((u) => (
            <button
              key={u.id_universe}
              onClick={() => setActiveUniverse(u.id_universe)}
              className={`px-3 py-1 text-xs rounded ${
                activeUniverse === u.id_universe
                  ? "bg-black text-white"
                  : "bg-gray-100"
              }`}
            >
              {u.label}
            </button>
          ))}

        </div>

        {/* =====================================================
            CONCEPTS FILTER (NEW)
        ===================================================== */}
        <div className="flex gap-2 flex-wrap">

          {concepts.map((c) => {

            const active = activeConcepts.includes(c.id_concept);

            return (
              <button
                key={c.id_concept}
                onClick={() => toggleConcept(c.id_concept)}
                className={`px-3 py-1 text-xs rounded border ${
                  active
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-200"
                }`}
              >
                {c.title}
              </button>
            );
          })}

        </div>

        {/* LOADING */}
        {loading && (
          <p className="text-sm text-gray-400">
            Chargement...
          </p>
        )}

        {/* CONTENT */}
        {!loading &&
          grouped.map(([title, groupItems]) => (

            <section key={title} className="space-y-2">

              <div className="flex justify-between items-center">
                <div className="text-sm font-semibold">
                  {title}
                </div>

                <div className="text-xs text-gray-400">
                  {groupItems.length}
                </div>
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
        <div className="xl:col-span-1 sticky top-6">
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
