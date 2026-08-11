"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import WatchCard from "@/components/watch/WatchCard";

import type {
  WatchItem,
} from "@/types/watch";

/* =========================================================
   TYPES
========================================================= */

type Props = {

  items: WatchItem[];

  loading: boolean;

  hasMore: boolean;

  onLoadMore: () => Promise<void> | void;

  onSelect: (
    item: WatchItem,
  ) => void;

  selectedIds: string[];

  onToggleSelect: (
    item: WatchItem,
  ) => void;

  title?: string;

  total?: number;

};

/* =========================================================
   HELPERS
========================================================= */

function getMonthKey(
  date?: string | null,
) {

  if (!date) {

    return "unknown";

  }

  const parsed =
    new Date(
      date,
    );

  if (
    Number.isNaN(
      parsed.getTime(),
    )
  ) {

    return "unknown";

  }

  return `${parsed.getFullYear()}-${String(
    parsed.getMonth() + 1,
  ).padStart(2, "0")}`;

}


function formatMonthLabel(
  key: string,
) {

  if (
    key === "unknown"
  ) {

    return "Autres";

  }

  const [
    year,
    month,
  ] = key
    .split("-")
    .map(Number);

  const date =
    new Date(
      year,
      month - 1,
      1,
    );

  return date
    .toLocaleDateString(
      "fr-FR",
      {
        month: "long",
        year: "numeric",
      },
    )
    .toUpperCase();

}

/* =========================================================
   COMPONENT
========================================================= */

export default function WatchGroupedByMonth({

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
    openMonth,
    setOpenMonth,
  ] = useState<string | null>(
    null,
  );

  const [
    isFetchingMore,
    setIsFetchingMore,
  ] = useState(false);

  /* =========================================================
     SAFE ITEMS
  ========================================================= */

  const safeItems =
    useMemo(() => {

      if (
        !Array.isArray(
          items,
        )
      ) {

        return [];

      }

      return items;

    }, [
      items,
    ]);

  /* =========================================================
     GROUP BY MONTH
  ========================================================= */

  const grouped =
    useMemo(() => {

      const map:
        Record<
          string,
          WatchItem[]
        > = {};

      safeItems.forEach(
        (item) => {

          const key =
            getMonthKey(
              item.published_at,
            );

          if (
            !map[key]
          ) {

            map[key] = [];

          }

          map[key].push(
            item,
          );

        },
      );

      return Object
        .entries(
          map,
        )
        .sort(
          ([a], [b]) => {

            if (
              a === "unknown"
            ) {

              return 1;

            }

            if (
              b === "unknown"
            ) {

              return -1;

            }

            return b.localeCompare(
              a,
            );

          },
        );

    }, [
      safeItems,
    ]);

  /* =========================================================
     OPEN FIRST MONTH
  ========================================================= */

  useEffect(() => {

    if (
      grouped.length === 0
    ) {

      setOpenMonth(
        null,
      );

      return;

    }

    setOpenMonth(
      (previous) => {

        if (
          previous
          && grouped.some(
            ([key]) =>
              key === previous,
          )
        ) {

          return previous;

        }

        return grouped[0][0];

      },
    );

  }, [
    grouped,
  ]);

  /* =========================================================
     TOGGLE MONTH
  ========================================================= */

  function toggleMonth(
    key: string,
  ) {

    setOpenMonth(
      (previous) =>
        previous === key
          ? null
          : key,
    );

  }

  /* =========================================================
     LOAD MORE
  ========================================================= */

  async function handleLoadMore() {

    if (
      loading
      || isFetchingMore
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

      <div className="
        animate-pulse
        space-y-2
        py-4
        border-b
        border-gray-100
      ">

        <div className="
          h-4
          w-1/3
          rounded
          bg-gray-200
        " />

        <div className="
          h-3
          w-3/4
          rounded
          bg-gray-200
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

      {/* HEADER */}

      {title && (

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

      )}

      {/* INITIAL LOADING */}

      {loading
        && safeItems.length === 0
        && (

        <div className="
          space-y-3
        ">

          {Array
            .from({
              length: 5,
            })
            .map(
              (_, index) => (

                <SkeletonRow
                  key={index}
                />

              ),
            )}

        </div>

      )}

      {/* EMPTY */}

      {!loading
        && safeItems.length === 0
        && (

        <div className="
          py-16
          text-center
          text-sm
          text-gray-400
        ">

          No content found.

        </div>

      )}

      {/* MONTHS */}

      {grouped.map(
        ([
          monthKey,
          monthItems,
        ]) => {

          const isOpen =
            openMonth === monthKey;

          return (

            <section
              key={
                monthKey
              }
              className="
                space-y-2
              "
            >

              <button

                type="button"

                onClick={() =>
                  toggleMonth(
                    monthKey,
                  )
                }

                className="
                  w-full
                  flex
                  items-center
                  justify-between
                  text-left
                  py-2
                  border-b
                  border-gray-100
                  hover:opacity-80
                  transition
                "

              >

                <span className="
                  text-xs
                  font-semibold
                  text-gray-500
                  uppercase
                  tracking-wide
                ">

                  {formatMonthLabel(
                    monthKey,
                  )}

                </span>

                <div className="
                  flex
                  items-center
                  gap-3
                ">

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {monthItems.length}

                  </span>

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {
                      isOpen
                        ? "−"
                        : "+"
                    }

                  </span>

                </div>

              </button>

              {isOpen && (

                <div className="
                  overflow-hidden
                  rounded-xl
                  border
                  border-gray-100
                  bg-white
                  divide-y
                  divide-gray-100
                ">

                  {monthItems.map(
                    (item) => (

                      <WatchCard

                        key={
                          item.id
                        }

                        item={
                          item
                        }

                        onClick={() =>
                          onSelect(
                            item,
                          )
                        }

                        selected={
                          selectedIds.includes(
                            item.id,
                          )
                        }

                        onToggleSelect={
                          onToggleSelect
                        }

                      />

                    ),
                  )}

                </div>

              )}

            </section>

          );

        },
      )}

      {/* LOAD MORE */}

      {hasMore
        && safeItems.length > 0
        && (

        <div className="
          flex
          flex-col
          items-center
          gap-2
          pt-4
        ">

          {(loading
            || isFetchingMore)
            && (

            <div className="
              text-xs
              text-gray-400
            ">

              Loading...

            </div>

          )}

          <button

            type="button"

            onClick={
              handleLoadMore
            }

            disabled={
              loading
              || isFetchingMore
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

            {
              loading
              || isFetchingMore
                ? "Loading..."
                : "Load more"
            }

          </button>

        </div>

      )}

    </div>

  );

}
