"use client";

import { useMemo, useState } from "react";

import FeedItemCard from "./FeedItemCard";

/* ========================================================= */

type FeedItem = {

  id: string;

  title: string;

  excerpt?: string | null;

  published_at?: string;

  topics?: any[];

  companies?: any[];

  solutions?: any[];
};

type Props = {

  items: FeedItem[];

  onClickItem: (
    item: FeedItem
  ) => void;

  userLang: string;
};

/* =========================================================
   HELPERS
========================================================= */

function getMonthKey(
  date?: string
) {

  if (!date)
    return "unknown";

  const d = new Date(date);

  return `${d.getFullYear()}-${d.getMonth()}`;
}

function formatMonthLabel(
  key: string
) {

  if (key === "unknown")
    return "Autres";

  const [year, month] =
    key
      .split("-")
      .map(Number);

  const date =
    new Date(year, month);

  return date
    .toLocaleDateString(
      "fr-FR",
      {
        month: "long",
        year: "numeric",
      }
    )
    .toUpperCase();
}

/* =========================================================
   COMPONENT
========================================================= */

export default function FeedGroupedByMonth({

  items,

  onClickItem,

  userLang,

}: Props) {

  /* =========================================================
     GROUPING
  ========================================================= */

  const grouped =
    useMemo(() => {

      const map:
        Record<
          string,
          FeedItem[]
        > = {};

      items.forEach((item) => {

        const key =
          getMonthKey(
            item.published_at
          );

        if (!map[key]) {

          map[key] = [];
        }

        map[key].push(item);

      });

      return Object
        .entries(map)

        .sort((a, b) => {

          if (a[0] === "unknown")
            return 1;

          if (b[0] === "unknown")
            return -1;

          return b[0]
            .localeCompare(a[0]);

        });

    }, [items]);

  /* =========================================================
     ACCORDION STATE
  ========================================================= */

  const [
    openMonth,
    setOpenMonth
  ] = useState<
    string | null
  >(
    grouped.length > 0
      ? grouped[0][0]
      : null
  );

  function toggleMonth(
    key: string
  ) {

    setOpenMonth(
      (prev) =>

        prev === key
          ? null
          : key
    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      space-y-6
    ">

      {grouped.map(
        ([monthKey, monthItems]) => {

          const isOpen =
            openMonth === monthKey;

          return (

            <div
              key={monthKey}
              className="
                space-y-2
              "
            >

              {/* =====================================================
                  HEADER (ACCORDION)
              ===================================================== */}

              <button
                onClick={() =>
                  toggleMonth(monthKey)
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
                    monthKey
                  )}

                </span>

                <div className="
                  flex
                  items-center
                  gap-3
                ">

                  {/* 🔥 COUNT */}

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {monthItems.length}

                  </span>

                  {/* ARROW */}

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {isOpen
                      ? "−"
                      : "+"}

                  </span>

                </div>

              </button>

              {/* =====================================================
                  CONTENT
              ===================================================== */}

              {isOpen && (

                <div className="
                  space-y-3
                  pt-2
                ">

                  {monthItems.map(
                    (item) => (

                      <FeedItemCard
                        key={item.id}

                        userLang={
                          userLang
                        }

                        item={item}

                        onClick={() =>
                          onClickItem(item)
                        }
                      />

                    )
                  )}

                </div>

              )}

            </div>

          );
        }
      )}

    </div>
  );
}
