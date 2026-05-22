"use client";

import FeedHeader from "@/components/feed/FeedHeader";
import FeedList from "@/components/feed/FeedList";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

/* ========================================================= */

type Universe = {
  id: string;
  label: string;
};

type Props = {

  query: string;

  setQuery: (
    q: string
  ) => void;

  onSearch: (
    q: string
  ) => void;

  universes: Universe[];

  selectedUniverse:
    string | null;

  onSelectUniverse: (
    id: string | null
  ) => void;

  selectedType: string;

  onSelectType: (
    type: string
  ) => void;

  items: FeedItem[];

  total: number;

  loading: boolean;

  hasMore: boolean;

  onLoadMore: () => void;

  onSelectItem: (
    item: FeedItem
  ) => void;

  onClickBadge: (
    badge: FeedBadge
  ) => void;

  loadingItemId:
    string | null;

  selectedIds: string[];

  onToggleSelect: (
    item: FeedItem
  ) => void;

  // 🔥 NEW
  preferences: {
    COMPANY: string[];
    TOPIC: string[];
    SOLUTION: string[];
  };

  onToggleFavorite: (
    companyId: string,
    isFav: boolean
  ) => void;

  // 🔥 NEW
  userLang: string;
};

/* ========================================================= */

export default function FeedExplorer({

  query,
  setQuery,
  onSearch,

  universes,
  selectedUniverse,
  onSelectUniverse,

  selectedType,
  onSelectType,

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

  // 🔥 NEW
  preferences,
  onToggleFavorite,

  // 🔥 NEW
  userLang,

}: Props) {

  return (

    <div className="
      space-y-8
    ">

      {/* =====================================================
         HEADER
      ===================================================== */}

      <FeedHeader
        query={query}

        setQuery={setQuery}

        onSearch={(q) =>
          onSearch(q)
        }

        universes={universes}

        selectedUniverse={
          selectedUniverse
        }

        onSelectUniverse={
          onSelectUniverse
        }

        selectedType={
          selectedType
        }

        onSelectType={
          onSelectType
        }

        loading={loading}
      />

      {/* =====================================================
         LIST
      ===================================================== */}

      <FeedList

        userLang={userLang}

        title="Results"

        items={items}

        total={total}

        loading={loading}

        hasMore={hasMore}

        onLoadMore={
          !loading
            ? onLoadMore
            : () => {}
        }

        onSelectItem={
          onSelectItem
        }

        onClickBadge={
          onClickBadge
        }

        loadingItemId={
          loadingItemId
        }

        selectedIds={
          selectedIds
        }

        onToggleSelect={
          onToggleSelect
        }

        // 🔥 NEW
        preferences={preferences}

        onToggleFavorite={
          onToggleFavorite
        }
      />

    </div>
  );
}
