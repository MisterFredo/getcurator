"use client";

import { useState, useEffect } from "react";

/* ========================================================= */

type Universe = {
  id: string;
  label: string;
  count?: number;
};

type Props = {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;

  universes: Universe[];
  selectedUniverse: string | null;
  onSelectUniverse: (id: string | null) => void;

  loading?: boolean; // ✅ AJOUT
};

/* ========================================================= */

export default function FeedHeader({
  query,
  setQuery,
  onSearch,
  universes,
  selectedUniverse,
  onSelectUniverse,
  loading = false, // ✅ default safe
}: Props) {
  const [input, setInput] = useState(query);

  // 🔥 sync input quand query change (important UX)
  useEffect(() => {
    setInput(query);
  }, [query]);

  function triggerSearch() {
    if (loading) return; // ✅ bloque double clic

    const value = input.trim();
    setQuery(value);
    onSearch();
  }

  return (
    <div className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-gray-100 pb-4 pt-2 space-y-3">

      {/* =====================================================
         UNIVERS FILTER
      ===================================================== */}
      <div className="flex gap-2 overflow-x-auto scrollbar-none px-1">

        <button
          onClick={() => !loading && onSelectUniverse(null)}
          className={`
            flex items-center gap-1
            whitespace-nowrap
            px-3 py-1.5 rounded-full text-xs border transition-all
            ${
              selectedUniverse === null
                ? "bg-black text-white border-black shadow-sm"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
            }
            ${loading ? "opacity-50 cursor-not-allowed" : ""}
          `}
        >
          Tous
        </button>

        {universes.map((u) => {
          const active = selectedUniverse === u.id;

          return (
            <button
              key={u.id}
              onClick={() => !loading && onSelectUniverse(u.id)}
              className={`
                flex items-center gap-1
                whitespace-nowrap
                px-3 py-1.5 rounded-full text-xs border transition-all
                ${
                  active
                    ? "bg-black text-white border-black shadow-sm scale-[1.02]"
                    : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                }
                ${loading ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              {u.label}

              {u.count !== undefined && (
                <span
                  className={`
                    ml-1 text-[10px] px-1.5 py-0.5 rounded-full
                    ${
                      active
                        ? "bg-white/20 text-white"
                        : "bg-gray-100 text-gray-500"
                    }
                  `}
                >
                  {u.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* =====================================================
         SEARCH
      ===================================================== */}
      <div className="flex items-center gap-3 px-1">

        <input
          value={input}
          disabled={loading} // ✅ important
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") triggerSearch();
          }}
          placeholder="Rechercher (Amazon, CTV, Retail media…)"
          className="
            flex-1
            border border-gray-200
            rounded-lg
            px-4 py-2
            text-sm
            bg-white
            focus:outline-none focus:ring-2 focus:ring-black
            disabled:opacity-50
          "
        />

        <button
          onClick={triggerSearch}
          disabled={loading} // ✅ clé
          className="
            px-4 py-2
            rounded-lg
            bg-black text-white
            text-sm
            hover:opacity-90 transition
            disabled:opacity-50 disabled:cursor-not-allowed
          "
        >
          {loading ? "..." : "Rechercher"} {/* ✅ feedback simple */}
        </button>

      </div>
    </div>
  );
}
