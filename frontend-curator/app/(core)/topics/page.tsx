"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useEntityDrawer } from "@/hooks/useEntityDrawer";
import TopicCard from "@/components/topics/TopicCard";
import { api } from "@/lib/api";

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

function sortTopics(
  items: Topic[],
  mode: SortMode,
  favorites: string[]
) {
  const copy = [...items];

  // 🔥 PRIORITÉ FAVORIS
  copy.sort((a, b) => {
    const aFav = favorites.includes(a.id_topic);
    const bFav = favorites.includes(b.id_topic);

    if (aFav && !bFav) return -1;
    if (!aFav && bFav) return 1;
    return 0;
  });

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

function groupByUniverse(
  topics: Topic[],
  mode: SortMode,
  favorites: string[]
) {
  const map: Record<string, Topic[]> = {};

  topics.forEach((t) => {
    const u = t.universe || "Autres";

    if (!map[u]) map[u] = [];
    map[u].push(t);
  });

  Object.keys(map).forEach((u) => {
    map[u] = sortTopics(map[u], mode, favorites);
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

  const [openUniverses, setOpenUniverses] =
    useState<Record<string, boolean>>({});

  const [favorites, setFavorites] =
    useState<string[]>([]);

  const searchParams = useSearchParams();

  const { loadingId, setLoadingId } =
    useEntityDrawer(
      "topic",
      "topic_id"
    );

  /* ---------------------------------------------------------
     LOAD TOPICS
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
     LOAD PREFS
  --------------------------------------------------------- */

  useEffect(() => {

    async function loadPrefs() {

      try {

        const res = await api.get(
          "/user/preferences"
        );

        const topicPrefs =
          Array.isArray(
            res?.preferences?.TOPIC
          )
            ? res.preferences.TOPIC
            : [];

        setFavorites(topicPrefs);

      } catch (e) {

        console.error(
          "❌ prefs error",
          e
        );
      }
    }

    loadPrefs();

  }, []);

  /* ---------------------------------------------------------
     AUTO OPEN ALL UNIVERS
  --------------------------------------------------------- */

  useEffect(() => {

    if (!topics.length) return;

    const universes = Array.from(
      new Set(
        topics.map((t) => t.universe)
      )
    );

    const initial: Record<string, boolean> = {};

    universes.forEach((u) => {
      initial[u] = true;
    });

    setOpenUniverses(initial);

  }, [topics]);

  /* ---------------------------------------------------------
     AUTO OPEN CURRENT
  --------------------------------------------------------- */

  useEffect(() => {

    const topicId =
      searchParams.get("topic_id");

    if (!topicId) return;

    const topic = topics.find(
      (t) => t.id_topic === topicId
    );

    if (!topic) return;

    setOpenUniverses((prev) => ({
      ...prev,
      [topic.universe]: true,
    }));

  }, [topics, searchParams]);

  /* ---------------------------------------------------------
     FAVORITE TOGGLE
  --------------------------------------------------------- */

  async function handleToggleFavorite(
    id: string,
    isFav: boolean
  ) {

    try {

      if (isFav) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "TOPIC",
            value_id: id,
          }
        );

      } else {

        await api.post(
          "/user/preferences/add",
          {
            type: "TOPIC",
            value_id: id,
          }
        );
      }

      setFavorites((prev) =>
        isFav
          ? prev.filter((p) => p !== id)
          : [...prev, id]
      );

    } catch (e) {

      console.error(
        "❌ favorite error",
        e
      );
    }
  }

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

  const favoriteTopics = topics.filter((t) =>
    favorites.includes(t.id_topic)
  );

  const otherTopics = topics.filter((t) =>
    !favorites.includes(t.id_topic)
  );

  const grouped = groupByUniverse(
    otherTopics,
    sortMode,
    favorites
  );

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
        </div>

        <div className="flex gap-2 text-xs">

          {[
            { key: "activity", label: "Activité" },
            { key: "growth", label: "Croissance" },
            { key: "alpha", label: "A → Z" },
          ].map((s) => (

            <button
              key={s.key}
              onClick={() =>
                setSortMode(s.key as SortMode)
              }
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

      {/* ⭐ FAVORITES */}

      {!loading && favoriteTopics.length > 0 && (

        <section className="space-y-2">

          <h2 className="text-xs font-semibold uppercase text-gray-500">
            Favoris
          </h2>

          <div className="
            grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8
            gap-3
          ">

            {sortTopics(
              favoriteTopics,
              sortMode,
              favorites
            ).map((t) => {

              const isFav =
                favorites.includes(t.id_topic);

              return (

                <TopicCard
                  key={t.id_topic}
                  id={t.id_topic}
                  label={t.label}
                  nbAnalyses={t.nb_analyses}
                  delta30d={t.delta_30d}
                  isLoading={loadingId === t.id_topic}
                  onClick={() =>
                    setLoadingId(t.id_topic)
                  }

                  isFavorite={isFav}

                  onToggleFavorite={() =>
                    handleToggleFavorite(
                      t.id_topic,
                      isFav
                    )
                  }
                />

              );
            })}

          </div>

        </section>

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

            <section
              key={universe}
              className="space-y-2"
            >

              <div
                onClick={() =>
                  toggleUniverse(universe)
                }
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
                </div>

              </div>

              {openUniverses[universe] && (

                <div className="pt-2">

                  <div className="
                    grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8
                    gap-3
                  ">

                    {items.map((t) => {

                      const isFav =
                        favorites.includes(t.id_topic);

                      return (

                        <TopicCard
                          key={t.id_topic}
                          id={t.id_topic}
                          label={t.label}
                          nbAnalyses={t.nb_analyses}
                          delta30d={t.delta_30d}
                          isLoading={loadingId === t.id_topic}
                          onClick={() =>
                            setLoadingId(t.id_topic)
                          }

                          isFavorite={isFav}

                          onToggleFavorite={() =>
                            handleToggleFavorite(
                              t.id_topic,
                              isFav
                            )
                          }
                        />

                      );
                    })}

                  </div>

                </div>

              )}

            </section>

          ))}

    </div>
  );
}
