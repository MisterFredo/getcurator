"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  BarChart3,
  ArrowUpRight,
} from "lucide-react";

import {
  getHomeNumbers,
} from "@/lib/numbers";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import type {
  PublicNumber,
} from "@/types/numbers";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  interlocutorId: string;
};

/* =========================================================
   CONFIG
========================================================= */

const HOME_NUMBERS_LIMIT = 10;

/* =========================================================
   FORMAT
========================================================= */

function formatNumber(
  item: PublicNumber,
): string {

  const formatter =
    new Intl.NumberFormat(
      "en-US",
      {
        maximumFractionDigits: 2,
      },
    );

  let value = "";

  if (
    item.value !== null
    && item.value !== undefined
  ) {

    value = formatter.format(
      item.value,
    );

  } else if (
    item.value_min !== null
    && item.value_max !== null
  ) {

    value = (
      `${formatter.format(item.value_min)}`
      + "–"
      + `${formatter.format(item.value_max)}`
    );

  } else if (
    item.value_min !== null
  ) {

    value =
      `≥ ${formatter.format(item.value_min)}`;

  } else if (
    item.value_max !== null
  ) {

    value =
      `≤ ${formatter.format(item.value_max)}`;

  }

  return [
    value,
    item.scale,
    item.unit,
  ]
    .filter(Boolean)
    .join(" ");

}

/* =========================================================
   COMPONENT
========================================================= */

export default function HomeNumbers({
  interlocutorId,
}: Props) {

  const [
    items,
    setItems,
  ] = useState<PublicNumber[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState(false);

  const {
    openRightDrawer,
  } = useDrawer();

  /* ========================================================
     LOAD
  ======================================================== */

  useEffect(() => {

    let cancelled = false;

    setItems([]);

    setError(false);

    if (!interlocutorId) {

      setLoading(false);

      return () => {
        cancelled = true;
      };

    }

    setLoading(true);

    getHomeNumbers(
      interlocutorId,
      HOME_NUMBERS_LIMIT,
    )
      .then(response => {

        if (cancelled) {
          return;
        }

        setItems(
          response.items ?? [],
        );

      })
      .catch(loadError => {

        if (cancelled) {
          return;
        }

        console.error(
          "Unable to load home Numbers:",
          loadError,
        );

        setItems([]);

        setError(true);

      })
      .finally(() => {

        if (!cancelled) {
          setLoading(false);
        }

      });

    return () => {
      cancelled = true;
    };

  }, [
    interlocutorId,
  ]);

  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <section className="space-y-4">

      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >

        <div>

          <div
            className="
              flex
              items-center
              gap-2
            "
          >

            <BarChart3
              size={18}
              className="text-emerald-700"
            />

            <h2
              className="
                text-base
                font-semibold
                text-gray-900
              "
            >
              Numbers
            </h2>

          </div>

          <p
            className="
              mt-1
              text-xs
              text-gray-500
            "
          >
            Validated figures selected
            for this profile.
          </p>

        </div>

        <Link
          href="/numbers"
          className="
            flex
            shrink-0
            items-center
            gap-1
            text-xs
            font-medium
            text-gray-500
            transition
            hover:text-gray-900
          "
        >
          View all

          <ArrowUpRight size={14} />
        </Link>

      </div>

      <div
        className="
          overflow-hidden
          rounded-xl
          border
          border-gray-200
          bg-white
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
            Loading Numbers...
          </div>

        ) : error ? (

          <div
            className="
              px-5
              py-10
              text-center
              text-sm
              text-gray-500
            "
          >
            Unable to load Numbers.
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
            No validated Numbers available
            for this profile.
          </div>

        ) : (

          <div className="divide-y divide-gray-100">

            {items.map(item => (

              <button
                key={item.id_number}
                type="button"
                disabled={!item.id_content}
                onClick={() => {

                  if (!item.id_content) {
                    return;
                  }

                  openRightDrawer(
                    "content",
                    item.id_content,
                    "silent",
                  );

                }}
                className="
                  block
                  w-full
                  px-5
                  py-4
                  text-left
                  transition
                  hover:bg-emerald-50/50
                  disabled:cursor-default
                "
              >

                <div
                  className="
                    text-lg
                    font-semibold
                    text-gray-900
                  "
                >
                  {formatNumber(item)}
                </div>

                <div
                  className="
                    mt-1
                    text-sm
                    leading-5
                    text-gray-700
                  "
                >
                  {item.label}
                </div>

                <div
                  className="
                    mt-2
                    flex
                    flex-wrap
                    gap-x-2
                    gap-y-1
                    text-xs
                    text-gray-500
                  "
                >

                  {item.entities
                    ?.slice(0, 2)
                    .map(entity => (
                      <span
                        key={
                          entity.entity_type
                          + ":"
                          + entity.entity_id
                        }
                      >
                        {entity.entity_label}
                      </span>
                    ))}

                  {item.zone && (
                    <span>
                      {item.zone}
                    </span>
                  )}

                  {item.period_label && (
                    <span>
                      {item.period_label}
                    </span>
                  )}

                </div>

                {item.content?.title && (

                  <div
                    className="
                      mt-2
                      truncate
                      text-xs
                      text-gray-400
                    "
                  >
                    {item.content.title}
                  </div>

                )}

              </button>

            ))}

          </div>

        )}

      </div>

    </section>

  );

}
