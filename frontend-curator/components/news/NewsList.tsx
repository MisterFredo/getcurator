"use client";

import NewsCard from "./NewsCard";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

/* ========================================================= */

type Props = {
  items: FeedItem[];

  loading: boolean;

  hasMore: boolean;

  selectedIds: string[];

  onToggleSelect: (
    item: FeedItem
  ) => void;

  onClickBadge?: (
    badge: FeedBadge
  ) => void;

  onLoadMore: () => void;
};

/* ========================================================= */

export default function NewsList({
  items,
  loading,
  hasMore,
  selectedIds,
  onToggleSelect,
  onClickBadge,
  onLoadMore,
}: Props) {

  /* =========================================================
     EMPTY
  ========================================================= */

  if (!loading && items.length === 0) {

    return (

      <div
        className="
          bg-white
          border
          rounded-xl
          p-10
          text-center
          text-sm
          text-gray-500
        "
      >
        No news found
      </div>

    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="space-y-4">

      {/* LIST */}

      {items.map((item) => (

        <NewsCard
          key={item.id}
          item={item}
          selected={selectedIds.includes(item.id)}
          onToggleSelect={onToggleSelect}
          onClickBadge={onClickBadge}
        />

      ))}

      {/* LOADING */}

      {loading && (

        <div
          className="
            text-center
            text-sm
            text-gray-500
            py-6
          "
        >
          Loading...
        </div>

      )}

      {/* LOAD MORE */}

      {!loading && hasMore && (

        <div className="flex justify-center pt-4">

          <button
            onClick={onLoadMore}
            className="
              px-4
              py-2
              rounded-lg
              border
              bg-white
              hover:bg-gray-50
              text-sm
            "
          >
            Load more
          </button>

        </div>

      )}

    </div>

  );
}
