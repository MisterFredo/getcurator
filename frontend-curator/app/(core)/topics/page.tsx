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
  universe: string;

  nb_analyses: number;
  delta_30d: number;
};

type SortMode = "alpha" | "activity" | "growth";

/* =========================================================
   FETCH
========================================================= */

async function fetchTopics(): Promise<Topic[]> {
  try {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
      console.warn("❌ No user_id");
      return [];
    }

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/topic/list-for-user`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "x-user-id": userId,
        },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      console.error("❌ API ERROR:", res.status);
      return [];
    }

    const json = await res.json();

    if (json.status !== "ok") {
      console.error("❌ API BAD STATUS:", json);
      return [];
    }

    return (json.topics || []).map((t: any) => ({
      id_topic: t.id_topic ?? t.ID_TOPIC,
      label: t.label ?? t.LABEL,

      universe:
        (t.universes?.[0] &&
          (typeof t.universes[0] === "string"
            ? t.universes[0]
            : t.universes[0].label)) ||
        "Autres",

      nb_analyses: t.nb_analyses ?? t.NB_ANALYSES ?? 0,
      delta_30d: t.delta_30d ?? t.DELTA_30D ?? 0,
    }));

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
   GROUP (1:1 UNIVERSE)
========================================================= */

function groupByUniverse(topics: Topic[], mode: SortMode) {
  const map: Record<string, Topic[]> = {};

  topics.forEach((t) => {
    const u = t.universe || "Autres";

    if (!map[u]) map[u] = [];
    map[u].push(t);
  });

  Object.keys(map).forEach((u) => {
    map[u] = sortTopics(map[u], mode);
  });

  return map;
}

/* =========================================================
   PAGE
========================================================= */

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortMode, setSortMode] = useState<SortMode>("activity");

  const [openUniverses, setOpenUniverses] = useState<Record<string, boolean>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);

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
     AUTO OPEN ALL UNIVERS (UX)
  --------------------------------------------------------- */

  useEffect(() => {
    if (!topics.length) return;

    const universes = Array.from(
      new Set(topics.map((t) => t.universe))
    );

    const initial: Record<string, boolean> = {};
    universes.forEach((u) => {
      initial[u] = true;
    });

    setOpenUniverses(initial);
  }, [topics]);

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
     RESET LOADER (FIX BUG)
  --------------------------------------------------------- */

  useEffect(() => {
    const topicId = searchParams.get("topic_id");

    if (!topicId) {
      setLoadingId(null);
      return;
    }

    if (loadingId && topicId !== loadingId) {
      setLoadingId(null);
    }
  }, [searchParams]);

  /* ---------------------------------------------------------
     AUTO OPEN CURRENT UNIVERSE
  --------------------------------------------------------- */

  useEffect(() => {
    const topicId = searchParams.get("topic_id");
    if (!topicId) return;

    const topic = topics.find((t) => t.id_topic === topicId);
    if (!topic) return;

    setOpenUniverses((prev) => ({
      ...prev,
      [topic.universe]: true,
    }));
  }, [topics, searchParams]);

  /* ---------------------------------------------------------
     HELPERS
  --------------------------------------------------------- */

  function toggleUniverse(u: string) {
    setOpenUniverses((prev) => ({
      ...prev,
      [u]: !prev[u],
    }));
  }

  /* ---------------------------------------------------------
     DATA
  --------------------------------------------------------- */

  const grouped = groupByUniverse(topics, sortMode);
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
        <p className="text-sm text-gray-400 animate-pulse">
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
          .sort(([a], [b]) => {
            if (a === "Autres") return 1;
            if (b === "Autres") return -1;
            return a.localeCompare(b);
          })
          .map(([universe, items]) => (

            <section key={universe} className="space-y-2">

              {/* HEADER */}
              <div
                onClick={() => toggleUniverse(universe)}
                className="
                  flex items-center justify-between
                  cursor-pointer
                  py-2 px-1
                  border-b border-gray-100
                  hover:bg-gray-50
                "
              >
                <h2 className="text-xs font-semibold uppercase text-gray-500">
                  {universe}
                </h2>

                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>{items.length}</span>
                  <span className={`
                    transition-transform
                    ${openUniverses[universe] ? "rotate-90" : ""}
                  `}>
                    ▶
                  </span>
                </div>
              </div>

              {/* GRID */}
              {openUniverses[universe] && (
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
                        isLoading={loadingId === t.id_topic}
                        onClick={() => setLoadingId(t.id_topic)}
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
