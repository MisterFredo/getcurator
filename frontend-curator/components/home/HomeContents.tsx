"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  watchLatest,
} from "@/lib/watch";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import WatchList
  from "@/components/watch/WatchList";

import type {
  WatchItem,
} from "@/types/watch";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  interlocutorId: string;
};

/* =========================================================
   CONSTANTS
========================================================= */

const HOME_CONTENT_LIMIT = 5;

/* =========================================================
   COMPONENT
========================================================= */

export default function HomeContents({
  interlocutorId,
}: Props) {

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const {
    openRightDrawer,
  } = useDrawer();

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    async function load() {

      if (!interlocutorId) {

        setItems([]);
        setTotal(0);
        return;

      }

      setLoading(
        true,
      );

      try {

        const res =
          await watchLatest({
            user_id:
              interlocutorId,

            limit:
              HOME_CONTENT_LIMIT,

            offset:
              0,
          });

        setItems(
          res.items,
        );

        setTotal(
          res.count,
        );

      } catch (e) {

        console.error(
          "❌ Home contents load error:",
          e,
        );

        setItems(
          [],
        );

        setTotal(
          0,
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, [
    interlocutorId,
  ]);

  /* =========================================================
     OPEN
  ========================================================= */

  function openContent(
    item: WatchItem,
  ) {

    openRightDrawer(
      "content",
      item.id,
    );

  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <section
      className="
        space-y-4
      "
    >

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div
        className="
          flex
          items-center
          justify-between
          gap-4
        "
      >

        <div>

          <h2
            className="
              text-base
              font-semibold
              text-gray-900
            "
          >
            Latest Contents
          </h2>

          <p
            className="
              mt-1
              text-xs
              text-gray-500
            "
          >
            The latest signals selected
            for this profile.
          </p>

        </div>

        <Link
          href="/watch"
          className="
            shrink-0
            text-xs
            font-medium
            text-gray-500
            transition
            hover:text-gray-900
          "
        >
          View all →
        </Link>

      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          overflow-hidden
        "
      >

        {loading ? (

          <div
            className="
              px-5
              py-10
              text-center
              text-sm
              text-gray-400
            "
          >
            Loading contents...
          </div>

        ) : items.length === 0 ? (

          <div
            className="
              px-5
              py-10
              text-center
              text-sm
              text-gray-400
            "
          >
            No recent contents available.
          </div>

        ) : (

          <WatchList

            title=""

            total={
              total
            }

            items={
              items
            }

            loading={
              false
            }

            hasMore={
              false
            }

            onLoadMore={() => {}}

            onSelect={
              openContent
            }

            selectedIds={
              []
            }

            onToggleSelect={() => {}}

          />

        )}

      </div>

    </section>

  );

}
