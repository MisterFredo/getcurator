"use client";

import { useMemo, useState } from "react";

import WatchCard from "@/components/watch/WatchCard";

import type {
  WatchItem,
} from "@/types/watch";

/* ========================================================= */

type Props = {

  items: WatchItem[];

  loading: boolean;

  hasMore: boolean;

  onLoadMore: () => Promise<void> | void;

  onSelect: (
    item: WatchItem,
  ) => void;

  // NEW
  selectedIds: string[];

  onToggleSelect: (
    item: WatchItem,
  ) => void;

  title?: string;

  total?: number;

};

/* ========================================================= */

export default function WatchList({

  items,

  loading,

  hasMore,

  onLoadMore,

  onSelect,

  selectedIds,

  onToggleSelect,

  title,

  total,

}: Props) {

  const [
    isFetchingMore,
    setIsFetchingMore,
  ] = useState(false);

  /* =========================================================
     SAFE ITEMS
  ========================================================= */

  const safeItems =
    useMemo(() => {

      if (!Array.isArray(items)) {

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
    ) {
      return;
    }

    try {

      setIsFetchingMore(
        true,
      );

      await onLoadMore();

    } finally {

      setIsFetchingMore(
        false,
      );

    }

  }

  /* =========================================================
     SKELETON
  ========================================================= */

  function SkeletonRow() {

    return (

      <div
        className="
          animate-pulse
          space-y-2
          py-4
          border-b
          border-gray-100
        "
      >

        <div
          className="
            h-4
            w-1/3
            rounded
            bg-gray-200
          "
        />

        <div
          className="
            h-3
            w-3/4
            rounded
            bg-gray-200
          "
        />

      </div>

    );

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      className="
        space-y-4
      "
    >

      {/* HEADER */}

      {title && (

        <div
          className="
            flex
            items-center
            justify-between
          "
        >

          <div
            className="
              text-sm
              font-semibold
              text-gray-700
            "
          >

            {title}

          </div>

          {total !== undefined && (

            <div
              className="
                text-xs
                text-gray-400
              "
            >

              {total} results

            </div>

          )}

        </div>

      )}

      {/* EMPTY */}

      {!loading &&
        safeItems.length === 0 && (

        <div
          className="
            py-16
            text-center
            text-sm
            text-gray-400
          "
        >

          No content found.

        </div>

      )}

      {/* INITIAL LOADING */}

      {loading &&
        safeItems.length === 0 && (

        <div
          className="
            space-y-3
          "
        >

          {Array.from({
            length: 5,
          }).map((_, index) => (

            <SkeletonRow
              key={index}
            />

          ))}

        </div>

      )}

      {/* ITEMS */}

      <div
        className="
          overflow-hidden
          rounded-xl
          border
          border-gray-100
          bg-white
          divide-y
          divide-gray-100
        "
      >

        {safeItems.map(

          item => (

            <WatchCard

              key={item.id}

              item={item}

              onClick={() =>
                onSelect(
                  item,
                )
              }

            />

          )

        )}

      </div>

      {/* LOAD MORE */}

      {hasMore &&
        safeItems.length > 0 && (

        <div
          className="
            flex
            flex-col
            items-center
            gap-2
            pt-6
          "
        >

          {(loading ||
            isFetchingMore) && (

            <div
              className="
                text-xs
                text-gray-400
              "
            >

              Loading...

            </div>

          )}

          <button

            onClick={
              handleLoadMore
            }

            disabled={
              loading ||
              isFetchingMore
            }

            className="
              rounded-full
              bg-black
              px-5
              py-2
              text-sm
              text-white
              transition
              hover:opacity-90
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >

            {loading ||
            isFetchingMore

              ? "Loading..."

              : "Load more"}

          </button>

        </div>

      )}

    </div>

  );

}
