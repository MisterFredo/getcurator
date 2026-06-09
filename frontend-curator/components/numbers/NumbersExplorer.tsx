"use client";

import NumberCard from "./NumberCard";

export default function NumbersExplorer({
  query,
  setQuery,
  onSearch,
  items,
  loading,
  hasMore,
  onLoadMore,
  onSelectItem,
}: any) {
  return (
    <div className="space-y-6">

      {/* SEARCH */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
          className="w-full px-3 py-2 border rounded text-sm"
        />
        <button
          onClick={onSearch}
          className="px-4 py-2 border rounded text-sm"
        >
          Search
        </button>
      </div>

      {/* LIST */}
      <div className="divide-y">
        {items.map((item: any) => (
          <NumberCard
            key={item.id_number}
            item={item}
            onClick={() => onSelectItem(item)}
          />
        ))}
      </div>

      {/* LOAD MORE */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onLoadMore}
            className="text-xs px-4 py-2 border rounded"
          >
            {loading ? "Chargement..." : "Voir plus"}
          </button>
        </div>
      )}
    </div>
  );
}
