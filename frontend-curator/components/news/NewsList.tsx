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

      <div className="
        text-center
        py-16
      ">

        <div className="
          text-sm
          text-gray-400
        ">
          No news found
        </div>

      </div>

    );
  }

  /* =========================================================
     SKELETON
  ========================================================= */

  function SkeletonRow() {

    return (

      <div className="
        animate-pulse
        py-4
        border-b
        border-gray-100
      ">

        <div className="
          flex
          items-start
          gap-4
        ">

          <div className="
            w-12
            h-12
            rounded-xl
            bg-gray-200
            shrink-0
          " />

          <div className="
            flex-1
            space-y-2
          ">

            <div className="
              h-3
              w-24
              rounded
              bg-gray-200
            " />

            <div className="
              flex
              gap-2
            ">

              <div className="
                h-5
                w-16
                rounded-full
                bg-gray-200
              " />

              <div className="
                h-5
                w-20
                rounded-full
                bg-gray-200
              " />

            </div>

            <div className="
              h-4
              w-3/4
              rounded
              bg-gray-200
            " />

            <div className="
              h-3
              w-full
              rounded
              bg-gray-100
            " />

            <div className="
              h-3
              w-2/3
              rounded
              bg-gray-100
            " />

          </div>

        </div>

      </div>

    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="space-y-4">

      {/* =====================================================
          LIST
      ===================================================== */}

      <div className="
        bg-white
        border
        border-gray-100
        rounded-xl
        overflow-hidden
      ">

        {/* LOADING INITIAL */}

        {loading &&
          items.length === 0 && (

            <div>

              {[...Array(5)].map(
                (_, i) => (
                  <SkeletonRow
                    key={i}
                  />
                )
              )}

            </div>

          )}

        {/* ITEMS */}

        {!(
          loading &&
          items.length === 0
        ) && (
          <div>

            {items.map((item) => (

              <NewsCard
                key={item.id}
                item={item}
                selected={selectedIds.includes(item.id)}
                onToggleSelect={onToggleSelect}
                onClickBadge={onClickBadge}
              />

            ))}

          </div>
        )}

      </div>

      {/* =====================================================
          LOAD MORE
      ===================================================== */}

      {hasMore && items.length > 0 && (

        <div className="
          flex
          flex-col
          items-center
          gap-2
          pt-6
        ">

          {loading && (

            <div className="
              text-xs
              text-gray-400
            ">
              Loading more...
            </div>

          )}

          <button
            onClick={onLoadMore}
            disabled={loading}
            className="
              text-sm
              px-5
              py-2
              rounded-full
              bg-black
              text-white
              hover:opacity-90
              transition
              disabled:opacity-50
              disabled:cursor-not-allowed
            "
          >
            {loading
              ? "Loading…"
              : "Load more"}
          </button>

        </div>

      )}

    </div>

  );
}
