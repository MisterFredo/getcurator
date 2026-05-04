"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

import NumberCard from "@/components/numbers/NumberCard";
import NumbersSelectionPanel from "@/components/numbers/NumbersSelectionPanel";
import NumbersHeader from "@/components/numbers/NumbersHeader";
import AnalysisDrawer from "@/components/drawers/AnalysisDrawer";

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

  const [universes, setUniverses] = useState<Universe[]>([]);
  const [activeUniverse, setActiveUniverse] = useState<string | null>(null);

  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [activeConcepts, setActiveConcepts] = useState<string[]>([]);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const [selectedItem, setSelectedItem] = useState<any | null>(null);

  /* ========================================================= */

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

  /* ========================================================= */

  useEffect(() => {
    api.get("/universe/list-for-user")
      .then((res) => setUniverses(res?.universes || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    api.get("/curator/concepts")
      .then((res) => setConcepts(res?.items || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    load();
  }, [activeUniverse, activeConcepts]);

  /* ========================================================= */

  function toggleSelect(item: any) {
    const id = item.ID_NUMBER;

    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((i) => i !== id)
        : [...prev, id]
    );

    setIsPanelOpen(true);
  }

  function toggleConcept(id: string) {
    setActiveConcepts((prev) =>
      prev.includes(id)
        ? prev.filter((c) => c !== id)
        : [...prev, id]
    );
  }

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
      <div className="xl:col-span-2 space-y-8">

        {/* UNIVERS */}
        <div className="flex gap-2 overflow-x-auto scrollbar-none px-1">
          <button
            onClick={() => setActiveUniverse(null)}
            className={`px-2.5 py-1 rounded-full text-[11px] border ${
              activeUniverse === null
                ? "bg-black text-white border-black"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
            }`}
          >
            Tous
          </button>

          {universes.map((u) => {
            const active = activeUniverse === u.id_universe;

            return (
              <button
                key={u.id_universe}
                onClick={() => setActiveUniverse(u.id_universe)}
                className={`px-2.5 py-1 rounded-full text-[11px] border ${
                  active
                    ? "bg-black text-white border-black"
                    : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                }`}
              >
                {u.label}
              </button>
            );
          })}
        </div>

        {/* SEARCH */}
        <NumbersHeader
          query={query}
          setQuery={setQuery}
          onSearch={(q) => load(q)}
        />

        {/* CONCEPTS */}
        <div className="flex gap-2 flex-wrap">
          {concepts.map((c) => {
            const active = activeConcepts.includes(c.id_concept);

            return (
              <button
                key={c.id_concept}
                onClick={() => toggleConcept(c.id_concept)}
                className={`px-3 py-1 text-xs rounded-full border ${
                  active
                    ? "bg-gray-800 text-white border-gray-800"
                    : "bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100"
                }`}
              >
                {c.title}
              </button>
            );
          })}
        </div>

        {/* LOADING */}
        {loading && (
          <p className="text-sm text-gray-400">Chargement...</p>
        )}

        {/* CONTENT */}
        {!loading &&
          grouped.map(([title, groupItems]) => {

            const firstItem = groupItems[0];

            const contentDate =
              firstItem?.published_at ||
              firstItem?.PUBLISHED_AT ||
              null;

            return (
              <section
                key={title}
                className="space-y-3 pb-6 border-b border-gray-100"
              >

                {/* HEADER */}
                <div
                  onClick={() => {
                    if (!firstItem?.ID_CONTENT) return;

                    setSelectedItem({
                      id: firstItem.ID_CONTENT,
                      type: "analysis",
                    });
                  }}
                  className="cursor-pointer group flex items-center justify-between"
                >
                  <div>
                    {/* TITLE */}
                    <div className="text-sm font-semibold text-gray-900 group-hover:underline">
                      {title}
                    </div>

                    {/* META */}
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                      <span>{groupItems.length} chiffre(s)</span>

                      {contentDate && (
                        <span>
                          • {new Date(contentDate).toLocaleDateString("fr-FR")}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-xs text-gray-400 group-hover:text-gray-600">
                      Voir →
                  </div>
                </div>

                {/* GRID */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
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
            );
          })}

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

      {/* DRAWER */}
      {selectedItem && (
        <AnalysisDrawer
          id={selectedItem.id}
          onClose={() => setSelectedItem(null)}
        />
      )}

    </div>
  );
}
