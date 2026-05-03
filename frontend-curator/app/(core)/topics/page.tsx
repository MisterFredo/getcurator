"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useDrawer } from "@/contexts/DrawerContext";
import TopicCard from "@/components/topics/TopicCard";

export const dynamic = "force-dynamic";

/* ========================================================= */

type Topic = {
  id_topic: string;
  label: string;
  topic_axis: string;
  nb_analyses: number;
  delta_30d: number;
};

type SortMode = "alpha" | "activity" | "growth";

/* =========================================================
   FETCH
========================================================= */

async function fetchTopics(): Promise<Topic[]> {
  try {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/topic/list`,
      { cache: "no-store" }
    );

    if (!res.ok) return [];

    const json = await res.json();

    if (json.status !== "ok") return [];

    return json.topics || [];

  } catch (e) {
    console.error("❌ fetchTopics error:", e);
    return [];
  }
}

/* =========================================================
   SORT
========================================================= */

function sortTopics(items: Topic[], mode: SortMode) {
  const copy = [...items];

  switch (mode) {
    case "activity":
      return copy.sort(
        (a, b) => (b.nb_analyses ?? 0) - (a.nb_analyses ?? 0)
      );

    case "growth":
      return copy.sort(
        (a, b) => (b.delta_30d ?? 0) - (a.delta_30d ?? 0)
      );

    default:
      return copy.sort((a, b) =>
        a.label.localeCompare(b.label, "fr", {
          sensitivity: "base",
        })
      );
  }
}

/* =========================================================
   GROUP
========================================================= */

function groupByAxis(topics: Topic[], mode: SortMode) {
  const map: Record<string, Topic[]> = {};

  topics.forEach((t) => {
    if (!map[t.topic_axis]) map[t.topic_axis] = [];
    map[t.topic_axis].push(t);
  });

  Object.keys(map).forEach((axis) => {
    map[axis] = sortTopics(map[axis], mode);
  });

  return map;
}

/* =========================================================
   PAGE
========================================================= */

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortMode, setSortMode] =
    useState<SortMode>("activity");

  // 🔥 ACCORDÉON
  const [openAxis, setOpenAxis] = useState<Record<string, boolean>>({});

  const { openLeftDrawer } = useDrawer();
  const searchParams = useSearchParams();

  const lastOpenedId = useRef<string | null>(null);

  /* ---------------------------------------------------------
     LOAD
  --------------------------------------------------------- */
  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await fetchTopics();
      setTopics(data);
      setLoading(false);
    }

    load();
  }, []);

  /* ---------------------------------------------------------
     DRAWER
  --------------------------------------------------------- */
  useEffect(() => {
    const topicId = searchParams.get("topic_id");

    if (!topicId) {
      lastOpenedId.current = null;
      return;
    }

    if (lastOpenedId.current === topicId) return;

    lastOpenedId.current = topicId;
    openLeftDrawer("topic", topicId);
  }, [searchParams, openLeftDrawer]);

  /* ---------------------------------------------------------
     AUTO OPEN AXIS (deep link)
  --------------------------------------------------------- */
  useEffect(() => {
    const topicId = searchParams.get("topic_id");
    if (!topicId) return;

    const topic = topics.find((t) => t.id_topic === topicId);
    if (!topic) return;

    const axis = topic.topic_axis;

    setOpenAxis((prev) => ({
      ...prev,
      [axis]: true,
    }));
  }, [topics, searchParams]);

  /* ---------------------------------------------------------
     HELPERS
  --------------------------------------------------------- */

  function toggleAxis(axis: string) {
    setOpenAxis((prev) => ({
      ...prev,
      [axis]: !prev[axis],
    }));
  }

  /* ---------------------------------------------------------
     DATA
  --------------------------------------------------------- */

  const grouped = groupByAxis(topics, sortMode);
  const hasContent = topics.length > 0;

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="space-y-8">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Topics
          </h1>
          <p className="text-sm text-gray-500">
            Cartographie des dynamiques du marché
          </p>
        </div>

        {/* SORT */}
        <div className="flex gap-2 text-xs">
          {[
            { key: "activity", label: "Activité" },
            { key: "growth", label: "Croissance" },
            { key: "alpha", label: "A → Z" },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => setSortMode(s.key as SortMode)}
              className={`
                px-3 py-1 rounded border
                ${
                  sortMode === s.key
                    ? "bg-teal-600 text-white border-teal-600"
                    : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                }
              `}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* LOADING */}
      {loading && (
        <p className="text-sm text-gray-400">
          Chargement des topics...
        </p>
      )}

      {/* EMPTY */}
      {!loading && !hasContent && (
        <p className="text-sm text-gray-400">
          Aucun topic disponible.
        </p>
      )}

      {/* CONTENT */}
      {!loading && hasContent &&
        Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([axis, items]) => (

            <section key={axis} className="space-y-2">

              {/* HEADER ACCORDÉON */}
              <div
                onClick={() => toggleAxis(axis)}
                className="
                  flex items-center justify-between
                  cursor-pointer
                  py-2 px-1
                  border-b border-gray-100
                  hover:bg-gray-50
                "
              >
                <h2 className="text-xs font-semibold uppercase text-gray-500">
                  {axis}
                </h2>

                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>{items.length}</span>
                  <span
                    className={`
                      transition-transform
                      ${openAxis[axis] ? "rotate-90" : ""}
                    `}
                  >
                    ▶
                  </span>
                </div>
              </div>

              {/* GRID */}
              {openAxis[axis] && (
                <div className="pt-2">
                  <div className="
                    grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8
                    gap-3
                  ">
                    {items.map((t) => (
                      <TopicCard
                        key={t.id_topic}
                        id={t.id_topic}
                        label={t.label}
                        nbAnalyses={t.nb_analyses}
                        delta30d={t.delta_30d}
                      />
                    ))}
                  </div>
                </div>
              )}

            </section>
          ))}

    </div>
  );
}
