"use client";

import { useState, useMemo } from "react";

import FeedItemCard from "@/components/feed/FeedItemCard";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

/* ========================================================= */

type Props = {
  items: FeedItem[] | any;

  loading: boolean;

  hasMore: boolean;

  onLoadMore: () => Promise<void> | void;

  onSelectItem: (
    item: FeedItem
  ) => void;

  title?: string;

  total?: number;

  mode?: "text" | "filters";

  onClickBadge?: (
    badge: FeedBadge
  ) => void;

  loadingItemId?:
    string | null;

  selectedIds?: string[];

  onToggleSelect?: (
    item: FeedItem
  ) => void;

  // 🔥 NEW
  preferences?: string[];

  onToggleFavorite?: (
    companyId: string,
    isFav: boolean
  ) => void;
};

/* ========================================================= */

export default function FeedList({
  items,
  loading,
  hasMore,
  onLoadMore,
  onSelectItem,
  title,
  total,
  mode = "filters",
  onClickBadge,
  loadingItemId,

  selectedIds = [],
  onToggleSelect,

  // 🔥 NEW
  preferences = [],
  onToggleFavorite,

}: Props) {

  const [isFetchingMore, setIsFetchingMore] =
    useState(false);

  /* =========================================================
     SAFE ITEMS
  ========================================================= */

  const safeItems: FeedItem[] =
    useMemo(() => {

      if (!Array.isArray(items)) {

        console.warn(
          "⚠️ FeedList received non-array items:",
          items
        );

        return [];
      }

      return items;

    }, [items]);

  /* =========================================================
     LOAD MORE
  ========================================================= */

  async function handleLoadMore() {

    if (
      loading ||
      isFetchingMore
    ) return;

    try {

      setIsFetchingMore(true);

      await onLoadMore();

    } finally {

      setIsFetchingMore(false);

    }
  }

  /* =========================================================
     HEADER
  ========================================================= */

  const headerLabel =
    useMemo(() => {

      if (!title) return null;

      return (

        <div className="
          flex
          items-center
          justify-between
        ">

          <div className="
            text-sm
            font-semibold
            text-gray-700
          ">
            {title}
          </div>

          {total !== undefined && (

            <div className="
              text-xs
              text-gray-400
            ">
              {total} results
            </div>

          )}

        </div>

      );

    }, [title, total]);

  /* =========================================================
     SKELETON
  ========================================================= */

  function SkeletonRow() {

    return (

      <div className="
        animate-pulse
        space-y-2
        py-3
        border-b
        border-gray-100
      ">

        <div className="
          h-3
          bg-gray-200
          rounded
          w-1/4
        " />

        <div className="
          h-4
          bg-gray-200
          rounded
          w-3/4
        " />

        <div className="
          h-3
          bg-gray-200
          rounded
          w-2/3
        " />

      </div>

    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      space-y-4
    ">

      {headerLabel}

      {/* EMPTY */}

      {!loading &&
        safeItems.length === 0 && (

        <div className="
          text-center
          py-16
        ">

          <div className="
            text-sm
            text-gray-400
          ">

            {mode === "text"
              ? "No results found"
              : "No data for selected filters"}

          </div>

        </div>

      )}

      {/* LOADING INITIAL */}

      {loading &&
        safeItems.length === 0 && (

        <div className="
          space-y-3
        ">

          {[...Array(5)].map((_, i) => (

            <SkeletonRow key={i} />

          ))}

        </div>

      )}

      {/* ITEMS */}

      <div className="
        divide-y
        divide-gray-100
        rounded-xl
        bg-white
        border
        border-gray-100
        overflow-hidden
      ">

        {safeItems.map((item) => {

          const isSelected =
            selectedIds.includes(item.id);

          // 🔥 FAVORITE LOGIC
          const companyIds =
            Array.isArray(item.companies)
              ? item.companies.map(
                  (c: any) => c.id_company
                )
              : [];

          const topicIds =
            Array.isArray(item.topics)
              ? item.topics.map(
                  (t: any) => t.id_topic
                )
              : [];

          const solutionIds =
            Array.isArray(item.solutions)
              ? item.solutions.map(
                  (s: any) => s.id_solution
                )
              : [];

          const isFavorite =

            companyIds.some(
              (id: string) =>
                preferences.includes(id)
            )

            || topicIds.some(
              (id: string) =>
                preferences.includes(id)
            )

            || solutionIds.some(
              (id: string) =>
                preferences.includes(id)
            );

          return (

            <div
              key={`${item.type}-${item.id}`}
              className={`
                relative
                flex
                items-start
                gap-3
                px-3
                py-2

                ${
                  isSelected
                    ? "bg-gray-50"
                    : ""
                }
              `}
            >

              {/* CHECKBOX */}

              <input
                type="checkbox"
                checked={isSelected}
                onChange={() =>
                  onToggleSelect?.(item)
                }
                className="
                  mt-2
                "
              />

              {/* CONTENT */}

              <div className="
                flex-1
                space-y-1
              ">

                <FeedItemCard
                  item={item}
                  onClick={() =>
                    onSelectItem(item)
                  }

                  // 🔥 NEW
                  onToggleFavorite={() => {
                    if (!onToggleFavorite) return;

                    const targetId =
                      companyIds[0]
                      || topicIds[0]
                      || solutionIds[0];

                    if (!targetId) return;

                    onToggleFavorite(
                      targetId,
                      isFavorite
                    );
                  }}
                />

              </div>

            </div>

          );
        })}

      </div>

      {/* LOAD MORE */}

      {hasMore &&
        safeItems.length > 0 && (

        <div className="
          flex
          flex-col
          items-center
          gap-2
          pt-6
        ">

          {(loading ||
            isFetchingMore) && (

            <div className="
              text-xs
              text-gray-400
            ">
              Loading more...
            </div>

          )}

          <button
            onClick={handleLoadMore}
            disabled={
              isFetchingMore ||
              loading
            }
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

            {loading ||
            isFetchingMore
              ? "Loading…"
              : "Load more"}

          </button>

        </div>

      )}

    </div>

  );
}
