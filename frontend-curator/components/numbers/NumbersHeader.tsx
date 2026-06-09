"use client";

import { useState } from "react";

/* ========================================================= */

type Props = {
  query: string;
  setQuery: (q: string) => void;
  onSearch: (q: string) => void;   // 🔥 CHANGEMENT
};

/* ========================================================= */

export default function NumbersHeader({
  query,
  setQuery,
  onSearch,
}: Props) {

  const [input, setInput] = useState(query);

  function triggerSearch() {
    const value = input.trim();

    setQuery(value);      // OK pour synchro globale
    onSearch(value);      // 🔥 on passe la vraie valeur
  }

  return (
    <div className="space-y-3">
      {/* SEARCH */}
      <div className="flex items-center gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") triggerSearch();
          }}
          placeholder="Ex : Amazon, CPM, France..."
          className="
            flex-1
            border border-gray-200
            rounded-lg
            px-4 py-2
            text-sm
            focus:outline-none focus:ring-2 focus:ring-black
          "
        />

        <button
          onClick={triggerSearch}
          className="
            px-4 py-2
            rounded-lg
            bg-black text-white
            text-sm
            hover:opacity-90 transition
          "
        >
          Search
        </button>
      </div>

    </div>
  );
}
