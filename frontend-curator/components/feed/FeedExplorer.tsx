"use client";

import FeedHeader from "@/components/feed/FeedHeader";
import FeedList from "@/components/feed/FeedList";

import type { FeedItem, FeedBadge } from "@/types/feed";

/* ========================================================= */

type Universe = {
  id: string;
  label: string;
};

type Props = {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;

  universes: Universe[];
  selectedUniverse: string | null;
  onSelectUniverse: (id: string | null) => void;

  items: FeedItem[];
  total: number;
  loading: boolean;
  hasMore: boolean;

  onLoadMore: () => void;
  onSelectItem: (item: FeedItem) => void;
  onClickBadge: (badge: FeedBadge) => void;

  loadingItemId: string | null;

  selectedIds: string[];
  onToggleSelect: (item: FeedItem) => void;
};

/* ========================================================= */

export default function FeedExplorer({
  query,
  setQuery,
  onSearch,

  universes,
  selectedUniverse,
  onSelectUniverse,

  items,
  total,
  loading,
  hasMore,

  onLoadMore,
  onSelectItem,
  onClickBadge,

  loadingItemId,

  selectedIds,
  onToggleSelect,
}: Props) {
  return (
    <div className="space-y-8">

      {/* HEADER */}
      <FeedHeader
        query={query}
        setQuery={setQuery}
        onSearch={onSearch}

        universes={universes}
        selectedUniverse={selectedUniverse}
        onSelectUniverse={onSelectUniverse}

        loading={loading} // ✅ AJOUT
      />

      {/* LIST */}
      <FeedList
        title="Results"
        items={items}
        total={total}
        loading={loading}
        hasMore={hasMore}

        onLoadMore={!loading ? onLoadMore : () => {}} // ✅ FIX

        onSelectItem={onSelectItem}
        onClickBadge={onClickBadge}

        loadingItemId={loadingItemId}

        selectedIds={selectedIds}
        onToggleSelect={onToggleSelect}
      />

    </div>
  );
}
